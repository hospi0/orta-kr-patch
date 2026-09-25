"""한글 최소 시험 — 폰트 경로만 검증한다.

`.msg` 편집은 시험1~3 으로 완전히 검증됐다(꽉 채움·짧게+널·개행 전부 정상).
남은 미검증 = **아틀라스 재압축 + 글리프 칸 배정**. 그것만 딱 떼어 시험한다.

  · `Zenkaku_Common.txb` 의 **필요한 칸만** 한글로 다시 그린다 (Menu 는 안 건드림)
  · **NEW GAME(idx 4) 한 줄만** 한글로 바꾼다
  · 나머지 항목은 **원본 일본어 그대로**

판정
  NEW GAME 한글 + 다른 항목 일부 글자가 한글로 깨짐
      -> 아틀라스도 배정도 정상. 전량 빌드로 간다.
  NEW GAME 이 «일본어 잡소리» + 다른 항목 멀쩡
      -> 아틀라스가 안 먹었다(내 PCMP 재압축을 게임이 못 읽는다).
  NEW GAME 빈칸
      -> 배정한 코드가 그 화면에서 안 잡힌다.
"""
import os
import shutil
import struct
from project import ROOT, WORK, FONT_DIR, GLYPH_W, GLYPH_H
from pcmp import decompress, build as pcmp_build
from dxt import decode_alpha, encode_alpha
from cells import PAGE_W, PAGE_H, PAGE_BYTES, COLS
from budget_menu import entries
from alloc import build_pool
import render

ORIG = os.path.join(WORK, 'orig')
REL_CMN = os.path.join('sprite', 'Font', 'Zenkaku_Common.txb')
REL_MSG = os.path.join('menudata', 'TextData', 'Text_MenuInst_JP.msg')

KO_TEXT = '처음부터 게임을 시작합니다.'
IDX = 4


def restore_all():
    for dp, dn, fns in os.walk(ORIG):
        for fn in fns:
            src = os.path.join(dp, fn)
            shutil.copy2(src, os.path.join(ROOT, os.path.relpath(src, ORIG)))


if __name__ == '__main__':
    restore_all()
    print('원본 전량 원복')

    syl = []
    for c in KO_TEXT:
        if 0xac00 <= ord(c) <= 0xd7a3 and c not in syl:
            syl.append(c)
    pool = build_pool()
    assert len(pool) >= len(syl)
    smap = {}
    for s, (ch, g, mcell, kind) in zip(syl, pool):
        smap[s] = (ch, g, kind)
    print('음절 %d개 배정:' % len(syl))
    for s, (ch, g, kind) in smap.items():
        print('   %s -> %s (%s, Common 칸 %d)' % (s, ch, kind, g))
    subs = ''.join(v[0] for v in smap.values())
    print('★대체로 쓴 원본 글자: %s' % subs)
    print('  -> 다른 메뉴 항목의 일본어에 이 글자가 있으면 한글로 보여야 정상이다.')

    # --- 폰트: 필요한 칸만 다시 그린다
    d = decompress(open(os.path.join(ORIG, REL_CMN), 'rb').read())
    pages = struct.unpack_from('<I', d, 4)[0]
    start = 0x20 if pages == 1 else 0x50
    head, body = d[:start], d[start:]
    planes = [bytearray(decode_alpha(body[i * PAGE_BYTES:(i + 1) * PAGE_BYTES],
                                     PAGE_W, PAGE_H)) for i in range(pages)]
    per_page = (PAGE_W // GLYPH_W) * (PAGE_H // GLYPH_H)
    for s, (ch, g, kind) in smap.items():
        page, idx = divmod(g, per_page)
        r, c = divmod(idx, COLS)
        gl = render.glyph(s)
        pl = planes[page]
        for y in range(GLYPH_H):
            base = (r * GLYPH_H + y) * PAGE_W + c * GLYPH_W
            pl[base:base + GLYPH_W] = gl[y * GLYPH_W:(y + 1) * GLYPH_W]
    newbody = b''.join(encode_alpha(bytes(p), PAGE_W, PAGE_H) for p in planes)
    packed = pcmp_build(head + newbody)
    o = open(os.path.join(ORIG, REL_CMN), 'rb').read()
    assert len(packed) <= len(o), (len(packed), len(o))
    with open(os.path.join(ROOT, REL_CMN), 'wb') as f:
        f.write(packed + b'\x00' * (len(o) - len(packed)))
    print('\n%s  %d B (원본과 동일), 칸 %d개 교체' % (REL_CMN, len(o), len(smap)))

    # --- 텍스트: idx 4 한 줄만
    b = bytearray()
    for c in KO_TEXT:
        if 0xac00 <= ord(c) <= 0xd7a3:
            b += smap[c][0].encode('cp932')
        else:
            b += c.encode('cp932')
    md = bytearray(open(os.path.join(ORIG, REL_MSG), 'rb').read())
    _, es = entries()
    e = es[IDX]
    assert len(b) <= e['bytes'], (len(b), e['bytes'])
    md[e['off']:e['off'] + e['bytes']] = bytes(b) + b'\x00' * (e['bytes'] - len(b))
    with open(os.path.join(ROOT, REL_MSG), 'wb') as f:
        f.write(bytes(md))
    print('%s  idx %d 만 교체  %dB / %dB' % (REL_MSG, IDX, len(b), e['bytes']))
    print('   기록 바이트:', ' '.join('%02x' % x for x in b))
