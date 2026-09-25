"""★도감 음절 줄이기 — «몇 글자를 고치면 ■ 가 몇 개 줄어드는가».

Menu 장면이 쓸 수 있는 칸은 355개(공용 164 + Menu 실측 188 + 3)로 고정이다.
필요 음절 781개 중 426개가 ■ 로 나온다. 칸을 늘리는 길은 막혀 있으니
(Menu 아틀라스는 칸번호↔위치가 불규칙해 실측 191자리 밖은 못 칠한다)
«서로 다른 음절 수»를 줄여야 한다.

한 음절을 없애려면 그 음절이 나오는 «모든 자리»를 고쳐야 한다.
그러니 드문 음절부터 없애는 게 압도적으로 싸다.

    python dbplan.py               # 비용 곡선
    python dbplan.py --list N      # 가장 싼 N개 음절과 그게 든 낱말
"""
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS, WORK
import check_ko as K

CODE = re.compile(r'\$[cw]\d+|%[si]\d')
WORD = re.compile(r'[가-힣]+')
CAP = 355          # build_all 이 보고한 Menu 배정 가능 칸 수


def gather():
    ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
    files = sorted(r for r in ko if K.scene_of(r) == 'Menu')
    cnt = collections.Counter()
    hits = collections.defaultdict(list)
    for rel in files:
        for k, t in ko[rel].items():
            clean = CODE.sub('', t)
            for ch in clean:
                if K.is_hangul(ch):
                    cnt[ch] += 1
            for m in WORD.finditer(clean.replace('\n', ' ')):
                for ch in set(m.group()):
                    hits[ch].append((os.path.basename(rel), k, m.group()))
    return ko, files, cnt, hits


def main():
    ko, files, cnt, hits = gather()
    # ★★■ 목록은 빌더가 남긴 것을 쓴다.
    #   ⛔charmap_all 로 «공용에 있으니 된다»고 세면 안 된다 — 공용 칸은
    #     «그 장면 원문이 그 칸을 가리키는 문자를 쓸 때»만 조회할 수 있다(164/259).
    nd = set(json.load(open(os.path.join(WORK, 'notdef.json'), encoding='utf-8'))['Menu'])
    have = set(cnt) - nd
    need_cut = len(cnt) - CAP
    print('필요 음절 %d개 · 배정 가능 %d칸 -> ★%d개를 없애야 ■ 가 0 이 된다'
          % (len(cnt), CAP, need_cut))
    print()

    # 없앨 후보 = 지금 ■ 인 음절(이미 칸을 받은 음절을 없애면 손해)
    bad = sorted(set(cnt) - have, key=lambda c: (cnt[c], c))
    print('지금 ■ 인 음절 %d개 · 그 글자 수 %d자' % (len(bad), sum(cnt[c] for c in bad)))
    print()
    print('%6s %10s %12s %10s' % ('없앨수', '고칠글자', '남는 ■ 음절', '누적비용'))
    tot = 0
    marks = [50, 100, 150, 200, 250, 300, 350, 400, len(bad)]
    i = 0
    for n in range(1, len(bad) + 1):
        tot += cnt[bad[n - 1]]
        if n in marks:
            print('%6d %10d %12d %10d자' % (n, cnt[bad[n - 1]], len(bad) - n, tot))
        i = n
    print()
    if '--list' in sys.argv:
        n = int(sys.argv[sys.argv.index('--list') + 1])
        print('가장 싼 음절 %d개와 그게 든 낱말' % n)
        for c in bad[:n]:
            ws = collections.Counter(w for _f, _k, w in hits[c])
            print('  %s (%d회) : %s' % (c, cnt[c],
                                        ' '.join('%s×%d' % (w, m) if m > 1 else w
                                                 for w, m in ws.most_common(8))))


if __name__ == '__main__':
    main()
