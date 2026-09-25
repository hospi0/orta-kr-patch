"""★한 글리프가 아틀라스 평면 «어디에» 있는지 전면 탐색(빠른 슬라이딩 상관).

오라클 = 다른(1페이지) 아틀라스의 같은 문자 칸. 1페이지 모델은 Common 으로 검증됐다.

    python findglyph.py <대상장면> <오라클장면> <문자들>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from project import ROOT, FONT_DIR, WORK, COMMON_TBL
from ztbl import ZTbl
from atlaswrite import Atlas, BLOCKS_X, PAGE_W, PAGE_H, CELLS_PER_PAGE, COLS

ORIG = os.path.join(WORK, 'orig')


def orig_of(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


def tbl(sc):
    p = os.path.join(FONT_DIR, COMMON_TBL if sc == 'Common' else 'Reisyo_%s_z_tbl.bin' % sc)
    return ZTbl(orig_of(p)).mapping()


def atl(sc):
    return Atlas(orig_of(os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % sc)))


def surface(a):
    body = bytes(a.body)
    rows = len(body) // 16 // BLOCKS_X
    img = np.zeros((rows * 4, PAGE_W), dtype=np.uint8)
    b = np.frombuffer(body, dtype=np.uint8).reshape(-1, 16)[:, :8]
    bits = np.unpackbits(b, axis=1, bitorder='little').reshape(-1, 16, 4)
    vals = (bits * np.array([1, 2, 4, 8])).sum(axis=2).astype(np.uint8) * 17
    vals = vals.reshape(-1, 4, 4)                     # 블록당 4x4
    k = 0
    for br in range(rows):
        for bx in range(BLOCKS_X):
            img[br * 4:br * 4 + 4, bx * 4:bx * 4 + 4] = vals[k]
            k += 1
    return img


def locate(surf, ref):
    r = ref.astype(np.float32)
    r = r - r.mean()
    rn = np.linalg.norm(r)
    if rn < 1e-6:
        return None
    r = (r / rn).ravel()
    win = sliding_window_view(surf.astype(np.float32), (28, 28))
    H, W = win.shape[:2]
    flat = win.reshape(H * W, -1)
    mu = flat.mean(axis=1, keepdims=True)
    c = flat - mu
    n = np.linalg.norm(c, axis=1)
    n[n < 1e-6] = 1e9
    score = (c @ r) / n
    j = int(np.argmax(score))
    return float(score[j]), j // W, j % W          # corr, y, x


def main():
    tgt, orc = sys.argv[1], sys.argv[2]
    chars = sys.argv[3]
    tt, ot = tbl(tgt), tbl(orc)
    ta, oa = atl(tgt), atl(orc)
    surf = surface(ta)
    print('%s 평면 %dx%d' % (tgt, surf.shape[1], surf.shape[0]))
    print('%-3s %8s %8s %6s %6s %10s %s'
          % ('자', '표의칸', '오라클칸', 'x', 'y', '실측칸(A모델)', 'corr'))
    for ch in chars:
        if ch not in tt or ch not in ot:
            print('%-3s  (표에 없음: %s)' % (ch, 'target' if ch not in tt else 'oracle'))
            continue
        ref = np.frombuffer(bytes(oa.cell_alpha(ot[ch])), dtype=np.uint8).reshape(28, 28)
        got = locate(surf, ref)
        if got is None:
            print('%-3s  (오라클 칸이 비었음)' % ch)
            continue
        corr, y, x = got
        page, yy = divmod(y, PAGE_H)
        model = page * CELLS_PER_PAGE + (yy // 28) * COLS + x // 28
        print('%-3s %8d %8d %6d %6d %10d   %.3f  %s'
              % (ch, tt[ch], ot[ch], x, y, model, corr,
                 '격자밖' if (x % 28 or yy % 28) else ''))


if __name__ == '__main__':
    main()
