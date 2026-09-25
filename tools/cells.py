"""아틀라스에서 «실제로 그려진 칸»을 세어 글리프 수를 확정한다.

★파생 수치가 아니라 실측 (feedback_screen_limits_measure_not_derive).
검산 = 반각 Arial 은 z_tbl 매핑 95개와 정확히 같아야 한다.
"""
import os
import struct
from pcmp import decompress
from dxt import decode_alpha
from ztbl import ZTbl
from project import (FONT_DIR, SCENES, COMMON_TBL, HANKAKU_TBL,
                     scene_tbl, scene_atlas, GLYPH_W, GLYPH_H)

PAGE_W = PAGE_H = 512
PAGE_BYTES = PAGE_W * PAGE_H
COLS = PAGE_W // GLYPH_W          # 18
ROWSC = PAGE_H // GLYPH_H         # 18
CELLS_PER_PAGE = COLS * ROWSC     # 324


def atlas_alpha(path):
    d = decompress(open(path, 'rb').read()) if open(path, 'rb').read(4) == b'PCMP' \
        else open(path, 'rb').read()
    pages = struct.unpack_from('<I', d, 4)[0]
    start = 0x20 if pages == 1 else 0x50
    body = d[start:]
    return pages, [decode_alpha(body[i * PAGE_BYTES:(i + 1) * PAGE_BYTES], PAGE_W, PAGE_H)
                   for i in range(pages)]


def filled_cells(pages_px):
    """[(페이지, 행, 열)] 중 알파가 0 이 아닌 칸. 인덱스 순서대로."""
    out = []
    for p, px in enumerate(pages_px):
        for r in range(ROWSC):
            for c in range(COLS):
                ink = 0
                for y in range(GLYPH_H):
                    base = (r * GLYPH_H + y) * PAGE_W + c * GLYPH_W
                    if any(px[base:base + GLYPH_W]):
                        ink = 1
                        break
                out.append((p, r, c, ink))
    return out


def report(name, tbl_path, atlas_path):
    pages, px = atlas_alpha(atlas_path)
    cells = filled_cells(px)
    ink = [i for i, (p, r, c, k) in enumerate(cells) if k]
    last_ink = ink[-1] if ink else -1
    t = ZTbl(tbl_path)
    mapped = t.mapping(drop_sentinel=False)
    # 실제 글리프 = 0..last_ink. 그 위 인덱스를 가리키는 매핑은 센티널이다.
    real = {c: g for c, g in mapped.items() if g <= last_ink}
    cap = pages * CELLS_PER_PAGE
    print('%-16s 페이지=%d 잉크칸=%4d 마지막=%4d 칸수=%4d 여유=%4d | 매핑문자 %4d/%4d'
          % (name, pages, len(ink), last_ink + 1, cap, cap - (last_ink + 1),
             len(real), len(mapped)))
    return len(ink), last_ink + 1, cap


if __name__ == '__main__':
    report('Arial(반각)', os.path.join(FONT_DIR, HANKAKU_TBL),
           os.path.join(FONT_DIR, 'font_hs_test_arial.txb'))
    report('Common', os.path.join(FONT_DIR, COMMON_TBL),
           os.path.join(FONT_DIR, 'Zenkaku_Common.txb'))
    for s in SCENES:
        report(s, scene_tbl(s), scene_atlas(s))
