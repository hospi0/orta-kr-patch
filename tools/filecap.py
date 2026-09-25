"""★파일 단위 용량 실측 — 그 «파일» 원문이 쓰는 문자로 그 파일 음절을 다 덮을 수 있나.

게임이 파일(화면) 단위로 글자를 올린다면, 코드는 그 파일 원문에서 나와야 한다.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, TRANS, WORK, COMMON_TBL
from ztbl import ZTbl
from atlaswrite import Atlas, CELLS_PER_PAGE
import check_ko as K
from build_all import SYSTEM_GLYPHS

ORIG = os.path.join(WORK, 'orig')


def oo(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


def tbl(sc):
    p = os.path.join(FONT_DIR, COMMON_TBL if sc == 'Common' else 'Reisyo_%s_z_tbl.bin' % sc)
    if not os.path.exists(p):
        return {}, 0
    m = ZTbl(oo(p)).mapping()
    ap = os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % sc)
    n = Atlas(oo(ap)).pages * CELLS_PER_PAGE if os.path.exists(ap) else 0
    return {c: g for c, g in m.items() if 0 < g < n}, n


corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
cmn, _ = tbl('Common')
sysc = {cmn[c] for c in SYSTEM_GLYPHS if c in cmn}
cache = {}

print('%-42s %6s %8s %8s %8s %6s'
      % ('파일', '음절', '공용칸', '장면칸', '합계', '판정'))
for rel in sorted(corpus):
    sc = K.scene_of(rel)
    if not sc:
        continue
    if sc not in cache:
        cache[sc] = tbl(sc)
    st, _n = cache[sc]
    u, syl = set(), set()
    for e in corpus[rel]:
        u |= {c for c in e['jp'] if ord(c) > 0x7f}
        t = ko.get(rel, {}).get(str(e['idx']))
        if t:
            syl |= {c for c in t if K.is_hangul(c)}
    cc = {cmn[c] for c in u if c in cmn} - sysc
    sccell = {st[c] for c in u if c in st and c not in cmn}
    tot = len(cc) + len(sccell)
    print('%-42s %6d %8d %8d %8d %6s'
          % (os.path.basename(rel), len(syl), len(cc), len(sccell), tot,
             'OK' if tot >= len(syl) else '★%d부족' % (len(syl) - tot)))
