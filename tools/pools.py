"""메뉴 화면에 한글을 넣을 때 쓸 수 있는 «칸»을 전부 센다.

세 갈래:
  A. Menu 아틀라스 **빈 칸**      — 아무것도 안 부순다 (새 SJIS 코드를 표에 새로 매핑)
  B. Common 아틀라스 **가나 칸**  — 다시 그리면 «모든 장면»의 가나가 깨진다
  C. Menu 아틀라스 **한자 칸**    — 다시 그리면 «메뉴 화면»의 그 한자만 깨진다
                                    (판도라의 상자 도감이 미번역이면 거기가 깨진다)
"""
import os
from ztbl import ZTbl
from cells import atlas_alpha, filled_cells, CELLS_PER_PAGE
from project import FONT_DIR, COMMON_TBL, LEADS, scene_tbl, scene_atlas


def cls(ch):
    o = ord(ch)
    if 0x3040 <= o <= 0x30ff:
        return '가나'
    if 0x4e00 <= o <= 0x9fff:
        return '한자'
    return '기호'


def all_sjis():
    out = []
    for li, lead in enumerate(LEADS):
        for ti in range(192):
            trail = 0x40 + ti
            if trail == 0x7f or trail > 0xfc:
                continue
            try:
                out.append((li * 192 + ti, bytes([lead, trail]).decode('cp932')))
            except Exception:
                pass
    return out


if __name__ == '__main__':
    cmn = ZTbl(os.path.join(FONT_DIR, COMMON_TBL))
    menu = ZTbl(scene_tbl('Menu'))
    cm = cmn.mapping(drop_sentinel=False)
    mm = menu.mapping(drop_sentinel=False)

    for name, m in (('Common', cm), ('Menu', mm)):
        k = {}
        for ch in m:
            k[cls(ch)] = k.get(cls(ch), 0) + 1
        print('%s 표 매핑문자 %d  %s' % (name, len(m), k))

    # 실제 «칸» 기준
    for name, tblpath, atlpath in (
            ('Common', os.path.join(FONT_DIR, COMMON_TBL),
             os.path.join(FONT_DIR, 'Zenkaku_Common.txb')),
            ('Menu', scene_tbl('Menu'), scene_atlas('Menu'))):
        pages, px = atlas_alpha(atlpath)
        cs = filled_cells(px)
        ink = [i for i, (p, r, c, k) in enumerate(cs) if k]
        cap = pages * CELLS_PER_PAGE
        last = ink[-1] + 1 if ink else 0
        print('\n%s: 페이지 %d, 칸 %d, 글리프 %d, **빈 칸 %d**'
              % (name, pages, cap, last, cap - last))
        t = ZTbl(tblpath)
        m = {c: g for c, g in t.mapping(drop_sentinel=False).items() if g < last}
        byc = {}
        for ch, g in m.items():
            byc.setdefault(cls(ch), set()).add(g)
        for k in ('가나', '한자', '기호'):
            print('   %s 이 쓰는 글리프 칸 %d' % (k, len(byc.get(k, ()))))

    # Menu 표에 아직 안 쓰인 SJIS 코드 (빈 칸에 새로 매핑할 후보)
    free_codes = [ch for i, ch in all_sjis() if ch not in mm and ch not in cm]
    print('\nMenu·Common 어느 표에도 없는 SJIS 코드: %d개 (빈 칸 매핑용)' % len(free_codes))
    print('   예:', ''.join(free_codes[:40]))
