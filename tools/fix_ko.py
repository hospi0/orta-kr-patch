"""번역문 자동 보정 — 검사기가 잡은 문제를 고쳐 `trans/ko.json` 에 되쓴다.

  python fix_ko.py            # 보고만
  python fix_ko.py --apply    # 실제로 고친다 (ko.json.bak 백업)

고치는 것
  1. cp932 로 못 넣는 문자 치환   · -> ・ / — -> ― 등
  2. 지정한 개행 복원             (원문에 있는데 번역에서 빠진 자리)
  3. 파일 예산 초과 -> 조판만 조인다
       ① 줄 끝 마침표 제거(2B)
       ② 공백을 반각으로(1B 절약) — ★낱말은 그대로 떨어진다
     ⛔문장은 건드리지 않는다. 두 단계로도 모자라면 그 파일을 보고만 하고 멈춘다.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS
import check_ko as K

KO = os.path.join(TRANS, 'ko.json')
BUDGET = os.path.join(TRANS, 'budget.json')

# 1. 못 넣는 문자 -> 대체
SUBST = {
    '·': '・',    # ·  가운뎃점 -> ・
    '—': '―',    # —  em dash -> ―
    '–': '―',    # –
    '…': '…',    # …  (cp932 에 있다)
}

# 2. 개행 복원: (파일 꼬리, 항목번호, 이 문자열 «뒤»에 개행을 넣는다)
NEWLINE_FIX = [
    ('MesData_Stage04_JP.msg', 13, '딸은 나중에 챙긴다!'),
]

HALF_SP = ' '


import re

# 한자 병기 — 「제도(帝都)」 처럼 괄호 안이 전부 한자인 것. 화면에서 군더더기이고
# 한자마다 글리프 칸까지 잡아먹는다.
KANJI_PAREN = re.compile(r'[（(]\s*[㐀-鿿]+\s*[)）]')


def fix_chars(t):
    t = KANJI_PAREN.sub('', t)
    out = []
    for c in t:
        out.append(SUBST.get(c, c))
    return ''.join(out)


# ★축약 1단계 — 문장부호 «뒤 공백»만 지운다. 부호는 그대로 둔다(쉼표 포함).
#   → [[feedback_removing_space_after_comma_looks_like_added_commas]]
PUNCT_SP = re.compile(r'([,\.!\?:;，。、！？：；」』）\)])[ 　 ]')


def drop_space_after_punct(t):
    """부호 뒤 공백을 «한 개» 지운다. 못 하면 None."""
    m = PUNCT_SP.search(t)
    if not m:
        return None
    return t[:m.end() - 1] + t[m.end():]


def trim_period(t):
    """줄 끝 마침표 하나 제거. 못 하면 None."""
    lines = t.split('\n')
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].endswith(('.', '。')):
            lines[i] = lines[i][:-1]
            return '\n'.join(lines)
    return None


def trim_space(t):
    """뒤에서부터 공백 하나를 반각으로. 못 하면 None."""
    for sp in ('　', ' '):
        j = t.rfind(sp)
        if j >= 0:
            return t[:j] + HALF_SP + t[j + 1:]
    return None


def main():
    apply = '--apply' in sys.argv
    corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
    ko = json.load(open(KO, encoding='utf-8'))
    budget = json.load(open(BUDGET, encoding='utf-8'))

    log = []

    # --- 1. 문자 치환 ---
    n = 0
    for rel, d in ko.items():
        for k, t in list(d.items()):
            f = fix_chars(t)
            if f != t:
                d[k] = f
                n += 1
                log.append('문자치환 %s idx%s' % (os.path.basename(rel), k))
    print('1. 문자 치환 %d항목' % n)

    # --- 2. 개행 복원 ---
    n = 0
    for tail, idx, after in NEWLINE_FIX:
        for rel, d in ko.items():
            if not rel.endswith(tail):
                continue
            t = d.get(str(idx))
            if t and after in t and '\n' not in t:
                d[str(idx)] = t.replace(after + ' ', after + '\n', 1) \
                    if after + ' ' in t else t.replace(after, after + '\n', 1)
                n += 1
                log.append('개행복원 %s idx%d' % (tail, idx))
    print('2. 개행 복원 %d항목' % n)

    # --- 3. 예산 맞추기 ---
    print('3. 예산 조정')
    for rel in sorted(ko):
        tot = budget.get(rel, {}).get('total')
        if tot is None:
            continue
        ent = {str(e['idx']): e for e in corpus[rel]}

        def used():
            s = 0
            for e in corpus[rel]:
                t = ko[rel].get(str(e['idx']))
                s += K.nbytes(t) if t else e['bytes']
            return s

        u = used()
        if u <= tot:
            continue
        need = u - tot
        print('   %-38s %+dB 초과 -> 조정' % (os.path.basename(rel), need))
        cuts = {'부호뒤공백': 0, '줄끝마침표': 0, '반각공백': 0}
        steps = [(drop_space_after_punct, '부호뒤공백', 2), (trim_period, '줄끝마침표', 2)]
        if '--halfsp' in sys.argv:
            steps.append((trim_space, '반각공백', 1))
        for fn, tag, gain in steps:  # noqa
            _ignore = ((drop_space_after_punct, '부호뒤공백', 2),
                              (trim_period, '줄끝마침표', 2))
            changed = True
            while used() > tot and changed:
                changed = False
                for k in sorted(ko[rel], key=lambda x: -len(ko[rel][x])):
                    r = fn(ko[rel][k])
                    if r is not None and K.nbytes(r) < K.nbytes(ko[rel][k]):
                        ko[rel][k] = r
                        cuts[tag] += 1
                        changed = True
                        if used() <= tot:
                            break
        left = tot - used()
        print('      부호뒤공백 %d · 줄끝마침표 %d · 반각공백 %d -> 남음 %dB %s'
              % (cuts['부호뒤공백'], cuts['줄끝마침표'], cuts['반각공백'], left,
                 '' if left >= 0 else '★여전히 초과 — 문장을 줄여야 합니다'))

    if apply:
        shutil.copy2(KO, KO + '.bak')
        with open(KO, 'w', encoding='utf-8', newline='') as f:
            json.dump(ko, f, ensure_ascii=False, indent=1)
        print('\n적용 완료 -> %s (백업 %s)' % (KO, KO + '.bak'))
    else:
        print('\n※ 보고만 했습니다. 반영하려면 --apply')
    return 0


if __name__ == '__main__':
    sys.exit(main())
