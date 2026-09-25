"""빌드된 레코드 한 줄을 «코드 -> 어느 표 -> 어느 칸 -> 우리가 칠한 음절» 로 추적한다.

    python trace_rec.py <파일> <ID> [장면]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, WORK, COMMON_TBL
from ztbl import ZTbl
from atlaswrite import Atlas, CELLS_PER_PAGE
from msgwalk import walk
import check_ko as K

ORIG = os.path.join(WORK, 'orig')


def oo(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


rel = sys.argv[1]
want_id = int(sys.argv[2])
sc = sys.argv[3] if len(sys.argv) > 3 else K.scene_of(rel)

cm = json.load(open(os.path.join(WORK, 'charmap_all.json'), encoding='utf-8'))
inv_c = {v[1]: s for s, v in cm['Common'].items()}
inv_s = {v[1]: s for s, v in cm.get(sc, {}).items()}
cto = ZTbl(oo(os.path.join(FONT_DIR, COMMON_TBL))).mapping()
sto = ZTbl(oo(os.path.join(FONT_DIR, 'Reisyo_%s_z_tbl.bin' % sc))).mapping()
nC = Atlas(oo(os.path.join(FONT_DIR, 'Zenkaku_Common.txb'))).pages * CELLS_PER_PAGE
nS = Atlas(oo(os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % sc))).pages * CELLS_PER_PAGE

n = open(os.path.join(ROOT, rel), 'rb').read()
o = open(os.path.join(ORIG, rel), 'rb').read()
tn = to = None
for st, i, off, ln in walk(n):
    if i == want_id:
        tn = n[off:off + ln].decode('cp932', 'replace')
for st, i, off, ln in walk(o):
    if i == want_id:
        to = o[off:off + ln].decode('cp932', 'replace')
print('원문: %r' % to)
print('빌드: %r' % tn)
print()
print('%-4s %-8s %-8s %-8s %-8s' % ('코드', '공용칸', '공용음절', '장면칸', '장면음절'))
for ch in (tn or ''):
    if ord(ch) < 0x80:
        continue
    cg, sg = cto.get(ch), sto.get(ch)
    pc = inv_c.get(cg) if cg is not None and cg < nC else None
    ps = inv_s.get(sg) if sg is not None and sg < nS else None
    print('%-4s %-8s %-8s %-8s %-8s   →화면예상 %s'
          % (ch, cg if cg is not None else '-', pc or '-',
             sg if sg is not None else '-', ps or '-',
             pc or ps or '(원본 글리프/■)'))
