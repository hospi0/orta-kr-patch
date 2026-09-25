"""★대체 코드가 «두 표»에 다 있어 어느 칸이 나올지 모르는 경우를 센다.

증상(2026-08-31 실기 도감): `유닛` -> `등닛`, `버서크` -> `버서경`.
음절에 준 코드가 공용 표에도, 그 장면 표에도 있으면 게임이 어느 쪽을 보느냐에 따라
«다른 칸»이 나온다. 그 칸에 다른 음절을 칠해 놨으면 엉뚱한 글자가 뜬다.

    python ambig.py [장면]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, WORK
from ztbl import ZTbl
import build_all as B


def main():
    pick = [a for a in sys.argv[1:] if not a.startswith('--')]
    cm = json.load(open(os.path.join(WORK, 'charmap_all.json'), encoding='utf-8'))
    cmn_map = ZTbl(B.pristine(B.tbl_path('Common'))).mapping()
    for sc in sorted(cm):
        if pick and sc not in pick:
            continue
        tp = B.tbl_path(sc)
        if sc == 'Common' or not os.path.exists(tp):
            continue
        my = ZTbl(B.pristine(tp)).mapping()
        # 그 장면에서 «공용 칸»을 쓰기로 한 음절 = 코드가 공용 표에 있는 것
        both = []
        for s, v in cm[sc].items():
            ch = v[0] if isinstance(v, list) else v
            if ch in cmn_map and ch in my:
                both.append((s, ch, cmn_map[ch], my[ch]))
        only_c = sum(1 for s, v in cm[sc].items()
                     if (v[0] if isinstance(v, list) else v) in cmn_map
                     and (v[0] if isinstance(v, list) else v) not in my)
        if both:
            print('%-14s 음절 %4d · 공용전용코드 %4d · ★두 표에 다 있음 %4d'
                  % (sc, len(cm[sc]), only_c, len(both)))
            for s, ch, gc, gm in both[:8]:
                print('     %s -> %r  공용칸 %-5d 장면칸 %-5d' % (s, ch, gc, gm))
        else:
            print('%-14s 음절 %4d · 공용전용코드 %4d · 겹침 없음'
                  % (sc, len(cm[sc]), only_c))


if __name__ == '__main__':
    main()
