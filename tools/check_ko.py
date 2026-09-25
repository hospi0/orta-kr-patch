"""번역문 검사 — 예산·제어코드·개행·글리프 칸을 한 번에 검산한다.

사용:
    python check_ko.py            # trans/corpus_parts/*.json 전부 검사
    python check_ko.py part_003   # 조각 하나만

검사 항목
  1. 파일별 바이트 예산   (밀어쓰기 가능 -> «파일 단위» 총량으로 본다)
  2. 제어코드 보존        $c# / $w####  — 개수와 값이 원문과 같은가
  3. 개행 수 보존         \n 이 줄면 조판이 무너지고 늘면 상자를 넘친다
  4. 글리프 칸            장면별 고유 한글 음절 수 <= 그 아틀라스 칸 수
  5. 쓸 수 없는 문자      cp932 로 못 넣는 기호

바이트 셈법 (빌더와 동일)
  한글 2 / 전각 2 / 반각 1 / \n 1
  ★반각 공백과 마침표는 빌더가 전각으로 바꾼다 -> 각 2바이트
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import FONT_DIR, TRANS, pristine
from atlaswrite import Atlas, CELLS_PER_PAGE
from ztbl import ZTbl

PARTS = os.path.join(TRANS, 'corpus_parts')
BUDGET = os.path.join(TRANS, 'budget.json')
CODE = re.compile(r'\$[cw]\d+')

# 파일 -> 그 화면이 쓰는 아틀라스(추정). ★실기로 확정된 것은 MenuInst=Common 뿐이다.
SCENE = {
    'Text_MenuInst': 'Common', 'Text_comment': 'Menu',
    'text_pdb_db_creature': 'Menu', 'text_pdb_db_empire': 'Menu',
    'text_pdb_db_world': 'Menu', 'Text_Movie': 'Movie',
    'Text_OpeningDemo': 'OpeningDemo', 'MesData_Tutorial': 'Tutorial',
    'Text_SubScenarioControl': 'SubScenario01',
    # ★548음절이라 324칸 아틀라스엔 못 들어간다. 판도라의 상자 맥락이라 Menu 로 잡는다(추정).
    'Text_SubScenarioDemo': 'Menu',
}


def scene_of(rel):
    b = os.path.basename(rel)[:-7]
    if b in SCENE:
        return SCENE[b]
    m = re.match(r'MesData_Stage(\d+)', b)
    if m:
        return 'Stage%d' % int(m.group(1))
    m = re.match(r'MesData_ms(\d)', b)
    if m:
        return 'Mission0%s' % m.group(1)
    m = re.match(r'MesData_sst(\d)', b)
    if m:
        return 'SubScenario0%s' % m.group(1)
    return None


HALF_SP = ' '   # 본문 안에서 «반각 공백(1B)»을 뜻하는 표식


def is_hangul(c):
    return 0xac00 <= ord(c) <= 0xd7a3


def nbytes(t):
    """빌더가 기록할 바이트 수."""
    n = 0
    for c in t:
        if c == '\n':
            n += 1
        elif c == HALF_SP:           # 반각 공백 표식 — 1바이트로 나간다
            n += 1
        elif is_hangul(c):
            n += 2
        elif c in ' .':          # 빌더가 전각으로 바꾼다
            n += 2
        else:
            try:
                n += len(c.encode('cp932'))
            except Exception:
                n += 2           # 못 넣는 문자 — 별도로 보고한다
    return n


def bad_chars(t):
    out = set()
    for c in t:
        if c in ('\n', HALF_SP) or is_hangul(c):
            continue
        try:
            c.encode('cp932')
        except Exception:
            out.add(c)
    return out


def atlas_cap(scene):
    f = os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % scene)
    tbl = os.path.join(FONT_DIR, 'Reisyo_Cmn_z_tbl_cmn.bin' if scene == 'Common'
                       else 'Reisyo_%s_z_tbl.bin' % scene)
    if not (os.path.exists(f) and os.path.exists(tbl)):
        return None
    a = Atlas(pristine(f))
    n = a.pages * CELLS_PER_PAGE
    used = {g for g in ZTbl(pristine(tbl)).mapping().values() if g < n}
    return n, len(used)


def load(only=None):
    """코퍼스 전체 + 병합된 번역(trans/ko.json). only 를 주면 그 파일만."""
    corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
    kop = os.path.join(TRANS, 'ko.json')
    ko = json.load(open(kop, encoding='utf-8')) if os.path.exists(kop) else {}
    items = []
    for rel in sorted(corpus):
        if only and only not in rel:
            continue
        for e in corpus[rel]:
            items.append({'file': rel, 'idx': e['idx'], 'budget': e['bytes'],
                          'jp': e['jp'], 'ko': ko.get(rel, {}).get(str(e['idx']))})
    return items


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    items = load(only)
    if not items:
        print('조각을 못 찾았습니다: %s' % PARTS)
        return 1
    budget = json.load(open(BUDGET, encoding='utf-8')) if os.path.exists(BUDGET) else {}

    done = [i for i in items if i.get('ko')]
    print('항목 %d개 중 번역됨 %d개 (%.1f%%)'
          % (len(items), len(done), 100.0 * len(done) / len(items)))

    # --- 1. 파일별 예산 ---
    per = {}
    for it in items:
        f = it['file']
        d = per.setdefault(f, {'used': 0, 'n': 0, 'ko': 0})
        t = it.get('ko') or it['jp']          # 미번역은 원문 그대로 나간다
        d['used'] += nbytes(t) if it.get('ko') else it['budget']
        d['n'] += 1
        d['ko'] += 1 if it.get('ko') else 0
    print('\n=== 1. 파일별 바이트 예산 ===')
    over = 0
    print('%-40s %6s %8s %8s %7s' % ('파일', '번역/항목', '필요B', '예산B', '남음'))
    for f in sorted(per):
        b = budget.get(f, {}).get('total')
        d = per[f]
        if b is None:
            print('%-40s %6s %8d %8s' % (os.path.basename(f),
                                         '%d/%d' % (d['ko'], d['n']), d['used'], '?'))
            continue
        left = b - d['used']
        if left < 0:
            over += 1
        print('%-40s %6s %8d %8d %7d %s'
              % (os.path.basename(f), '%d/%d' % (d['ko'], d['n']),
                 d['used'], b, left, '★초과' if left < 0 else ''))
    print('예산 초과 파일 %d개' % over)

    # --- 2. 제어코드 / 3. 개행 ---
    print('\n=== 2~3. 제어코드·개행 보존 ===')
    bad = []
    for it in done:
        a, b = CODE.findall(it['jp']), CODE.findall(it['ko'])
        if a != b:
            bad.append((it, '제어코드 %s -> %s' % (a, b)))
        elif it['jp'].count('\n') != it['ko'].count('\n'):
            bad.append((it, '개행 %d -> %d'
                        % (it['jp'].count('\n'), it['ko'].count('\n'))))
    for it, msg in bad[:25]:
        print('  %s idx%-4d %s' % (os.path.basename(it['file']), it['idx'], msg))
    print('문제 %d건' % len(bad))

    # --- 4. 글리프 칸 ---
    print('\n=== 4. 장면별 글리프 칸 ===')
    byscene = {}
    for it in done:
        sc = scene_of(it['file'])
        byscene.setdefault(sc, set()).update(c for c in it['ko'] if is_hangul(c))
    cmn = atlas_cap('Common')
    print('%-16s %8s %8s %8s' % ('아틀라스', '필요음절', '칸(전용)', '판정'))
    for sc in sorted(byscene, key=lambda x: (x is None, x)):
        need = len(byscene[sc])
        cap = atlas_cap(sc) if sc else None
        if cap is None:
            print('%-16s %8d %8s  (아틀라스 미상)' % (str(sc), need, '?'))
            continue
        tot = cap[0] + (cmn[0] if sc != 'Common' and cmn else 0)
        print('%-16s %8d %8d %8s' % (sc, need, tot, 'OK' if need <= tot else '★초과'))

    # --- 5. 못 쓰는 문자 ---
    ng = set()
    for it in done:
        ng |= bad_chars(it['ko'])
    print('\n=== 5. cp932 로 못 넣는 문자 ===')
    print('  %s' % (''.join(sorted(ng)) if ng else '없음'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
