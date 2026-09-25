"""파괴 시험 2 — `sprite/Font/` 의 **모든 아틀라스를 통째로 비운다**.

시험1 결과: `Zenkaku_Common.txb` 를 전부 비워도 일본어가 멀쩡히 나왔다.
  ⇒ 그 파일은 이 화면이 안 쓴다.
이번엔 `Zenkaku_*.txb` + `font_hs_test_arial.txb` 를 **전부** 비운다.

판정
  일본어가 사라짐 -> 폰트는 sprite/Font 안에 있다. 어느 파일인지 하나씩 좁힌다.
  멀쩡히 나옴     -> 폰트가 **sprite/Font 밖**에 있다. XBE 내장이거나 다른 디렉터리.
"""
import os
import shutil
import struct
from project import ROOT, WORK, FONT_DIR
from pcmp import decompress, build as pcmp_build
from dxt import encode_alpha
from cells import PAGE_W, PAGE_H, PAGE_BYTES

ORIG = os.path.join(WORK, 'orig')


def restore_all():
    for dp, dn, fns in os.walk(ORIG):
        for fn in fns:
            src = os.path.join(dp, fn)
            shutil.copy2(src, os.path.join(ROOT, os.path.relpath(src, ORIG)))


def backup(rel):
    dst = os.path.join(ORIG, rel)
    if not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, rel), dst)


def blank(rel):
    backup(rel)
    o = open(os.path.join(ORIG, rel), 'rb').read()
    d = decompress(o) if o[:4] == b'PCMP' else o
    pages = struct.unpack_from('<I', d, 4)[0]
    start = 0x20 if pages == 1 else 0x50
    head = d[:start]
    body = b''.join(encode_alpha(bytes(PAGE_W * PAGE_H), PAGE_W, PAGE_H)
                    for _ in range(pages))
    if len(head) + len(body) != len(d):
        print('  건너뜀(크기 불일치) %s' % rel)
        return False
    new = pcmp_build(head + body) if o[:4] == b'PCMP' else head + body
    if len(new) > len(o):
        print('  건너뜀(압축이 큼) %s' % rel)
        return False
    with open(os.path.join(ROOT, rel), 'wb') as f:
        f.write(new + b'\x00' * (len(o) - len(new)))
    print('  비움 %-40s %d p%d' % (os.path.basename(rel), len(o), pages))
    return True


if __name__ == '__main__':
    restore_all()
    print('원본 전량 원복')
    n = 0
    for fn in sorted(os.listdir(FONT_DIR)):
        if fn.lower().endswith('.txb'):
            rel = os.path.join('sprite', 'Font', fn)
            if blank(rel):
                n += 1
    print('\n%d개 아틀라스를 공백으로. .msg 는 전부 원본.' % n)
