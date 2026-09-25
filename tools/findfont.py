"""Common 과 «같은 글리프 배치»를 가진 아틀라스를 전 디스크에서 찾는다.

근거: Common 을 통째로 비웠는데도 일본어가 정상 출력됐다.
      그런데 글리프 인덱스 배치(あ=104 …)는 z_tbl 그대로 맞는다.
      ⇒ **같은 배치를 가진 사본이 다른 파일에 있다.**

지문 = 칸별 잉크 픽셀 수 324개. 크기 제한 없이, **모든 페이지**를 본다.
"""
import os
import struct
from pcmp import decompress
from dxt import decode_alpha
from cells import PAGE_W, PAGE_H, PAGE_BYTES, COLS
from project import ROOT, FONT_DIR, GLYPH_W, GLYPH_H, pristine

MAX = 40 * 1024 * 1024


def planes_of(path):
    d = open(path, 'rb').read()
    if d[:4] == b'PCMP':
        try:
            d = decompress(d)
        except Exception:
            return
    if d[:4] != b'TXRB':
        return
    pages = struct.unpack_from('<I', d, 4)[0]
    if not 1 <= pages <= 64:
        return
    start = 0x20 if pages == 1 else 0x50
    for i in range(pages):
        s = start + i * PAGE_BYTES
        if s + PAGE_BYTES > len(d):
            return
        yield i, decode_alpha(d[s:s + PAGE_BYTES], PAGE_W, PAGE_H)


def sig(plane):
    out = []
    for g in range(COLS * (PAGE_H // GLYPH_H)):
        r, c = divmod(g, COLS)
        n = 0
        for y in range(GLYPH_H):
            b = (r * GLYPH_H + y) * PAGE_W + c * GLYPH_W
            n += sum(1 for v in plane[b:b + GLYPH_W] if v)
        out.append(n)
    return out


if __name__ == '__main__':
    base = None
    for i, pl in planes_of(pristine(os.path.join(FONT_DIR, 'Zenkaku_Common.txb'))):
        base = sig(pl)
        break
    nz = sum(1 for v in base if v)
    print('기준 Zenkaku_Common: 잉크 칸 %d' % nz)

    hits = []
    for dp, dn, fns in os.walk(ROOT):
        for fn in fns:
            if not fn.lower().endswith(('.txb', '.spr', '.bin')):
                continue
            p = os.path.join(dp, fn)
            if os.path.getsize(p) > MAX:
                continue
            rel = os.path.relpath(p, ROOT)
            try:
                for i, pl in planes_of(p):
                    s = sig(pl)
                    same = sum(1 for a, b in zip(base, s) if a == b and a > 0)
                    if same >= 150:
                        hits.append((same, rel, i))
                        print('  %-52s p%d  일치 %d/%d' % (rel, i, same, nz))
            except Exception as e:
                continue
    print('\n후보 %d개' % len(hits))
    for h in sorted(hits, reverse=True)[:10]:
        print('  %4d  %s p%d' % h)
