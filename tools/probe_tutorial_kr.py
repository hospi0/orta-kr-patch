"""Tutorial 실전 시험 — 「진짜 번역이 되는가」를 한 빌드로 가른다.

지금까지 증명된 건 **오프닝 자막 268자에서 한자 칸 6개를 덮어쓴 것**뿐이다.
「자막 계열 26%는 뚫렸다」는 근거 없는 호언이었다. 여기서 두 가지를 동시에 묻는다.

  질문1. 자막 계열이 정말 `Zenkaku_<장면>` 을 쓰는가
         (`Zenkaku_Menu` 는 이름이 그런데도 메뉴가 안 썼다 —
          [[feedback_verify_which_asset_the_screen_uses]])
  질문2. **아틀라스 빈 칸 + z_tbl 새 코드 배정**이 통하는가
         ★이게 안 되면 원문에 쓰인 한자 코드 수만큼만 음절을 쓸 수 있어
           사실상 번역이 불가능하다. 지금까지 한 번도 안 해봤다.

대상 = TUTORIAL 들어가면 **바로 나오는 첫 설명문**(게임 진행 불필요).
    원문 `ドラゴンは$c5左スティック$c7で\n操作します。`
    번역 `드래곤은$c5왼쪽스틱$c7으로\n조작합니다。`

15음절을 **절반씩 다른 방식**으로 넣는다.
    앞 8음절 «드래곤은왼쪽스틱» = 기존 한자 칸을 덮어쓰고 그 한자 코드를 그대로 쓴다
    뒤 7음절 «으로조작합니다»   = **빈 칸**에 그리고 z_tbl 에 **새 SJIS 코드**를 매핑

화면 판정
    앞뒤 다 한글        -> 질문1·2 둘 다 통과. 전면 번역 가능.
    앞만 한글, 뒤 깨짐  -> 빈 칸 배정이 안 된다. 음절 수가 원문 한자 수로 묶인다.
    전부 일본어         -> Tutorial 아틀라스를 안 쓴다. Menu 와 같은 경우.
★`.msg` 는 **원문 길이를 절대 넘지 않게** 제자리 덮어쓰기 + 널 패딩.
"""
import os
import shutil
import struct
import sys
import msgfile
from atlaswrite import Atlas, CELLS_PER_PAGE
from ztbl import ZTbl
from project import ROOT, WORK, FONT_DIR, pristine, scene_tbl, scene_atlas
import render2

ORIG = os.path.join(WORK, 'orig')
MSG_REL = os.path.join('messageevent', 'MesData_Tutorial_JP.msg')
TBL_REL = os.path.join('sprite', 'Font', 'Reisyo_Tutorial_z_tbl.bin')
ATL_REL = os.path.join('sprite', 'Font', 'Zenkaku_Tutorial.txb')

SRC = 'ドラゴンは$c5左スティック$c7で\n操作します。'
KO_REUSE = '드래곤은왼쪽스틱'      # 기존 한자 칸 재활용
KO_NEW = '으로조작합니다'          # 빈 칸 + 새 코드 배정
KO_TEXT = '드래곤은$c5왼쪽스틱$c7으로\n조작합니다。'


def restore_all():
    n = 0
    for dp, dn, fns in os.walk(ORIG):
        for fn in fns:
            src = os.path.join(dp, fn)
            shutil.copy2(src, os.path.join(ROOT, os.path.relpath(src, ORIG)))
            n += 1
    return n


def backup(rel):
    src = os.path.join(ORIG, rel)
    if not os.path.exists(src):
        os.makedirs(os.path.dirname(src), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, rel), src)
    return src


