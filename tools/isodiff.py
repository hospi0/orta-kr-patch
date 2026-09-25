"""원본 ISO ↔ 패치 ISO 의 «다른 섹터 수»를 센다 — xdelta 크기가 왜 큰지 가른다.

작으면: 배치는 같고 내용만 다르다 -> xdelta 가 작아야 정상(-B 를 키우면 된다)
크면  : ISO 배치 자체가 달라졌다 -> 파일 크기를 원래대로 맞춰야 한다
"""
import os
import sys

A = r'F:\hospi\roms\xbox roms\Panzer Dragoon Orta (USA).xiso.iso'
B = r'F:\hospi\roms\xbox roms\Panzer Dragoon Orta (KR test).xiso'
SEC = 2048
CH = 1 << 24


def main():
    sa, sb = os.path.getsize(A), os.path.getsize(B)
    print('원본 %d B · 패치 %d B · 차이 %+d' % (sa, sb, sb - sa))
    diff = total = 0
    first = None
    with open(A, 'rb') as fa, open(B, 'rb') as fb:
        off = 0
        while True:
            a = fa.read(CH)
            b = fb.read(CH)
            if not a or not b:
                break
            n = min(len(a), len(b))
            for i in range(0, n, SEC):
                total += 1
                if a[i:i + SEC] != b[i:i + SEC]:
                    diff += 1
                    if first is None:
                        first = off + i
            off += n
            sys.stderr.write('\r  %d%%  다른 섹터 %d   ' % (off * 100 // sa, diff))
    sys.stderr.write('\r' + ' ' * 40 + '\r')
    print('섹터 %d개 중 다른 섹터 %d개 (%.2f%%)' % (total, diff, diff * 100.0 / total))
    print('처음 달라지는 위치: %s' % (first if first is not None else '없음'))
    print('다른 섹터 용량 = %.1f MB' % (diff * SEC / 2 ** 20))


if __name__ == '__main__':
    main()
