"""Tutorial 아틀라스 판정 — 변수를 하나로 줄인 최소 시험.

앞선 시험(probe_tutorial_kr.py)은 **아틀라스와 `.msg` 를 동시에** 바꿨는데,
하필 아틀라스에서 바꾼 칸(以位威意易移遺一)이 그 문장에 안 나오는 글자여서
화면으로는 아무것도 구분할 수 없었다. **또 양성 대조를 빠뜨린 것이다.**

여기서는 `.msg` 를 손대지 않고, 화면에 **실제로 보이는 글자**만 바꾼다.

    TUTORIAL 첫 화면 원문
        ドラゴンは$c5左スティック$c7で
        操作します。

    바꾸는 글자 = 左 操 作  (전부 이 화면에 보인다)
    기대 화면
        ドラゴンは왼スティックで
        조작します。

판정
    한글 3자가 뜬다      -> `Zenkaku_Tutorial` 을 쓴다. 앞 시험의 실패는 `.msg` 쪽이다.
    일본어 그대로        -> 이 화면은 그 아틀라스를 **안 쓴다**. Menu 와 같은 경우.
"""
import os
import shutil
import sys
from atlaswrite import Atlas
from ztbl import ZTbl
from project import ROOT, WORK, FONT_DIR
import render2

ORIG = os.path.join(WORK, 'orig')
TBL_REL = os.path.join('sprite', 'Font', 'Reisyo_Tutorial_z_tbl.bin')
ATL_REL = os.path.join('sprite', 'Font', 'Zenkaku_Tutorial.txb')
MAP = {'左': '왼', '操': '조', '作': '작'}


def restore_all():
    n = 0
    for dp, dn, fns in os.walk(ORIG):
        for fn in fns:
            src = os.path.join(dp, fn)
            shutil.copy2(src, os.path.join(ROOT, os.path.relpath(src, ORIG)))
            n += 1
    return n


def main(dry):
    print('원본 전량 원복: %d개  (★.msg 도 원복 — 변수는 아틀라스 하나뿐)' % restore_all())
    tbl = ZTbl(os.path.join(ORIG, TBL_REL))
    atl = Atlas(os.path.join(ORIG, ATL_REL))
    m = tbl.mapping(drop_sentinel=True)
    inv = {}
    for c, g in m.items():
        inv.setdefault(g, []).append(c)

    for src_ch, ko in MAP.items():
        if src_ch not in m:
            sys.exit('★%r 가 Tutorial 표에 없다' % src_ch)
        g = m[src_ch]
        if len(inv[g]) != 1:
            sys.exit('★%r(칸 %d)는 센티널이다 — %d글자가 공유' % (src_ch, g, len(inv[g])))
        before = atl.ink(g)
        if before == 0:
            sys.exit('★%r(칸 %d)가 빈칸이다' % (src_ch, g))
        atl.set_cell(g, render2.glyph(ko, 'bold', 24))
        print('   %s → %s  (칸 %d, 잉크 %d→%d)' % (src_ch, ko, g, before, atl.ink(g)))

    data = atl.to_bytes(keep_size=True)
    print('\n아틀라스 %d B = 원본 %d B' % (len(data), len(atl.raw)))
    if dry:
        print('[미리보기만 — 게임 트리는 원본 그대로다]')
        return
    open(os.path.join(ROOT, ATL_REL), 'wb').write(data)
    print('적용 완료. TUTORIAL 첫 화면 한 장이면 된다.')


if __name__ == '__main__':
    main('--dry' in sys.argv)
