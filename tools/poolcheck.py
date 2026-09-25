"""★대체 코드 풀을 «그 장면 원문이 실제로 쓰는 글자»로 잡을 수 있는지 실측.

근거: 그 화면이 원본에서 그 글자를 «멀쩡히 그렸다»는 것은, 그 화면이 쓰는 표에
그 글자가 있다는 뜻이다. 우리가 만들어 낸 코드는 그 보장이 없다.
→ 2026-08-31 판도라 도감이 전부 notdef(■) 로 나온 원인.

칸은 «그 글자가 가리키는 칸»을 그대로 쓴다 — 조회가 반드시 성공한다.
"""
import json
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, TRANS, WORK, COMMON_TBL
from ztbl import ZTbl
from atlaswrite import Atlas, CELLS_PER_PAGE
import check_ko as K

ORIG = os.path.join(WORK, 'orig')


def oo(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


def tbl(sc):
    p = os.path.join(FONT_DIR, COMMON_TBL if sc == 'Common' else 'Reisyo_%s_z_tbl.bin' % sc)
    if not os.path.exists(p):
        return {}
    m = ZTbl(oo(p)).mapping()
    ap = os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % sc)
    n = Atlas(oo(ap)).pages * CELLS_PER_PAGE if os.path.exists(ap) else 0
    return {c: g for c, g in m.items() if 0 < g < n}


corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
cmn = tbl('Common')

need = collections.defaultdict(set)     # 장면 -> 한글 음절
used = collections.defaultdict(set)     # 장면 -> 원문이 쓰는 전각 문자
for rel in corpus:
    sc = K.scene_of(rel)
    if not sc:
        continue
    for e in corpus[rel]:
        used[sc] |= {c for c in e['jp'] if ord(c) > 0x7f}
        t = ko.get(rel, {}).get(str(e['idx']))
        if t:
            need[sc] |= {c for c in t if K.is_hangul(c)}

print('%-16s %6s %8s %8s %8s %8s'
      % ('장면', '음절', '원문자', '장면표에', '공용표에', '쓸수있는칸'))
short = []
for sc in sorted(need):
    st = tbl(sc)
    u = used[sc]
    ins = {c for c in u if c in st}
    inc = {c for c in u if c in cmn}
    # 장면 표에 있는 글자 -> 그 칸을 쓰면 조회 성공이 보장된다.
    #   ⛔공용 표에도 있는 글자는 «공용이 먼저 이길» 수 있어 뺀다(칸이 달라진다).
    usable = {c: st[c] for c in ins if c not in cmn}
    cells = set(usable.values())
    ok = len(cells) >= len(need[sc])
    print('%-16s %6d %8d %8d %8d %8d %s'
          % (sc, len(need[sc]), len(u), len(ins), len(inc), len(cells),
             '' if ok else '★부족'))
    if not ok:
        short.append((sc, len(need[sc]), len(cells)))
print()
print('부족한 장면 %d개' % len(short))
for sc, n, c in short:
    print('   %-16s 음절 %d > 쓸 수 있는 칸 %d' % (sc, n, c))
