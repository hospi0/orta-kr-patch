"""인게임 대사 한 줄을 «코드 -> 어느 표가 어느 칸을 주나» 로 추적."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, TRANS, WORK, COMMON_TBL
from ztbl import ZTbl, SENTINEL
from atlaswrite import Atlas, CELLS_PER_PAGE
from msgrec import records

ORIG = os.path.join(WORK, 'orig')


def oo(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


rel = sys.argv[1] if len(sys.argv) > 1 else r'messageevent\MesData_Stage01_JP.msg'
idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
sc = sys.argv[3] if len(sys.argv) > 3 else 'Stage1'

ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
cm = json.load(open(os.path.join(WORK, 'charmap_all.json'), encoding='utf-8'))
scmap = {v[0]: (s, v[1]) for s, v in cm[sc].items()}      # 코드 -> (음절, 칸)
inv = {v[1]: s for s, v in cm[sc].items()}
inv_c = {v[1]: s for s, v in cm['Common'].items()}

st = ZTbl(os.path.join(FONT_DIR, 'Reisyo_%s_z_tbl.bin' % sc)).mapping(drop_sentinel=False)
ct = ZTbl(os.path.join(FONT_DIR, COMMON_TBL)).mapping(drop_sentinel=False)
sto = ZTbl(oo(os.path.join(FONT_DIR, 'Reisyo_%s_z_tbl.bin' % sc))).mapping(drop_sentinel=False)
cto = ZTbl(oo(os.path.join(FONT_DIR, COMMON_TBL))).mapping(drop_sentinel=False)
nS = Atlas(os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % sc)).pages * CELLS_PER_PAGE
nC = Atlas(os.path.join(FONT_DIR, 'Zenkaku_Common.txb')).pages * CELLS_PER_PAGE

print('원문 ko: %r' % ko[rel][str(idx)])
d = open(os.path.join(ROOT, rel), 'rb').read()
t = records(d)[idx]['jp']
print('빌드된 텍스트: %r' % t)
print()
print('%-3s %-6s %-8s %-8s %-8s %-8s %s'
      % ('코드', '의도음절', '장면표', '거기음절', '공용표', '거기음절', '비고'))
for ch in t:
    if ord(ch) < 0x80:
        continue
    want = scmap.get(ch, ('-', None))
    sg, cg = st.get(ch), ct.get(ch)
    note = ''
    if cg is not None and cg != SENTINEL and cg < nC:
        note = '★공용이 먼저 이기면 %s' % inv_c.get(cg, '(원본글자)')
    print('%-3s %-8s %-8s %-8s %-8s %-8s %s'
          % (ch, want[0],
             sg if sg is not None else '없음',
             inv.get(sg, '-') if sg is not None else '-',
             cg if cg is not None else '없음',
             inv_c.get(cg, '-') if cg is not None else '-',
             note))
