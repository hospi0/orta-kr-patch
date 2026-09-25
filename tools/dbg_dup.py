"""대체 코드 중복 검사 — 한 코드가 두 칸에 배정되면 표에서 나중 것이 이긴다."""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import FONT_DIR, WORK, COMMON_TBL, pristine
from ztbl import ZTbl

cm = json.load(open(os.path.join(WORK, 'charmap_all.json'), encoding='utf-8'))

print('%-16s %6s %8s %8s' % ('장면', '음절', '중복코드', '피해음절'))
tot = 0
for sc in sorted(cm):
    bycode = collections.defaultdict(list)
    for s, (code, cell) in cm[sc].items():
        bycode[code].append((s, cell))
    dup = {c: v for c, v in bycode.items() if len(v) > 1}
    victims = sum(len(v) - 1 for v in dup.values())
    tot += victims
    if dup:
        print('%-16s %6d %8d %8d   예: %s'
              % (sc, len(cm[sc]), len(dup), victims,
                 list(dup.items())[:2]))
    else:
        print('%-16s %6d %8d %8d' % (sc, len(cm[sc]), 0, 0))
print()
print('중복으로 «틀린 글자»가 되는 음절 총 %d개' % tot)

# 장면 간 코드 중복도 본다 — 한 코드가 두 장면에서 다른 칸이면 표는 장면별이라 무방하나
# 같은 표(Common)를 함께 보는 경우 문제가 된다.
allcode = collections.defaultdict(set)
for sc in cm:
    for s, (code, cell) in cm[sc].items():
        allcode[code].add(sc)
cross = {c: v for c, v in allcode.items() if len(v) > 1}
print('두 장면 이상에서 같은 코드를 쓴 경우 %d개' % len(cross))
