"""TXRB 헤더(서브텍스처 표)를 실측으로 해독한다.

★폰트 베이스는 «서술자·리터럴»에서 — 통계로 때우지 말 것
  (feedback_font_base_from_descriptor_not_statistics).
"""
import os
import sys
import struct
from pcmp import decompress
from project import ROOT, FONT_DIR, pristine

SAMPLES = [
    ('Zenkaku_Common', os.path.join(FONT_DIR, 'Zenkaku_Common.txb')),
    ('Zenkaku_Menu', os.path.join(FONT_DIR, 'Zenkaku_Menu.txb')),
    ('name_entry', os.path.join(ROOT, 'sprite', 'name_entry.txb')),
    ('pdtex_title', os.path.join(ROOT, 'sprite', 'pdtex_title.txb')),
    ('pdtex_monolouge', os.path.join(ROOT, 'sprite', 'pdtex_monolouge.txb')),
    ('circle(raw)', os.path.join(ROOT, 'circle.txb')),
    ('shotbb(raw)', os.path.join(ROOT, 'shotbb.txb')),
]

for name, p in SAMPLES:
    p = pristine(p)
    if not os.path.exists(p):
        continue
    d = open(p, 'rb').read()
    if d[:4] == b'PCMP':
        d = decompress(d)
    n = struct.unpack_from('<I', d, 4)[0]
    print('=== %-18s 풀림 %9d  TXRB[1]=%d' % (name, len(d), n))
    for r in range(0, 0x80, 16):
        print('    %04x %s' % (r, ' '.join('%02x' % b for b in d[r:r + 16])))
    print('    u32:', [hex(x) for x in struct.unpack_from('<24I', d, 0)])
    print()
