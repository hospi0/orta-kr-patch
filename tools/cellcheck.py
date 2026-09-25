"""글리프 인덱스 -> 아틀라스 칸 검산 + «같은 배치를 가진 다른 폰트 파일»이 있는지 훑기.

사용: python cellcheck.py [파일경로|all]
"""
import os
import sys
import struct
from pcmp import decompress
from dxt import decode_alpha
from atlas import write_png
from cells import PAGE_W, PAGE_H, PAGE_BYTES, COLS
from ztbl import ZTbl
from project import ROOT, FONT_DIR, COMMON_TBL, WORK, GLYPH_W, GLYPH_H, pristine

TARGET = list(range(100, 118))


def load_plane(path):
    d = open(path, 'rb').read()
    if d[:4] == b'PCMP':
        d = decompress(d)
    if d[:4] != b'TXRB':
        return None, 0
    pages = struct.unpack_from('<I', d, 4)[0]
    start = 0x20 if pages == 1 else 0x50
    if len(d) < start + PAGE_BYTES:
        return None, 0
    return decode_alpha(d[start:start + PAGE_BYTES], PAGE_W, PAGE_H), pages


def strip_png(plane, name):
    w = GLYPH_W * len(TARGET)
    s = bytearray(w * GLYPH_H)
    for k, g in enumerate(TARGET):
        r, c = divmod(g, COLS)
        for y in range(GLYPH_H):
            src = (r * GLYPH_H + y) * PAGE_W + c * GLYPH_W
            s[y * w + k * GLYPH_W:y * w + k * GLYPH_W + GLYPH_W] = plane[src:src + GLYPH_W]
    return write_png(os.path.join(WORK, 'atlas', name), w, GLYPH_H, bytes(s))


def ink_sig(plane):
    """칸별 잉크 픽셀 수 — 다른 파일과 같은 배치인지 비교용 지문."""
    sig = []
    for g in range(324):
        r, c = divmod(g, COLS)
        n = 0
        for y in range(GLYPH_H):
            base = (r * GLYPH_H + y) * PAGE_W + c * GLYPH_W
            n += sum(1 for v in plane[base:base + GLYPH_W] if v)
        sig.append(n)
    return sig


if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else 'check'
    cmn_plane, _ = load_plane(pristine(os.path.join(FONT_DIR, 'Zenkaku_Common.txb')))
    if arg == 'check':
        t = ZTbl(pristine(os.path.join(FONT_DIR, COMMON_TBL)))
        bycell = {}
        for ch, g in t.mapping(drop_sentinel=False).items():
            bycell.setdefault(g, []).append(ch)
        print('z_tbl:', ' '.join(bycell.get(g, ['?'])[0] for g in TARGET))
        print('->', strip_png(cmn_plane, 'cellcheck_Common.png'))
    elif arg == 'all':
        base = ink_sig(cmn_plane)
        print('Zenkaku_Common 과 «칸별 잉크량»이 같은 파일 찾기 (사본 탐지)')
        for dp, dn, fns in os.walk(ROOT):
            for fn in fns:
                if not fn.lower().endswith('.txb'):
                    continue
                p = os.path.join(dp, fn)
                if os.path.getsize(p) > 3 * 1024 * 1024:
                    continue
                try:
                    pl, pages = load_plane(p)
                except Exception:
                    continue
                if pl is None:
                    continue
                s = ink_sig(pl)
                same = sum(1 for a, b in zip(base, s) if a == b)
                if same >= 250:
                    rel = os.path.relpath(p, ROOT)
                    print('  %-46s 페이지 %d  일치 칸 %d/324' % (rel, pages, same))
                    strip_png(pl, 'cellcheck_%s.png' % fn.replace('.txb', ''))
