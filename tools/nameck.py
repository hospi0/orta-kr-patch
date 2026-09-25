"""★고유명사 표기가 파일마다 갈리지 않았는지 대조한다.

원문의 «가타카나 낱말»을 기준으로 삼는다. 같은 가타카나가 나오는 항목들에서
한국어 표기가 둘 이상으로 갈리면 그게 불일치다.

찾는 법
  · 가타카나 T 가 나오는 항목 집합 E(T) 를 만든다.
  · 한국어 낱말 w 마다 «E(T) 안에서 나오는 비율»과 «E(T) 밖에서 나오는 비율»을 본다.
    T 의 번역이라면 E(T) 에 몰려 있다.
  · 그런 낱말이 둘 이상이고 서로 «비슷한 철자»면 표기가 갈린 것이다.

    python nameck.py            # 갈린 것만
    python nameck.py --all      # 가타카나별 표기 전부
"""
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS
import check_ko as K

CODE = re.compile(r'\$[cw]\d+|%[si]\d')
WORD = re.compile(r'[가-힣]{2,}')
KATA = re.compile(r'[ァ-ヴー]{2,}')


def near(a, b):
    """편집거리 1 이하인가 — 표기 흔들림(메아/메어, 챠/차)을 잡는다."""
    if a == b:
        return False
    # ⛔조사가 붙었을 뿐인 짝(포드 / 포드를)은 «갈림»이 아니다
    if a.startswith(b) or b.startswith(a):
        return False
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(1 for x, y in zip(a, b) if x != y) == 1
    s, t = (a, b) if len(a) < len(b) else (b, a)
    for i in range(len(t)):
        if t[:i] + t[i + 1:] == s:
            return True
    return False


def main():
    ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
    corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
    ent = {}                       # (파일,idx) -> (원문, 번역)
    for rel in corpus:
        for e in corpus[rel]:
            t = ko.get(rel, {}).get(str(e['idx']))
            if t:
                ent[(rel, e['idx'])] = (e['jp'], CODE.sub('', t))

    kata_e = collections.defaultdict(set)
    word_e = collections.defaultdict(set)
    for key, (jp, t) in ent.items():
        for m in KATA.findall(jp):
            kata_e[m].add(key)
        for w in WORD.findall(t.replace('\n', ' ')):
            word_e[w].add(key)

    show_all = '--all' in sys.argv
    bad = 0
    for T in sorted(kata_e, key=lambda x: (-len(kata_e[x]), x)):
        E = kata_e[T]
        if len(E) < 2:
            continue
        cands = []
        for w, W in word_e.items():
            inside = len(E & W)
            if inside < 2:
                continue
            # E 안에 몰려 있고, E 를 상당히 덮어야 «그 이름»이다
            if inside / len(W) >= 0.8 and inside / len(E) >= 0.3:
                cands.append((w, inside, len(W)))
        cands.sort(key=lambda x: -x[1])
        if not cands:
            continue
        # 서로 비슷한 철자가 둘 이상이면 표기가 갈린 것
        split = [(a, b) for i, a in enumerate(cands)
                 for b in cands[i + 1:] if near(a[0], b[0])]
        if split or show_all:
            tag = '★갈림' if split else '     '
            print('%s %-14s 항목 %2d : %s'
                  % (tag, T, len(E),
                     ' · '.join('%s(%d/%d)' % (w, i, n) for w, i, n in cands[:5])))
            bad += bool(split)
    print()
    print('표기가 갈린 가타카나 %d개' % bad)


if __name__ == '__main__':
    main()
