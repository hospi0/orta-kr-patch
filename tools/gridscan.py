"""«28x28 글리프 격자»처럼 생긴 텍스처를 전 디스크에서 찾는다.

판정: 512 폭 DXT3 알파로 풀었을 때
  · 잉크가 28x28 칸 안에 들어가고 칸 경계 1px 이 비어 있는 칸이 많다
  · 그런 칸이 30개 이상
글리프 격자는 이 조건을 강하게 만족하고, 일반 그림은 거의 못 만족한다.
"""
import os
import sys
import struct
from pcmp import decompress
from dxt import decode_alpha
from project import ROOT, GLYPH_W, GLYPH_H

W = 512
PAGE = W * W


def pages_of(path):
    d = open(path, 'rb').read()
    if d[:4] == b'PCMP':
        try:
            d = decompress(d)
        except Exception:
            return
    if d[:4] != b'TXRB':
        return
    n = struct.unpack_from('<I', d, 4)[0]
    if not 1 <= n <= 64:
        return
    body = d[0x20:]
    for i in range(max(1, len(body) // PAGE)):
        s = i * PAGE
        if s + PAGE > len(body):
            return
        yield i, decode_alpha(body[s:s + PAGE], W, W)


def grid_score(pl):
    cols, rows = W // GLYPH_W, W // GLYPH_H
    good = 0
    for r in range(rows):
        for c in range(cols):
            ink = 0
            border = 0
            for y in range(GLYPH_H):
                b = (r * GLYPH_H + y) * W + c * GLYPH_W
                row = pl[b:b + GLYPH_W]
                ink += sum(1 for v in row if v)
                if y in (0, GLYPH_H - 1):
                    border += sum(1 for v in row if v)
                else:
                    border += (1 if row[0] else 0) + (1 if row[-1] else 0)
            if 30 <= ink <= 500 and border == 0:
                good += 1
    return good


if __name__ == '__main__':
    only = sys.argv[1] if len(sys.argv) > 1 else None
    res = []
    for dp, dn, fns in os.walk(ROOT):
        for fn in fns:
            if not fn.lower().endswith('.txb'):
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, ROOT)
            if only and only.lower() not in rel.lower():
                continue
            if os.path.getsize(p) > 40 * 1024 * 1024:
                continue
            try:
                for i, pl in pages_of(p):
                    s = grid_score(pl)
                    if s >= 30:
                        res.append((s, rel, i))
                        print('  %-52s p%-2d 격자칸 %d' % (rel, i, s))
                    if i > 8:
                        break
            except Exception:
                continue
    print('\n후보 %d' % len(res))
    for s, rel, i in sorted(res, reverse=True)[:15]:
        print('  %4d  %s p%d' % (s, rel, i))
