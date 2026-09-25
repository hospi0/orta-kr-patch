"""DXT3(BC2) 디코드/인코드. 폰트 아틀라스가 이 포맷이다.

블록 16바이트 = 알파 8바이트(픽셀당 4비트) + DXT1 컬러 8바이트.
★폰트 글자는 **알파 채널**에 있다. 컬러는 대개 단색이다.
"""
import struct


def decode_alpha(data, w, h):
    """DXT3 알파 채널만 8bit 그레이스케일로."""
    bw, bh = w // 4, h // 4
    out = bytearray(w * h)
    for by in range(bh):
        for bx in range(bw):
            i = (by * bw + bx) * 16
            a = int.from_bytes(data[i:i + 8], 'little')
            for py in range(4):
                for px in range(4):
                    v = (a >> (4 * (py * 4 + px))) & 0xF
                    out[(by * 4 + py) * w + bx * 4 + px] = v * 17
    return bytes(out)


def encode_alpha(gray, w, h, color_block=b'\xff\xff\xff\xff\x00\x00\x00\x00'):
    """8bit 그레이(글자 모양) -> DXT3 블록열. 컬러는 고정 단색."""
    bw, bh = w // 4, h // 4
    out = bytearray()
    for by in range(bh):
        for bx in range(bw):
            a = 0
            for py in range(4):
                for px in range(4):
                    v = gray[(by * 4 + py) * w + bx * 4 + px] >> 4
                    a |= v << (4 * (py * 4 + px))
            out += a.to_bytes(8, 'little')
            out += color_block
    return bytes(out)


def decode_color(data, w, h):
    """DXT3 의 컬러 절반을 휘도로 (원본 색을 확인할 때만)."""
    bw, bh = w // 4, h // 4
    out = bytearray(w * h)
    for by in range(bh):
        for bx in range(bw):
            i = (by * bw + bx) * 16 + 8
            c0, c1 = struct.unpack_from('<HH', data, i)
            bits = struct.unpack_from('<I', data, i + 4)[0]

            def lum(c):
                r = ((c >> 11) & 31) * 255 // 31
                g = ((c >> 5) & 63) * 255 // 63
                b = (c & 31) * 255 // 31
                return (r * 30 + g * 59 + b * 11) // 100
            l0, l1 = lum(c0), lum(c1)
            pal = [l0, l1, (2 * l0 + l1) // 3, (l0 + 2 * l1) // 3]
            for py in range(4):
                for px in range(4):
                    out[(by * 4 + py) * w + bx * 4 + px] = pal[(bits >> (2 * (py * 4 + px))) & 3]
    return bytes(out)
