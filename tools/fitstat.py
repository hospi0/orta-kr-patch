"""번역문을 «원문과 정확히 같은 바이트»로 넣을 수 있는지 실측.

빌더의 encode() 와 같은 셈법으로 번역문 바이트를 재고, 원문 바이트와 비교한다.
  · R <= L 이면 전각공백(2B)/반각공백(1B) 로 채워 딱 맞출 수 있다.
  · R  > L 이면 줄여야 한다 — 그 양을 파일별로 집계한다.
"""
import json
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS, WORK
import check_ko as K

FW = {' ': '　', '.': '。'}


def nbytes(t, smap_len=2):
    n = 0
    for c in t:
        if c == '\n':
            n += 1
        elif c == K.HALF_SP:
            n += 1
        elif K.is_hangul(c):
            n += smap_len
        else:
            n += len(FW.get(c, c).encode('cp932'))
    return n


corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))

rows = []
tot_over = tot_items = 0
over_bytes = 0
for rel in sorted(corpus):
    kk = ko.get(rel, {})
    n = over = ob = 0
    worst = 0
    for e in corpus[rel]:
        t = kk.get(str(e['idx']))
        if not t:
            continue
        n += 1
        r = nbytes(t)
        if r > e['bytes']:
            over += 1
            ob += r - e['bytes']
            worst = max(worst, r - e['bytes'])
    rows.append((os.path.basename(rel), n, over, ob, worst))
    tot_items += n
    tot_over += over
    over_bytes += ob

print('%-42s %6s %6s %8s %6s' % ('파일', '번역', '초과', '초과바이트', '최대'))
for r in rows:
    print('%-42s %6d %6d %8d %6d' % r)
print()
print('번역 항목 %d · 원문보다 긴 항목 %d (%.1f%%) · 초과 합계 %d B · '
      % (tot_items, tot_over, 100.0 * tot_over / max(tot_items, 1), over_bytes))
