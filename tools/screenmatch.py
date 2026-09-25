"""★★화면 스크린샷의 글자를 «아틀라스 칸»과 픽셀로 대조해 칸 번호를 확정한다.

눈으로 「갈 같다」고 읽지 말고 숫자로 가른다 → [[feedback_dont_argue_with_user_screen_reading]]
반대로 내 판독을 사용자 판독보다 앞세우지도 않는다. 이 도구는 그 둘 사이의 심판이다.

    python screenmatch.py <스샷.png> <x0> <y0> <칸수> <전진폭> <장면...>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from project import FONT_DIR
from atlaswrite import Atlas, CELLS_PER_PAGE


def cell_bank(scenes):
    bank = []
    for sc in scenes:
        p = os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % sc)
        if not os.path.exists(p):
            continue
        a = Atlas(p)
        n = a.pages * CELLS_PER_PAGE
        for g in range(n):
            arr = np.frombuffer(bytes(a.cell_alpha(g)), dtype=np.uint8)
            arr = arr.reshape(28, 28).astype(np.float32)
            if arr.max() < 16:
                continue
            bank.append((sc, g, arr))
    return bank


def norm(a):
    a = a.astype(np.float32)
    a = a - a.mean()
    n = np.linalg.norm(a)
    return a / n if n > 1e-6 else a


def best(patch, bank, k=5):
    p = norm(patch)
    out = []
    for sc, g, arr in bank:
        out.append((float((p * norm(arr)).sum()), sc, g))
    out.sort(reverse=True)
    return out[:k]


def main():
    png, x0, y0, n, adv = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), \
        int(sys.argv[4]), float(sys.argv[5])
    scenes = sys.argv[6:] or ['Menu']
    im = Image.open(png).convert('L')
    # 화면은 640x480 을 2배로 띄운 것 — 원래 해상도로 되돌린다
    im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
    a = np.asarray(im, dtype=np.float32)
    # 글자는 어둡다 -> 뒤집어 «잉크가 밝은» 마스크로
    a = 255.0 - a
    bank = cell_bank(scenes)
    print('대조 후보 칸 %d개 (%s)' % (len(bank), ','.join(scenes)))
    for i in range(n):
        x = int(round(x0 + i * adv))
        y = int(round(y0))
        patch = a[y:y + 28, x:x + 28]
        if patch.shape != (28, 28):
            print('%2d  범위밖' % i)
            continue
        r = best(patch, bank)
        print('%2d (x=%3d)  %s' % (i, x,
              '  '.join('%s#%d %.3f' % (sc, g, s) for s, sc, g in r)))


if __name__ == '__main__':
    main()
