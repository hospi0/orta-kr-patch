"""남은 조판 문제를 «원문과 나란히» 나열한다.

  줄초과 : 원문보다 줄이 많다 -> 상자 위아래를 침범
  줄부족 : 원문보다 줄이 적다 -> 어느 한 줄이 창 폭을 넘칠 수 있다(폭도 같이 잰다)
  붙음   : 12자 이상 공백 없이 이어진다
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


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else 'all'
    corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
    ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
    n = 0
    for rel in sorted(corpus):
        kk = ko.get(rel, {})
        for e in corpus[rel]:
            t = kk.get(str(e['idx']))
            if not t:
                continue
            jl = CODE.sub('', e['jp']).split('\n')
            kl = CODE.sub('', t).split('\n')
            jam = any(len(m) >= 12 for ln in kl
                      for m in re.findall(r'[가-힣]+', ln))
            wj = max(width(x) for x in jl)
            wk = max(width(x) for x in kl)
            tag = None
            if len(kl) > len(jl):
                tag = '줄초과 %d>%d' % (len(kl), len(jl))
            elif len(kl) < len(jl):
                tag = '줄부족 %d<%d' % (len(kl), len(jl))
            if jam:
                tag = (tag + ' + 붙음') if tag else '붙음'
            if not tag:
                continue
            if want != 'all' and want not in tag and want not in rel:
                continue
            n += 1
            print('=== %s idx %s  [%s]  폭 원문%d/번역%d'
                  % (os.path.basename(rel), e['idx'], tag, wj, wk))
            print('  원문: %s' % e['jp'].replace('\n', ' / '))
            print('  번역: %s' % t.replace('\n', ' / '))
    print()
    print('총 %d건' % n)


if __name__ == '__main__':
    main()
