"""한 «행» 안에서 글리프 상자의 실제 x 좌표를 잰다 — 열 간격이 28 이 아닐 수 있다.

    python rowgrid.py <장면> <y> [y2 ...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from project import ROOT, FONT_DIR, WORK
from atlaswrite import Atlas, BLOCKS_X, PAGE_W

ORIG = os.path.join(WORK, 'orig')


def oo(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


def surface(a):
    body = bytes(a.body)
    rows = len(body) // 16 // BLOCKS_X
    b = np.frombuffer(body, dtype=np.uint8).reshape(-1, 16)[:, :8]
    bits = np.unpackbits(b, axis=1, bitorder='little').reshape(-1, 16, 4)
    vals = (bits * np.array([1, 2, 4, 8])).sum(axis=2).astype(np.uint8) * 17
    vals = vals.reshape(-1, 4, 4)
    img = np.zeros((rows * 4, PAGE_W), dtype=np.uint8)
    k = 0
    for br in range(rows):
        for bx in range(BLOCKS_X):
            img[br * 4:br * 4 + 4, bx * 4:bx * 4 + 4] = vals[k]
            k += 1
    return img


sc = sys.argv[1]
a = Atlas(oo(os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % sc)))
s = surface(a)
for ys in sys.argv[2:]:
    y = int(ys)
    band = s[y:y + 28, :]
    col = (band > 40).sum(axis=0)
    runs, run = [], None
    for i, v in enumerate(col):
        on = v > 0
        if on and run is None:
            run = i
        if not on and run is not None:
            runs.append((run, i))
            run = None
    if run is not None:
        runs.append((run, PAGE_W))
    print('y=%d  잉크 덩어리 %d개' % (y, len(runs)))
    print('   ', [(r[0], r[1] - r[0]) for r in runs])
    if len(runs) > 1:
        st = [r[0] for r in runs]
        print('    시작 간격:', [st[i + 1] - st[i] for i in range(len(st) - 1)])
