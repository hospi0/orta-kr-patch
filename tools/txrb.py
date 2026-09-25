"""TXRB 컨테이너 해석 — 폭·포맷·페이지.

실측으로 확정한 헤더 (세션2)
    0x00 'TXRB'
    0x04 u32  pages          서브텍스처(페이지) 수
    0x14 u32  width          ★텍스처 폭. survey.md 에 「용도불명」이라 적혀 있었다
    0x18 u32  fmt            하위 바이트가 픽셀 포맷, 상위가 밉맵 관련으로 보인다
    데이터 시작 = pages==1 이면 0x20, 아니면 0x20 + pages*0x0C

높이 필드는 없다 — 데이터 크기 / (폭 * bpp) 로 역산한다.
bpp 는 포맷 하위 바이트에서, 그 추정이 정수 높이를 못 내면 후보를 다 시도한다.
"""
import os
import struct
from pcmp import decompress

# 포맷 하위 바이트 -> 픽셀당 바이트. 실측으로 채워 나간다.
#   0x06 = DXT3(BC2) 1B/px  (Zenkaku_* 512x512 = 262144 로 확인)
BPP = {0x06: 1.0}
BPP_CANDIDATES = (0.5, 1.0, 2.0, 4.0)


class Txrb:
    def __init__(self, path):
        self.path = path
        raw = open(path, 'rb').read()
        self.packed = raw[:4] == b'PCMP'
        d = decompress(raw) if self.packed else raw
        self.data = d
        self.ok = d[:4] == b'TXRB'
        if not self.ok:
            return
        self.pages = struct.unpack_from('<I', d, 4)[0]
        self.width = struct.unpack_from('<I', d, 0x14)[0]
        self.fmt = struct.unpack_from('<I', d, 0x18)[0]
        self.start = 0x20 if self.pages == 1 else 0x20 + self.pages * 0x0C
        self.body = len(d) - self.start

    def page_bytes(self):
        if not self.ok or not (0 < self.pages <= 256):
            return 0
        return self.body // self.pages

    def guesses(self):
        """[(bpp, height)] — 폭과 페이지 크기로 높이가 정수로 떨어지는 조합."""
        if not self.ok or not self.width or self.width > 4096:
            return []
        pb = self.page_bytes()
        out = []
        pref = BPP.get(self.fmt & 0xFF)
        for bpp in ([pref] if pref else []) + [b for b in BPP_CANDIDATES if b != pref]:
            rowb = self.width * bpp
            if rowb <= 0 or pb % rowb:
                continue
            h = int(pb / rowb)
            if 8 <= h <= 4096:
                out.append((bpp, h))
        return out

    def page(self, i):
        pb = self.page_bytes()
        return self.data[self.start + i * pb: self.start + (i + 1) * pb]


if __name__ == '__main__':
    import sys
    import collections
    from txbsurvey import txb_files
    from project import ROOT
    scope = sys.argv[1] if len(sys.argv) > 1 else 'rest'
    fmts = collections.Counter()
    nogeuss = []
    rows = []
    for rel in txb_files(scope):
        t = Txrb(os.path.join(ROOT, rel))
        if not t.ok:
            continue
        fmts[t.fmt] += 1
        g = t.guesses()
        rows.append((rel, t))
        if not g:
            nogeuss.append(rel)
    print('%s: TXRB %d개' % (scope, len(rows)))
    print('\n-- fmt 분포 --')
    for f, c in fmts.most_common(12):
        print('   0x%06X  %4d   (하위=0x%02X)' % (f, c, f & 0xFF))
    print('\n-- 폭 분포 --')
    for w, c in collections.Counter(t.width for _, t in rows).most_common(10):
        print('   %-6s %d' % (w, c))
    print('\n크기 역산 실패 %d개' % len(nogeuss))
    for r in nogeuss[:8]:
        print('   ', r)
