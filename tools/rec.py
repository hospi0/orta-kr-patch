"""문자열 앞뒤 레코드 헤더를 뜯어본다 — 길이/문자수 필드가 있는지."""
import os
import struct
from project import WORK
from budget_menu import entries, source

d = open(source(), 'rb').read()
_, es = entries()


def show(i, back=0x40):
    e = es[i]
    off = e['off']
    s = max(0, off - back)
    print('--- idx %d  문자열 @%05x  %dB  %r' % (i, off, e['bytes'], e['jp']))
    for r in range(s, off, 16):
        row = d[r:r + 16]
        print('  %05x %s  %s' % (r, ' '.join('%02x' % b for b in row),
                                 ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)))
    print('  %05x <- 문자열 시작' % off)
    # 헤더 dword 들 중 길이(바이트) 또는 글자수와 같은 값이 있는가
    nb, nc = e['bytes'], len(e['jp'])
    for k in range(s, off, 4):
        v = struct.unpack_from('<I', d, k)[0]
        tag = []
        if v == nb:
            tag.append('=바이트수')
        if v == nc:
            tag.append('=글자수')
        if v == nb + 1:
            tag.append('=바이트+1')
        if tag:
            print('    @%05x %08x  %s' % (k, v, ' '.join(tag)))


if __name__ == '__main__':
    for i in (2, 3, 4, 5):
        show(i)
        print()
    # 헤더 안 포인터로 보이는 값들의 «차이»가 문자열 간격과 맞는지
    print('=== 문자열 오프셋 간격 vs 헤더 포인터 간격')
    for i in range(1, 8):
        print('  idx %d off %05x  간격 %d' % (i, es[i]['off'], es[i]['off'] - es[i - 1]['off']))
