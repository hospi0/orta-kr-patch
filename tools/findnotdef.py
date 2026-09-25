"""★★«글자 없음» 표시(■ 등 시스템 글리프)가 어느 칸인지 — 그 칸은 절대 덮으면 안 된다.

2026-08-31 판도라 도감이 통째로 「갈」로 나온 원인:
Common 칸 40(=■)에 한글을 칠했더니, 표에서 못 찾은 «모든» 글자가 그 한글로 나왔다.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, WORK, COMMON_TBL, SCENES
from ztbl import ZTbl

ORIG = os.path.join(WORK, 'orig')
# 시스템 글리프 후보 — 「글자 없음」·자리표시로 쓰일 만한 것들
SYS = '■□◆◇●○※〓＊★☆'


def oo(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


cm = json.load(open(os.path.join(WORK, 'charmap_all.json'), encoding='utf-8'))
print('%-16s %s' % ('장면', '시스템 글리프의 칸 (★= 우리가 덮어썼다)'))
rows = [('Common', COMMON_TBL)] + [(s, 'Reisyo_%s_z_tbl.bin' % s) for s in SCENES]
danger = []
for sc, fn in rows:
    p = os.path.join(FONT_DIR, fn)
    if not os.path.exists(p):
        continue
    m = ZTbl(oo(p)).mapping()
    painted = {v[1]: s for s, v in cm.get(sc, {}).items()}
    out = []
    for ch in SYS:
        g = m.get(ch)
        if g is None:
            continue
        if g in painted:
            out.append('%s#%d★%s' % (ch, g, painted[g]))
            danger.append((sc, ch, g, painted[g]))
        else:
            out.append('%s#%d' % (ch, g))
    print('%-16s %s' % (sc, ' '.join(out)))
print()
print('★덮어쓴 시스템 칸 %d개' % len(danger))
for sc, ch, g, s in danger:
    print('   %-16s %s 칸%-5d <- %s' % (sc, ch, g, s))
