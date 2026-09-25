"""판도라 도감 문자들이 표에서 «어떤 값»을 갖는지 — 필터 없이 날것으로."""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, TRANS, WORK, COMMON_TBL, SCENES
from ztbl import ZTbl, SENTINEL
from atlaswrite import Atlas, CELLS_PER_PAGE

ORIG = os.path.join(WORK, 'orig')
def orig_of(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p

corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
rel = [r for r in corpus if 'db_world' in r][0]
s = set()
for e in corpus[rel]:
    s |= {c for c in e['jp'] if ord(c) > 0x7f}
print('원문 고유 전각 %d자' % len(s))

for name in ['Common'] + list(SCENES):
    p = os.path.join(FONT_DIR, COMMON_TBL if name == 'Common'
                     else 'Reisyo_%s_z_tbl.bin' % name)
    if not os.path.exists(p):
        continue
    t = ZTbl(orig_of(p))
    raw = t.mapping(drop_sentinel=False)
    ap = os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % name)
    n = Atlas(orig_of(ap)).pages * CELLS_PER_PAGE if os.path.exists(ap) else 0
    have = {c: raw[c] for c in s if c in raw}
    sent = sum(1 for g in have.values() if g == SENTINEL)
    over = sum(1 for g in have.values() if g != SENTINEL and g >= n)
    good = len(have) - sent - over
    if len(have):
        print('%-16s 칸수 %5d · 표에있음 %4d (쓸모 %4d · 센티널 %4d · 범위밖 %4d)'
              % (name, n, len(have), good, sent, over))
