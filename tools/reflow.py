"""번역문 줄바꿈 재정렬 — 원문과 «같은 줄 수»로 다시 흘린다.

  python reflow.py            # 보고만
  python reflow.py --apply

원문은 창 폭에 맞춰 손으로 줄을 나눠 놨다. 번역문이 그보다 줄이 많으면 창을 넘치고,
적으면 문단이 성겨 보인다. 문장은 «한 글자도» 건드리지 않고 줄바꿈 위치만 옮긴다.

규칙
  · 문단 시작 = 줄 첫 글자가 전각 공백(　). 그 표시는 그대로 살린다.
  · 빈 줄은 빈 줄로 남긴다(문단 사이 간격).
  · 제어코드 `$c0` `$w0020` 는 **폭 0** 으로 센다(화면에 안 보인다).
  · 줄 폭 상한 = 그 항목 «원문»의 최대 줄 폭. 그래도 줄이 넘치면 상한을 조금씩 올린다.
"""
import json
import os
import re
import shutil
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS
import check_ko as K

KO = os.path.join(TRANS, 'ko.json')
CODE = re.compile(r'\$[cw]\d+')
HALF = K.HALF_SP          # U+00A0 = 본문 안 «반각 공백» 표식


def _word(ch):
    """낱말 글자(한글·영숫자)인가 — 줄을 합칠 때 공백이 필요한지 가른다."""
    return K.is_hangul(ch) or ch.isalnum()


def width(s):
    """화면 폭(반각 칸 수). 제어코드는 0."""
    s = CODE.sub('', s)
    return sum(2 if unicodedata.east_asian_width(c) in 'WFA' else 1 for c in s)


def paragraphs(lines):
    """[(선두표시, 본문)] — 선두표시는 '　' 또는 ''. 빈 줄은 (None, '')."""
    out = []
    for ln in lines:
        if ln == '':
            out.append([None, ''])
        elif ln.startswith('　') or not out or out[-1][0] is None:
            out.append(['　' if ln.startswith('　') else '', ln.lstrip('　')])
        else:
            # ★★줄을 합칠 때 «끊긴 자리의 공백»을 되살린다.
            #   원문의 줄바꿈은 낱말 경계다. 그냥 이어 붙이면 `Tutorial1-1드래곤`
            #   처럼 낱말이 붙어 버리고, 다시 접을 자리도 사라진다.
            #   부호 옆이면 넣지 않는다(이 프로젝트 규칙 = 부호 뒤 공백 삭제).
            a = out[-1][1][-1:]
            b = ln[:1]
            join = HALF if a and b and _word(a) and _word(b) else ''
            out[-1][1] += join + ln
    return out


def wrap(text, limit, first_indent=''):
    """폭 limit 로 접는다. 공백·부호 뒤에서 우선 끊는다."""
    if not text:
        return ['']
    lines = []
    cur = first_indent
    i = 0
    while i < len(text):
        m = CODE.match(text, i)
        tok = m.group(0) if m else text[i]
        if width(cur + tok) > limit and width(cur.strip()) > 0:
            # 뒤에서부터 끊기 좋은 자리를 찾는다
            # ★★U+00A0(반각 공백 표식)도 «끊을 자리»다.
            #   2026-08-31 실기: 이걸 빠뜨려 `Tutorial1-1드 / 래곤 이동` 처럼
            #   낱말 한가운데가 끊겼다(halfsp.py 로 공백을 전부 U+00A0 로 바꾼 뒤).
            cut = max(cur.rfind(' '), cur.rfind('　'), cur.rfind(' '))
            if cut > len(first_indent):
                lines.append(cur[:cut].rstrip())
                cur = cur[cut + 1:]
            else:
                lines.append(cur)
                cur = ''
        cur += tok
        i += len(tok)
    if cur.strip():
        lines.append(cur)
    return lines or ['']


