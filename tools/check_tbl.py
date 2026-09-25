"""z_tbl 의 글리프 인덱스가 아틀라스 칸 수 안에 들어가는지 검산.

★「값의 개수」가 아니라 **최대 인덱스**가 진짜 제약이다.
"""
import os
from ztbl import ZTbl, SENTINEL
from project import FONT_DIR, SCENES, COMMON_TBL, HANKAKU_TBL, scene_tbl

CELLS = 324          # 512x512 페이지 / 28x28 = 18*18


def real_glyphs(t):
    """진짜 글리프 인덱스는 0..N-1 로 **빈틈없이 연속**이다.
    그 위의 값들은 센티널(미수록 구역이 통째로 가리키는 자리)이라 버린다."""
    vals = set(t.mapping(drop_sentinel=False).values())
    n = 0
    while n in vals:
        n += 1
    return n, sorted(v for v in vals if v >= n)


def row(name, path):
    t = ZTbl(path)
    n, junk = real_glyphs(t)
    cap = t.pages * CELLS
    m = {c: g for c, g in t.mapping(drop_sentinel=False).items() if g < n}
    print('%-16s pages=%d 글리프=%5d 칸=%5d 여유=%5d  매핑문자=%5d  센티널=%s %s'
          % (name, t.pages, n, cap, cap - n, len(m),
             junk[:3], '★초과' if n > cap else ''))
    return t, n, cap


if __name__ == '__main__':
    row('Arial(반각)', os.path.join(FONT_DIR, HANKAKU_TBL))
    row('Common', os.path.join(FONT_DIR, COMMON_TBL))
    for s in SCENES:
        row(s, scene_tbl(s))
