"""원본 ↔ 빌드 결과의 walk 항목을 나란히 놓고 «어디서부터 어긋나는지» 찾는다."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, WORK
from msgwalk import walk

ORIG = os.path.join(WORK, 'orig')
rel = sys.argv[1]
o = open(os.path.join(ORIG, rel), 'rb').read()
n = open(os.path.join(ROOT, rel), 'rb').read()
wo, wn = walk(o), walk(n)
print('원본 %d 항목 / 새 %d 항목' % (len(wo), len(wn)))
print('%-4s %-9s %-8s %-5s | %-9s %-8s %-5s' % ('#', 'ID', 'off', 'len', 'ID', 'off', 'len'))
shown = 0
for i in range(max(len(wo), len(wn))):
    a = wo[i] if i < len(wo) else (None, None, None, None)
    b = wn[i] if i < len(wn) else (None, None, None, None)
    diff = (a[1] != b[1])
    if diff or shown < 0:
        pass
    if diff:
        print('%-4d %-9s %-8s %-5s | %-9s %-8s %-5s   ★첫 어긋남'
              % (i, a[1], a[2], a[3], b[1], b[2], b[3]))
        for j in range(max(0, i - 4), min(i + 6, max(len(wo), len(wn)))):
            x = wo[j] if j < len(wo) else (None,) * 4
            y = wn[j] if j < len(wn) else (None,) * 4
            tx = o[x[2]:x[2] + x[3]].decode('cp932', 'replace') if x[2] is not None else ''
            ty = n[y[2]:y[2] + y[3]].decode('cp932', 'replace') if y[2] is not None else ''
            print('  %-4d %-8s %-4s %-22r | %-8s %-4s %-22r'
                  % (j, x[1], x[3], tx[:18].replace('\n', '/'),
                     y[1], y[3], ty[:18].replace('\n', '/')))
        break
else:
    print('ID 순서는 끝까지 같다.')
