"""★msgrec 의 «가짜 항목»에 번역이 붙어 있으면 텍스트가 아닌 자리를 덮어쓴다.

판정: walk(진짜 구조) 의 텍스트 오프셋 집합에 없는데 ko.json 에 번역이 있는 레코드.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, TRANS, WORK
from msgrec import records
from msgwalk import walk

ORIG = os.path.join(WORK, 'orig')
corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))

tot = 0
for rel in sorted(corpus):
    o = open(os.path.join(ORIG, rel), 'rb').read()
    woff = {off for st, i, off, ln in walk(o)}
    kk = ko.get(rel, {})
    rows = []
    for e in corpus[rel]:
        if str(e['idx']) not in kk:
            continue
        if e['off'] in woff:
            continue
        rows.append(e)
    if rows:
        print('=== %s : 가짜 항목에 번역 %d개' % (os.path.basename(rel), len(rows)))
        for e in rows[:8]:
            print('   idx %-4d off %-6d %dB  jp=%r' % (e['idx'], e['off'], e['bytes'], e['jp'][:30]))
            print('        ko=%r' % kk[str(e['idx'])][:30])
        tot += len(rows)
print()
print('총 %d개 — 이 자리는 «텍스트가 아니다». 번역을 빼야 한다.' % tot)
