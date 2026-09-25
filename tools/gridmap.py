"""★★★다중 페이지 아틀라스의 «표값 -> 픽셀 위치» 완전 대응표를 만든다.

실측으로 얻은 사실(2026-08-31, `tools/menupos.py` 469쌍):
  · 한 행 안의 칸 간격은 **28**.
  · x 시작점이 **페이지마다** 다르다 — page0=16 · page1=20 · page2=24 · page3=0.
  · 표값은 «읽는 순서»로 단조 증가한다(469쌍 중 역행 1건).

가설: 표값 = «잉크가 있는 칸»을 읽는 순서로 센 번호(빈 칸은 건너뛴다).
      이걸 실측 469쌍으로 검증한다.

    python gridmap.py <장면>      -> work/gridmap_<장면>.json  {표값: [x, y]}
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from project import ROOT, FONT_DIR, WORK
from ztbl import ZTbl
from atlaswrite import Atlas, BLOCKS_X, PAGE_W, PAGE_H

ORIG = os.path.join(WORK, 'orig')


def oo(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


def surface(a):
    body = bytes(a.body)
    rows = len(body) // 16 // BLOCKS_X
    b = np.frombuffer(body, dtype=np.uint8).reshape(-1, 16)[:, :8]
    bits = np.unpackbits(b, axis=1, bitorder='little').reshape(-1, 16, 4)
    vals = (bits * np.array([1, 2, 4, 8])).sum(axis=2).astype(np.uint8) * 17
    vals = vals.reshape(-1, 4, 4)
    img = np.zeros((rows * 4, PAGE_W), dtype=np.uint8)
    k = 0
    for br in range(rows):
        for bx in range(BLOCKS_X):
            img[br * 4:br * 4 + 4, bx * 4:bx * 4 + 4] = vals[k]
            k += 1
    return img


def grid(pages, offs):
    """읽는 순서로 (x, y) 를 늘어놓는다."""
    out = []
    for p in range(pages):
        off = offs[p]
        cols = (PAGE_W - off) // 28
        for r in range(PAGE_H // 28):
            for c in range(cols):
                out.append((off + c * 28, p * PAGE_H + r * 28))
    return out


def main():
    sc = sys.argv[1] if len(sys.argv) > 1 else 'Menu'
    a = Atlas(oo(os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % sc)))
    surf = surface(a)
    offs = [(16 + 4 * p) % 28 for p in range(a.pages)]
    print('%s 페이지 %d · x 시작점 %s' % (sc, a.pages, offs))
    cells = grid(a.pages, offs)
    ink = [int((surf[y:y + 28, x:x + 28] > 40).sum()) for x, y in cells]
    print('격자 칸 %d개 · 잉크 있는 칸 %d개' % (len(cells), sum(1 for v in ink if v)))

    # 잉크 있는 칸에 읽는 순서로 번호를 매긴다
    val2pos, k = {}, 0
    for (x, y), v in zip(cells, ink):
        if v:
            val2pos[k] = (x, y)
            k += 1
    print('번호 매긴 칸 %d개' % k)

    # --- 실측 469쌍으로 검증 ---
    pp = os.path.join(WORK, 'pos_%s.json' % sc)
    hit = miss = 0
    if os.path.exists(pp):
        pos = json.load(open(pp, encoding='utf-8'))
        m = ZTbl(oo(os.path.join(FONT_DIR, 'Reisyo_%s_z_tbl.bin' % sc))).mapping()
        bad = []
        for c, xy in pos.items():
            v = m.get(c)
            if v is None or v == 0:
                continue
            got = val2pos.get(v)
            if got == tuple(xy):
                hit += 1
            else:
                miss += 1
                if len(bad) < 10:
                    bad.append((c, v, tuple(xy), got))
        print('검증: 일치 %d · 불일치 %d' % (hit, miss))
        for c, v, want, got in bad:
            print('   %s 표값 %-5d 실측 %-12s 예측 %s' % (c, v, want, got))
    dst = os.path.join(WORK, 'gridmap_%s.json' % sc)
    with open(dst, 'w', encoding='utf-8', newline='') as f:
        json.dump({str(k2): list(v2) for k2, v2 in val2pos.items()}, f)
    print('-> %s' % dst)


if __name__ == '__main__':
    main()
