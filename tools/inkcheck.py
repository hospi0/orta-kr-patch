"""현재 «디스크에 실제로 들어간» 폰트 파일들의 잉크량을 센다. 내 빌드 검산용."""
import os
import struct
from pcmp import decompress
from dxt import decode_alpha
from cells import PAGE_BYTES, PAGE_W, PAGE_H
from project import ROOT, FONT_DIR

print('%-36s %10s %10s' % ('file', '잉크(현재)', '잉크(원본)'))
ORIG = os.path.join(os.path.dirname(FONT_DIR), '..', '..')
from project import WORK
for fn in sorted(os.listdir(FONT_DIR)):
    if not fn.lower().endswith('.txb'):
        continue
    rel = os.path.join('sprite', 'Font', fn)
    def ink(path):
        d = open(path, 'rb').read()
        if d[:4] == b'PCMP':
            d = decompress(d)
        pages = struct.unpack_from('<I', d, 4)[0]
        start = 0x20 + (pages - 1) * 16
        tot = 0
        for i in range(pages):
            s = start + i * PAGE_BYTES
            if s + PAGE_BYTES > len(d):
                break
            tot += sum(1 for v in decode_alpha(d[s:s + PAGE_BYTES], PAGE_W, PAGE_H) if v)
        return tot
    cur = ink(os.path.join(ROOT, rel))
    ob = os.path.join(WORK, 'orig', rel)
    orig = ink(ob) if os.path.exists(ob) else -1
    flag = '' if cur == 0 else '  ★안 비워짐'
    print('%-36s %10d %10d%s' % (fn, cur, orig, flag))
