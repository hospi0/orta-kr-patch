"""글리프 격자 탐색 — 폭·포맷을 넓혀서.

DXT3 알파 말고 **A8(바이트 = 알파)** 해석도 본다. 폭도 256/512/1024 를 다 본다.
★검출기엔 양성 대조 필수 — 원본 `Zenkaku_Common.txb` 가 반드시 잡혀야 한다
  (feedback_scan_coverage_and_detectors).
"""
import os
import sys
import struct
from pcmp import decompress
from dxt import decode_alpha
from project import ROOT, GLYPH_W, GLYPH_H, FONT_DIR

WIDTHS = (256, 512, 1024)


def score(pl, W, H):
    cols, rows = W // GLYPH_W, H // GLYPH_H
    good = 0
    for r in range(rows):
        for c in range(cols):
            ink = border = 0
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


def variants(path):
    d = open(path, 'rb').read()
    if d[:4] == b'PCMP':
        try:
            d = decompress(d)
        except Exception:
            return
    if d[:4] != b'TXRB':
        return
    body = d[0x20:]
    for W in WIDTHS:
        chunk = W * W
        if len(body) < chunk:
            continue
        # DXT3 알파
        yield ('dxt3', W), decode_alpha(body[:chunk], W, W)
        # A8 직독
        yield ('a8', W), body[:chunk]


if __name__ == '__main__':
    only = sys.argv[1] if len(sys.argv) > 1 else None
    # 양성 대조
    ctrl = os.path.join(FONT_DIR, 'Zenkaku_Common.txb')
    best = 0
    for (fmt, W), pl in variants(ctrl):
        s = score(pl, W, W)
        if s:
            print('[대조] Zenkaku_Common %s w%d -> %d' % (fmt, W, s))
        best = max(best, s)
    if best < 30:
        sys.exit('★검출기가 원본 폰트를 못 잡는다 — 기준을 고쳐야 한다')
    print('대조 통과 (최고 %d)\n' % best)

    hits = []
    for dp, dn, fns in os.walk(ROOT):
        for fn in fns:
            if not fn.lower().endswith('.txb'):
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, ROOT)
            if only and only.lower() not in rel.lower():
                continue
            if 'sprite\\Font' in rel:
                continue                      # 이미 아는 것
            if os.path.getsize(p) > 40 * 1024 * 1024:
                continue
            try:
                for (fmt, W), pl in variants(p):
                    s = score(pl, W, W)
                    if s >= 30:
                        hits.append((s, rel, fmt, W))
                        print('  %-50s %-5s w%-5d 격자칸 %d' % (rel, fmt, W, s))
            except Exception:
                continue
    print('\n후보 %d' % len(hits))
    for h in sorted(hits, reverse=True)[:15]:
        print('  %4d  %-46s %s w%d' % h)
