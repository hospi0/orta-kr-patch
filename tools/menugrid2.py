"""★★★Menu 아틀라스 «표값 -> 픽셀 위치» 를 «글리프 대조 + 순서 제약»으로 푼다.

배경
  · Menu 는 4쪽짜리라 `값 = 라스터 번호` 공식이 안 맞는다(쪽마다 x 기준 16/20/24/0).
  · 기존 앵커 191자리는 «1쪽 장면 아틀라스»를 사전으로 삼은 글리프 대조 결과이고
    정확하다(menugrid.py 가 189/189 재현). 다만 수가 적어 도감 음절이 426개나 ■ 다.
  · 실측: 잉크 있는 자리 1146개 · 표의 서로 다른 값 1144개 → 거의 1:1.
    그리고 «값 오름차순 = 자리 라스터순»이 189/190 쌍에서 성립한다.

그래서
  1. 각 자리의 글리프를 사전에서 찾아 «가능한 값 후보»를 만든다(모호해도 남긴다).
  2. 자리 순서와 값 순서를 «단조 증가»로 묶는 최장 정합을 DP 로 찾는다.
     → 후보가 여럿이어도 순서가 답을 하나로 좁힌다.

    python menugrid2.py            # 결과 보고
    python menugrid2.py --save     # work/gridmap_Menu.json 을 새로 쓴다(백업 남김)
"""
import collections
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import WORK, pristine
from atlaswrite import Atlas, CELLS_PER_PAGE
from ztbl import ZTbl
import build_all as B
from menugrid import BASE, SCENES, build_dict


def positions(a):
    out = []
    for p in range(a.pages):
        for r in range(18):
            for c in range(18):
                x = BASE[p] + c * 28
                if x > 511:
                    continue
                out.append((x, p * 512 + r * 28))
    return out


def main():
    d, nfile = build_dict()
    menu_tbl = ZTbl(pristine(B.tbl_path('Menu'))).mapping()
    a = Atlas(pristine(B.atlas_path('Menu')))
    pos = [xy for xy in positions(a) if a.ink_xy(*xy) > 0]
    vals = sorted(set(menu_tbl.values()))
    vidx = {v: i for i, v in enumerate(vals)}
    print('사전 글리프 %d개 · 잉크 자리 %d개 · 서로 다른 표값 %d개'
          % (len(d), len(pos), len(vals)))

    # 자리 -> 가능한 값 순위 후보
    cand = []
    nempty = 0
    for xy in pos:
        key = bytes(a.cell_alpha_xy(*xy))
        chs = d.get(key) or ()
        vs = sorted({vidx[menu_tbl[c]] for c in chs if c in menu_tbl})
        if not vs:
            nempty += 1
        cand.append(vs)
    sizes = collections.Counter(len(c) for c in cand)
    print('후보 수 분포:', sorted(sizes.items())[:8], '… 후보 없음 %d' % nempty)

    # --- 단조 최장 정합 DP ---
    # dp[i] = (자리 i 까지 봤을 때) 값순위 j 를 마지막으로 쓴 최대 개수
    # 자리는 순서대로, 값 순위도 증가해야 한다.
    import bisect
    best_len = [0] * (len(vals) + 1)     # best_len[j] = 값순위 j 를 «마지막»으로 쓴 최대 길이
    choice = {}
    seq = []
    # 표준 «증가 부분수열» 변형: 각 자리에서 후보 j 를 쓸 때
    #   길이 = 1 + max(best_len[0..j-1])
    prefix = [0] * (len(vals) + 2)
    parent = {}
    bestj = [None] * (len(vals) + 2)
    for i, vs in enumerate(cand):
        upd = []
        for j in vs:
            # j 앞에서의 최대 길이
            m, mp = 0, None
            for jj in range(j):
                if best_len[jj] > m:
                    m, mp = best_len[jj], jj
            upd.append((j, m + 1, (i, mp)))
        for j, L, par in upd:
            if L > best_len[j]:
                best_len[j] = L
                parent[j] = par
    L = max(best_len)
    print('단조 정합 최대 길이 %d' % L)


if __name__ == '__main__':
    main()
