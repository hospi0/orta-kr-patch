"""★★줄바꿈이 «낱말 한가운데»를 끊은 곳을 찾는다 — 병합 전 번역과 대조해서.

증상(2026-08-31 실기): 튜토리얼 제목이 `Tutorial1-1드 / 래곤 이동` 으로 나왔다.
reflow 가 폭에 맞춰 다시 접으면서 «공백이 아닌 자리»에서 끊은 것이다.

⛔「줄바꿈 앞뒤가 둘 다 글자면 쪼갠 것」으로 판정하면 안 된다 —
  낱말 경계에서 끊고 공백을 지운 정상 줄바꿈이 전부 걸린다(461곳 오탐).

판정: «병합 전 번역»(공백이 살아 있는 판본)에서 그 자리가 낱말 경계였는지 본다.
  · 공백만 지운 알맹이가 같아야 비교한다. 다르면 판정 불가로 넘긴다.

    python splitscan.py            # 목록
    python splitscan.py --fix      # trans/split_fix.json 으로 «고칠 후보»를 뽑는다
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS
import unjam

WS = re.compile(r'[\s 　]+')


def bare(t):
    return WS.sub('', t)


def gaps(s, nl=True):
    """원본 s 에서 «공백이 있는 알맹이 경계» 집합. 경계 p = 앞에 알맹이 p글자.

    nl=False 면 «줄바꿈»으로 생긴 경계는 세지 않는다.
    ⛔줄바꿈을 공백으로 세면, 우리가 줄을 합친 자리가 전부 «공백 누락»으로 잡힌다.
    """
    out, n = set(), 0
    for ch in s:
        if WS.match(ch):
            if nl or ch != '\n':
                out.add(n)
        else:
            n += 1
    return out


def breaks(t):
    """우리 번역 t 의 `\\n` 이 놓인 알맹이 경계 목록."""
    out, n = [], 0
    for ch in t:
        if ch == '\n':
            out.append(n)
        elif not WS.match(ch):
            n += 1
    return out


def main():
    ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
    srcs = unjam.load_sources()
    bad = {}
    judged = 0
    for rel in sorted(ko):
        base = os.path.basename(rel)
        for k, t in sorted(ko[rel].items(), key=lambda x: int(x[0])):
            if '\n' not in t:
                continue
            cand = None
            for _name, rows in srcs:
                s = rows.get(rel, {}).get(k) or rows.get(base, {}).get(k)
                if s and bare(s) == bare(t):
                    if cand is None or len(gaps(s)) > len(gaps(cand)):
                        cand = s
            if cand is None:
                continue
            judged += 1
            g = gaps(cand)
            hit = [p for p in breaks(t) if p not in g]
            if hit:
                bad.setdefault(rel, []).append((k, t, cand, hit))

    n = 0
    for rel in sorted(bad):
        print('== %s (%d곳)' % (os.path.basename(rel), len(bad[rel])))
        for k, t, s, hit in bad[rel]:
            print('  idx %-5s %s' % (k, t.replace(' ', ' ').replace('\n', ' / ')))
            print('        병합전 %s' % s.replace(' ', ' ').replace('\n', ' / '))
            n += 1
    print()
    print('판정한 항목 %d개 · 낱말을 쪼갠 줄바꿈 %d곳' % (judged, n))


if __name__ == '__main__':
    main()
