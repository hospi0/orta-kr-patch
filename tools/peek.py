"""아무 .txb 나 DXT3 알파로 풀어 앞부분을 그린다."""
import os
import sys
import struct
from pcmp import decompress
from dxt import decode_alpha
from atlas import write_png
from cells import PAGE_W, PAGE_H, PAGE_BYTES
from project import ROOT, WORK

rel = sys.argv[1]
rows = int(sys.argv[2]) if len(sys.argv) > 2 else 280
p = os.path.join(ROOT, rel.replace('/', os.sep))
d = open(p, 'rb').read()
if d[:4] == b'PCMP':
    d = decompress(d)
pages = struct.unpack_from('<I', d, 4)[0]
start = 0x20 if pages == 1 else 0x50
print('%s  풀림 %d  페이지 %d' % (rel, len(d), pages))
pl = decode_alpha(d[start:start + PAGE_BYTES], PAGE_W, PAGE_H)
name = 'peek_%s.png' % os.path.basename(rel).replace('.txb', '')
print('->', write_png(os.path.join(WORK, 'atlas', name), PAGE_W, rows, pl[:PAGE_W * rows]))
