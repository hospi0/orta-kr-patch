"""★★`.msg` 도 Xbox HDD 캐시에 올라가는지 훑는다.

2026-08-31: 인게임 대사와 판도라 도감이 «원본 일본어»로 그려지고 있다(글리프만 우리 한글).
⇒ 게임이 우리 `.msg` 가 아닌 다른 사본을 읽는다는 뜻. 폰트와 같은 함정을 의심한다
   → [[feedback_game_caches_assets_to_xbox_hdd]]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, WORK

HDD = r'D:\hospi\XEMU\XEMU FILES\Pre-built Xbox HDD image\xbox_hdd.qcow2'
ORIG = os.path.join(WORK, 'orig')
N = 64

needles = {}
for dp, dn, fn in os.walk(ORIG):
    for f in sorted(fn):
        if not f.endswith('.msg'):
            continue
        p = os.path.join(dp, f)
        rel = os.path.relpath(p, ORIG)
        needles[rel + ' [원본]'] = open(p, 'rb').read()[:N]
        cur = os.path.join(ROOT, rel)
        if os.path.exists(cur):
            needles[rel + ' [현재]'] = open(cur, 'rb').read()[:N]

hits = {k: [] for k in needles}
CH = 1 << 25
with open(HDD, 'rb') as f:
    base, tail = 0, b''
    while True:
        b = f.read(CH)
        if not b:
            break
        buf = tail + b
        for k, nd in needles.items():
            i = buf.find(nd)
            while i >= 0:
                hits[k].append(base - len(tail) + i)
                i = buf.find(nd, i + 1)
        base += len(b)
        tail = buf[-N:]

found = 0
for k in sorted(hits):
    if hits[k]:
        found += 1
        print('%-56s %d곳  %s' % (k, len(hits[k]), hits[k][:6]))
print()
print('캐시에서 발견된 항목 %d / %d' % (found, len(needles)))
