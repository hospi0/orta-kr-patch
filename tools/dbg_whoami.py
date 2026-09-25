"""화면에 나온 «틀린 글자»로 «어느 표+아틀라스가 쓰였는지» 역추적한다.

판도라 도감 <드래곤> 항목이 화면에 `<입갈갈>` 로 나왔다.
우리 번역은 `＜드래곤＞` 이고, Menu 배정으로 드→略 · 래→践 · 곤→莱 로 인코딩돼 있다.
⇒ «略→입 · 践→갈 · 莱→갈» 이 되는 (표, 아틀라스) 짝을 찾으면 그게 그 화면의 폰트다.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, TRANS, WORK, COMMON_TBL, SCENES
from ztbl import ZTbl
from atlaswrite import Atlas, CELLS_PER_PAGE

cm = json.load(open(os.path.join(WORK, 'charmap_all.json'), encoding='utf-8'))
codes = ['略', '践', '莱']          # 드 · 래 · 곤
want = ['입', '갈', '갈']

print('%-16s %-24s %s' % ('장면', '코드->칸', '그 칸에 우리가 넣은 음절'))
for name in ['Common'] + list(SCENES):
    p = os.path.join(FONT_DIR, COMMON_TBL if name == 'Common'
                     else 'Reisyo_%s_z_tbl.bin' % name)
    ap = os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % name)
    if not (os.path.exists(p) and os.path.exists(ap)):
        continue
    m = ZTbl(p).mapping(drop_sentinel=False)
    n = Atlas(ap).pages * CELLS_PER_PAGE
    bycell = {v[1]: s for s, v in cm.get(name, {}).items()}
    cells, syls = [], []
    for c in codes:
        g = m.get(c)
        cells.append(g)
        syls.append(bycell.get(g, '·') if g is not None and g < n else '—')
    hit = '  ★★일치' if syls == want else ''
    print('%-16s %-24s %s%s' % (name, str(cells), ''.join(syls), hit))
