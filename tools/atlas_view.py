"""아틀라스를 DXT3 알파로 풀어 PNG 로. 격자 확인용."""
import os
import sys
import struct
from pcmp import decompress
from atlas import write_png
from dxt import decode_alpha, decode_color
from project import WORK, FONT_DIR, scene_atlas


def atlas_pixels(name):
    path = (os.path.join(FONT_DIR, 'font_hs_test_arial.txb') if name == 'arial'
            else scene_atlas(name))
    d = decompress(open(path, 'rb').read())
    pages = struct.unpack_from('<I', d, 4)[0]
    start = 0x20 if pages == 1 else 0x50
    return d, pages, d[start:]


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'arial'
    W = int(sys.argv[2]) if len(sys.argv) > 2 else 512
    ROWS = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    d, pages, pix = atlas_pixels(name)
    per = 262144
    H = per // W                      # DXT3 = 1바이트/픽셀
    print('%s: 풀림 %d, 페이지 %d, 페이지당 %dx%d' % (name, len(d), pages, W, H))
    outdir = os.path.join(WORK, 'atlas')
    a = decode_alpha(pix[:per], W, H)
    p = write_png(os.path.join(outdir, '%s_dxt3_alpha.png' % name), W, min(ROWS, H),
                  a[:W * min(ROWS, H)])
    print('->', os.path.basename(p))
    c = decode_color(pix[:per], W, H)
    p = write_png(os.path.join(outdir, '%s_dxt3_color.png' % name), W, min(ROWS, H),
                  c[:W * min(ROWS, H)])
    print('->', os.path.basename(p))
