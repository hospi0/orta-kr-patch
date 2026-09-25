"""XISO(Xbox 디스크 이미지) 파일 표를 읽는다 — «제자리 패치»용.

왜: `extract-xiso -c` 로 다시 구우면 파일 배치가 통째로 달라져(섹터 99.86% 상이)
    xdelta 가 ISO 크기만큼 커진다. 원본 ISO 의 «그 파일 자리»에 직접 써넣으면
    바뀐 섹터만 달라져 배포 패치가 작아진다.

포맷 (XDVDFS)
    0x10000  magic "MICROSOFT*XBOX*MEDIA" (20B)
    +0x14    u32 root_dir_sector
    +0x18    u32 root_dir_size
    디렉터리 항목(4바이트 정렬, 이진 트리):
        u16 left · u16 right · u32 start_sector · u32 size · u8 attr · u8 name_len · name
      · left/right 는 «4바이트 단위» 오프셋. 0xFFFF 는 없음.
      · attr & 0x10 이면 디렉터리.
"""
import os
import struct
import sys

SECTOR = 2048
MAGIC = b'MICROSOFT*XBOX*MEDIA'
HDR = 0x10000


class Xiso:
    def __init__(self, path):
        self.path = path
        self.f = open(path, 'rb')
        self.f.seek(HDR)
        if self.f.read(20) != MAGIC:
            raise ValueError('XISO 가 아니다(매직 불일치): %s' % path)
        self.root_sector, self.root_size = struct.unpack('<II', self.f.read(8))

    def _read_dir(self, sector, size, prefix, out):
        self.f.seek(sector * SECTOR)
        buf = self.f.read(size)
        stack = [0]
        seen = set()
        while stack:
            off = stack.pop()
            if off in seen or off + 14 > len(buf):
                continue
            seen.add(off)
            l, r, start, sz, attr = struct.unpack_from('<HHIIB', buf, off)
            nl = buf[off + 13]
            name = buf[off + 14:off + 14 + nl].decode('latin-1')
            if l != 0xFFFF:
                stack.append(l * 4)
            if r != 0xFFFF:
                stack.append(r * 4)
            if not name:
                continue
            p = prefix + name
            if attr & 0x10:
                if sz:
                    self._read_dir(start, sz, p + '\\', out)
            else:
                out[p] = (start * SECTOR, sz)

    def files(self):
        out = {}
        self._read_dir(self.root_sector, self.root_size, '', out)
        return out


if __name__ == '__main__':
    x = Xiso(sys.argv[1])
    fs = x.files()
    print('파일 %d개 · 루트 섹터 %d (%d B)' % (len(fs), x.root_sector, x.root_size))
    for p in sorted(fs)[:15]:
        print('  %-52s @%-12d %10d B' % (p, fs[p][0], fs[p][1]))
