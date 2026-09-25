"""디스크 전체에서 «글리프 격자»를 찾는다 — 이미지 대조가 아니라 «주기성»으로.

세션4에서 Common/OpeningDemo 를 둘 다 비웠는데도 히라가나가 남았다.
⇒ 제3의 폰트가 반드시 있다. 그걸 찾는다.

기존 gridscan2 는 28x28 고정이라 다른 칸 크기를 원리상 못 봤다.
여기서는 칸 크기 16~48, 폭 128~1024, 포맷 DXT3알파 / A8 / ARGB4444알파 를 전부 돈다.
PCMP 는 «재귀»로 푼다(안에 또 PCMP 가 들어 있을 수 있다).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, pristine
from pcmp import decompress

WIDTHS = (128, 256, 512, 1024)
CELLS = (16, 20, 24, 28, 32, 40, 48)
MAXFILE = 48 << 20
SKIP_EXT = ('.sfd', '.wav', '.xbe', '.bik', '.ogg')


def blobs(buf):
    """(포맷이름, 2D 알파배열) 후보들."""
    out = []
    n = len(buf)
    a = np.frombuffer(buf, np.uint8)
    for w in WIDTHS:
        # DXT3 알파: 블록당 16B, 앞 8B 가 4x4 니블
        bw = w // 4
        nb = n // 16
        bh = nb // bw
        if 8 <= bh <= 1024 and bh * bw * 16 <= n:
            arr = a[:bh * bw * 16].reshape(bh, bw, 16)[:, :, :8]
            px = np.empty((bh, bw, 16), np.uint8)
            px[:, :, 0::2] = (arr & 15) * 17
            px[:, :, 1::2] = (arr >> 4) * 17
            out.append(('dxt3a/w%d' % w,
                        px.reshape(bh, bw, 4, 4).transpose(0, 2, 1, 3).reshape(bh * 4, w)))
        # A8
        h = n // w
        if 8 <= h <= 2048:
            out.append(('a8/w%d' % w, a[:w * h].reshape(h, w)))
        # ARGB4444 (상위 니블 = 알파)
        h2 = n // (w * 2)
        if 8 <= h2 <= 2048:
            out.append(('4444/w%d' % w, (a[1:w * h2 * 2:2] >> 4).reshape(h2, w) * 17))
    return out


def grid_score(img, cell):
    """칸 경계에 잉크가 «없고» 칸 안엔 «있는» 정도. 0~1."""
    h, w = img.shape
    if h < cell * 4 or w < cell * 4:
        return 0.0, 0
    ink = img > 8
    m = float(ink.mean())
    if m < 0.02 or m > 0.60:
        return 0.0, 0
    colp = ink.mean(0)
    rowp = ink.mean(1)

    def best_phase(prof):
        """경계 줄의 잉크가 가장 낮은 위상. ★헤더 때문에 위상이 어긋나므로 탐색한다."""
        bs, bp = 1e9, 0
        for ph in range(cell):
            v = prof[ph::cell]
            if len(v) < 4:
                continue
            if v.mean() < bs:
                bs, bp = float(v.mean()), ph
        return bs, bp

    ec, pc = best_phase(colp)
    er, pr = best_phase(rowp)
    s = max(0.0, 1 - ec / m) * max(0.0, 1 - er / m)
    if s <= 0:
        return 0.0, 0
    # 위상에 맞춰 칸을 잘라 «글자가 든 칸» 수를 센다
    y0, x0 = (pr + 1) % cell, (pc + 1) % cell
    sub = ink[y0:, x0:]
    nr, nc2 = sub.shape[0] // cell, sub.shape[1] // cell
    if nr < 3 or nc2 < 3:
        return 0.0, 0
    cells = sub[:nr * cell, :nc2 * cell].reshape(nr, cell, nc2, cell).sum(axis=(1, 3))
    used = float((cells > 20).mean())
    return s * used, int((cells > 20).sum())


def unpack(buf, depth=0):
    """PCMP 재귀 해제. [(태그, 바이트)]"""
    out = [('raw', buf)]
    if depth < 3 and buf[:4] == b'PCMP':
        try:
            d = decompress(buf)
            out += [('pcmp%d:%s' % (depth + 1, t), b) for t, b in unpack(d, depth + 1)]
        except Exception:
            pass
    return out


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    files = []
    for dp, dn, fn in os.walk(ROOT):
        for f in fn:
            p = os.path.join(dp, f)
            if f.lower().endswith(SKIP_EXT):
                continue
            if only and only.lower() not in p.lower():
                continue
            try:
                if os.path.getsize(p) > MAXFILE or os.path.getsize(p) < 4096:
                    continue
            except OSError:
                continue
            files.append(p)
    print('후보 파일 %d개' % len(files))

    hits = []
    for i, p in enumerate(files):
        if i % 200 == 0:
            print('  ... %d/%d' % (i, len(files)), flush=True)
        try:
            raw = open(pristine(p), 'rb').read()
        except OSError:
            continue
        for tag, buf in unpack(raw):
            if len(buf) < 4096:
                continue
            for fmt, img in blobs(buf):
                for cell in CELLS:
                    s, nc = grid_score(img, cell)
                    if s > 0.30 and nc >= 40:
                        hits.append((round(s, 3), nc, os.path.relpath(p, ROOT),
                                     tag, fmt, cell))
    hits.sort(reverse=True)
    seen = set()
    print('\n=== 격자 검출 상위 (파일별 최고 1건) ===')
    for h in hits:
        if h[2] in seen:
            continue
        seen.add(h[2])
        print('  %.3f  칸%3d개  %-42s %-10s %-11s cell=%d' % h)
        if len(seen) >= 40:
            break
    if not seen:
        print('  0건')


if __name__ == '__main__':
    main()
