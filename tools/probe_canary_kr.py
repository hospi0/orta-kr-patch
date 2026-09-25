"""★한글 카나리아 — 「비우기」 대신 「한글로 바꿔 그리기」로 폰트 출처를 판정한다.

지금까지의 파괴 시험은 전부 «비우기»였는데 판정이 약하다. 글자가 안 보이는 건
"이 파일을 쓰는데 지웠다" 일 수도 "원래 안 쓴다" 일 수도 있다. 여기서 헤맸다.

바꿔 그리면 애매함이 없다 — **한글이 뜨면 그 파일이 그 화면의 폰트다.**
게다가 성공하면 그게 곧 최종 산출물이다.

★`.msg` 는 **원본 그대로 둔다.** 텍스트 변수를 빼서 폰트만 본다.
★카나리아 글자는 각 화면 원문에 실제로 나오는 것만 골랐다(빈도 확인함) —
  세션1 에서 확인 없이 고른 표식이 표식 구실을 못 했다.

판정표 (한 빌드로 4가지가 동시에 갈린다)

    화면            가나가 한글        장면 한자가 한글
    오프닝 자막     Common 쓴다        Zenkaku_OpeningDemo 쓴다
    메인 메뉴 설명  Common 쓴다        Zenkaku_Menu 쓴다

  메뉴 쪽이 둘 다 «일본어 그대로» 면 → 제3의 폰트 확정, 사냥을 계속한다.
  (오프라인 증거도 그쪽이다: 메뉴 원문 전각 321자 중 92자가 어느 표에도 없다.)
"""
import os
import shutil
import sys
from atlaswrite import Atlas
from ztbl import ZTbl
from project import ROOT, WORK, FONT_DIR, pristine, GLYPH_W, GLYPH_H
import render2

# ⛔「꽉 찬 흰 네모」 표식은 **쓰지 말 것**.
#   알파를 전부 255 로 채우면 원본 컬러(=원본 글자)가 100% 그대로 통과해
#   화면엔 «원본 글자가 멀쩡히» 나온다. 세션2 에서 이걸 「그 칸을 안 쓴다」로
#   잘못 읽었다. 판정에는 알파·컬러를 둘 다 바꾸는 **한글**을 쓴다.
BLOCK = '■'


def block_cell():
    return bytes([255] * (GLYPH_W * GLYPH_H))


ORIG = os.path.join(WORK, 'orig')

# 아틀라스별 카나리아: {원문 글자: 한글 or BLOCK}
CANARY = {
    # ★★같은 글자를 두 아틀라스에서 **서로 다른 한글**로 바꾼다.
    #   그래야 「어느 쪽이 이기는가」가 한 빌드로 갈린다.
    #   대상 = NEW GAME 설명문 「最初からゲームを開始します。」
    #     最 : Menu 없음 / Common 280
    #     初 : Menu 510  / Common 284
    #     開 : Menu 119  / Common 269
    #     始 : Menu 412  / Common 282
    'Zenkaku_Common.txb': (
        'Reisyo_Cmn_z_tbl_cmn.bin',
        {'最': '최', '初': '춘', '開': '하', '始': '늘'},
    ),
    # ★`Zenkaku_Menu.txb` — 이름부터 메뉴 폰트인데 세션1~2 에 **한 번도 시험 못 했다**.
    #   기존 PCMP 인코더가 이 파일에서만 무수정 왕복 +2578 B 라 크기를 못 맞췄기 때문.
    #   `lzopt.py`(chain 4096 + lazy matching)로 -7463 B 가 되어 이제 넣을 수 있다.
    'Zenkaku_Menu.txb': (
        'Reisyo_Menu_z_tbl.bin',
        {'初': '초', '開': '개', '始': '시'},
    ),
    # 양성 대조 — 이미 실기에서 한글이 확인된 경로. 이게 안 뜨면 빌드가 반영 안 된 것이다.
    # ★세션2 에 양성 대조 없는 빌드를 돌려 결론을 못 낸 적이 있다. 반복 금지.
    'Zenkaku_OpeningDemo.txb': (
        'Reisyo_OpeningDemo_z_tbl.bin',
        {'人': '강', '生': '산', '類': '진', '自': '수', '造': '해', '兵': '별'},
    ),
}


def restore_all():
    n = 0
    for dp, dn, fns in os.walk(ORIG):
        for fn in fns:
            src = os.path.join(dp, fn)
            shutil.copy2(src, os.path.join(ROOT, os.path.relpath(src, ORIG)))
            n += 1
    return n


def apply(dry=False):
    for atl_name, (tbl_name, mapping) in CANARY.items():
        atl_rel = os.path.join('sprite', 'Font', atl_name)
        # ★조사·읽기는 항상 무수정본에서 (project.pristine). 백업이 없으면 원본 트리.
        tbl = ZTbl(pristine(os.path.join(FONT_DIR, tbl_name)))
        m = tbl.mapping(drop_sentinel=True)
        a = Atlas(pristine(os.path.join(FONT_DIR, atl_name)))
        done = []
        for src_ch, ko in mapping.items():
            if src_ch not in m:
                print('  ⚠ %s: 원문자 %r 가 표에 없다 — 건너뜀' % (atl_name, src_ch))
                continue
            g = m[src_ch]
            before = a.ink(g)
            if before == 0:
                print('  ⚠ %s: %r(칸 %d) 이 원래 빈칸 — 표식 구실을 못 한다' % (atl_name, src_ch, g))
                continue
            a.set_cell(g, block_cell() if ko == BLOCK else render2.glyph(ko, 'bold', 24))
            done.append('%s→%s(칸%d, 잉크 %d→%d)' % (src_ch, ko, g, before, a.ink(g)))
        print('%-26s %d칸 교체' % (atl_name, len(done)))
        for d in done:
            print('    ', d)
        try:
            data = a.to_bytes(keep_size=True)
        except ValueError as e:
            print('  ★크기 초과로 중단:', e)
            return False
        print('    재압축 %d B = 원본 %d B (크기 유지)' % (len(data), len(a.raw)))
        if not dry:
            with open(os.path.join(ROOT, atl_rel), 'wb') as f:
                f.write(data)
    return True


if __name__ == '__main__':
    dry = '--dry' in sys.argv
    print('원본 전량 원복: %d개' % restore_all())
    print("폰트:", render2.font_desc("bold", 24))
    ok = apply(dry)
    print()
    if dry:
        print('[미리보기만 — 게임 트리는 원본 그대로다]')
    elif ok:
        print('게임 트리에 적용 완료. 이제 ISO 를 재조립해 실기로 볼 것.')
        print('  .msg 는 손대지 않았다 — 원문 일본어 그대로다.')
