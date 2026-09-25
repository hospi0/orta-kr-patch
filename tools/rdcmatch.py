"""RenderDoc 으로 뽑은 텍스처가 디스크의 어느 파일인지 «픽셀로» 특정한다.

사용:  python rdcmatch.py "..\my files\font.png"

이름·크기 추측 금지 — 잉크 마스크 IoU 로 판정한다
(feedback_verify_which_asset_the_screen_uses).
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, pristine
from txrb import Txrb


def target_mask(path):
    im = np.array(Image.open(path).convert('RGBA'))
    a = im[..., 3]
    rgb = im[..., :3].max(axis=2)
    return (a > 8), (rgb > 8), im.shape[1], im.shape[0]


def dxt3_alpha(buf, w, h):
    """DXT3(BC2) 블록의 앞 8바이트 = 4x4 알파 니블."""
    bw, bh = w // 4, h // 4
    need = bw * bh * 16
    if len(buf) < need:
        return None
    out = np.zeros((h, w), np.uint8)
    arr = np.frombuffer(buf[:need], np.uint8).reshape(bh, bw, 16)
    al = arr[:, :, :8]                      # (bh,bw,8) 행당 2바이트
    lo = (al & 0x0F) * 17
    hi = (al >> 4) * 17
    px = np.empty((bh, bw, 16), np.uint8)
    px[:, :, 0::2] = lo
    px[:, :, 1::2] = hi
    px = px.reshape(bh, bw, 4, 4)
    for y in range(4):
        out[y::4, :] = px[:, :, y, :].reshape(bh, bw * 4)[:, :w] if False else 0
    # 위 루프 대신 정석 재배치
    out = px.transpose(0, 2, 1, 3).reshape(h, w)
    return out


def dxt3_color(buf, w, h):
    """블록 뒤 8바이트 = BC1 컬러. 밝기만 뽑는다(0/1 근사)."""
    bw, bh = w // 4, h // 4
    need = bw * bh * 16
    if len(buf) < need:
        return None
    arr = np.frombuffer(buf[:need], np.uint8).reshape(bh, bw, 16)
    c = arr[:, :, 8:]
    c0 = c[:, :, 0].astype(np.uint16) | (c[:, :, 1].astype(np.uint16) << 8)
    c1 = c[:, :, 2].astype(np.uint16) | (c[:, :, 3].astype(np.uint16) << 8)
    def lum(v):
        r = ((v >> 11) & 31) * 8
        g = ((v >> 5) & 63) * 4
        b = (v & 31) * 8
        return (r * 77 + g * 150 + b * 29) >> 8
    l0, l1 = lum(c0), lum(c1)
    idx = c[:, :, 4:8]
    bits = np.unpackbits(idx, axis=2, bitorder='little').reshape(bh, bw, 4, 4, 2)
    sel = bits[..., 0] | (bits[..., 1] << 1)
    tbl = np.stack([l0, l1, (2 * l0 + l1) // 3, (l0 + 2 * l1) // 3], axis=2)
    out = np.take_along_axis(tbl[:, :, :, None, None].repeat(4, 3).repeat(4, 4),
                             sel[:, :, None, :, :], axis=2)[:, :, 0]
    return out.transpose(0, 2, 1, 3).reshape(h, w).astype(np.uint8)


def a8(buf, w, h):
    if len(buf) < w * h:
        return None
    return np.frombuffer(buf[:w * h], np.uint8).reshape(h, w)


def unswizzle(buf, w, h, bpp=1):
    n = w * h
    if len(buf) < n * bpp:
        return None
    lw, lh = w.bit_length() - 1, h.bit_length() - 1
    ys, xs = np.mgrid[0:h, 0:w]
    u = np.zeros((h, w), np.int64)
    bit = 1
    xx, yy = xs.copy(), ys.copy()
    for i in range(max(lw, lh)):
        if i < lw:
            u |= (xx & 1) * bit
            bit <<= 1
            xx >>= 1
        if i < lh:
            u |= (yy & 1) * bit
            bit <<= 1
            yy >>= 1
    src = np.frombuffer(buf[:n * bpp], np.uint8)
    if bpp == 1:
        return src[u]
    return None


def iou(a, b):
    inter = np.count_nonzero(a & b)
    union = np.count_nonzero(a | b)
    return inter / union if union else 0.0


def main():
    tgt = sys.argv[1]
    ma, mc, W, H = target_mask(tgt)
    print('표적 %s  %dx%d  알파잉크 %d px  컬러잉크 %d px'
          % (os.path.basename(tgt), W, H, ma.sum(), mc.sum()))

    files = []
    for dp, dn, fn in os.walk(ROOT):
        for f in fn:
            if f.lower().endswith(('.txb', '.spr', '.ees', '.rsb')):
                files.append(os.path.join(dp, f))

    results = []
    for p in files:
        try:
            t = Txrb(pristine(p))
        except Exception:
            continue
        if not t.ok or t.width != W:
            continue
        pb = t.page_bytes()
        if pb < W * H // 2:
            continue
        body = t.data[t.start:]
        for pg in range(min(t.pages, 16)):
            buf = body[pg * pb:(pg + 1) * pb]
            cands = {
                'dxt3a': dxt3_alpha(buf, W, H),
                'dxt3c': dxt3_color(buf, W, H),
                'a8': a8(buf, W, H),
                'a8sw': unswizzle(buf, W, H, 1),
            }
            for tag, img in cands.items():
                if img is None:
                    continue
                for flip in (False, True):
                    m = (img[::-1] if flip else img) > 8
                    for tm, tn in ((ma, 'A'), (mc, 'C')):
                        s = iou(m, tm)
                        if s > 0.30:
                            results.append((s, os.path.relpath(p, ROOT), pg, tag,
                                            'flip' if flip else 'as-is', tn))
    results.sort(reverse=True)
    print('\n=== IoU 상위 ===')
    for r in results[:15]:
        print('  %.4f  %-45s p%d %-6s %-5s vs%s' % r)
    if not results:
        print('  일치 없음 (>0.30)')


if __name__ == '__main__':
    main()
