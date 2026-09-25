"""화면 관측 (코드 -> 보이는 글자) 로 «게임이 쓰는 색인 식»을 역추적한다.

관측(판도라 도감 <드래곤>, 2026-08-31):
    略(드) -> 입     践(래) -> 갈     莱(곤) -> 갈
같은 글자가 나온 두 코드가 있다는 게 핵심 단서다 — 서로 다른 칸을 가리켜야 하는데
같은 칸으로 접혔다.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import WORK, LEADS, ZTBL_STRIDE

cm = json.load(open(os.path.join(WORK, 'charmap_all.json'), encoding='utf-8'))
menu = cm['Menu']
bycell = {v[1]: s for s, v in menu.items()}

obs = [('略', '입'), ('践', '갈'), ('莱', '갈')]
print('%-4s %-6s %-8s %-6s %-8s %-8s %s'
      % ('코드', 'SJIS', '우리칸', '보인글자', '그 글자칸', 'ztbl색인', 'lead/trail'))
for code, seen in obs:
    b = code.encode('cp932')
    ours = menu[[s for s, v in menu.items() if v[0] == code][0]][1]
    tgt = menu.get(seen, [None, None])[1]
    idx = LEADS.index(b[0]) * ZTBL_STRIDE + (b[1] - 0x40)
    print('%-4s %04X   %-8d %-6s %-8s %-8d %02X/%02X'
          % (code, int.from_bytes(b, 'big'), ours, seen, tgt, idx, b[0], b[1]))

print()
print('«갈» 칸 = %d · «입» 칸 = %d' % (menu['갈'][1], menu['입'][1]))
print()
# 그 칸들을 «누가» 원래 가리켰나 — 원본 Menu 표에서
from project import FONT_DIR, ROOT, COMMON_TBL
from ztbl import ZTbl
ORIG = os.path.join(WORK, 'orig')
p = os.path.join(FONT_DIR, 'Reisyo_Menu_z_tbl.bin')
mo = ZTbl(os.path.join(ORIG, os.path.relpath(p, ROOT))).mapping(drop_sentinel=False)
inv = {}
for c, g in mo.items():
    inv.setdefault(g, []).append(c)
for cellname, cell in (('갈', menu['갈'][1]), ('입', menu['입'][1])):
    print('칸 %-5d (지금 %s) 를 원본 Menu 표에서 가리키던 문자: %s'
          % (cell, cellname, ''.join(inv.get(cell, ['-']))))
