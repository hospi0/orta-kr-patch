"""★★빌드가 «의도한 칸에 의도한 글자»를 실제로 넣었는지 되읽어 검산한다.

지금까지는 «썼다»고 믿고 넘어갔다. 되읽기 검산이 없었다.
판정: 패치된 아틀라스의 칸 g 를 다시 뽑아, 우리가 그리려던 글리프와 겹치는지(IoU).

    python verify_cells.py            # 전 장면 요약
    python verify_cells.py Menu       # 한 장면 상세
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import FONT_DIR, WORK
from atlaswrite import Atlas, CELLS_PER_PAGE
import render3 as R


def iou(a, b):
    ai = [1 if x > 96 else 0 for x in a]
    bi = [1 if x > 96 else 0 for x in b]
    inter = sum(1 for x, y in zip(ai, bi) if x and y)
    union = sum(1 for x, y in zip(ai, bi) if x or y)
    return inter / union if union else 1.0


def main():
    pick = sys.argv[1] if len(sys.argv) > 1 else None
    cm = json.load(open(os.path.join(WORK, 'charmap_all.json'), encoding='utf-8'))
    R.calibrate(sorted({s for d in cm.values() for s in d}))
    print('%-16s %5s %6s %6s %6s  %s' % ('장면', '칸', '평균IoU', '나쁨', '페이지', '보기'))
    for sc in sorted(cm):
        if pick and sc != pick:
            continue
        ap = os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % sc)
        if not os.path.exists(ap):
            continue
        a = Atlas(ap)
        n = a.pages * CELLS_PER_PAGE
        tot = 0.0
        bad = []
        rows = []
        for s, (code, g) in sorted(cm[sc].items(), key=lambda kv: str(kv[1][1])):
            # ★자리는 «칸 번호»(int) 또는 «픽셀 좌표»([x, y]) 다 → build_all 참조
            if isinstance(g, list):
                got = a.cell_alpha_xy(g[0], g[1])
                g = tuple(g)
            elif g >= n:
                bad.append((s, g, -1.0))
                continue
            else:
                got = a.cell_alpha(g)
            v = iou(got, R.glyph(s))
            tot += v
            rows.append((s, g, v))
            if v < 0.5:
                bad.append((s, g, v))
        k = len(cm[sc])
        print('%-16s %5d %6.3f %6d %6d  %s'
              % (sc, k, tot / max(k, 1), len(bad), a.pages,
                 ' '.join('%s#%s(%.2f)' % r for r in bad[:6])))
        if pick:
            print()
            print('  칸 오름차순 40개:')
            for s, g, v in rows[:40]:
                print('   %s  자리%-12s IoU %.3f' % (s, g, v))


if __name__ == '__main__':
    main()
