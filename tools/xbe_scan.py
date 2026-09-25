"""default.xbe 안에 텍스처 컨테이너나 글리프 격자가 들어 있는지 훑는다."""
import os
import struct
from dxt import decode_alpha
from atlas import write_png
from project import ROOT, WORK, GLYPH_W, GLYPH_H

p = os.path.join(ROOT, 'default.xbe')
d = open(p, 'rb').read()
print('default.xbe %d B' % len(d))

for magic in (b'TXRB', b'PCMP', b'DDS ', b'XPR0', b'XPR1'):
    offs = []
    i = d.find(magic)
    while i >= 0 and len(offs) < 20:
        offs.append(i)
        i = d.find(magic, i + 1)
    print('  %-6s %d곳 %s' % (magic.decode('latin1', 'replace'), len(offs),
                              [hex(o) for o in offs[:8]]))

# 글리프 격자 탐색: 폭 256/512, 셀 크기 여러 개, DXT3알파 / A8
def score(pl, W, H, gw, gh):
    good = 0
    for r in range(H // gh):
        for c in range(W // gw):
            ink = border = 0
            for y in range(gh):
                b = (r * gh + y) * W + c * gw
                row = pl[b:b + gw]
                ink += sum(1 for v in row if v)
                if y in (0, gh - 1):
                    border += sum(1 for v in row if v)
                else:
                    border += (1 if row[0] else 0) + (1 if row[-1] else 0)
            if 20 <= ink <= 600 and border == 0:
                good += 1
    return good


best = []
for W in (256, 512):
    H = 256
    step = W * H
    for off in range(0, len(d) - step, step // 2):
        chunk = d[off:off + step]
        for fmt in ('a8', 'dxt3'):
            pl = chunk if fmt == 'a8' else decode_alpha(chunk, W, H)
            for gw, gh in ((16, 16), (20, 20), (24, 24), (28, 28), (32, 32)):
                s = score(pl, W, H, gw, gh)
                if s >= 40:
                    best.append((s, off, W, fmt, gw))
best.sort(reverse=True)
print('\n격자 후보 %d' % len(best))
for s, off, W, fmt, gw in best[:12]:
    print('  점수 %3d  off 0x%06x  w%d %s cell%d' % (s, off, W, fmt, gw))
if best:
    s, off, W, fmt, gw = best[0]
    chunk = d[off:off + W * 256]
    pl = chunk if fmt == 'a8' else decode_alpha(chunk, W, 256)
    print('->', write_png(os.path.join(WORK, 'atlas', 'xbe_hit.png'), W, 256, pl))
