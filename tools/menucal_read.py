"""★★★menucal 시험 빌드 스샷을 판독해 «표값 -> 아틀라스 자리»를 뽑는다.

화면엔 라벨 12종(가나다라마바사아자카파하)과 ■(못 그린 칸)만 나온다.
자리 후보는 «예측 라스터 번호 ~ +N» 로 좁혀져 있으므로 라벨 하나로 자리가 확정된다.

화면 격자(실측): 첫 칸 x=174 · 열 간격 60 · 줄 간격 56 · 한 줄 16칸.

판독 요령
  · 라벨을 «폰트 견본»과 맞추면 안 된다 — 저해상도라 서로 뭉개진다(가·사로만 몰렸다).
    같은 라벨은 화면에서 «픽셀까지 똑같이» 그려지므로 군집이 훨씬 정확하다.
  · 군집에 이름을 붙이는 건 «이미 자리를 아는 값 191개»가 해 준다.
    그 값이 나올 자리의 라벨은 미리 알 수 있으니, 그게 곧 정답표다.
  · 어느 스샷이 어느 조각인지는 «줄 수 + 마지막 줄 칸 수»로 가른다(조각마다 유일).

    python menucal_read.py <스샷.png> ...
    python menucal_read.py --save <스샷.png> ...   # work/gridmap_Menu2.json 기록
"""
import collections
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import WORK

PLAN = os.path.join(WORK, 'menucal.json')
X0, DX, DY, COLS = 174, 60, 56, 16
CAN = 44                  # 견본 캔버스
FILL = 0.90               # 이 이상 채워져 있으면 ■


def mask_of(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.int16)
    return (a[:, :, 0] > 170) & (a[:, :, 1] > 170) & (a[:, :, 2] > 170)


def rows_of(m):
    band = m[:, X0:X0 + 15 * DX]
    s = band.sum(axis=1)
    groups, st = [], None
    for y in range(len(s)):
        if s[y] > 3:
            if st is None:
                st = y
        elif st is not None:
            groups.append((st, y - 1))
            st = None
    if st is not None:
        groups.append((st, len(s) - 1))
    groups = [g for g in groups if g[1] - g[0] >= 18]
    # 56 간격으로 이어지는 첫 줄을 시작으로 잡는다
    for i in range(len(groups) - 1):
        if abs((groups[i + 1][0] - groups[i][0]) - DY) <= 3:
            return groups[i][0], groups
    return (groups[0][0], groups) if groups else (None, [])


