"""Reisyo_*_z_tbl.bin / Arial_h_tbl.bin 읽기·쓰기.

포맷 (docs/survey.md):
    0x00 u32 zenkaku   1 = 2바이트(전각), 0 = 1바이트(반각)
    0x04 u32 pages     아틀라스 페이지 수 (Menu 만 4, 나머지 1)
    0x08 u32 glyph_w   28
    0x0c u32 glyph_h   28
    0x10 u32 atlas_w   512
    0x14 u16 * N       코드 -> 글리프 인덱스, 0xFFFF = 없음
                       전각: N = 9024, 인덱스 = 리드순번*192 + (트레일-0x40)
                       반각: 인덱스 = 바이트값
    이후 0 패딩 (파일은 2048 배수)

★해시가 아니라 직접 표다. 아무 SJIS 코드나 원하는 글리프에 붙일 수 있다.
"""
import struct
from project import LEADS, ZTBL_STRIDE, ZTBL_ENTRIES

# NEC/IBM 중복한자 구역이 통째로 가리키는 자리. 진짜 글리프가 아니다.
SENTINEL = 7196


class ZTbl:
    def __init__(self, path):
        self.path = path
        with open(path, 'rb') as f:
            self.raw = f.read()
        (self.zenkaku, self.pages, self.glyph_w,
         self.glyph_h, self.atlas_w) = struct.unpack_from('<5I', self.raw, 0)
        n = ZTBL_ENTRIES if self.zenkaku else 256
        self.ent = list(struct.unpack_from('<%dH' % n, self.raw, 0x14))

    # --- 인덱스 <-> 문자 ---
    @staticmethod
    def index_of(ch):
        """문자 -> 표 인덱스. 전각 전용."""
        b = ch.encode('cp932')
        if len(b) != 2:
            raise ValueError('전각이 아니다: %r' % ch)
        lead, trail = b[0], b[1]
        return LEADS.index(lead) * ZTBL_STRIDE + (trail - 0x40)

    @staticmethod
    def char_of(i):
        li, ti = divmod(i, ZTBL_STRIDE)
        if li >= len(LEADS):
            return None
        trail = 0x40 + ti
        if trail == 0x7f or trail > 0xfc:
            return None
        try:
            return bytes([LEADS[li], trail]).decode('cp932')
        except Exception:
            return None

    # --- 조회 ---
    def mapping(self, drop_sentinel=True):
        """{문자: 글리프인덱스}. 반각 표는 {바이트값: 인덱스}."""
        m = {}
        for i, g in enumerate(self.ent):
            if g == 0xffff or (drop_sentinel and g == SENTINEL):
                continue
            if self.zenkaku:
                c = self.char_of(i)
                if c is not None:
                    m[c] = g
            else:
                m[i] = g
        return m

    def glyph_count(self, drop_sentinel=True):
        return len(set(self.mapping(drop_sentinel).values()))

    def capacity(self, cells_per_page):
        return self.pages * cells_per_page

    # --- 기록 ---
    def set(self, ch, glyph):
        self.ent[self.index_of(ch) if self.zenkaku else ch] = glyph

    def to_bytes(self):
        out = bytearray(self.raw)
        struct.pack_into('<%dH' % len(self.ent), out, 0x14, *self.ent)
        return bytes(out)


if __name__ == '__main__':
    import sys, os
    from project import FONT_DIR, SCENES, COMMON_TBL, CELLS_PER_PAGE, scene_tbl
    print('%-16s %7s %7s %6s %6s' % ('scene', 'glyphs', 'cells', 'free', 'pages'))
    rows = [('Common', os.path.join(FONT_DIR, COMMON_TBL))]
    rows += [(s, scene_tbl(s)) for s in SCENES]
    for name, p in rows:
        t = ZTbl(p)
        g, cap = t.glyph_count(), t.capacity(CELLS_PER_PAGE)
        print('%-16s %7d %7d %6d %6d' % (name, g, cap, cap - g, t.pages))
