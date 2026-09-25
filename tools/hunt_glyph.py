"""메뉴가 실제로 쓰는 폰트를 «글리프 비트맵 바이트»로 추적한다.

지금까지 실기로 확정된 것 (2026-08-12)
  · `sprite/Font/` 아틀라스 **28개를 전부 공백**으로 만들어도
    **메인 메뉴 설명 상자**의 일본어는 멀쩡히 나온다.
    ⇒ 그 화면은 그 파일들을 쓰지 않는다.
    ⚠️다른 화면(스테이지 자막·튜토리얼·판도라의 상자)까지 미사용이라는 뜻은 **아니다** — 미확인.

방법
  원본 `Zenkaku_Common.txb` 에서 «あ» 글리프가 들어 있는 DXT3 블록의 바이트를 뽑아,
  디스크의 모든 파일(PCMP 면 풀어서)에서 **그 바이트열을 그대로 찾는다.**
  블록 16바이트는 연속이라 배치·해상도·파일형식과 무관하게 걸린다.
"""
import os
import sys
import struct
from pcmp import decompress
from project import ROOT, FONT_DIR, GLYPH_W, GLYPH_H, pristine
from cells import COLS

PAGE_W = 512
BLOCKS_PER_ROW = PAGE_W // 4


def cell_blocks(data, start, gidx):
    """글리프 칸 하나가 쓰는 DXT3 블록 16바이트들을 돌려준다."""
    r, c = divmod(gidx, COLS)
    y0, x0 = r * GLYPH_H, c * GLYPH_W
    out = []
    for by in range(y0 // 4, (y0 + GLYPH_H) // 4):
        for bx in range(x0 // 4, (x0 + GLYPH_W) // 4):
            off = start + (by * BLOCKS_PER_ROW + bx) * 16
            out.append(data[off:off + 16])
    return out


def pick_needles(n=6):
    p = pristine(os.path.join(FONT_DIR, 'Zenkaku_Common.txb'))
    d = decompress(open(p, 'rb').read())
    pages = struct.unpack_from('<I', d, 4)[0]
    start = 0x20 if pages == 1 else 0x50
    cand = []
    for gidx, name in ((104, 'あ'), (112, 'お'), (108, 'う')):
        for b in cell_blocks(d, start, gidx):
            alpha = b[:8]
            # 잉크가 충분히 있고 단조롭지 않은 블록만 = 고유한 지문
            if alpha.count(0) <= 2 and len(set(alpha)) >= 5:
                cand.append((name, gidx, b))
    return cand[:n]


if __name__ == '__main__':
    needles = pick_needles()
    print('지문 %d개 (원본 Zenkaku_Common 의 글리프 블록):' % len(needles))
    for nm, g, b in needles:
        print('   %s 칸%d  %s' % (nm, g, b.hex()))
    if not needles:
        sys.exit('지문을 못 뽑았다')

    hits = {}
    scanned = 0
    for dp, dn, fns in os.walk(ROOT):
        for fn in fns:
            p = os.path.join(dp, fn)
            sz = os.path.getsize(p)
            if sz > 60 * 1024 * 1024:
                continue
            ext = os.path.splitext(fn)[1].lower()
            if ext in ('.wav', '.wma', '.sfd', '.aix', '.pwv'):
                continue
            try:
                raw = open(p, 'rb').read()
            except Exception:
                continue
            bodies = [raw]
            if raw[:4] == b'PCMP':
                try:
                    bodies.append(decompress(raw))
                except Exception:
                    pass
            scanned += 1
            for body in bodies:
                for nm, g, b in needles:
                    if b in body:
                        rel = os.path.relpath(p, ROOT)
                        hits.setdefault(rel, set()).add(nm)
    print('\n훑은 파일 %d개' % scanned)
    if not hits:
        print('★어느 파일에서도 그 글리프 바이트가 안 나온다.')
        print('  -> 폰트가 이 포맷이 아니거나(다른 bpp/압축), 디스크 밖(XBE 내장·시스템 폰트)이다.')
    for rel, ns in sorted(hits.items()):
        print('  %-52s %s' % (rel, ''.join(sorted(ns))))
