"""화면에서 «나온 글자»와 «■(notdef)» 를 가르는 성질을 찾는다.

빌드된 텍스트의 각 코드에 대해:
  · 원본 공용표에 있나 / 값은?
  · 원본 장면표에 있나 / 값은?
  · 우리가 «새로 만든» 코드인가, «원래 있던» 코드를 재사용한 것인가
를 늘어놓는다. 화면과 눈으로 맞춰 보면 판정 기준이 드러난다.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, WORK, COMMON_TBL
from ztbl import ZTbl, SENTINEL
from atlaswrite import Atlas, CELLS_PER_PAGE
from msgrec import records

ORIG = os.path.join(WORK, 'orig')


def oo(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


rel = sys.argv[1] if len(sys.argv) > 1 else r'menudata\TextData\text_pdb_db_world_JP.msg'
idx = int(sys.argv[2]) if len(sys.argv) > 2 else 76
sc = sys.argv[3] if len(sys.argv) > 3 else 'Menu'

cm = json.load(open(os.path.join(WORK, 'charmap_all.json'), encoding='utf-8'))
bycode = {v[0]: (s, v[1]) for s, v in cm[sc].items()}
cto = ZTbl(oo(os.path.join(FONT_DIR, COMMON_TBL))).mapping(drop_sentinel=False)
sto = ZTbl(oo(os.path.join(FONT_DIR, 'Reisyo_%s_z_tbl.bin' % sc))).mapping(drop_sentinel=False)

d = open(os.path.join(ROOT, rel), 'rb').read()
t = records(d)[idx]['jp']
print('빌드된 텍스트: %s' % t.replace('\n', ' / '))
print()
print('%-4s %-5s %-9s %-9s %-6s' % ('코드', '음절', '원본공용표', '원본장면표', '코드출처'))
for ch in t:
    if ord(ch) < 0x80 or ch == '　':
        continue
    syl = bycode.get(ch, ('-', None))[0]
    cg, sg = cto.get(ch), sto.get(ch)
    src = '기존' if sg is not None else '새코드'
    print('%-4s %-6s %-9s %-9s %-6s'
          % (ch, syl,
             cg if cg is not None else '-',
             sg if sg is not None else '-',
             src))
