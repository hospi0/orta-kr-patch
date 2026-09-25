"""검증 빌드 — 메인 메뉴 설명문이 Zenkaku_Common 을 쓰는지 실기로 확정한다.

변수는 «아틀라스 칸» 하나뿐. `.msg` 는 건드리지 않는다.
화면의 `最初からゲームを開始します。` 가
        처음부터게임을시작합니다 。
로 바뀌면 확정이다.

★칸은 Reisyo_Cmn_z_tbl_cmn.bin 의 인덱스를 그대로 쓴다(2026-08-30 확정).
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import FONT_DIR, COMMON_TBL, pristine, WORK
from ztbl import ZTbl
from atlaswrite import Atlas
import render2

# 화면 문장 -> 한글. す 는 남는 칸이라 비운다. 。 은 원본 유지.
PAIRS = [('最', '처'), ('初', '음'), ('か', '부'), ('ら', '터'),
         ('ゲ', '게'), ('ー', '임'), ('ム', '을'), ('を', '시'),
         ('開', '작'), ('始', '합'), ('し', '니'), ('ま', '다'),
         ('す', None)]

def main():
    tbl = ZTbl(pristine(os.path.join(FONT_DIR, COMMON_TBL))).mapping()
    src = pristine(os.path.join(FONT_DIR, 'Zenkaku_Common.txb'))
    dst = os.path.join(FONT_DIR, 'Zenkaku_Common.txb')
    a = Atlas(src)

    print('원본 %s (%d B, 페이지 %d)' % (os.path.basename(src), len(a.raw), a.pages))
    for jp, kr in PAIRS:
        g = tbl.get(jp)
        if g is None:
            print('  ★%s 가 Cmn 표에 없다 — 중단' % jp)
            return 1
        before = a.ink(g)
        gray = bytes(28 * 28) if kr is None else render2.glyph(kr, 'bold', 24)
        a.set_cell(g, gray, color=True)
        print('  %s -> %s  칸 %3d (행 %2d 열 %2d)  잉크 %d -> %d'
              % (jp, kr or '(빈칸)', g, g // 18, g % 18, before, a.ink(g)))

    new, old = a.save(dst, keep_size=True)
    print('저장 %s  %d B (원본 %d B) — 크기 %s'
          % (dst, new, old, '동일' if new == old else '★다름'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
