"""★화면에 보이는 «우리 한글»을 «원본 일본어»로 되돌린다.

우리가 칠한 칸 -> 원본 표에서 그 칸을 가리키던 문자. 원본 롬을 우리 폰트로 돌렸을 때
화면이 무슨 글자인지 읽는 데 쓴다.

    python unmap.py <음절들> [장면...]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, WORK, COMMON_TBL, SCENES
from ztbl import ZTbl

ORIG = os.path.join(WORK, 'orig')


def oo(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


cm = json.load(open(os.path.join(WORK, 'charmap_all.json'), encoding='utf-8'))
syls = sys.argv[1]
scenes = sys.argv[2:] or ['Common', 'Menu']
for sc in scenes:
    p = os.path.join(FONT_DIR, COMMON_TBL if sc == 'Common' else 'Reisyo_%s_z_tbl.bin' % sc)
    if not os.path.exists(p):
        continue
    m = ZTbl(oo(p)).mapping()
    inv = {}
    for c, g in m.items():
        inv.setdefault(g, []).append(c)
    print('=== %s ===' % sc)
    for s in syls:
        v = cm.get(sc, {}).get(s)
        if not v:
            print('  %s  (이 장면엔 안 칠함)' % s)
            continue
        code, cell = v
        print('  %s  칸%-5d <- 원본 문자: %s' % (s, cell, ''.join(inv.get(cell, ['?']))[:12]))
