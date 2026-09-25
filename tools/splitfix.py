"""★낱말을 쪼갠 줄바꿈을 «병합 전 번역»의 줄 구조로 되돌린다.

splitscan.py 가 찾은 자리만 고친다. 공백은 반각(U+00A0)으로 넣어 예산을 아낀다.
결과는 `trans/jam_fix.json` 으로 내보내고, 반영은 `jamfix.py --apply` 가 한다
(제어코드·cp932·음절 수요 검사를 그쪽이 하므로 여기서 직접 쓰지 않는다).

    python splitfix.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS
import check_ko as K
import splitscan as S
import unjam

H = K.HALF_SP


def half(t):
    """줄 첫머리 전각 공백(들여쓰기)은 남기고 낱말 사이만 반각으로."""
    out = []
    for ln in t.split('\n'):
        i = 0
        while i < len(ln) and ln[i] == '　':
            i += 1
        out.append(ln[:i] + ln[i:].replace(' ', H).replace(' ', H))
    return '\n'.join(out)


def main():
    ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
    corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
    srcs = unjam.load_sources()
    fix = {}
    for rel in sorted(ko):
        base = os.path.basename(rel)
        budget = {e['idx']: e['bytes'] for e in corpus.get(rel, [])}
        for k, t in sorted(ko[rel].items(), key=lambda x: int(x[0])):
            if '\n' not in t:
                continue
            cand = None
            for _n, rows in srcs:
                s = rows.get(rel, {}).get(k) or rows.get(base, {}).get(k)
                if s and S.bare(s) == S.bare(t):
                    if cand is None or len(S.gaps(s)) > len(S.gaps(cand)):
                        cand = s
            if cand is None:
                continue
            if not [p for p in S.breaks(t) if p not in S.gaps(cand)]:
                continue
            new = half(cand)
            fix.setdefault(base, {})[k] = new
            print('%-28s idx %-5s %+3dB  %s' % (
                base, k, K.nbytes(new) - K.nbytes(t),
                new.replace(H, ' ').replace('\n', ' / ')))
    with open(os.path.join(TRANS, 'jam_fix.json'), 'w', encoding='utf-8') as f:
        json.dump(fix, f, ensure_ascii=False, indent=1)
    print()
    print('-> trans/jam_fix.json  (%d파일 %d항목). 반영은 jamfix.py --apply'
          % (len(fix), sum(len(v) for v in fix.values())))


if __name__ == '__main__':
    main()
