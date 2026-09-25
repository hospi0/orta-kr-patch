import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import WORK
p = os.path.join(WORK, 'orig', sys.argv[1])
a = int(sys.argv[2], 0)
b = int(sys.argv[3], 0)
d = open(p, 'rb').read()
for off in range(a & ~15, b, 16):
    row = d[off:off + 16]
    print('%06X  %-47s  %s' % (off, ' '.join('%02X' % x for x in row),
          ''.join(chr(x) if 32 <= x < 127 else '.' for x in row)))
