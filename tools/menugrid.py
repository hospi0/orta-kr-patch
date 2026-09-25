"""★★★Menu 아틀라스의 «표값 -> 픽셀 위치»를 글리프 대조로 확정한다.

왜: Menu 는 4쪽짜리라 `값 = 라스터 번호` 공식이 안 맞는다(쪽마다 x 기준이 16/20/24/0).
    기존 `work/gridmap_Menu.json` 191자리는 노이즈가 ±0~5칸이라
    실기에서 «유닛 -> 등닛», «버서크 -> 버서경» 같은 엉뚱한 글자가 나왔다.

방법: 1쪽짜리 장면 아틀라스는 «값 = 칸 번호»가 확실하다(실기 검증됨).
      거기서 문자별 글리프 비트맵을 사전으로 모은 뒤, Menu 아틀라스의 각 격자 자리
      비트맵을 그 사전에서 찾는다. 찾으면 그 문자의 Menu 표값이 곧 그 자리의 값이다.

    python menugrid.py            # 대조 결과 보고
    python menugrid.py --save     # work/gridmap_Menu2.json 으로 저장
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import WORK, pristine
from atlaswrite import Atlas, CELLS_PER_PAGE
from ztbl import ZTbl
import build_all as B

BASE = {0: 16, 1: 20, 2: 24, 3: 0}
SCENES = ['Common', 'Movie', 'Tutorial', 'OpeningDemo'] + \
         ['Stage%d' % i for i in range(1, 11)] + \
         ['Mission0%d' % i for i in range(1, 6)] + \
         ['SubScenario0%d' % i for i in range(1, 8)]


def grid_positions():
    """Menu 아틀라스의 모든 격자 자리 (라스터 순서)."""
    out = []
    for p in range(4):
        for r in range(18):
            for c in range(18):
                x = BASE[p] + c * 28
                if x + 28 > 512:
                    continue
                out.append((p * 324 + r * 18 + c, x, p * 512 + r * 28))
    return out


def build_dict():
    """{글리프비트맵: {문자}} — 1쪽 장면에서만 모은다(값=칸번호가 확실)."""
    d = collections.defaultdict(set)
    nfile = 0
    for sc in SCENES:
        tp, ap = B.tbl_path(sc), B.atlas_path(sc)
        if not (os.path.exists(tp) and os.path.exists(ap)):
            continue
        a = Atlas(pristine(ap))
        if a.pages != 1:
            continue
        nfile += 1
        m = ZTbl(pristine(tp)).mapping()
        for ch, v in m.items():
            if not (0 <= v < CELLS_PER_PAGE):
                continue
            key = bytes(a.cell_alpha(v))
            if any(key):
                d[key].add(ch)
    return d, nfile


def main():
    d, nfile = build_dict()
    uniq = {k: next(iter(v)) for k, v in d.items() if len(v) == 1}
    print('사전 — 1쪽 장면 %d개에서 서로 다른 글리프 %d개 (그중 문자가 하나로 확정 %d개)'
          % (nfile, len(d), len(uniq)))

    menu_tbl = ZTbl(pristine(B.tbl_path('Menu'))).mapping()
    a = Atlas(pristine(B.atlas_path('Menu')))
    pos = grid_positions()
    print('Menu 격자 자리 %d개 · 표 문자 %d개' % (len(pos), len(menu_tbl)))

    found = {}
    ambig = blank = miss = 0
    for raster, x, y in pos:
        key = bytes(a.cell_alpha_xy(x, y))
        if not any(key):
            blank += 1
            continue
        cand = d.get(key)
        if not cand:
            miss += 1
            continue
        chs = [c for c in cand if c in menu_tbl]
        vs = {menu_tbl[c] for c in chs}
        if len(vs) != 1:
            ambig += 1
            continue
        found[vs.pop()] = (x, y, raster)
    print('  맞춘 자리 %d · 사전에 없음 %d · 빈칸 %d · 모호 %d'
          % (len(found), miss, blank, ambig))

    # delta = 라스터 - 표값
    dd = collections.Counter(r - v for v, (x, y, r) in found.items())
    print('  delta(라스터-값) 분포:', sorted(dd.items())[:10])

    old = {int(k): tuple(v) for k, v in json.load(
        open(os.path.join(WORK, 'gridmap_Menu.json'), encoding='utf-8')).items()}
    both = set(old) & set(found)
    agree = sum(1 for v in both if old[v] == found[v][:2])
    print('  기존 앵커와 겹치는 값 %d개 중 위치가 같은 것 %d개' % (len(both), agree))

    if '--save' in sys.argv:
        out = {str(v): [x, y] for v, (x, y, r) in found.items()}
        p = os.path.join(WORK, 'gridmap_Menu2.json')
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print('-> %s (%d자리)' % (p, len(out)))


if __name__ == '__main__':
    main()
