"""★★스샷 글자 ↔ 아틀라스 칸 픽셀 대조 (위치 미세탐색 포함).

    python screenmatch2.py <스샷.png> <y> <x1,x2,x3,...> [장면...]
좌표는 «640x480 원해상도» 기준. y 는 글자 줄의 윗변 근처.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from project import FONT_DIR
from atlaswrite import Atlas, CELLS_PER_PAGE

SCENES_DEFAULT = ['Menu']


def nrm(a):
    a = a.astype(np.float32)
    a = a - a.mean()
    n = np.linalg.norm(a)
    return a / n if n > 1e-6 else a


def bank(scenes):
    out = []
    for sc in scenes:
        p = os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % sc)
        if not os.path.exists(p):
            continue
        a = Atlas(p)
        for g in range(a.pages * CELLS_PER_PAGE):
            arr = np.frombuffer(bytes(a.cell_alpha(g)), dtype=np.uint8)
            arr = arr.reshape(28, 28).astype(np.float32)
            if arr.max() < 16:
                continue
            out.append((sc, g, nrm(arr)))
    return out


def main():
    png, y0 = sys.argv[1], int(sys.argv[2])
    xs = [int(v) for v in sys.argv[3].split(',')]
    scenes = sys.argv[4:] or SCENES_DEFAULT
    im = Image.open(png).convert('L')
    im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
    g = np.asarray(im, dtype=np.float32)
    ink = np.clip(120.0 - g, 0, None)
    bk = bank(scenes)
    stack = np.stack([a for _, _, a in bk])
    keys = [(sc, gi) for sc, gi, _ in bk]
    print('후보 칸 %d개 (%s)' % (len(bk), ','.join(scenes)))
    for x in xs:
        rows = []
        for dy in range(-8, 5):
            for dx in range(-8, 5):
                p = ink[y0 + dy:y0 + dy + 28, x + dx:x + dx + 28]
                if p.shape != (28, 28):
                    continue
                sc_ = stack.reshape(len(bk), -1) @ nrm(p).reshape(-1)
                j = int(np.argmax(sc_))
                rows.append((float(sc_[j]), keys[j], dx, dy))
        rows.sort(reverse=True)
        seen, top = set(), []
        for s, k, dx, dy in rows:
            if k in seen:
                continue
            seen.add(k)
            top.append((s, k, dx, dy))
            if len(top) == 4:
                break
        print('x=%3d  %s' % (x, '  '.join(
            '%s#%d %.3f(d%+d,%+d)' % (k[0], k[1], s, dx, dy) for s, k, dx, dy in top)))


if __name__ == '__main__':
    main()
