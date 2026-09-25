"""★도감(Menu 장면) 음절 예산 계산 — «몇 개를 줄여야 ■ 가 사라지는가».

Menu 장면 = 도감 3파일 + 무비 갤러리 설명 + 서브시나리오 데모.
이 장면이 쓸 수 있는 칸은 «공용 아틀라스에서 받은 칸» + «Menu 아틀라스에서 실측한 자리»
로 정해져 있다. 필요 음절이 그보다 많으면 남는 음절은 전부 ■ 로 나온다.

    python dbsyl.py             # 현황 + 줄여야 할 양
    python dbsyl.py --rare N    # 드문 음절 N개와 그게 든 낱말을 뽑는다
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


def menu_files(ko):
    return [r for r in ko if K.scene_of(r) == 'Menu']


def main():
    ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
    files = sorted(menu_files(ko))
    cnt = collections.Counter()
    where = collections.defaultdict(set)
    for rel in files:
        for k, t in ko[rel].items():
            for ch in CODE.sub('', t):
                if K.is_hangul(ch):
                    cnt[ch] += 1
                    where[ch].add((os.path.basename(rel), k))
    print('Menu 장면 파일 %d개' % len(files))
    for rel in files:
        n = sum(1 for t in ko[rel].values() for c in t if K.is_hangul(c))
        print('  %-32s 항목 %4d · 한글 %6d자' % (os.path.basename(rel), len(ko[rel]), n))
    print()
    print('서로 다른 음절 %d개 · 총 %d자' % (len(cnt), sum(cnt.values())))

    # 실제 배정 결과(빌드가 남긴 것)를 읽어 «칠한 자리»를 센다
    from project import WORK
    cm = json.load(open(os.path.join(WORK, 'charmap_all.json'), encoding='utf-8'))
    painted = set(cm.get('Menu', {}))
    common = set(cm.get('Common', {}))
    ok = (painted | common) & set(cnt)
    bad = set(cnt) - ok
    print('  · 공용 아틀라스로 해결   %4d' % len(common & set(cnt)))
    print('  · Menu 아틀라스로 해결   %4d' % len(painted & set(cnt)))
    print('  · ■ 로 나오는 음절       %4d  (글자 수 %d)'
          % (len(bad), sum(cnt[c] for c in bad)))
    print()
    print('★목표 = 서로 다른 음절을 %d개 이하로 (지금 %d개, %d개 초과)'
          % (len(ok), len(cnt), len(cnt) - len(ok)))

    n = 40
    for a in sys.argv[1:]:
        if a.startswith('--rare'):
            n = int(sys.argv[sys.argv.index(a) + 1])
    rare = sorted(bad, key=lambda c: (cnt[c], c))
    print()
    print('■ 음절을 «드문 순»으로 %d개 — 이걸 없애면 그만큼 줄어든다' % min(n, len(rare)))
    line = []
    for c in rare[:n]:
        line.append('%s(%d)' % (c, cnt[c]))
    print('  ' + ' '.join(line))
    print()
    tail = collections.Counter()
    for c in bad:
        tail[cnt[c]] += 1
    print('■ 음절의 출현 횟수 분포:')
    for k in sorted(tail)[:12]:
        print('   %3d회 짜리 %4d개' % (k, tail[k]))


if __name__ == '__main__':
    main()
