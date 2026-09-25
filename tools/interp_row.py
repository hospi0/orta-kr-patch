"""★★검증된 앵커로 «행 단위»로만 채워 표값->위치 대응표를 만든다.

앞선 `interp_pos.py` 는 «격자 전체»를 가로질러 보간했다. 행을 넘나드는 구간은
칸 수와 표값 차가 우연히 맞을 수 있어 **틀린 자리를 만든다**(도감에 엉뚱한 한글이 났다).

여기서는 훨씬 보수적으로:
  · 같은 «행»(페이지+행) 안에 앵커가 2개 이상 있고
  · 그 앵커들이 전부 «표값 차 == 열 차» 를 만족할 때만
  · 그 행을 1:1 로 채운다.
그 외는 **버린다**(추측하지 않는다).

    python interp_row.py [장면=Menu]   -> work/gridmap_<장면>.json
"""
import json
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, WORK
from ztbl import ZTbl
from atlaswrite import Atlas, PAGE_W, PAGE_H
from gridmap import oo

sc = sys.argv[1] if len(sys.argv) > 1 else 'Menu'
a = Atlas(oo(os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % sc)))
offs = [(16 + 4 * p) % 28 for p in range(a.pages)]
cols = [(PAGE_W - o) // 28 for o in offs]
print('%s 페이지 %d · x시작 %s · 페이지별 열수 %s' % (sc, a.pages, offs, cols))

pos = json.load(open(os.path.join(WORK, 'pos_%s.json' % sc), encoding='utf-8'))
m = ZTbl(oo(os.path.join(FONT_DIR, 'Reisyo_%s_z_tbl.bin' % sc))).mapping()

# (페이지, 행) -> {열: 표값}
rows = collections.defaultdict(dict)
dup = 0
for c, (x, y) in pos.items():
    v = m.get(c)
    if v is None or v == 0:
        continue
    p = y // PAGE_H
    r = (y % PAGE_H) // 28
    col = (x - offs[p]) // 28
    if (x - offs[p]) % 28 or not (0 <= col < cols[p]):
        continue
    if col in rows[(p, r)] and rows[(p, r)][col] != v:
        dup += 1
        rows[(p, r)][col] = None
    else:
        rows[(p, r)].setdefault(col, v)
print('앵커가 있는 행 %d개 (열 충돌 %d)' % (len(rows), dup))

# ★★행마다 «기준선 base = 표값 - 열» 을 다수결로 정한다.
#   오라클 대조는 비슷한 글자에 잘못 붙는 오탐이 섞인다(何 가 価 자리에 붙었다).
#   같은 행의 앵커 다수가 같은 base 를 가리키면 그게 맞고, 나머지는 이상치다.
def gidx(p, r):
    return p * (PAGE_H // 28) + r


# 1) 행마다 후보 기준선(다수결)과 지지 수
cand = {}
for (p, r), d in rows.items():
    pts = sorted((c, v) for c, v in d.items() if v is not None)
    if not pts:
        continue
    cnt = collections.Counter(v - c for c, v in pts)
    base, n = cnt.most_common(1)[0]
    cand[gidx(p, r)] = (base, n, len(pts), p, r)

# 2) 확실한 행 = 지지 2 이상 + 이상치 1 이하
firm = {g: v for g, v in cand.items() if v[1] >= 2 and v[2] - v[1] <= 1}
# 3) 나머지는 «이웃 행의 추세»로 검증한다.
#    기준선은 행마다 +15~20 으로 단조 증가한다(실측). 그 창 안이면 받는다.
order = sorted(cand)
accept = dict(firm)
for g in order:
    if g in accept:
        continue
    base = cand[g][0]
    lo = max((x for x in accept if x < g), default=None)
    hi = min((x for x in accept if x > g), default=None)
    ok = True
    if lo is not None:
        d1 = base - accept[lo][0]
        if not (14 * (g - lo) <= d1 <= 22 * (g - lo)):
            ok = False
    if hi is not None:
        d2 = accept[hi][0] - base
        if not (14 * (hi - g) <= d2 <= 22 * (hi - g)):
            ok = False
    if lo is None and hi is None:
        ok = False
    if ok:
        accept[g] = cand[g]

# 4) ★최종 자체검증 — 그 행의 앵커가 «하나라도» 기준선과 어긋나면 그 행은 버린다.
#    (앵커가 3개 이상이면 이상치 1개까지는 오탐으로 보고 허용)
final = {}
for g, (base, n, tot, p, r) in accept.items():
    out = tot - n
    if out == 0 or (n >= 3 and out <= 1):
        final[g] = (base, n, tot, p, r)
print('자체검증 통과 행 %d / %d' % (len(final), len(accept)))
accept = final

val2pos, filled = {}, 0
for g, (base, n, tot, p, r) in sorted(accept.items()):
    for col in range(cols[p]):
        v = base + col
        if v <= 0:
            continue
        val2pos[v] = (offs[p] + col * 28, p * PAGE_H + r * 28)
        filled += 1
print('확실한 행 %d개 + 추세로 받은 행 %d개 = %d개 · 자리 %d개'
      % (len(firm), len(accept) - len(firm), len(accept), filled))

# 앵커 자체와 어긋나지 않는지 재검산
bad = 0
for c, xy in pos.items():
    v = m.get(c)
    if v in val2pos and val2pos[v] != tuple(xy):
        bad += 1
print('앵커와 어긋난 자리 %d개' % bad)

dst = os.path.join(WORK, 'gridmap_%s.json' % sc)
with open(dst, 'w', encoding='utf-8', newline='') as f:
    json.dump({str(k): list(v) for k, v in val2pos.items()}, f)
print('-> %s (표값 %d개)' % (dst, len(val2pos)))
