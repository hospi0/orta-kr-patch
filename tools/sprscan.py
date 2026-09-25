"""`.spr` 98개에 글리프·픽셀이 있는지 본다.

세션2 로 확정: 타이틀/메뉴 화면은 `.txb` 를 안 쓴다(499개를 전부 비워도 멀쩡했고,
같은 빌드에서 오프닝 데모 배경은 전부 사라져 **양성 대조가 성립**했다).
`.spr` 은 전부 `sprite/` 에 있고 이름이 화면과 정확히 대응한다
(`pdx_title` / `pdbox_main_menu` / `pdbox_main_menu_window` / `pdx_option` …).

★추측하지 말고 그려서 눈으로 볼 것
  (feedback_font_glyph_too_small_draw_pixels).
"""
import os
import struct
import sys
from atlas import write_png
from project import ROOT, WORK

SPR_DIR = os.path.join(ROOT, 'sprite')


def header(path):
    d = open(path, 'rb').read()
    n = struct.unpack_from('<I', d, 0)[0]
    ents = []
    off = 4
    stride = 0x20
    while off + stride <= len(d) and len(ents) < n:
        a, b, c = struct.unpack_from('<3I', d, off)
        ents.append((a, b, c))
        off += stride
    return d, n, ents, off


def render_tail(path, out_dir, widths=(64, 128, 256, 512)):
    """헤더 뒤 데이터를 여러 폭으로 8bit 그레이로 그려 본다."""
    d, n, ents, tail = header(path)
    body = d[tail:]
    base = os.path.splitext(os.path.basename(path))[0]
    made = []
    for w in widths:
        h = len(body) // w
        if h < 16:
            continue
        made.append(write_png(os.path.join(out_dir, '%s_w%d.png' % (base, w)),
                              w, min(h, 2048), body[:w * min(h, 2048)]))
    return d, n, ents, tail, made


if __name__ == '__main__':
    names = sys.argv[1:] or ['pdx_title.spr', 'pdbox_main_menu.spr',
                             'pdbox_main_menu_window.spr', 'pdx_option.spr']
    out = os.path.join(WORK, 'spr')
    os.makedirs(out, exist_ok=True)
    for nm in names:
        p = os.path.join(SPR_DIR, nm)
        if not os.path.exists(p):
            print('없음', nm)
            continue
        d, n, ents, tail, made = render_tail(p, out)
        print('== %-34s %8d B  헤더[0]=%d  엔트리표 끝 0x%X  본문 %d B'
              % (nm, len(d), n, tail, len(d) - tail))
        print('   엔트리 앞 4개:', ents[:4])
        nz = sum(1 for b in d[tail:tail + 200000] if b)
        print('   본문 앞 200KB 비제로 비율 %.1f%%' % (100 * nz / min(200000, len(d) - tail)))
        for m in made:
            print('   ->', os.path.basename(m))
