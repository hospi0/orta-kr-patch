"""파괴 시험 3 — `sprite/`(Font 제외) + `menudata/` 의 **모든 .txb 픽셀을 0으로**.

포맷을 몰라도 되게 «헤더 0x20 뒤 전부 0» 으로 만든다. 크기는 원본과 동일.

지금까지 확정
  · `sprite/Font/` 28개를 비우면 **오프닝 자막이 깨진다** -> 그 파일들은 쓰인다.
  · 그런데 **메인 메뉴 설명문은 멀쩡하다** -> 메뉴는 다른 폰트를 쓴다.
  · 512폭 DXT3 28x28 격자는 디스크에 `sprite/Font` 26개뿐 (검출기 양성대조 통과).

판정
  메뉴 설명문이 깨짐 -> 폰트는 여기 있는 .txb 중 하나. 디렉터리 단위로 좁힌다.
  멀쩡함             -> .txb 가 아니다. .spr / XBE 내장으로 간다.
"""
import os
import shutil
from project import ROOT, WORK
from pcmp import decompress, build as pcmp_build

ORIG = os.path.join(WORK, 'orig')
SKIP = os.path.join('sprite', 'Font')


def restore_all():
    for dp, dn, fns in os.walk(ORIG):
        for fn in fns:
            src = os.path.join(dp, fn)
            shutil.copy2(src, os.path.join(ROOT, os.path.relpath(src, ORIG)))


def targets():
    for sub in ('sprite', 'menudata'):
        for dp, dn, fns in os.walk(os.path.join(ROOT, sub)):
            for fn in fns:
                if not fn.lower().endswith('.txb'):
                    continue
                rel = os.path.relpath(os.path.join(dp, fn), ROOT)
                if rel.startswith(SKIP):
                    continue
                yield rel


def blank(rel):
    src = os.path.join(ORIG, rel)
    if not os.path.exists(src):
        os.makedirs(os.path.dirname(src), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, rel), src)
    o = open(src, 'rb').read()
    if o[:4] == b'PCMP':
        d = decompress(o)
        new = pcmp_build(d[:0x20] + bytes(len(d) - 0x20))
        if len(new) > len(o):
            return False
        new += b'\x00' * (len(o) - len(new))
    elif o[:4] == b'TXRB':
        new = o[:0x20] + bytes(len(o) - 0x20)
    else:
        return False
    with open(os.path.join(ROOT, rel), 'wb') as f:
        f.write(new)
    return True


if __name__ == '__main__':
    restore_all()
    print('원본 전량 원복')
    n = skipped = 0
    for rel in targets():
        if blank(rel):
            n += 1
        else:
            skipped += 1
            print('  건너뜀 %s' % rel)
    print('\n%d개 텍스처를 «픽셀 전부 0» 으로 (건너뜀 %d). sprite/Font 와 .msg 는 원본.'
          % (n, skipped))
