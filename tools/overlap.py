"""Common 과 Menu 두 표에 «둘 다» 있는 문자를 센다.

빈 상자가 나온 이유 추정: 내가 고른 대체 SJIS 코드가 전부 **Common 표에 없는** 코드라,
이 화면이 Common 으로 그린다면 전부 미매핑(0xFFFF) → 아무것도 안 그려진다.

→ 어느 표를 보든 맞게 하려면 **두 표에 다 있는 문자**를 골라
   **두 아틀라스의 해당 칸을 똑같이 칠하면** 된다 (렌더러 순서와 무관).
"""
import os
from ztbl import ZTbl
from cells import atlas_alpha, filled_cells, CELLS_PER_PAGE
from project import FONT_DIR, COMMON_TBL, scene_tbl, scene_atlas

CMN_ATL = os.path.join(FONT_DIR, 'Zenkaku_Common.txb')


def live_glyph_count(atlas_path):
    pages, px = atlas_alpha(atlas_path)
    ink = [i for i, (p, r, c, k) in enumerate(filled_cells(px)) if k]
    return pages, (ink[-1] + 1 if ink else 0), pages * CELLS_PER_PAGE


if __name__ == '__main__':
    cm = ZTbl(os.path.join(FONT_DIR, COMMON_TBL)).mapping(drop_sentinel=False)
    mm = ZTbl(scene_tbl('Menu')).mapping(drop_sentinel=False)
    cp, cn, ccap = live_glyph_count(CMN_ATL)
    mp, mn, mcap = live_glyph_count(scene_atlas('Menu'))
    print('Common 글리프 %d / 칸 %d' % (cn, ccap))
    print('Menu   글리프 %d / 칸 %d' % (mn, mcap))

    both = {ch: (cm[ch], mm[ch]) for ch in cm if ch in mm
            and cm[ch] < cn and mm[ch] < mn}
    # 글리프 쌍이 겹치지 않게 하나씩만
    seen_c, seen_m, pairs = set(), set(), []
    def cls(ch):
        o = ord(ch)
        return '가나' if 0x3040 <= o <= 0x30ff else (
            '한자' if 0x4e00 <= o <= 0x9fff else '기호')
    for ch, (g, h) in sorted(both.items(), key=lambda kv: (kv[1][0], kv[0])):
        if g in seen_c or h in seen_m:
            continue
        seen_c.add(g); seen_m.add(h)
        pairs.append((ch, g, h, cls(ch)))
    print('\n두 표에 다 있고 글리프 쌍이 유일한 문자: %d개' % len(pairs))
    k = {}
    for ch, g, h, c in pairs:
        k[c] = k.get(c, 0) + 1
    print('   ', k)
    print('    예:', ''.join(p[0] for p in pairs[:50]))

    only_c = [ch for ch in cm if ch not in mm and cm[ch] < cn]
    print('\nCommon 에만 있는 문자 %d개' % len(only_c))
