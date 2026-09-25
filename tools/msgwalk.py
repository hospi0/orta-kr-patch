"""★★`.msg` 를 «게임이 걷는 방식» 그대로 걸어서 구조가 온전한지 검증한다.

2026-08-31 해독 — `NO DATA ID=3100` 화면이 준 단서로 진짜 구조를 알아냈다.

## 진짜 포맷

파일은 «항목»이 죽 이어진 것이다. 항목은 두 가지 머리를 가진다.

    [ID 머리 36B]  u32 ID · u32 1 · u32 10 · u32 ptr · u32 0 · u32 ptr
    [문자열 머리 24B] u32 M · u32 A · u32 0 · u32 P1 · u32 P2 · u32 0
    <SJIS 텍스트> NUL

  · **ID 머리**는 «새 항목의 시작»에만 붙는다. 지문 = 두 번째·세 번째 u32 가 1·10.
    ID 머리가 붙은 항목은 머리 전체가 60B 이고, 실제로 ID머리+0x20 에 **60** 이 적혀 있다
    (= 항목 시작에서 텍스트까지의 거리).
  · 같은 ID 안의 «두 번째 문자열»부터는 24B 머리만 붙는다.
  · 다음 항목은 **텍스트의 NUL 다음 바이트를 4로 올림한 자리**에서 시작한다.

★★그래서 규칙은 «레코드 오프셋이 4의 배수»가 아니라 이것이다:

    다음 항목 시작 = align4(NUL 위치 + 1)

  ⇒ 번역문 뒤에 **NUL 을 찍고 그 뒤에 채움 바이트를 더 넣으면** 게임이 계산한
    다음 항목 자리가 실제 자리보다 앞이 되어 **그 뒤 전부가 어긋난다.**
    화면에는 `NO DATA ID=####` 로 나온다(ID 를 못 찾은 것).
  ⇒ 채움은 «NUL 앞»에, 즉 텍스트의 일부로 넣어야 한다.

사용:
    python msgwalk.py                 # 원본·현재 트리 전부 걸어서 대조
    python msgwalk.py <파일>          # 한 파일만, 항목을 나열
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, WORK

ORIG = os.path.join(WORK, 'orig')


def is_id_head(d, p):
    if p + 36 > len(d):
        return False
    if p + 60 > len(d):
        return False
    a, b, c = struct.unpack_from('<3I', d, p)
    # ⛔세 번째 u32 를 10 으로 고정하면 안 된다 — 10·20·30 이 다 나온다
    #   (MesData_Stage01 0x4B4 가 20, 0x50C 가 30). 판정식 비교는 tools/try_sig.py.
    return b == 1 and 0 < c <= 100 and c % 10 == 0 and 0 < a < 0x7FFFFFFF


def walk(d):
    """[(항목시작, ID or None, 텍스트오프셋, 텍스트바이트)] · 끝까지 못 가면 예외."""
    out = []
    p = 0
    n = len(d)
    while p + 24 <= n:
        # 꼬리 여백이면 끝
        if d[p:p + 24] == bytes(24):
            break
        start = p
        ident = None
        if is_id_head(d, p):
            ident = struct.unpack_from('<I', d, p)[0]
            p += 36
        p += 24
        e = d.find(b'\x00', p)
        if e < 0:
            raise ValueError('0x%X: 종단 NUL 없음' % p)
        out.append((start, ident, p, e - p))
        p = (e + 1 + 3) & ~3
    return out


def report(path, label):
    d = open(path, 'rb').read()
    try:
        w = walk(d)
    except ValueError as ex:
        return None, '★%s' % ex
    ids = [i for _, i, _, _ in w if i is not None]
    return w, '%s 항목 %d개 · ID %d개 (%s..%s)' % (
        label, len(w), len(ids),
        min(ids) if ids else '-', max(ids) if ids else '-')


def main():
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        p = sys.argv[1]
        d = open(p, 'rb').read()
        w = walk(d)
        for start, ident, off, ln in w:
            t = d[off:off + ln].decode('cp932', 'replace').replace('\n', '/')
            print('%08X  %-8s %6d  %s' % (start, ident if ident is not None else '',
                                          ln, t[:60]))
        print('항목 %d개' % len(w))
        return 0

    bad = 0
    for dp, dn, fn in os.walk(ORIG):
        for f in sorted(fn):
            if not f.endswith('.msg'):
                continue
            rel = os.path.relpath(os.path.join(dp, f), ORIG)
            wo, so = report(os.path.join(ORIG, rel), '원본')
            wn, sn = report(os.path.join(ROOT, rel), '현재')
            mark = ''
            if wo and wn:
                io = [i for _, i, _, _ in wo if i is not None]
                inn = [i for _, i, _, _ in wn if i is not None]
                if io != inn:
                    mark = '  ★★ID 목록 불일치'
                    bad += 1
                elif len(wo) != len(wn):
                    mark = '  ★항목 수 다름'
                    bad += 1
            else:
                mark = '  ★★걷기 실패'
                bad += 1
            print('%-42s %-40s %-40s%s' % (f, so, sn, mark))
    print()
    print('문제 파일 %d개' % bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
