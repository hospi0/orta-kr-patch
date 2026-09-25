"""아틀라스의 «실제 칸 격자»를 잉크 프로파일로 실측한다 (28 이라고 가정하지 않는다).

    python gridmeasure.py <장면>
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
print('%s 평면 %dx%d · pages=%d' % (sc, s.shape[1], s.shape[0], a.pages))

col = (s > 40).sum(axis=0)
empty = [i for i, v in enumerate(col) if v == 0]
print('세로로 «완전히 빈» 열 %d개: %s' % (len(empty), empty[:40]))
if len(empty) > 1:
    d = [empty[i + 1] - empty[i] for i in range(len(empty) - 1)]
    from collections import Counter
    print('  빈 열 간격 빈도:', Counter(d).most_common(6))

row = (s > 40).sum(axis=1)
er = [i for i, v in enumerate(row) if v == 0]
print('가로로 «완전히 빈» 행 %d개 (앞 40): %s' % (len(er), er[:40]))
if len(er) > 1:
    d = [er[i + 1] - er[i] for i in range(len(er) - 1)]
    from collections import Counter
    print('  빈 행 간격 빈도:', Counter(d).most_common(6))