def patch(m, y0, r, c):
    """칸을 «원점 그대로» 잘라 낸다.

    ⛔잉크 상자로 정규화하면 안 된다 — 저해상도에서 라벨이 서로 뭉개진다.
      같은 라벨은 화면에서 «같은 자리에 같은 픽셀»로 그려지므로 원점 정렬이 제일 정확하다.
    """
    y, x = max(y0 + r * DY - 6, 0), X0 + c * DX
    sub = m[y:y + CAN, x:x + CAN]
    if sub.shape != (CAN, CAN) or not sub.any():
        return None, 0
    ys, xs = np.where(sub)
    box = sub[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return sub.ravel().astype(np.float32), float(box.mean())


def main():
    save = '--save' in sys.argv
    shots = sorted(a for a in sys.argv[1:] if not a.startswith('--'))
    plan = json.load(open(PLAN, encoding='utf-8'))
    labels = plan['labels']
    positions = [tuple(p) for p in plan['positions']]
    pidx = {xy: i for i, xy in enumerate(positions)}
    known = {int(k): tuple(x) for k, x in json.load(
        open(os.path.join(WORK, 'gridmap_Menu.json'), encoding='utf-8')).items()}
    # 조각 지문: (줄 수, 마지막 줄 칸 수)
    sig = {}
    for ch in plan['chunks']:
        n = len(ch['values']) + 2
        sig[((n + COLS - 1) // COLS, n % COLS or COLS)] = ch

    cells, meta, pend = [], [], []
    for p in shots:
        m = mask_of(p)
        y0, _g = rows_of(m)
        if y0 is None:
            print('★%s 글자 못 찾음' % os.path.basename(p))
            continue
        grid = {}
        for r in range(13):
            for c in range(COLS):
                v, f = patch(m, y0, r, c)
                if v is None:
                    continue
                grid[(r, c)] = len(cells)
                cells.append(v)
                meta.append((p, r, c, f))
        nrow = max(r for r, _c in grid) + 1
        last = max(c for r, c in grid if r == nrow - 1) + 1
        ch = sig.get((nrow, last))
        print('%s : %d줄 · 마지막 %d칸 -> 조각 %s'
              % (os.path.basename(p), nrow, last,
                 ch['chunk'] if ch else '(뒤에서 소거법으로)'))
        pend.append((p, grid, ch, nrow, last))
    # ★꼬리 칸이 «화면에 아예 안 나오는» 값이면 지문이 어긋난다 -> 남은 하나로 소거
    left = [c for c in plan['chunks']
            if c['chunk'] not in {x[2]['chunk'] for x in pend if x[2]}]
    for i, (p, grid, ch, nrow, last) in enumerate(pend):
        if ch is None and len(left) == 1:
            ch = left[0]
            print('  %s -> 소거법으로 조각 %d' % (os.path.basename(p), ch['chunk']))
        if ch:
            for (r, c), j in grid.items():
                meta[j] = meta[j] + (ch, r * COLS + c)

    # --- 군집 ---
    A = np.array(cells)
    cid, cents = [], []
    for v in A:
        for i, cv in enumerate(cents):
            if np.mean(np.abs(cv - v)) < 0.03:
                cid.append(i)
                break
        else:
            cents.append(v)
            cid.append(len(cents) - 1)
    print('군집 %d개' % len(cents))

    # --- 군집 이름: ①머리표(조각마다 라벨이 정해져 있다) ②자리를 아는 값 ---
    vote = collections.defaultdict(collections.Counter)
    for i, md in enumerate(meta):
        if len(md) < 6:
            continue
        _p, _r, _c, f, ch, k = md
        if f > FILL:
            continue
        if k < 2:
            vote[cid[i]][labels[ch['chunk'] % len(labels)]] += 3
            continue
        vi = k - 2
        if vi < len(ch['values']):
            v = ch['values'][vi]
            if v in known and known[v] in pidx:
                vote[cid[i]][labels[pidx[known[v]] % len(labels)]] += 1
    name = {}
    for g, cnt in vote.items():
        lab, n = cnt.most_common(1)[0]
        if n >= 0.6 * sum(cnt.values()):
            name[g] = lab
    print('이름 붙은 군집 %d개 : %s'
          % (len(name), ''.join(sorted(set(name.values())))))
    big = collections.Counter(cid)
    for g, n in big.most_common(16):
        print('   군집 %-3d %4d칸  이름 %s' % (g, n, name.get(g, '?')))

    # --- 판독 -> 자리 확정 ---
    out, bad, blank, box = {}, 0, 0, 0
    for i, md in enumerate(meta):
        if len(md) < 6:
            continue
        _p, _r, _c, f, ch, k = md
        if k < 2:
            continue
        vi = k - 2
        if vi >= len(ch['values']):
            continue
        v = ch['values'][vi]
        if f > FILL:
            box += 1
            continue
        lab = name.get(cid[i])
        if lab is None:
            bad += 1
            continue
        cands = [j for j in range(max(v - 3, 0), min(v + 12, len(positions)))
                 if labels[j % len(labels)] == lab]
        if len(cands) == 1:
            out[v] = positions[cands[0]]
        else:
            bad += 1
    tot = sum(len(c['values']) for c in plan['chunks'])
    print()
    print('값 %d개 중 — 자리 확정 %d · ■ %d · 판독불가 %d · 화면에 없음 %d'
          % (tot, len(out), box, bad, tot - len(out) - box - bad))
    both = [v for v in known if v in out]
    agree = sum(1 for v in both if out[v] == known[v])
    print('기존 앵커와 겹치는 %d개 중 일치 %d개  ★이게 100%% 여야 믿을 수 있다'
          % (len(both), agree))
    if save and both and agree == len(both):
        merged = {str(k): list(x) for k, x in known.items()}
        merged.update({str(k): list(x) for k, x in out.items()})
        with open(os.path.join(WORK, 'gridmap_Menu2.json'), 'w',
                  encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False)
        print('-> work/gridmap_Menu2.json (%d자리)' % len(merged))
    return 0


if __name__ == '__main__':
    sys.exit(main())
