"""원본 `.msg` 의 «불변식»을 검증한다 — 재조립 규칙의 근거.

  1. 모든 항목 시작은 4의 배수다.
  2. 텍스트의 NUL 다음 «다음 항목 시작»까지의 채움 바이트는 전부 0 이다.
  3. 다음 항목 시작 == align4(NUL 위치 + 1)  (walk 가 이미 이 규칙으로 걷는다)

⇒ 이 셋이 참이면 재조립은 «텍스트 + NUL + 0패딩(4정렬)» 로 하면 되고,
  길이 차가 4의 배수일 필요가 «없다».
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import WORK
from msgwalk import walk

ORIG = os.path.join(WORK, 'orig')

bad = 0
files = 0
for dp, dn, fn in os.walk(ORIG):
    for f in sorted(fn):
        if not f.endswith('.msg'):
            continue
        p = os.path.join(dp, f)
        d = open(p, 'rb').read()
        w = walk(d)
        files += 1
        msgs = []
        for i, (start, ident, off, ln) in enumerate(w):
            if start % 4:
                msgs.append('항목%d 시작 0x%X 가 4의 배수가 아님' % (i, start))
            nul = off + ln
            nxt = w[i + 1][0] if i + 1 < len(w) else None
            if nxt is not None:
                if nxt != ((nul + 1 + 3) & ~3):
                    msgs.append('항목%d 다음시작 %d != align4(%d)' % (i, nxt, nul + 1))
                if any(d[nul:nxt]):
                    msgs.append('항목%d 채움에 0 아닌 바이트 %r' % (i, d[nul:nxt]))
        if msgs:
            bad += 1
            print('★', f)
            for m in msgs[:5]:
                print('   ', m)
print()
print('검사 %d개 파일 · 위반 %d개' % (files, bad))
