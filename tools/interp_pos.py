"""검증된 앵커 사이를 «격자 칸 수»로 메워 표값->위치 대응표를 완성한다.

원리: 표값과 위치는 «읽는 순서»로 단조 증가한다(실측). 앵커 두 개 사이에서
      «격자 칸 수 차이 == 표값 차이» 이면 그 구간은 1:1 이므로 안전하게 메울 수 있다.
      그렇지 않은 구간은 **버린다**(추측하지 않는다).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from project import ROOT, FONT_DIR, WORK
from ztbl import ZTbl
from atlaswrite import Atlas, PAGE_W, PAGE_H
from gridmap import surface, oo, grid

sc = sys.argv[1] if len(sys.argv) > 1 else 'Menu'
a = Atlas(oo(os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % sc)))
offs = [(16 + 4 * p) % 28 for p in range(a.pages)]
cells = grid(a.pages, offs)
idx_of = {xy: i for i, xy in enumerate(cells)}
print('격자 %d칸' % len(cells))

pos = json.load(open(os.path.join(WORK, 'pos_%s.json' % sc), encoding='utf-8'))
m = ZTbl(oo(os.path.join(FONT_DIR, 'Reisyo_%s_z_tbl.bin' % sc))).mapping()
anchors = {}
for c, xy in pos.items():
    v = m.get(c)
    if v is None or v == 0:
        continue
    k = idx_of.get(tuple(xy))
    if k is None:
        continue
    if v in anchors and anchors[v] != k:
        anchors[v] = None
    else:
        anchors[v] = k
anchors = {v: k for v, k in anchors.items() if k is not None}
seq = sorted(anchors.items())
print('앵커 %d개 (표값 %d~%d)' % (len(seq), seq[0][0], seq[-1][0]))

ok_span = bad_span = filled = 0
val2k = dict(anchors)
for (v1, k1), (v2, k2) in zip(seq, seq[1:]):
    if v2 - v1 == k2 - k1 and v2 - v1 > 0:
        ok_span += 1
        for d in range(1, v2 - v1):
            val2k[v1 + d] = k1 + d
            filled += 1
    else:
        bad_span += 1
print('구간: 1:1 %d개 · 안 맞음 %d개 · 메운 값 %d개' % (ok_span, bad_span, filled))
print('완성된 표값 %d개' % len(val2k))
out = {str(v): list(cells[k]) for v, k in val2k.items()}
dst = os.path.join(WORK, 'gridmap_%s.json' % sc)
with open(dst, 'w', encoding='utf-8', newline='') as f:
    json.dump(out, f)
print('-> %s' % dst)
