"""폰트 아틀라스 픽셀 포맷 실측.

★추측하지 말고 그려서 눈으로 볼 것 (feedback_font_glyph_too_small_draw_pixels,
  feedback_palette_measure_dont_guess).
"""
import os
import sys
import zlib
import struct
from pcmp import decompress
from project import scene_atlas, WORK


def load(name):
    return decompress(open(scene_atlas(name), 'rb').read())


def write_png(path, w, h, gray):
    """gray = bytes 길이 w*h, 8bit 그레이스케일."""
    rows = b''.join(b'\x00' + gray[y * w:(y + 1) * w] for y in range(h))
    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c))
    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 0, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(rows, 9))
           + chunk(b'IEND', b''))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(png)
    return path


def unswizzle(data, w, h, bpp_bytes=1):
    """Xbox 모튼(Z-order) 스위즐 해제."""
    out = bytearray(len(data))
    lw = w.bit_length() - 1
    lh = h.bit_length() - 1
    for y in range(h):
        for x in range(w):
            u = 0
            bit = 1
            xx, yy = x, y
            for i in range(max(lw, lh)):
                if i < lw:
                    u |= (xx & 1) * bit
                    bit <<= 1
                    xx >>= 1
                if i < lh:
                    u |= (yy & 1) * bit
                    bit <<= 1
                    yy >>= 1
            src = u * bpp_bytes
            dst = (y * w + x) * bpp_bytes
            out[dst:dst + bpp_bytes] = data[src:src + bpp_bytes]
    return bytes(out)


def expand4(data):
    """4bpp -> 8bpp (니블 두 개, 저니블 먼저)."""
    out = bytearray(len(data) * 2)
    for i, b in enumerate(data):
        out[i * 2] = (b & 0x0F) * 17
        out[i * 2 + 1] = (b >> 4) * 17
    return bytes(out)


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'Common'
    d = load(name)
    print('풀린 크기 %d (0x%x)' % (len(d), len(d)))
    hdr = struct.unpack_from('<8I', d, 0)
    print('TXRB 헤더:', [hex(x) for x in hdr])
    off = hdr[5]
    print('데이터 오프셋 필드 0x%x' % off)
    print('0x20~0x200 비제로 바이트 수:', sum(1 for b in d[0x20:0x200] if b))
    body = d[off:]
    print('본문 %d 바이트' % len(body))
    hist = [0] * 256
    for b in body[:200000]:
        hist[b] += 1
    top = sorted(range(256), key=lambda i: -hist[i])[:8]
    print('바이트 빈도 상위:', [(hex(i), hist[i]) for i in top])
    nib = [0] * 16
    for b in body[:200000]:
        nib[b & 15] += 1
        nib[b >> 4] += 1
    print('니블 빈도:', nib)

    outdir = os.path.join(WORK, 'atlas')
    W = 512
    # 0x20~0x200 이 전부 0 이라 픽셀은 0x20 부터로 보는 게 맞다:
    # 262176 - 32 = 262144 = 512*512(8bpp) = 512*1024(4bpp) 로 딱 떨어진다.
    pix = d[0x20:]
    CROP = int(sys.argv[2]) if len(sys.argv) > 2 else 224      # 8줄(28px)
    for tag, px in (('8bpp', pix), ('4bpp', expand4(pix))):
        h = len(px) // W
        write_png(os.path.join(outdir, '%s_%s_full.png' % (name, tag)), W, h, px[:W * h])
        c = min(CROP, h)
        p = write_png(os.path.join(outdir, '%s_%s_crop.png' % (name, tag)), W, c, px[:W * c])
        print('  ->', p, 'crop %dx%d (full %dx%d)' % (W, c, W, h))
