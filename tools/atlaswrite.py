"""아틀라스 «칸 단위» 글리프 덮어쓰기.

★★★**알파와 컬러를 둘 다** 갈아끼운다.

  세션2 에서 알파만 바꿨다가 실기에서 «깨진 조각»이 나왔다. 원인은
  `docs/survey.md` 의 「컬러 절반은 대개 단색」이 **틀렸기** 때문이다 —
  컬러 채널에도 **같은 글자가 또렷이 그려져 있다**(실측: 글자 칸의 비단색
  픽셀이 알파 잉크보다 오히려 많다). 게임은 컬러 × 알파로 그리므로
  알파만 바꾸면 화면엔 **내 한글 ∩ 원본 한자**의 교집합만 남는다.
  지문: 알파를 전부 255 로 채운 칸(人)만 «원본 글자 그대로» 멀쩡히 나왔다.
  → [[feedback_verify_which_asset_the_screen_uses]] 와 같은 종류의 실수다.
     문서에 적힌 관찰을 **검증 없이** 믿었다.

  실측한 원본 컬러 블록: 글자 있는 블록은 c0=0xFFFF(흰) / c1=0x0000(검) 계열
  (215종 중 최빈), c0>c1 이라 DXT1 **4색 모드**다.

칸 28x28 은 4의 배수라 **DXT 블록 경계에 정확히 맞는다** — 칸 하나 = 7x7 블록.
그래서 이웃 칸을 침범하지 않는다.

크기 규칙: 파일 크기를 바꾸면 부팅불가일 수 있다(docs/survey.md 6.1 미확인 리스크).
`save()` 는 재압축 결과가 원본보다 크면 **거부**하고, 작으면 뒤를 0 으로 패딩해
원본과 **같은 크기**로 맞춘다.
"""
import os
import struct
from pcmp import decompress, build as pcmp_build
from project import GLYPH_W, GLYPH_H

PAGE_W = PAGE_H = 512
PAGE_BYTES = PAGE_W * PAGE_H          # DXT3 = 픽셀당 1바이트
BLOCKS_X = PAGE_W // 4                # 128
CELL_BLOCKS = GLYPH_W // 4            # 7
COLS = PAGE_W // GLYPH_W              # 18
ROWSC = PAGE_H // GLYPH_H             # 18
CELLS_PER_PAGE = COLS * ROWSC         # 324


