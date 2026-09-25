"""표의 «값»이 SJIS 순서로 단조 증가하는지 — 값이 무슨 뜻인지 알아내는 실마리."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, WORK, COMMON_TBL
from ztbl import ZTbl

ORIG = os.path.join(WORK, 'orig')


def oo(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


for sc in (sys.argv[1:] or ['Common', 'Menu', 'Stage1']):
    p = os.path.join(FONT_DIR, COMMON_TBL if sc == 'Common' else 'Reisyo_%s_z_tbl.bin' % sc)
    t = ZTbl(oo(p))
    m = t.mapping(drop_sentinel=False)
    items = sorted(m.items(), key=lambda kv: kv[0].encode('cp932'))
    # 값 0 (=글리프 없음으로 추정) 제외
    items = [(c, g) for c, g in items if g != 0]
    vals = [g for c, g in items]
    inc = sum(1 for i in range(len(vals) - 1) if vals[i + 1] > vals[i])
    eq = sum(1 for i in range(len(vals) - 1) if vals[i + 1] == vals[i])
    dec = len(vals) - 1 - inc - eq
    print('%-14s 항목 %5d · 최대값 %5d · 증가 %5d · 같음 %4d · 감소 %4d'
          % (sc, len(vals), max(vals), inc, eq, dec))
    print('    앞 24: %s' % ' '.join('%s=%d' % (c, g) for c, g in items[:24]))
