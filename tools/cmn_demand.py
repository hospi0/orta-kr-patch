"""Common 장면(메인 메뉴 + XBE)의 «음절 수요»를 세어, 줄이기 쉬운 후보를 뽑는다.

공용 아틀라스는 칸이 274개뿐인데 수요가 279라 5개가 ■ 로 밀린다.
한 번만 쓰이는 음절을 다른 표현으로 바꾸면 수요가 그만큼 준다.
"""
import json
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS
import check_ko as K

corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
xk = json.load(open(os.path.join(TRANS, 'xbe_ko.json'), encoding='utf-8'))

cnt = collections.Counter()
where = collections.defaultdict(list)
for rel in corpus:
    if K.scene_of(rel) != 'Common':
        continue
    for e in corpus[rel]:
        t = ko.get(rel, {}).get(str(e['idx']))
        if not t:
            continue
        for s in set(c for c in t if K.is_hangul(c)):
            cnt[s] += t.count(s)
            where[s].append(('msg', e['idx'], t))
for off, t in xk.items():
    for s in set(c for c in t if K.is_hangul(c)):
        cnt[s] += t.count(s)
        where[s].append(('xbe', off, t))

print('Common 고유 음절 %d개 (쓸 수 있는 칸 274)' % len(cnt))
once = [s for s, n in cnt.items() if n == 1]
print('딱 한 번만 쓰이는 음절 %d개: %s' % (len(once), ' '.join(sorted(once))))
print()
print('--- 한 번만 쓰이는 음절이 든 문구 ---')
seen = set()
for s in sorted(once):
    for kind, key, t in where[s][:1]:
        line = t.replace('\n', ' / ')
        print('  %s  [%s %s] %s' % (s, kind, key, line[:70]))
