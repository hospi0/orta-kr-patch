"""★★★대체 코드 풀 = «그 장면 원문이 실제로 쓰는 글자» — 가능한지 실측.

2026-08-31 실기로 확정된 규칙:
    게임은 «그 화면 원문이 쓰는 글자»만 폰트에 올린다.
    우리가 지어낸 코드는 그 집합 밖이라 notdef(■) 가 된다.
  판별식 19/19 일치 (나온 코드 5개는 전부 원문에 있고, ■ 14개는 전부 없다).

배정 규칙
  · 원문 문자가 **공용표**에 있으면 -> 공용 칸. 공용은 전 장면이 공유하므로 **전역 1:1**.
  · 공용에 없고 **장면표**에 있으면 -> 장면 칸. 장면별로 자유롭게 배정.
  · notdef·시스템 글리프 칸은 제외.
"""
import json
import os
import sys
import collections

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

need = collections.defaultdict(set)
used = collections.defaultdict(set)
for rel in corpus:
    sc = K.scene_of(rel)
    if not sc:
        continue
    for e in corpus[rel]:
        used[sc] |= {c for c in e['jp'] if ord(c) > 0x7f}
        t = ko.get(rel, {}).get(str(e['idx']))
        if t:
            need[sc] |= {c for c in t if K.is_hangul(c)}

# --- 전역 공용 칸: 어느 장면에서든 «원문이 쓰는» 공용 문자의 칸 ---
glob_cells = set()
for sc in need:
    glob_cells |= {cmn[c] for c in used[sc] if c in cmn}
glob_cells -= sysc
print('전역 공용 칸(원문이 실제로 쓰는 공용 문자의 칸) %d개' % len(glob_cells))

all_syl = set().union(*need.values())
print('전 게임 고유 음절 %d개' % len(all_syl))
print()

print('%-16s %6s %8s %8s %8s %6s'
      % ('장면', '음절', '공용가능', '장면전용', '합계', '판정'))
bad = 0
for sc in sorted(need):
    st, n = tbl(sc)
    u = used[sc]
    c_cells = {cmn[c] for c in u if c in cmn} - sysc
    s_cells = {st[c] for c in u if c in st and c not in cmn}
    tot = len(c_cells) + len(s_cells)
    ok = tot >= len(need[sc])
    if not ok:
        bad += 1
    print('%-16s %6d %8d %8d %8d %6s'
          % (sc, len(need[sc]), len(c_cells), len(s_cells), tot,
             'OK' if ok else '★부족'))
print()
print('부족한 장면 %d개' % bad)
print()
print('※ 공용 칸은 전 장면이 «같은 음절»을 봐야 하므로, 전역으로 %d개 음절까지만 담을 수 있다.'
      % len(glob_cells))
