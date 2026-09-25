"""빌드 결과에서 «원본엔 글자가 있는데 새 파일은 비어 버린» 항목을 찾는다.

화면의 `NO TEXT` = 게임이 ID 는 찾았는데 텍스트가 비었다는 뜻이다.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, WORK
from msgwalk import walk

ORIG = os.path.join(WORK, 'orig')
bad = 0
for dp, dn, fn in os.walk(ORIG):
    for f in sorted(fn):
        if not f.endswith('.msg'):
            continue
        rel = os.path.relpath(os.path.join(dp, f), ORIG)
        o = open(os.path.join(ORIG, rel), 'rb').read()
        n = open(os.path.join(ROOT, rel), 'rb').read()
        wo, wn = walk(o), walk(n)
        # ID 로 짝짓는다
        io = {i: (off, ln) for st, i, off, ln in wo if i is not None}
        inn = {i: (off, ln) for st, i, off, ln in wn if i is not None}
        for i in sorted(set(io) & set(inn)):
            lo, ln_ = io[i][1], inn[i][1]
            if lo > 0 and ln_ == 0:
                bad += 1
                print('★%s ID %s : 원본 %dB -> 새 0B' % (f, i, lo))
            elif lo > 4 and ln_ < lo // 3:
                print('  %s ID %s : 원본 %dB -> 새 %dB (많이 짧아짐)' % (f, i, lo, ln_))
print()
print('비어 버린 항목 %d개' % bad)
