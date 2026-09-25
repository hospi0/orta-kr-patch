"""붙은 줄을 «원문과 나란히» 뽑는다 — 띄어쓰기 복원 작업용.

    python jamlist.py [파일조각] [--min 12]
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS

CODE = re.compile(r'\$[cw]\d+|%[si]\d')


def runs(t, lo):
    out = []
    for ln in CODE.sub('', t).split('\n'):
        for m in re.finditer(r'[가-힣]+', ln):
            if len(m.group()) >= lo:
                out.append(m.group())
    return out


def main():
    pick = None
    lo = 12
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == '--min':
            lo = int(args[i + 1])
        elif not a.startswith('--'):
            pick = a
    corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
    ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
    n = 0
    for rel in sorted(corpus):
        if pick and pick not in rel:
            continue
        kk = ko.get(rel, {})
        for e in corpus[rel]:
            t = kk.get(str(e['idx']))
            if not t:
                continue
            r = runs(t, lo)
            if not r:
                continue
            n += 1
            print('=== %s idx %s   (최장 %d자)'
                  % (os.path.basename(rel), e['idx'], max(len(x) for x in r)))
            print('  원문: %s' % e['jp'].replace('\n', ' / '))
            print('  번역: %s' % t.replace('\n', ' / '))
    print()
    print('붙은 항목 %d개 (기준 %d자 이상)' % (n, lo))


if __name__ == '__main__':
    main()
