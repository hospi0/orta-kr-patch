"""게임이 뽑아 쓴 칸이 «원본 Menu 표»의 값인지 확인 — 낡은 표를 읽고 있나?"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, WORK
from ztbl import ZTbl

ORIG = os.path.join(WORK, 'orig')
p = os.path.join(FONT_DIR, 'Reisyo_Menu_z_tbl.bin')
po = os.path.join(ORIG, os.path.relpath(p, ROOT))
mo = ZTbl(po).mapping(drop_sentinel=False)     # 원본
mn = ZTbl(p).mapping(drop_sentinel=False)      # 현재(패치본)

obs = [('略', '드', 1081, 1085), ('践', '래', 639, 162), ('莱', '곤', 1067, 162)]
print('%-4s %-4s %8s %8s %8s %8s' % ('코드', '음절', '우리칸', '화면칸', '원본표', '현재표'))
for code, syl, ours, seen in obs:
    print('%-4s %-4s %8d %8d %8s %8s'
          % (code, syl, ours, seen, mo.get(code, '없음'), mn.get(code, '없음')))
print()
hit = sum(1 for code, s, o, seen in obs if mo.get(code) == seen)
print('★원본 표가 화면 칸과 일치하는 코드: %d / %d' % (hit, len(obs)))
