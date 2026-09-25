"""실측한 «표값 -> 픽셀위치» 469쌍에서 규칙을 찾는다."""
import json
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, WORK
from ztbl import ZTbl

ORIG = os.path.join(WORK, 'orig')


def oo(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


pos = json.load(open(os.path.join(WORK, 'pos_Menu.json'), encoding='utf-8'))
m = ZTbl(oo(os.path.join(FONT_DIR, 'Reisyo_Menu_z_tbl.bin'))).mapping()
rows = []
for c, (x, y) in pos.items():
    v = m.get(c)
    if v is None:
        continue
    rows.append((v, x, y, c))
rows.sort()
print('쌍 %d개 · 표값 범위 %d ~ %d' % (len(rows), rows[0][0], rows[-1][0]))
print()
# 표값 순서와 픽셀 순서가 같은가 (선형 인덱스로 환산)
def lin(x, y):
    page = y // 512
    row = (y % 512) // 28
    return page, row, x


bad = 0
prev = None
for v, x, y, c in rows:
    p, r, xx = lin(x, y)
    key = (p, r, xx)
    if prev is not None and key < prev:
        bad += 1
    prev = key
print('표값 오름차순인데 위치가 «역행»한 곳: %d / %d' % (bad, len(rows) - 1))
print()
print('%-6s %-4s %-4s %-4s %-5s %-6s %s' % ('표값', '페이지', '행', 'x', 'x%28', 'x//28', '문자'))
for v, x, y, c in rows[:20]:
    p, r, xx = lin(x, y)
    print('%-6d %-6d %-4d %-4d %-5d %-6d %s' % (v, p, r, x, x % 28, x // 28, c))
print()
# 페이지별 x%28 분포
d = collections.defaultdict(collections.Counter)
for v, x, y, c in rows:
    d[y // 512][x % 28] += 1
for p in sorted(d):
    print('페이지 %d 의 x%%28 분포: %s' % (p, dict(d[p].most_common(6))))
print()
# 같은 행 안에서 표값 간격 vs x 간격
byrow = collections.defaultdict(list)
for v, x, y, c in rows:
    byrow[(y // 512, (y % 512) // 28)].append((v, x, c))
shown = 0
for k in sorted(byrow):
    lst = sorted(byrow[k])
    if len(lst) < 4:
        continue
    print('페이지%d 행%-2d : %s' % (k[0], k[1],
          ' '.join('%s=%d@%d' % (c, v, x) for v, x, c in lst[:9])))
    shown += 1
    if shown >= 6:
        break
