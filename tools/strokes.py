"""획 두께·알파 계조 실측 — 한글 글리프를 원본 글꼴에 맞추기 위한 기준값.

세션2 실기에서 한글이 «점선처럼 끊겨» 나왔다. 원본 한자는 멀쩡한데 한글만
끊긴 건 획이 가늘어서다. 추측으로 굵히지 말고 원본을 재어서 맞춘다.
"""
import collections
import os
import statistics
import sys
from atlaswrite import Atlas
from ztbl import ZTbl
from project import FONT_DIR, pristine, GLYPH_W, GLYPH_H


def runs(cell, thr=1):
    """수평 런 길이 목록 = 획 두께의 대용치."""
    out = []
    for y in range(GLYPH_H):
        n = 0
        for x in range(GLYPH_W):
            if cell[y * GLYPH_W + x] >= thr:
                n += 1
            else:
                if n:
                    out.append(n)
                n = 0
        if n:
            out.append(n)
    return out


def stats(cells, label):
    allruns, alpha, solid, tot = [], collections.Counter(), 0, 0
    for c in cells:
        if not any(c):
            continue
        allruns += runs(c)
        for v in c:
            if v:
                alpha[v] += 1
                tot += 1
                if v >= 240:
                    solid += 1
    h = collections.Counter(allruns)
    print('== %s ==' % label)
    print('   런 길이 분포:', ' '.join('%d:%d' % (k, h[k]) for k in sorted(h)[:10]))
    print('   런 중앙값 %.1f  최빈 %d  (런 %d개)'
          % (statistics.median(allruns), h.most_common(1)[0][0], len(allruns)))
    print('   잉크 픽셀 중 알파 240+ 비율 %.1f%%  (%d/%d)' % (solid * 100 / tot, solid, tot))
    print('   알파 상위:', [(k, v) for k, v in alpha.most_common(5)])
    return statistics.median(allruns), solid * 100 / tot


def orig_cells(scene='OpeningDemo', limit=200):
    tblname = 'Reisyo_%s_z_tbl.bin' % scene
    t = ZTbl(pristine(os.path.join(FONT_DIR, tblname))).mapping()
    a = Atlas(pristine(os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % scene)))
    out = []
    for ch, g in t.items():
        if g >= a.pages * 324:
            continue
        c = a.cell_alpha(g)
        if any(c):
            out.append(c)
        if len(out) >= limit:
            break
    return out


if __name__ == '__main__':
    scene = sys.argv[1] if len(sys.argv) > 1 else 'OpeningDemo'
    stats(orig_cells(scene), '원본 %s 글리프' % scene)
    print()
    import render
    stats([render.glyph(c) for c in '강산진수해별봄여름가을겨울'],
          '내 렌더 (%s %dpx)' % (os.path.basename(render.font_path()), render.SIZE))
