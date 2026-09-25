"""TXRB 를 «헤더의 폭»으로 정확히 그린다.

폭 = u32 @0x14 (Zenkaku_Common 이 0x200=512 로 검증됨). 데이터는 0x20 부터.
사용: python render_txb.py <상대경로> [출력줄수]
"""
import os
import sys
import struct
from pcmp import decompress
from dxt import decode_alpha
from atlas import write_png
from project import ROOT, WORK

rel = sys.argv[1]
rows = int(sys.argv[2]) if len(sys.argv) > 2 else 512
p = os.path.join(ROOT, rel.replace('/', os.sep))
d = open(p, 'rb').read()
if d[:4] == b'PCMP':
    d = decompress(d)
n = struct.unpack_from('<I', d, 4)[0]
W = struct.unpack_from('<I', d, 0x14)[0]
fmt = struct.unpack_from('<I', d, 0x18)[0]
body = d[0x20:]
H = len(body) // W
print('%s  풀림 %d  서브텍스처 %d  폭 %d  fmt 0x%x  -> %dx%d' % (rel, len(d), n, W, fmt, W, H))
rows = min(rows, H)
img = decode_alpha(body[:W * rows], W, rows)
name = 'rt_%s.png' % os.path.basename(rel).replace('.txb', '')
print('->', write_png(os.path.join(WORK, 'atlas', name), W, rows, img))
