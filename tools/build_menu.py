"""시험 빌드 — 메뉴 화면 한글화 (시험2: Common 아틀라스 기준).

바꾸는 파일:
  sprite/Font/Zenkaku_Common.txb           칸을 한글로 다시 그린다  ← 본체
  sprite/Font/Zenkaku_Menu.txb             Common 과 겹치는 문자의 칸만 같이 칠한다
  menudata/TextData/Text_MenuInst_JP.msg   번역문 제자리 덮어쓰기
  (z_tbl 은 **손대지 않는다** — 기존 매핑을 그대로 재활용하기 때문)

★파일 크기는 전부 원본과 **바이트 단위로 동일**.
★원본은 work/orig/ 에 백업하고 빌드는 **항상 백업본에서 시작**한다(멱등).
"""
import os
import sys
import shutil
import struct

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'trans'))
from Text_MenuInst_ko import KO                       # noqa: E402
from project import ROOT, WORK, FONT_DIR, GLYPH_W, GLYPH_H   # noqa: E402
from atlaswrite import Atlas                           # noqa: E402
from check_menu import prepare, encode, fit                 # noqa: E402
from budget_menu import entries                        # noqa: E402
import render3 as render                               # noqa: E402

ORIG = os.path.join(WORK, 'orig')
REL_CMN = os.path.join('sprite', 'Font', 'Zenkaku_Common.txb')
REL_MENU = os.path.join('sprite', 'Font', 'Zenkaku_Menu.txb')
REL_MTBL = os.path.join('sprite', 'Font', 'Reisyo_Menu_z_tbl.bin')
REL_MSG = os.path.join('menudata', 'TextData', 'Text_MenuInst_JP.msg')
TARGETS = [REL_CMN, REL_MENU, REL_MTBL, REL_MSG]


def backup():
    for rel in TARGETS:
        dst = os.path.join(ORIG, rel)
        if not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(ROOT, rel), dst)
    print('원본 백업 -> %s' % ORIG)


def orig_bytes(rel):
    return open(os.path.join(ORIG, rel), 'rb').read()


def write_same_size(rel, data):
    o = orig_bytes(rel)
    if len(data) != len(o):
        raise SystemExit('★크기가 다르다 %s: %d != %d' % (rel, len(data), len(o)))
    with open(os.path.join(ROOT, rel), 'wb') as f:
        f.write(data)
    print('  기록 %-42s %d B' % (rel, len(data)))


def restore(rel):
    shutil.copy2(os.path.join(ORIG, rel), os.path.join(ROOT, rel))
    print('  원복 %-42s' % rel)


def paint(rel, cells):
    """cells = {글리프인덱스: 음절} — 아틀라스 칸을 다시 그려 같은 크기로 낸다.

    ★★알파와 컬러를 **둘 다** 쓴다(Atlas.set_cell). 알파만 바꾸면 화면엔
      «내 한글 ∩ 원본 한자»의 교집합만 남는다 —
      [[feedback_dxt_color_channel_also_has_glyph]].
    """
    a = Atlas(os.path.join(ORIG, rel))
    for g, syl in cells.items():
        a.set_cell(g, render.glyph(syl), color=True)
    out = a.to_bytes(keep_size=True)
    write_same_size(rel, out)
    print('    칸 %d개 갈아끼움 (페이지 %d)' % (len(cells), a.pages))


def patch_text(smap):
    d = bytearray(orig_bytes(REL_MSG))
    _, es = entries()
    n = 0
    trims = []
    for i, e in enumerate(es):
        t = KO.get(i)
        if not t:
            continue
        # ★★«정확히» 원문 길이로. 널을 늘리면 그 뒤 색인이 전부 밀려 화면이 다 빈칸이 된다.
        t, log = fit(t, e['bytes'], smap)
        if log:
            trims.append('    idx %-3d %s -> %r' % (i, '+'.join(log), t[:38]))
        b = encode(t, smap, width=e['bytes'])
        assert len(b) == e['bytes'], '길이 불일치 %d: %d != %d' % (i, len(b), e['bytes'])
        d[e['off']:e['off'] + e['bytes']] = b
        n += 1
    write_same_size(REL_MSG, bytes(d))
    print('    번역 %d줄 반영 (예산 맞추려 줄인 줄 %d개)' % (n, len(trims)))
    for t in trims[:8]:
        print(t)


if __name__ == '__main__':
    backup()
    restore(REL_MTBL)                     # 시험1 에서 건드린 표를 되돌린다
    syl, st, short, smap = prepare(persist=True)
    if short:
        raise SystemExit('★슬롯 부족 %d' % len(short))
    cmn_cells = {v[1]: s for s, v in st['map'].items()}
    menu_cells = {v[2]: s for s, v in st['map'].items() if v[2] >= 0}
    # ★모든 음절에 «같은 변환»을 쓰려면 집합 전체로 한 번만 보정한다(간격 균일).
    render.calibrate(sorted(st['map']))
    print('음절 %d개  (Common 칸 %d, Menu 칸 %d)  폰트 %s'
          % (len(st['map']), len(cmn_cells), len(menu_cells), render.desc()))
    paint(REL_CMN, cmn_cells)
    if menu_cells:
        paint(REL_MENU, menu_cells)
    else:
        restore(REL_MENU)
    patch_text(smap)
    print('\n완료. 배정표 = work/slots.json')
