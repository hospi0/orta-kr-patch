"""★★★Menu(4페이지) 아틀라스의 «글리프 실제 픽셀 위치»를 실측해 표로 만든다.

왜:
  Menu 아틀라스는 우리 28px 격자에 안 맞는다(행마다 x 시작이 다르다).
  칸 번호 공식을 맞추려다 여러 번 헛짚었다. 공식을 포기하고 **위치를 직접 잰다.**

방법(양성 대조 내장):
  1페이지 아틀라스(Common·Movie·Stage…)는 표↔그림이 정확하다(Common 칸 40..55 = ■0123…).
  그 아틀라스의 글리프를 «정답 그림»으로 삼아, Menu 평면에서 그 그림이 있는 자리를 찾는다.
  ⇒ 그 문자(코드)를 쓰면 게임이 그 자리를 그린다는 뜻이므로, 거기에 한글을 칠하면 된다.

    python menupos.py [장면=Menu]     -> work/pos_<장면>.json  {문자: [x, y]}
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from project import ROOT, FONT_DIR, WORK, COMMON_TBL, SCENES
from ztbl import ZTbl
from atlaswrite import Atlas, BLOCKS_X, PAGE_W, PAGE_H

ORIG = os.path.join(WORK, 'orig')
ONE_PAGE = ['Common'] + [s for s in SCENES if s != 'Menu']


def oo(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


def tbl(sc):
    p = os.path.join(FONT_DIR, COMMON_TBL if sc == 'Common' else 'Reisyo_%s_z_tbl.bin' % sc)
    return ZTbl(oo(p)).mapping() if os.path.exists(p) else {}


def atl(sc):
    return Atlas(oo(os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % sc)))


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


def nrm(v):
    v = v.astype(np.float32).ravel()
    v = v - v.mean()
    n = np.linalg.norm(v)
    return v / n if n > 1e-6 else v


def main():
    sc = sys.argv[1] if len(sys.argv) > 1 else 'Menu'
    a = atl(sc)
    surf = surface(a)
    st = tbl(sc)
    print('%s 평면 %dx%d · 표 문자 %d' % (sc, surf.shape[1], surf.shape[0], len(st)))

    # 후보 자리: y = 페이지*512 + 행*28, x = 4의 배수
    cand = []
    for page in range(a.pages):
        for row in range(PAGE_H // 28):
            y = page * PAGE_H + row * 28
            for x in range(0, PAGE_W - 28 + 1, 4):
                cand.append((x, y))
    M = np.stack([nrm(surf[y:y + 28, x:x + 28]) for x, y in cand])
    print('후보 자리 %d개' % len(M))

    # 오라클 글리프 (1페이지 아틀라스 = 신뢰)
    ref = {}
    for o in ONE_PAGE:
        try:
            m, aa = tbl(o), atl(o)
        except Exception:
            continue
        n = aa.pages * 324
        for c, g in m.items():
            if c in ref or c not in st or g >= n:
                continue
            arr = np.frombuffer(bytes(aa.cell_alpha(g)), dtype=np.uint8).reshape(28, 28)
            if arr.max() < 16:
                continue
            ref[c] = nrm(arr)
    print('오라클로 쓸 수 있는 문자 %d개' % len(ref))

    out, good = {}, 0
    chars = sorted(ref)
    R = np.stack([ref[c] for c in chars])
    B = 200
    # ★★«최고점»만 보면 안 된다 — 비슷한 글자(何↔価)에 잘못 붙는다.
    #   1등이 «확실히» 앞설 때만 앵커로 인정한다. 애매하면 버린다.
    #   기준: 1등 ≥ 0.99 이고 2등과의 차이 ≥ 0.03
    #   ⛔이걸 안 하면 행마다 기준선이 흔들려 위치표가 통째로 어긋난다.
    MIN, MARGIN = 0.99, 0.03
    for i in range(0, len(chars), B):
        sc_ = R[i:i + B] @ M.T
        for j in range(sc_.shape[0]):
            row = sc_[j]
            k = int(np.argmax(row))
            v = float(row[k])
            second = float(np.partition(row, -2)[-2])
            if v >= MIN and v - second >= MARGIN:
                out[chars[i + j]] = list(cand[k])
                good += 1
    print('위치를 확정한 문자 %d / %d' % (good, len(chars)))
    dst = os.path.join(WORK, 'pos_%s.json' % sc)
    with open(dst, 'w', encoding='utf-8', newline='') as f:
        json.dump(out, f, ensure_ascii=False)
    print('-> %s' % dst)


if __name__ == '__main__':
    main()
