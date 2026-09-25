"""연속 칸 범위를 그려 «표가 말하는 글자»와 «실제 그림»의 어긋남을 잰다.

    python pagemodel2.py <장면> <시작칸> <개수> <출력.png>
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


sc, start, cnt, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
tp = os.path.join(FONT_DIR, COMMON_TBL if sc == 'Common' else 'Reisyo_%s_z_tbl.bin' % sc)
ap = os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % sc)
m = ZTbl(orig_of(tp)).mapping()
a = Atlas(orig_of(ap))
bycell = {}
for c, g in sorted(m.items()):
    bycell.setdefault(g, '')
    bycell[g] += c

img = Image.new('L', (cnt * 28, 28), 0)
line = []
for i, g in enumerate(range(start, start + cnt)):
    img.paste(Image.frombytes('L', (28, 28), bytes(a.cell_alpha(g))), (i * 28, 0))
    line.append(bycell.get(g, '·'))
img.resize((cnt * 56, 56), Image.NEAREST).save(out)
print('칸 %d..%d' % (start, start + cnt - 1))
print('표가 말하는 글자: ' + ' '.join('%-2s' % c[:2] for c in line))
print('-> %s' % out)
