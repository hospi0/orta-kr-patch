"""msgrec(구 파서) 항목 ↔ msgwalk(진짜 구조) 항목 대조.

번역표 `trans/ko.json` 은 msgrec 의 «순번»으로 매겨져 있다. 새 빌더는 walk 로
걷기 때문에, 두 파서의 «텍스트 오프셋»으로 짝을 맞출 수 있는지 먼저 확인한다.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS, WORK
from msgwalk import walk

ORIG = os.path.join(WORK, 'orig')
corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))

tot_w = tot_c = matched = ko_matched = ko_lost = 0
print('%-42s %6s %6s %6s %6s %6s' % ('파일', 'walk', 'rec', '짝', '번역', '유실'))
for rel in sorted(corpus):
    d = open(os.path.join(ORIG, rel), 'rb').read()
    w = walk(d)
    woff = {off: (start, ln) for start, ident, off, ln in w}
    es = corpus[rel]
    kk = ko.get(rel, {})
    m = lost = kom = 0
    for e in es:
        if e['off'] in woff:
            m += 1
            if str(e['idx']) in kk:
                kom += 1
        elif str(e['idx']) in kk:
            lost += 1
    tot_w += len(w)
    tot_c += len(es)
    matched += m
    ko_matched += kom
    ko_lost += lost
    print('%-42s %6d %6d %6d %6d %6d'
          % (os.path.basename(rel), len(w), len(es), m, kom, lost))
print()
print('walk %d · rec %d · 오프셋 일치 %d · 번역이 붙은 항목 %d · 짝 못 찾은 번역 %d'
      % (tot_w, tot_c, matched, ko_matched, ko_lost))
