"""★페이지 모델 검증 — 원본 표가 가리키는 칸에 정말 그 글자가 있나?

Menu 는 4페이지다. 우리 Atlas 는 «512x512 페이지가 순서대로 이어진다»고 가정한다.
그 가정이 틀리면 칸 번호가 통째로 어긋난다. 페이지별로 몇 글자씩 뽑아 그려서 눈으로 판정한다.

    python pagemodel.py <장면> <출력.png>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from project import ROOT, FONT_DIR, WORK, COMMON_TBL
from ztbl import ZTbl
from atlaswrite import Atlas, CELLS_PER_PAGE

ORIG = os.path.join(WORK, 'orig')


def orig_of(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


def main():
    sc = sys.argv[1]
    out = sys.argv[2]
    tp = os.path.join(FONT_DIR, COMMON_TBL if sc == 'Common'
                      else 'Reisyo_%s_z_tbl.bin' % sc)
    ap = os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % sc)
    m = ZTbl(orig_of(tp)).mapping()
    a = Atlas(orig_of(ap))
    n = a.pages * CELLS_PER_PAGE
    bycell = {}
    for c, g in sorted(m.items()):
        bycell.setdefault(g, c)
    cols = 16
    rows = []
    for page in range(a.pages):
        pick = [g for g in sorted(bycell) if g // CELLS_PER_PAGE == page][:cols]
        rows.append((page, pick))
    img = Image.new('L', (cols * 28, len(rows) * 28), 0)
    for r, (page, pick) in enumerate(rows):
        line = ''
        for c, g in enumerate(pick):
            cell = Image.frombytes('L', (28, 28), bytes(a.cell_alpha(g)))
            img.paste(cell, (c * 28, r * 28))
            line += bycell[g]
        print('페이지 %d (칸 %s..): 표가 말하는 글자 = %s'
              % (page, pick[0] if pick else '-', line))
    img.resize((cols * 56, len(rows) * 56), Image.NEAREST).save(out)
    print('-> %s  (윗줄부터 페이지 0,1,2,3)' % out)


if __name__ == '__main__':
    main()
