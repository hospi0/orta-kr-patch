"""미조사 `.txb` 297개(=sprite/ menudata/ 밖)를 한 번에 비운다.

세션1이 비운 건 sprite+menudata 230개뿐이다. 전체는 527개.
메뉴 설명문의 폰트가 이 297개 안에 있으면 이 빌드에서 글자가 깨진다.
없으면 «디스크의 어떤 .txb 도 아니다»가 확정돼 탐색 범위가 통째로 바뀐다.

★되돌리기: work/orig 에 원본을 먼저 복사한 뒤에만 쓴다.
"""
import os
import shutil
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, WORK
from pcmp import decompress

try:
    from lzopt import build as lz_build
except ImportError:
    from pcmp import build as lz_build


def backup(p):
    rel = os.path.relpath(p, ROOT)
    dst = os.path.join(WORK, 'orig', rel)
    if not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(p, dst)
    return dst


def blank(p):
    """TXRB 본문을 0 으로. 크기는 원본과 동일하게 유지."""
    src = backup(p)
    raw = open(src, 'rb').read()
    packed = raw[:4] == b'PCMP'
    d = decompress(raw) if packed else raw
    if d[:4] != b'TXRB':
        return None
    pages = struct.unpack_from('<I', d, 4)[0]
    start = 0x20 if pages == 1 else 0x20 + pages * 0x0C
    if not (0 < pages <= 256) or start >= len(d):
        return None
    new = d[:start] + bytes(len(d) - start)
    out = lz_build(new) if packed else new
    if len(out) > len(raw):
        return 'skip(재압축 큼 %+d)' % (len(out) - len(raw))
    out = out + bytes(len(raw) - len(out))
    with open(p, 'wb') as f:
        f.write(out)
    return 'ok'


def main():
    targets = []
    for dp, dn, fn in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT).replace('\\', '/').lower()
        if rel.startswith('sprite') or rel.startswith('menudata'):
            continue
        for f in fn:
            if f.lower().endswith('.txb'):
                targets.append(os.path.join(dp, f))
    print('대상 .txb %d개 (sprite/ menudata/ 제외)' % len(targets))
    ok = skip = bad = 0
    for p in sorted(targets):
        r = blank(p)
        if r == 'ok':
            ok += 1
        elif r is None:
            bad += 1
        else:
            skip += 1
            print('  %s %s' % (os.path.relpath(p, ROOT), r))
    print('비움 %d / TXRB아님 %d / 건너뜀 %d' % (ok, bad, skip))


if __name__ == '__main__':
    main()