class Atlas:
    def __init__(self, path):
        self.path = path
        self.raw = open(path, 'rb').read()
        self.packed = self.raw[:4] == b'PCMP'
        d = decompress(self.raw) if self.packed else self.raw
        self.pages = struct.unpack_from('<I', d, 4)[0]
        self.start = 0x20 if self.pages == 1 else 0x50
        self.head = d[:self.start]
        self.body = bytearray(d[self.start:])
        assert len(self.body) == self.pages * PAGE_BYTES, \
            '본문 %d != 페이지 %d * %d' % (len(self.body), self.pages, PAGE_BYTES)

    # --- 칸 <-> 블록 주소 ---
    def _block_off(self, gidx, brow, bcol):
        page, rem = divmod(gidx, CELLS_PER_PAGE)
        r, c = divmod(rem, COLS)
        by = r * CELL_BLOCKS + brow
        bx = c * CELL_BLOCKS + bcol
        return page * PAGE_BYTES + (by * BLOCKS_X + bx) * 16

    def cell_alpha(self, gidx):
        """칸 idx 를 28x28 그레이(0~255)로."""
        out = bytearray(GLYPH_W * GLYPH_H)
        for brow in range(CELL_BLOCKS):
            for bcol in range(CELL_BLOCKS):
                o = self._block_off(gidx, brow, bcol)
                a = int.from_bytes(self.body[o:o + 8], 'little')
                for py in range(4):
                    for px in range(4):
                        v = (a >> (4 * (py * 4 + px))) & 0xF
                        out[(brow * 4 + py) * GLYPH_W + bcol * 4 + px] = v * 17
        return bytes(out)

    def cell_color(self, gidx):
        """칸 idx 의 컬러 채널을 28x28 휘도로. ★여기에도 글자가 그려져 있다."""
        out = bytearray(GLYPH_W * GLYPH_H)
        for brow in range(CELL_BLOCKS):
            for bcol in range(CELL_BLOCKS):
                o = self._block_off(gidx, brow, bcol) + 8
                c0, c1 = struct.unpack_from('<HH', self.body, o)
                bits = struct.unpack_from('<I', self.body, o + 4)[0]

                def lum(c):
                    r = ((c >> 11) & 31) * 255 // 31
                    g = ((c >> 5) & 63) * 255 // 63
                    b = (c & 31) * 255 // 31
                    return (r * 30 + g * 59 + b * 11) // 100
                l0, l1 = lum(c0), lum(c1)
                pal = [l0, l1, (2 * l0 + l1) // 3, (l0 + 2 * l1) // 3] if c0 > c1 \
                    else [l0, l1, (l0 + l1) // 2, 0]
                for py in range(4):
                    for px in range(4):
                        i = (bits >> (2 * (py * 4 + px))) & 3
                        out[(brow * 4 + py) * GLYPH_W + bcol * 4 + px] = pal[i]
        return bytes(out)

    def set_cell(self, gidx, gray, color=True):
        """칸 idx 를 교체. gray = 28*28 bytes.

        ★기본값 color=True — 알파와 컬러를 **둘 다** 쓴다.
          컬러를 안 쓰면 화면엔 원본 글자와의 교집합만 나온다(모듈 설명 참조).
        """
        assert len(gray) == GLYPH_W * GLYPH_H, '글리프 크기가 %d' % len(gray)
        assert 0 <= gidx < self.pages * CELLS_PER_PAGE, '칸 %d 는 범위 밖' % gidx
        for brow in range(CELL_BLOCKS):
            for bcol in range(CELL_BLOCKS):
                a = 0
                bits = 0
                for py in range(4):
                    for px in range(4):
                        v = gray[(brow * 4 + py) * GLYPH_W + bcol * 4 + px]
                        a |= (v >> 4) << (4 * (py * 4 + px))
                        # DXT1 4색 모드(c0=흰 0xFFFF, c1=검 0x0000)의 팔레트
                        #   0=255  2=170  3=85  1=0   → 경계는 그 중간값
                        i = 0 if v >= 212 else 2 if v >= 128 else 3 if v >= 43 else 1
                        bits |= i << (2 * (py * 4 + px))
                o = self._block_off(gidx, brow, bcol)
                self.body[o:o + 8] = a.to_bytes(8, 'little')
                if color:
                    struct.pack_into('<HHI', self.body, o + 8, 0xFFFF, 0x0000, bits)


    # ═══ ★★★픽셀 좌표로 칸을 다루기 ═══════════════════════════════════
    #  다중 페이지 아틀라스(Menu)는 «칸 번호 -> 위치» 공식이 우리 모델과 다르다.
    #  x 시작점이 페이지마다 달라(0->16 1->20 2->24 3->0) 28px 격자에 안 맞는다.
    #  ⇒ 공식을 맞추려 하지 말고 **실측한 픽셀 좌표**로 직접 쓴다
    #    (tools/menupos.py 로 오라클 대조, tools/interp_pos.py 로 완성).
    #  x·y 는 둘 다 4의 배수라 DXT 블록 경계에 맞는다.

    def _block_off_xy(self, x, y, brow, bcol):
        by = y // 4 + brow
        bx = x // 4 + bcol
        return (by * BLOCKS_X + bx) * 16

    def cell_alpha_xy(self, x, y):
        out = bytearray(GLYPH_W * GLYPH_H)
        for brow in range(CELL_BLOCKS):
            for bcol in range(CELL_BLOCKS):
                o = self._block_off_xy(x, y, brow, bcol)
                a = int.from_bytes(self.body[o:o + 8], 'little')
                for py in range(4):
                    for px in range(4):
                        v = (a >> (4 * (py * 4 + px))) & 0xF
                        out[(brow * 4 + py) * GLYPH_W + bcol * 4 + px] = v * 17
        return bytes(out)

    def ink_xy(self, x, y):
        return sum(1 for v in self.cell_alpha_xy(x, y) if v)

    def set_at(self, x, y, gray, color=True):
        assert len(gray) == GLYPH_W * GLYPH_H
        assert x % 4 == 0 and y % 4 == 0, '(%d,%d) 는 블록 경계가 아니다' % (x, y)
        for brow in range(CELL_BLOCKS):
            for bcol in range(CELL_BLOCKS):
                a = 0
                bits = 0
                for py in range(4):
                    for px in range(4):
                        v = gray[(brow * 4 + py) * GLYPH_W + bcol * 4 + px]
                        a |= (v >> 4) << (4 * (py * 4 + px))
                        i = 0 if v >= 212 else 2 if v >= 128 else 3 if v >= 43 else 1
                        bits |= i << (2 * (py * 4 + px))
                o = self._block_off_xy(x, y, brow, bcol)
                self.body[o:o + 8] = a.to_bytes(8, 'little')
                if color:
                    struct.pack_into('<HHI', self.body, o + 8, 0xFFFF, 0x0000, bits)

    def ink(self, gidx):
        return sum(1 for v in self.cell_alpha(gidx) if v)

    # --- 저장 ---
    def to_bytes(self, keep_size=True):
        d = self.head + bytes(self.body)
        # ★개선 인코더(lzopt)를 먼저 쓴다 — 기존 그리디는 Zenkaku_Menu 에서
        #   무수정 왕복만으로도 +2578 B 라 그 파일을 아예 못 건드렸다.
        #   chain 48->4096 + lazy matching 으로 -7463 B 가 됐다.
        try:
            from lzopt import build as lz_build
            out = lz_build(d) if self.packed else d
        except Exception:
            out = pcmp_build(d) if self.packed else d
        if keep_size and len(out) != len(self.raw):
            if len(out) > len(self.raw):
                raise ValueError('재압축이 원본보다 크다: %d > %d (%+d B)'
                                 % (len(out), len(self.raw), len(out) - len(self.raw)))
            out = out + bytes(len(self.raw) - len(out))
        return out

    def save(self, dst, keep_size=True):
        b = self.to_bytes(keep_size)
        with open(dst, 'wb') as f:
            f.write(b)
        return len(b), len(self.raw)


def verify_roundtrip(path):
    """★인코더는 디코더보다 잘 깨진다 — 아무것도 안 고친 왕복이 바이트 동일한가."""
    a = Atlas(path)
    d = a.head + bytes(a.body)
    re = decompress(pcmp_build(d)) if a.packed else d
    orig = decompress(a.raw) if a.packed else a.raw
    return re == orig, len(pcmp_build(d)) if a.packed else len(d), len(a.raw)


if __name__ == '__main__':
    import sys
    from project import FONT_DIR, pristine
    p = pristine(os.path.join(FONT_DIR, sys.argv[1] if len(sys.argv) > 1
                              else 'Zenkaku_Common.txb'))
    ok, newlen, oldlen = verify_roundtrip(p)
    print('%s' % os.path.basename(p))
    print('  무수정 왕복 픽셀 일치: %s' % ('OK' if ok else '★불일치'))
    print('  재압축 %d B / 원본 %d B (%+d)' % (newlen, oldlen, newlen - oldlen))
    a = Atlas(p)
    print('  페이지 %d, 칸 %d' % (a.pages, a.pages * CELLS_PER_PAGE))