def reflow(ko_text, jp_text, width_first=False, box=None):
    """box = «파일 전체» 원문 최대 줄 폭. 주면 그걸 상한으로 쓴다.

    ★한 항목의 원문 폭은 그 문장이 우연히 짧았을 뿐일 수 있다. 같은 화면을 쓰는
      파일 안에서 «가장 넓은 원문 줄»이 창 폭의 하한이고, 그게 진짜 상한에 가깝다.
      (Tutorial: 항목별 28 vs 파일 전체 40 — 이 차이 때문에 줄이 3줄로 늘어났다)

    width_first=True 면 «줄 폭»을 상한에 맞추고 줄 수는 늘어나도 둔다.
    ★줄 폭이 원문을 넘으면 화면 밖으로 잘린다. 폭이 줄 수보다 우선이다.
    """
    jl = jp_text.split('\n')
    target = len(jl)
    limit0 = box if box else max(width(x) for x in jl)
    paras = paragraphs(ko_text.split('\n'))

    def build(limit):
        out = []
        for head, body in paras:
            if head is None:
                out.append('')
                continue
            out += wrap(body, limit, head)
        return out

    if width_first or box:
        # ★상한을 넘기지 않는다 — 넘치면 화면 밖으로 잘린다
        return '\n'.join(build(limit0)), limit0
    for limit in range(limit0, limit0 + 13):
        out = build(limit)
        if len(out) <= target:
            # 줄이 모자라면 빈 줄로 채우지 않는다 — 적은 건 안전하다
            return '\n'.join(out), limit
    return None, None


def main():
    apply = '--apply' in sys.argv
    ko = json.load(open(KO, encoding='utf-8'))
    items = {(i['file'], i['idx']): i for i in K.load()}
    box_mode = '--box' in sys.argv
    boxw = {}
    # ★--boxw=N : 상자 폭을 «직접» 준다.
    #   ⛔파일 안 최대 원문폭으로 잡으면 안 되는 화면이 있다 — 도감은 항목마다 폭이
    #     같은 상자를 쓰는데, 파일 최대(42)로 잡으면 41칸짜리가 화면 밖으로 나간다.
    #     실측(2026-08-31 스샷 픽셀): 도감 상자는 약 38칸.
    force = None
    for a in sys.argv[1:]:
        if a.startswith('--boxw='):
            force = int(a.split('=', 1)[1])
    if box_mode:
        for (rel0, _i0), it0 in items.items():
            w0 = max(width(x) for x in it0['jp'].splitlines() or [''])
            boxw[rel0] = max(boxw.get(rel0, 0), w0)
        if force:
            for rel0 in list(boxw):
                if 'pdb_db' in rel0:
                    boxw[rel0] = force
    fixed = fail = 0
    saved = 0
    for rel, d in ko.items():
        for k, t in list(d.items()):
            it = items.get((rel, int(k)))
            if it is None:
                continue
            jp = it['jp']
            wf = '--width' in sys.argv
            bw = boxw.get(rel) if box_mode else None
            if box_mode:
                # ★멀쩡한 항목은 건드리지 않는다 — 문제가 있는 것만 다시 흘린다.
                #   문제 = 원문보다 줄이 많거나(상자 침범), 어느 줄이 창 폭을 넘거나(가로 잘림)
                bad = (t.count('\n') > jp.count('\n')
                       or max(width(x) for x in t.split('\n')) > bw)
                if not bad:
                    continue
            elif not wf and jp.count('\n') == t.count('\n'):
                continue
            new, limit = reflow(t, jp, width_first=wf, box=bw)
            if new is not None and new == t:
                continue
            if new is None:
                fail += 1
                print('  ★%s idx%s 못 맞춤 (원문 %d줄)'
                      % (os.path.basename(rel), k, jp.count('\n') + 1))
                continue
            if CODE.findall(new) != CODE.findall(t):
                fail += 1
                print('  ★%s idx%s 제어코드가 변함 — 건너뜀' % (os.path.basename(rel), k))
                continue
            g = K.nbytes(t) - K.nbytes(new)
            saved += g
            fixed += 1
            print('  %-28s idx%-4s %d줄 -> %d줄 (원문 %d줄, 폭%d) %+dB'
                  % (os.path.basename(rel), k, t.count('\n') + 1,
                     new.count('\n') + 1, jp.count('\n') + 1, limit, -g))
            if apply:
                d[k] = new
    print('\n정리 %d건 / 실패 %d건 / %+dB' % (fixed, fail, -saved))
    if apply:
        # ⛔고정 이름이면 이전 백업을 덮는다 — 안 겹치는 이름으로.
        bak = KO + '.bak_reflow'
        i = 0
        while os.path.exists(bak):
            i += 1
            bak = KO + '.bak_reflow%d' % i
        shutil.copy2(KO, bak)
        print('백업 -> %s' % os.path.basename(bak))
        with open(KO, 'w', encoding='utf-8', newline='') as f:
            json.dump(ko, f, ensure_ascii=False, indent=1)
        print('적용 -> %s' % KO)
    else:
        print('※ 보고만. 반영하려면 --apply')


if __name__ == '__main__':
    main()
