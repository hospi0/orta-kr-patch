"""판도라 도감 <드래곤> 항목이 «어떤 칸»으로 그려지는지 추적."""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, TRANS, WORK, COMMON_TBL, pristine
from ztbl import ZTbl, SENTINEL
from atlaswrite import Atlas, CELLS_PER_PAGE

rel = r'menudata\TextData\text_pdb_db_world_JP.msg'
ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
cm = json.load(open(os.path.join(WORK, 'charmap_all.json'), encoding='utf-8'))
menu = cm['Menu']                      # 음절 -> [코드, 칸]
t = ko[rel]['76']

mt = ZTbl(os.path.join(FONT_DIR, 'Reisyo_Menu_z_tbl.bin'))
ct = ZTbl(os.path.join(FONT_DIR, COMMON_TBL))
mmap, cmap = mt.mapping(drop_sentinel=False), ct.mapping(drop_sentinel=False)
atlas = Atlas(os.path.join(FONT_DIR, 'Zenkaku_Menu.txb'))
print('Menu 아틀라스: 페이지 %d · 칸 %d · z_tbl pages=%d'
      % (atlas.pages, atlas.pages * CELLS_PER_PAGE, mt.pages))
print('Common z_tbl pages=%d' % ct.pages)
print()

syls = [c for c in t if 0xac00 <= ord(c) <= 0xd7a3]
uniq = sorted(set(syls))
print('이 항목이 쓰는 음절 %d개(고유 %d)' % (len(syls), len(uniq)))
rows = []
for s in uniq:
    code, cell = menu[s]
    inmenu = mmap.get(code, None)
    incmn = cmap.get(code, None)
    rows.append((s, code, cell, inmenu, incmn))
print('%-3s %-3s %6s %8s %10s' % ('음절', '코드', '배정칸', 'Menu표', 'Cmn표'))
for s, code, cell, im, ic in rows[:40]:
    print('%-4s %-4s %6d %8s %10s' % (s, code, cell, im, ic))
print()
cells = [r[2] for r in rows]
print('배정칸 범위 %d ~ %d' % (min(cells), max(cells)))
hist = collections.Counter(c // CELLS_PER_PAGE for c in cells)
print('페이지별 분포:', dict(sorted(hist.items())))
print('Menu 전체 배정칸 범위 %d ~ %d'
      % (min(v[1] for v in menu.values()), max(v[1] for v in menu.values())))
h2 = collections.Counter(v[1] // CELLS_PER_PAGE for v in menu.values())
print('Menu 전체 페이지 분포:', dict(sorted(h2.items())))
