"""★조판 상태 진단 — 「붙은 줄」과 「줄 수 초과」를 센다.

두 증상이 서로 반대다:
  · 붙음   : 띄어쓰기·마침표를 지워 낱말이 붙었다(메뉴 설명문)
  · 넘침   : 원문보다 줄이 많아 상자 위아래를 침범한다(도감 설명문)
예산이 빠듯한 줄 알고 기계적으로 줄인 흔적이다. 지금은 `.msg` 를 키울 수 있다.
"""
import json
import os
import re
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS
import check_ko as K

corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
CODE = re.compile(r'\$[cw]\d+|%[si]\d')


def strip_code(t):
    return CODE.sub('', t)


rows = []
tot = collections.Counter()
for rel in sorted(corpus):
    kk = ko.get(rel, {})
    jam = over = under = n = 0
    for e in corpus[rel]:
        t = kk.get(str(e['idx']))
        if not t:
            continue
        n += 1
        jl = strip_code(e['jp']).split('\n')
        kl = strip_code(t).split('\n')
        if len(kl) > len(jl):
            over += 1
        elif len(kl) < len(jl):
            under += 1
        # 「붙음」 = 한 줄에 한글이 12자 넘게 이어지는데 공백이 하나도 없다
        for ln in kl:
            run = max((len(x) for x in re.findall(r'[가-힣]+', ln)), default=0)
            if run >= 12:
                jam += 1
                break
    if n:
        rows.append((os.path.basename(rel), n, jam, over, under))
        tot['n'] += n
        tot['jam'] += jam
        tot['over'] += over
        tot['under'] += under

print('%-42s %6s %6s %6s %6s' % ('파일', '번역', '붙음', '줄초과', '줄부족'))
for r in rows:
    print('%-42s %6d %6d %6d %6d' % r)
print()
print('합계 : 번역 %d · 붙음 %d · 줄초과 %d · 줄부족 %d'
      % (tot['n'], tot['jam'], tot['over'], tot['under']))
