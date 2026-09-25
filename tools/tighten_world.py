"""도감 문체 일괄 정리 — 뜻이 안 변하는 군더더기만 줄인다.

⛔뜻이 달라질 수 있는 치환은 넣지 않는다. 줄 수도 안 변한다(개행을 안 건드림).
★적용 후 반드시 `check_ko.py` 로 개행·제어코드를 재검산할 것.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS
import check_ko as K

KO = os.path.join(TRANS, 'ko.json')

# (찾을 것, 바꿀 것) — 긴 것부터 적용해야 짧은 규칙에 먹히지 않는다
RULES = [
    ('되어 있다', '돼 있다'),
    ('되어 있으며', '돼 있으며'),
    ('되어 있고', '돼 있고'),
    ('하고 있다', '한다'),
    ('하고 있으며', '하며'),
    ('되고 있다', '된다'),
    ('되고 있으며', '되며'),
    ('이루고 있다', '이룬다'),
    ('가지고 있다', '지닌다'),
    ('보유하고 있다', '지닌다'),
    ('활용하고 있다', '활용한다'),
    ('여겨지고 있다', '여겨진다'),
    ('알려져 있다', '알려졌다'),
    ('것으로 보인다', '듯하다'),
    ('것이라고 한다', '다고 한다'),
    ('라고 할 수 있다', '이다'),
    ('할 수 있다고 한다', '한다고 한다'),
    ('하기 위해서는', '하려면'),
    ('하기 위하여', '하려'),
    ('하기 위해', '하려'),
    ('에 대한', '의'),
    ('에 있어서', '에서'),
    ('에 있어', '에'),
    ('이기 때문에', '이라'),
    ('때문에', '탓에'),
    ('그러나 ', '허나 '),
    ('그리고 ', ''),
    ('또한 ', ''),
    ('매우 ', ''),
    ('아주 ', ''),
    ('상당히 ', ''),
    ('수많은', '숱한'),
    ('여겨진다', '보인다'),
    ('진행되어', '진행돼'),
    ('형성되어', '형성돼'),
    ('구성되어', '이루어져'),
    ('사용된다', '쓰인다'),
    ('사용하는', '쓰는'),
    ('사용하여', '써'),
    ('이용하여', '써'),
    ('통하여', '통해'),
    ('하였다', '했다'),
    ('되었다', '됐다'),
    ('하여야', '해야'),
    ('것이다', '것'),
]


def tighten(t):
    for a, b in RULES:
        t = t.replace(a, b)
    return t


def main():
    apply = '--apply' in sys.argv
    target = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') \
        else 'world'
    ko = json.load(open(KO, encoding='utf-8'))
    tot = n = 0
    for rel, d in ko.items():
        if target not in rel:
            continue
        for k, t in list(d.items()):
            s = tighten(t)
            if s == t:
                continue
            if s.count('\n') != t.count('\n'):
                print('★idx%s 개행이 변한다 — 건너뜀' % k)
                continue
            g = K.nbytes(t) - K.nbytes(s)
            if g <= 0:
                continue
            tot += g
            n += 1
            if apply:
                d[k] = s
    print('%s : %d항목에서 %d B 절약' % (target, n, tot))
    if apply:
        shutil.copy2(KO, KO + '.bak5')
        with open(KO, 'w', encoding='utf-8', newline='') as f:
            json.dump(ko, f, ensure_ascii=False, indent=1)
        print('적용 -> %s' % KO)
    else:
        print('※ 보고만. 반영하려면 --apply')


if __name__ == '__main__':
    main()
