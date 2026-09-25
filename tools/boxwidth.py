"""파일별 «창 폭»을 원문에서 추정한다.

한 항목의 원문 최대 줄 폭은 그 항목이 «우연히» 짧았을 뿐일 수 있다.
같은 화면을 쓰는 파일 안에서 «가장 넓은 원문 줄»이 창 폭의 하한이다.
"""
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS

CODE = re.compile(r'\$[cw]\d+|%[si]\d')


def width(s):
    s = CODE.sub('', s)
    return sum(2 if unicodedata.east_asian_width(c) in 'WFA' else 1 for c in s)


corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
print('%-42s %8s %8s %8s' % ('파일', '원문최대', '번역최대', '번역>원문'))
for rel in sorted(corpus):
    wj = wk = 0
    over = 0
    for e in corpus[rel]:
        for ln in e['jp'].split('\n'):
            wj = max(wj, width(ln))
        t = ko.get(rel, {}).get(str(e['idx']))
        if t:
            m = max(width(x) for x in t.split('\n'))
            wk = max(wk, m)
    for e in corpus[rel]:
        t = ko.get(rel, {}).get(str(e['idx']))
        if t and max(width(x) for x in t.split('\n')) > wj:
            over += 1
    print('%-42s %8d %8d %8d' % (os.path.basename(rel), wj, wk, over))