def main(dry):
    print('원본 전량 원복: %d개' % restore_all())
    for r in (MSG_REL, TBL_REL, ATL_REL):
        backup(r)

    tbl = ZTbl(os.path.join(ORIG, TBL_REL))
    atl = Atlas(os.path.join(ORIG, ATL_REL))
    m = tbl.mapping(drop_sentinel=True)

    # --- 원문에서 이 문장이 어디 있는지 ---
    data = bytearray(open(os.path.join(ORIG, MSG_REL), 'rb').read())
    hits = [(o, t) for o, k, t in msgfile.scan(bytes(data)) if k == 'jp' and t == SRC]
    if not hits:
        sys.exit('★원문을 못 찾았다')
    off, _ = hits[0]
    src_b = SRC.encode('cp932')
    # ★예산은 «치환 바이트열» 로 재야 한다. KO_TEXT 를 cp932 로 인코딩하면
    #   한글이 통째로 날아가 9B 같은 헛수치가 나온다(예전에 그렇게 찍혔다).
    #   실제 검사는 아래 out 을 다 만든 뒤에 한다.
    print('\n대상 문자열 0x%06X  원문 %d B' % (off, len(src_b)))

    used = set(SRC)

    # --- 앞 8음절: 기존 한자 칸 재활용 ---
    # ★★센티널 배제 — 미수록 한자 구역이 통째로 한 칸(주로 0)을 가리킨다.
    #   `drop_sentinel` 은 알려진 값 하나만 거른다. **여러 글자가 같은 칸을
    #   가리키면 그건 진짜 글리프가 아니다**로 판정해야 한다.
    inv = {}
    for c, g in m.items():
        inv.setdefault(g, []).append(c)
    donors = [c for c in sorted(m, key=lambda c: m[c])
              if c not in used and 0x4e00 <= ord(c) <= 0x9fff
              and len(inv[m[c]]) == 1 and atl.ink(m[c]) > 0]
    print('재활용 가능한 «단독 매핑» 한자 %d개 (전체 매핑 %d)' % (len(donors), len(m)))
    if len(donors) < len(KO_REUSE):
        sys.exit('★재활용할 한자가 모자란다')
    reuse = {}
    for ko, ch in zip(KO_REUSE, donors):
        reuse[ko] = (ch, m[ch])

    # --- 뒤 7음절: 빈 칸 + 새 SJIS 코드 ---
    ink = {g for g in range(atl.pages * CELLS_PER_PAGE) if atl.ink(g) > 0}
    empties = [g for g in range(atl.pages * CELLS_PER_PAGE) if g not in ink]
    # 새 코드 = z_tbl 에서 미매핑(0xFFFF)이고 cp932 로 왕복되는 한자
    free_codes = []
    for i, v in enumerate(tbl.ent):
        if v != 0xffff:
            continue
        c = ZTbl.char_of(i)
        if c and c not in used and 0x4e00 <= ord(c) <= 0x9fff:
            free_codes.append(c)
    print('빈 칸 %d개 / 미매핑 한자 코드 %d개' % (len(empties), len(free_codes)))
    if len(empties) < len(KO_NEW) or len(free_codes) < len(KO_NEW):
        sys.exit('★빈 칸이나 자유 코드가 모자란다')
    new = {}
    for ko, ch, g in zip(KO_NEW, free_codes, empties):
        new[ko] = (ch, g)

    # --- 아틀라스에 그리고 z_tbl 갱신 ---
    print('\n[앞 8음절] 기존 한자 칸 재활용')
    for ko, (ch, g) in reuse.items():
        atl.set_cell(g, render2.glyph(ko, 'bold', 24))
        print('   %s ← %s (칸 %d, 코드 %s)' % (ko, ch, g, ch.encode('cp932').hex().upper()))
    print('[뒤 7음절] ★빈 칸 + 새 코드 배정')
    for ko, (ch, g) in new.items():
        atl.set_cell(g, render2.glyph(ko, 'bold', 24))
        tbl.set(ch, g)
        print('   %s ← %s (빈칸 %d, 코드 %s)' % (ko, ch, g, ch.encode('cp932').hex().upper()))

    # --- .msg 제자리 덮어쓰기 ---
    out = bytearray()
    for c in KO_TEXT:
        if c in reuse:
            out += reuse[c][0].encode('cp932')
        elif c in new:
            out += new[c][0].encode('cp932')
        else:
            out += c.encode('cp932')          # $c5 / \n / 。
    if len(out) > len(src_b):
        sys.exit('★치환 바이트열이 원문보다 길다 (%d > %d)' % (len(out), len(src_b)))
    data[off:off + len(src_b)] = bytes(out) + bytes(len(src_b) - len(out))
    print('\n.msg 치환 %dB (원문 %dB, 널 패딩 %dB)' % (len(out), len(src_b), len(src_b) - len(out)))

    atl_bytes = atl.to_bytes(keep_size=True)
    tbl_bytes = tbl.to_bytes()
    print('아틀라스 %d B = 원본 %d B / z_tbl %d B = 원본 %d B'
          % (len(atl_bytes), len(atl.raw), len(tbl_bytes), len(tbl.raw)))

    if dry:
        print('\n[미리보기만 — 게임 트리는 원본 그대로다]')
        return
    open(os.path.join(ROOT, ATL_REL), 'wb').write(atl_bytes)
    open(os.path.join(ROOT, TBL_REL), 'wb').write(tbl_bytes)
    open(os.path.join(ROOT, MSG_REL), 'wb').write(bytes(data))
    print('\n적용 완료. TUTORIAL 첫 화면을 볼 것.')


if __name__ == '__main__':
    main('--dry' in sys.argv)
