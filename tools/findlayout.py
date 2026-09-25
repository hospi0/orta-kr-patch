"""★★다중 페이지 아틀라스의 «진짜 칸 배치»를 실측한다.

방법(양성 대조가 내장된다):
  1. Common 아틀라스는 1페이지고, 표↔그림이 맞는 게 확인됐다(칸 40..55 = ■0123456789ABCDE).
     ⇒ Common 의 칸 그림은 «정답 글리프»다.
  2. Common 과 Menu 두 표에 «둘 다» 있는 문자를 고른다.
  3. Menu 아틀라스의 알파 평면 전체를 펴서, 그 정답 글리프가 «실제로 어디 있는지» 찾는다.
  4. 표가 말하는 칸 번호와 실제 픽셀 좌표를 맞춰 보면 배치 규칙이 나온다.

    python findlayout.py [장면=Menu] [개수=12]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from project import ROOT, FONT_DIR, WORK, COMMON_TBL
from ztbl import ZTbl
from atlaswrite import Atlas, PAGE_W, PAGE_H, BLOCKS_X, CELLS_PER_PAGE, COLS

ORIG = os.path.join(WORK, 'orig')


def orig_of(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


def alpha_surface(a):
    """아틀라스 본문을 «블록 128개/행» 으로 편 알파 이미지(높이 = 512*pages)."""
    body = bytes(a.body)
    rows = len(body) // 16 // BLOCKS_X          # 블록 행 수
    img = np.zeros((rows * 4, PAGE_W), dtype=np.uint8)
    for br in range(rows):
        base = br * BLOCKS_X * 16
        for bx in range(BLOCKS_X):
            blk = body[base + bx * 16: base + bx * 16 + 8]
            v = int.from_bytes(blk, 'little')
            for yy in range(4):
                for xx in range(4):
                    nib = (v >> ((yy * 4 + xx) * 4)) & 0xF
                    img[br * 4 + yy, bx * 4 + xx] = nib * 17
    return img


def main():
    sc = sys.argv[1] if len(sys.argv) > 1 else 'Menu'
    want = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    cmn_t = ZTbl(orig_of(os.path.join(FONT_DIR, COMMON_TBL))).mapping()
    cmn_a = Atlas(orig_of(os.path.join(FONT_DIR, 'Zenkaku_Common.txb')))
    sc_t = ZTbl(orig_of(os.path.join(FONT_DIR, 'Reisyo_%s_z_tbl.bin' % sc))).mapping()
    sc_a = Atlas(orig_of(os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % sc)))
    surf = alpha_surface(sc_a)
    print('%s 알파 평면 %dx%d · 페이지 %d' % (sc, surf.shape[1], surf.shape[0], sc_a.pages))

    both = [c for c in sc_t if c in cmn_t and sc_t[c] >= CELLS_PER_PAGE]
    both.sort(key=lambda c: sc_t[c])
    print('%-3s %8s %10s %10s %10s' % ('자', '표의칸', '실제 x', '실제 y', '맞은칸(모델)'))
    n = 0
    for c in both:
        ref = np.frombuffer(bytes(cmn_a.cell_alpha(cmn_t[c])), dtype=np.uint8)
        ref = ref.reshape(28, 28).astype(np.float32)
        if ref.max() < 16:
            continue
        r = ref - ref.mean()
        rn = np.linalg.norm(r)
        if rn < 1e-6:
            continue
        r = r / rn
        bestv, bestp = -2.0, None
        H, W = surf.shape
        for y in range(0, H - 28, 4):
            for x in range(0, W - 28, 4):
                p = surf[y:y + 28, x:x + 28].astype(np.float32)
                p = p - p.mean()
                pn = np.linalg.norm(p)
                if pn < 1e-6:
                    continue
                v = float((p / pn * r).sum())
                if v > bestv:
                    bestv, bestp = v, (x, y)
        if bestv < 0.75:
            continue
        x, y = bestp
        gcol, grow = x // 28, y // 28
        model = (y // PAGE_H) * CELLS_PER_PAGE + ((y % PAGE_H) // 28) * COLS + gcol
        print('%-3s %8d %10d %10d %10d   corr %.3f'
              % (c, sc_t[c], x, y, model, bestv))
        n += 1
        if n >= want:
            break


if __name__ == '__main__':
    main()
