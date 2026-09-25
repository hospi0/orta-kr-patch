"""corpus.json 의 «원문»이 정말 무수정 원본인지 검산 — 대체 코드가 섞였을 가능성."""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, TRANS, WORK
from msgrec import records

ORIG = os.path.join(WORK, 'orig')
corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
rel = [r for r in corpus if 'db_world' in r][0]

# 1) corpus 의 jp 와 work/orig 의 실제 바이트를 대조
d = open(os.path.join(ORIG, rel), 'rb').read()
rs = records(d)
same = diff = 0
for e in corpus[rel]:
    i = e['idx']
    if i >= len(rs):
        continue
    if rs[i]['jp'] == e['jp']:
        same += 1
    else:
        diff += 1
        if diff <= 3:
            print('불일치 idx %d' % i)
            print('  corpus: %r' % e['jp'][:80])
            print('  orig  : %r' % rs[i]['jp'][:80])
print('corpus vs work/orig : 같음 %d · 다름 %d' % (same, diff))

# 2) 문제의 «어느 표에도 없는» 글자가 원본 어디에 나오는지
probe = '久九乾仰任併修倍候偉働僚兄克六冬冷'
cnt = collections.Counter()
where = {}
for i, r in enumerate(rs):
    for ch in r['jp']:
        if ch in probe:
            cnt[ch] += 1
            where.setdefault(ch, (i, r['jp'][:60]))
print()
print('work/orig 안에서 그 글자들:')
for ch in probe:
    if ch in cnt:
        i, t = where[ch]
        print('  %s x%-3d  idx %-4d %r' % (ch, cnt[ch], i, t))
    else:
        print('  %s 없음' % ch)
