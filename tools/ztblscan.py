"""★디스크 전체에서 «z_tbl 머리 서명»을 찾는다 — Menu 아틀라스를 쓰는 «다른 표» 사냥.

z_tbl 머리 (docs/survey.md · tools/ztbl.py):
    u32 zenkaku(1) · u32 pages · u32 glyph_w(28) · u32 glyph_h(28) · u32 atlas_w(512)

⇒ 서명 = `01 00 00 00 ?? ?? ?? ?? 1C 00 00 00 1C 00 00 00 00 02 00 00`
파일 «어디에서든» 찾는다(컨테이너 안에 박혀 있을 수 있다). 압축 파일은 PCMP 해제도 시도.
"""
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, WORK

ORIG = os.path.join(WORK, 'orig')
SIG = re.compile(
    rb'\x01\x00\x00\x00.{4}\x1c\x00\x00\x00\x1c\x00\x00\x00\x00\x02\x00\x00',
    re.S)


def scan(d, name, out):
    for m in SIG.finditer(d):
        off = m.start()
        pages = struct.unpack_from('<I', d, off + 4)[0]
        if not (1 <= pages <= 16):
            continue
        out.append((name, off, pages, len(d)))


def main():
    hits = []
    files = 0
    pcmp = 0
    for dp, dn, fn in os.walk(ROOT):
        for f in sorted(fn):
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, ROOT)
            o = os.path.join(ORIG, rel)
            src = o if os.path.exists(o) else p
            try:
                d = open(src, 'rb').read()
            except Exception:
                continue
            files += 1
            scan(d, rel, hits)
            if d[:4] == b'PCMP':
                try:
                    from pcmp import decompress
                    u = decompress(d)
                    pcmp += 1
                    scan(u, rel + '  (PCMP해제)', hits)
                except Exception:
                    pass
    print('파일 %d개 검사 (PCMP 해제 %d개)' % (files, pcmp))
    print('%-56s %10s %6s %10s' % ('파일', '오프셋', '페이지', '파일크기'))
    for name, off, pages, size in hits:
        print('%-56s %10d %6d %10d' % (name, off, pages, size))
    print('총 %d건' % len(hits))


if __name__ == '__main__':
    main()
