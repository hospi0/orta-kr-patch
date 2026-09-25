"""`.msg` 레코드 파서 — 휴리스틱 스캔을 대체한다.

★2026-08-30 실측으로 확정한 문법
    각 문자열 앞에 **24바이트 레코드**가 붙는다.
        u32 0xFFFFFFFF   marker
        u32 A            매개변수(값이 제각각 — 용도 미상)
        u32 0
        u32 P1           포인터로 보임(개발 빌드의 절대주소)
        u32 P2           포인터로 보임
        u32 0
        <SJIS 텍스트> NUL

⛔기존 `msgfile.scan()` 은 문자열 «모양»으로 찾는 휴리스틱이라 항목을 놓쳤다.
  Text_OpeningDemo_JP 는 실제 17개인데 6개만 잡혔다.
  → [[feedback_scan_coverage_and_detectors]] 와 같은 함정이다.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MARK = b'\xff\xff\xff\xff'
HDR = 24


def _lead(b):
    return 0x81 <= b <= 0x9f or 0xe0 <= b <= 0xef


def _trail(b):
    return 0x40 <= b <= 0xfc and b != 0x7f


def _strlen(d, s):
    """s 부터 NUL 까지가 «온전한 텍스트»면 길이, 아니면 None."""
    n = len(d)
    j = s
    while j < n:
        c = d[j]
        if c == 0:
            break
        if 0x20 <= c < 0x7f or c == 0x0a:
            j += 1
        elif _lead(c) and j + 1 < n and _trail(d[j + 1]):
            j += 2
        else:
            return None
    if j >= n or d[j] != 0:
        return None
    return j - s


def records(d, minlen=2):
    """[{off, bytes, pad, jp, M, A, P1, P2, rec}] — 파일 순서대로.

    ★마커 값으로 찾지 않는다. 파일마다 다르다(OpeningDemo 0xFFFFFFFF / Tutorial 1).
      «문자열»을 먼저 찾고, 그 앞 24바이트가 레코드 모양인지로 검증한다.
    """
    out = []
    n = len(d)
    i = 0
    while i < n:
        s = j = i
        while j < n:
            c = d[j]
            if 0x20 <= c < 0x7f or c == 0x0a:
                j += 1
            elif _lead(c) and j + 1 < n and _trail(d[j + 1]):
                j += 2
            else:
                break
        L = j - s
        if L >= minlen and j < n and d[j] == 0 and s >= HDR:
            M, A, z1, P1, P2, z2 = struct.unpack_from('<6I', d, s - HDR)
            if z1 == 0 and z2 == 0:
                try:
                    t = d[s:j].decode('cp932')
                except Exception:
                    t = None
                if t:
                    pad = 0
                    while j + pad < n and d[j + pad] == 0:
                        pad += 1
                    out.append({'rec': s - HDR, 'off': s, 'bytes': L, 'pad': pad,
                                'M': M, 'A': A, 'P1': P1, 'P2': P2, 'jp': t})
                    i = j + 1
                    continue
        i = s + 1 if L == 0 else j + 1 if (j < n and d[j] == 0) else s + 1
    return out


def parse_file(path):
    with open(path, 'rb') as f:
        return records(f.read())


if __name__ == '__main__':
    from project import ROOT, pristine
    from msgfile import scan
    tot_new = tot_old = 0
    print('%-46s %7s %7s %8s' % ('파일', '레코드', '기존', '글자'))
    for dp, dn, fn in os.walk(ROOT):
        for f in sorted(fn):
            if not (f.lower().endswith('.msg') and '_JP' in f):
                continue
            p = os.path.join(dp, f)
            d = open(pristine(p), 'rb').read()
            rs = records(d)
            old = len(scan(d))
            tot_new += len(rs)
            tot_old += old
            print('%-46s %7d %7d %8d'
                  % (f, len(rs), old, sum(len(r['jp']) for r in rs)))
    print('합계  레코드 %d / 기존 %d  (+%d)' % (tot_new, tot_old, tot_new - tot_old))
