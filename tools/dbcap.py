"""★도감이 «이론상» 쓸 수 있는 글리프 자리가 몇 개인가 — 오라클을 완전히 갖췄다고 가정.

제약 세 겹:
  1. 아틀라스에 «잉크가 있는 칸»이 몇 개인가          (물리적 상한)
  2. 코드는 «그 파일 원문이 실제로 쓰는 문자»여야 한다 (실기 확정 규칙)
  3. 그 문자가 가리키는 자리를 «알아야» 한다          (지금의 병목 — 오라클 커버리지)

1번을 하면 3번이 사라진다. 그때의 상한이 2번이다.
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
from gridmap import surface, oo, grid

corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))

cmn = ZTbl(oo(os.path.join(FONT_DIR, COMMON_TBL))).mapping()
n_cmn = Atlas(oo(os.path.join(FONT_DIR, 'Zenkaku_Common.txb'))).pages * CELLS_PER_PAGE
sysc = {cmn[c] for c in SYSTEM_GLYPHS if c in cmn}
menu = ZTbl(oo(os.path.join(FONT_DIR, 'Reisyo_Menu_z_tbl.bin'))).mapping()
a = Atlas(oo(os.path.join(FONT_DIR, 'Zenkaku_Menu.txb')))
surf = surface(a)
offs = [(16 + 4 * p) % 28 for p in range(a.pages)]
cells = grid(a.pages, offs)
inked = sum(1 for x, y in cells if (surf[y:y + 28, x:x + 28] > 40).sum())
print('Menu 아틀라스: 격자 %d칸 · 잉크 있는 칸 %d개  ← 물리적 상한' % (len(cells), inked))
known = len(json.load(open(os.path.join(WORK, 'gridmap_Menu.json'), encoding='utf-8')))
print('지금 «자리를 아는» 표값: %d개  ← 현재 병목' % known)
print()

print('%-36s %6s %8s %8s %8s %6s'
      % ('파일', '필요음절', 'Menu코드', '공용코드', '합계상한', '판정'))
tot = collections.Counter()
for rel in sorted(corpus):
    if K.scene_of(rel) != 'Menu':
        continue
    u, syl = set(), set()
    for e in corpus[rel]:
        u |= {c for c in e['jp'] if ord(c) > 0x7f}
        t = ko.get(rel, {}).get(str(e['idx']))
        if t:
            syl |= {c for c in t if K.is_hangul(c)}
    # 그 파일 원문이 쓰는 문자 중 Menu 표에서 «진짜 칸»을 가리키는 것
    mslot = {menu[c] for c in u if c in menu and menu[c] != 0 and c not in cmn}
    cslot = {cmn[c] for c in u if c in cmn and cmn[c] != 0} - sysc
    print('%-36s %6d %8d %8d %8d %6s'
          % (os.path.basename(rel), len(syl), len(mslot), len(cslot),
             len(mslot) + len(cslot),
             'OK' if len(mslot) + len(cslot) >= len(syl) else
             '%d부족' % (len(syl) - len(mslot) - len(cslot))))
    tot['syl'] += len(syl)
