"""★가설: 판도라 도감은 «Common 표»로 조회하고, 못 찾으면 `■`(Common 칸 40)을 그린다.

우리는 그 ■ 칸에 «갈»을 칠했다. 그래서 못 찾은 글자마다 갈이 나온다.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, WORK, COMMON_TBL
from ztbl import ZTbl, SENTINEL

ORIG = os.path.join(WORK, 'orig')


def oo(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


cm = json.load(open(os.path.join(WORK, 'charmap_all.json'), encoding='utf-8'))
cmn_o = ZTbl(oo(os.path.join(FONT_DIR, COMMON_TBL))).mapping(drop_sentinel=False)
menu_o = ZTbl(oo(os.path.join(FONT_DIR, 'Reisyo_Menu_z_tbl.bin'))).mapping(drop_sentinel=False)
inv_c = {v[1]: s for s, v in cm['Common'].items()}
inv_m = {v[1]: s for s, v in cm['Menu'].items()}

print('원본 Common 표에서 칸 40 을 가리키는 문자: %s'
      % ''.join(c for c, g in cmn_o.items() if g == 40)[:40])
print('우리가 Common 칸 40 에 칠한 음절: %s' % inv_c.get(40))
print()
print('%-4s %-6s %-10s %-10s %-10s %-10s'
      % ('코드', '뜻', 'Cmn표값', '거기 우리음절', 'Menu표값', '거기 우리음절'))
for code, syl in (('略', '드'), ('践', '래'), ('莱', '곤')):
    cg = cmn_o.get(code)
    mg = menu_o.get(code)
    print('%-4s %-6s %-10s %-10s %-10s %-10s'
          % (code, syl,
             cg if cg is not None else '없음',
             inv_c.get(cg, '-') if cg is not None else '-',
             mg if mg is not None else '없음',
             inv_m.get(mg, '-') if mg is not None else '-'))
print()
print('참고: 센티널 = %d' % SENTINEL)
