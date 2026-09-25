"""XBE 문구를 바꿨을 때 Common 음절 수요가 얼마나 주는지 계산한다.

    python cmn_try.py            # 현재 수요와 «쓸 수 있는 음절 목록»
    python cmn_try.py --apply    # trans/xbe_try.json 의 대안을 반영해 재계산
"""
import json
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS
import check_ko as K

CAP = 274      # 공용 아틀라스에서 쓸 수 있는 칸 수 (build_all 실측)


def demand(xk):
    corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
    ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
    cnt = collections.Counter()
    for rel in corpus:
        if K.scene_of(rel) != 'Common':
            continue
        for e in corpus[rel]:
            t = ko.get(rel, {}).get(str(e['idx']))
            if t:
                cnt.update(c for c in t if K.is_hangul(c))
    for t in xk.values():
        cnt.update(c for c in t if K.is_hangul(c))
    return cnt


def main():
    xk = json.load(open(os.path.join(TRANS, 'xbe_ko.json'), encoding='utf-8'))
    base = demand(xk)
    print('현재 고유 음절 %d / 칸 %d  -> ■ %d개'
          % (len(base), CAP, max(0, len(base) - CAP)))

    alt_p = os.path.join(TRANS, 'xbe_try.json')
    if not os.path.exists(alt_p):
        print()
        print('※ trans/xbe_try.json 에 {오프셋: 대안문구} 를 넣고 다시 실행하세요.')
        print()
        print('--- 이미 쓰이는 음절(새로 안 늘어남) ---')
        print(' '.join(sorted(base)))
        return
    alt = json.load(open(alt_p, encoding='utf-8'))
    xk2 = dict(xk)
    xk2.update(alt)
    new = demand(xk2)
    gone = sorted(set(base) - set(new))
    added = sorted(set(new) - set(base))
    print()
    print('바꾼 문구 %d개' % len(alt))
    print('사라진 음절 %d개: %s' % (len(gone), ' '.join(gone)))
    print('새로 생긴 음절 %d개: %s' % (len(added), ' '.join(added)))
    print('결과: 고유 음절 %d -> %d  (■ %d -> %d)'
          % (len(base), len(new), max(0, len(base) - CAP), max(0, len(new) - CAP)))
    if '--apply' in sys.argv:
        if len(new) > CAP:
            print('★아직 %d개 초과 — 반영하지 않습니다.' % (len(new) - CAP))
            return 1
        with open(os.path.join(TRANS, 'xbe_ko.json'), 'w',
                  encoding='utf-8', newline='') as f:
            json.dump(xk2, f, ensure_ascii=False, indent=1)
        print('★trans/xbe_ko.json 에 반영했습니다.')


if __name__ == '__main__':
    sys.exit(main() or 0)
