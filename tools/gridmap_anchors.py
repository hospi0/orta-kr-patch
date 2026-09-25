"""★★검증된 앵커«만»으로 표값->위치 대응표를 만든다. 보간하지 않는다.

배경: Menu(4페이지) 아틀라스는 «표값 ↔ 열»이 1:1 이 아니다. 행 단위·구간 단위로
      보간해 봤으나 앵커와 어긋나는 자리가 계속 생겼고, 실기에서 «엉뚱한 한글»로 나왔다.
      사용자 판정: 「빈칸은 이해하는데 중간에 외계어가 있음」.
  ⇒ **추측하지 않는다.** 오라클 픽셀 대조(상관 1.000)로 확인한 자리만 쓴다.
     못 채운 음절은 정직하게 ■ 로 나간다.

    python gridmap_anchors.py [장면=Menu]  -> work/gridmap_<장면>.json
"""
import json
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import FONT_DIR, WORK
from ztbl import ZTbl
from gridmap import oo

sc = sys.argv[1] if len(sys.argv) > 1 else 'Menu'
pos = json.load(open(os.path.join(WORK, 'pos_%s.json' % sc), encoding='utf-8'))
m = ZTbl(oo(os.path.join(FONT_DIR, 'Reisyo_%s_z_tbl.bin' % sc))).mapping()

v2p, conflict = {}, 0
for c, xy in pos.items():
    v = m.get(c)
    if not v:                      # 0 = 글리프 없음 자리
        continue
    t = tuple(xy)
    if v in v2p and v2p[v] != t:
        v2p[v] = None
        conflict += 1
    else:
        v2p.setdefault(v, t)
v2p = {v: t for v, t in v2p.items() if t is not None}

# 한 자리에 표값이 둘 이상 붙으면 위험하다 — 자리 기준으로도 1:1 이어야 한다
byp = collections.Counter(v2p.values())
v2p = {v: t for v, t in v2p.items() if byp[t] == 1}

print('%s : 앵커 %d개 · 충돌 %d · 쓸 수 있는 «표값->자리» %d개'
      % (sc, len(pos), conflict, len(v2p)))
dst = os.path.join(WORK, 'gridmap_%s.json' % sc)
with open(dst, 'w', encoding='utf-8', newline='') as f:
    json.dump({str(k): list(v) for k, v in v2p.items()}, f)
print('-> %s' % dst)
