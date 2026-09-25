"""후보 배치로 칸을 그려 «표가 말하는 글자»와 맞는지 눈으로 판정.

후보
  A  지금 모델 : 페이지마다 512x512, 페이지 안에서 18x18 (페이지 아래 8픽셀 버림)
  B  연속      : 512x(512*pages) 한 장으로 보고 y = (g//18)*28  (페이지 경계 틈 없음)

    python layout_try.py <장면> <시작칸> <개수> <출력접두사>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from project import ROOT, FONT_DIR, WORK, COMMON_TBL
from ztbl import ZTbl
from atlaswrite import Atlas, BLOCKS_X, PAGE_W, PAGE_H, CELLS_PER_PAGE, COLS

ORIG = os.path.join(WORK, 'orig')


def orig_of(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


def surface(a):
    body = bytes(a.body)
    rows = len(body) // 16 // BLOCKS_X
    img = np.zeros((rows * 4, PAGE_W), dtype=np.uint8)
    for br in range(rows):
        base = br * BLOCKS_X * 16
        for bx in range(BLOCKS_X):
            v = int.from_bytes(body[base + bx * 16: base + bx * 16 + 8], 'little')
            for yy in range(4):
                for xx in range(4):
                    img[br * 4 + yy, bx * 4 + xx] = ((v >> ((yy * 4 + xx) * 4)) & 0xF) * 17
    return img


def posA(g):
    page, rem = divmod(g, CELLS_PER_PAGE)
    r, c = divmod(rem, COLS)
    return c * 28, page * PAGE_H + r * 28


def posB(g):
    r, c = divmod(g, COLS)
    return c * 28, r * 28


sc, start, cnt, pref = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
tp = os.path.join(FONT_DIR, COMMON_TBL if sc == 'Common' else 'Reisyo_%s_z_tbl.bin' % sc)
m = ZTbl(orig_of(tp)).mapping()
a = Atlas(orig_of(os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % sc)))
surf = surface(a)
print('평면 %dx%d' % (surf.shape[1], surf.shape[0]))
bycell = {}
for c, g in sorted(m.items()):
    bycell.setdefault(g, c)
print('표: ' + ' '.join(bycell.get(g, '·') for g in range(start, start + cnt)))
for name, fn in (('A', posA), ('B', posB)):
    img = Image.new('L', (cnt * 28, 28), 0)
    for i, g in enumerate(range(start, start + cnt)):
        x, y = fn(g)
        if y + 28 > surf.shape[0]:
            continue
        img.paste(Image.fromarray(surf[y:y + 28, x:x + 28]), (i * 28, 0))
    img.resize((cnt * 56, 56), Image.NEAREST).save('%s_%s.png' % (pref, name))
    print('-> %s_%s.png' % (pref, name))
