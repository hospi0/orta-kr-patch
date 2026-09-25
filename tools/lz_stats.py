"""원본 PCMP 스트림과 «내 압축기» 출력의 토큰 통계를 비교한다.

★게임 해제기가 내 스트림을 못 읽으면 폰트가 통째로 안 뜬다.
  내 디코더로 왕복되는 것만으로는 부족하다 — 원본이 «실제로 쓰는 범위» 안에
  머물러야 안전하다.
"""
import os
import struct
import sys
from pcmp import decompress, lzss_encode
from project import ROOT, FONT_DIR, scene_atlas


def walk(comp, out_size):
    """스트림을 훑어 (최대오프셋, 최대길이, 제로필횟수, 토큰수, 리터럴수)."""
    out_len = 0
    idx, ilen = 0, len(comp)
    b, bits = comp[idx], 8
    idx += 1
    mo = ml = zf = ntok = nlit = 0
    while out_len < out_size:
        if idx > ilen:
            break
        op = b & 0x80
        b = (b << 1) & 0xff
        bits -= 1
        if bits == 0:
            if idx >= ilen:
                break
            b, bits = comp[idx], 8
            idx += 1
        ntok += 1
        if op:
            if idx + 1 >= ilen:
                break
            off = ((comp[idx] >> 4) | (comp[idx + 1] << 4)) + 1
            cnt = (comp[idx] & 0x0F) + 3
            idx += 2
            mo = max(mo, off)
            ml = max(ml, cnt)
            if off > out_len:
                zf += 1
            out_len += cnt
        else:
            nlit += 1
            out_len += 1
            idx += 1
    return mo, ml, zf, ntok, nlit


def load_payload(path):
    d = open(path, 'rb').read()
    out_size, comp_size = struct.unpack_from('<II', d, 0x14)
    avail = len(d) - 0x20
    if comp_size == 0 or comp_size > avail:
        comp_size = avail
    return d[0x20:0x20 + comp_size], out_size


if __name__ == '__main__':
    files = [scene_atlas('Menu'), scene_atlas('Common'),
             os.path.join(FONT_DIR, 'font_hs_test_arial.txb'),
             os.path.join(ROOT, 'RenderSettingBin01.rsb')]
    print('%-26s %-30s %-30s' % ('', '원본', '내 압축기'))
    print('%-26s %8s %5s %6s %6s  %8s %5s %6s %6s'
          % ('file', 'maxOff', 'mLen', 'zeroF', 'lit%', 'maxOff', 'mLen', 'zeroF', 'lit%'))
    for p in files:
        comp, osz = load_payload(p)
        a = walk(comp, osz)
        dec = decompress(open(p, 'rb').read())
        mine = lzss_encode(dec)
        b = walk(mine, len(dec))
        print('%-26s %8d %5d %6d %5.0f%%  %8d %5d %6d %5.0f%%'
              % (os.path.basename(p), a[0], a[1], a[2], 100.0 * a[4] / a[3],
                 b[0], b[1], b[2], 100.0 * b[4] / b[3]))
        print('    크기: 원본 %d  내것 %d  (%.1f%%)' % (len(comp), len(mine),
                                                     100.0 * len(mine) / len(comp)))
