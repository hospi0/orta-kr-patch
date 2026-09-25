"""파괴 시험 — `Zenkaku_Common.txb` 의 **모든 칸을 지운다**.

`.msg` 는 원본 그대로 두고 폰트만 통째로 비운다.

판정 (TUTORIAL 등 일본어 설명문을 본다)
  글자가 사라지거나 깨짐 -> 이 파일을 **쓴다**. 그럼 내 «칸 덮어쓰기»에 버그가 있다.
  일본어가 멀쩡히 나옴   -> 이 파일을 **안 쓴다**. 진짜 폰트 출처를 다시 찾아야 한다.
"""
import os
import shutil
import struct
from project import ROOT, WORK, FONT_DIR
from pcmp import decompress, build as pcmp_build
from dxt import decode_alpha, encode_alpha
from cells import PAGE_W, PAGE_H, PAGE_BYTES

ORIG = os.path.join(WORK, 'orig')
REL = os.path.join('sprite', 'Font', 'Zenkaku_Common.txb')


def restore_all():
    for dp, dn, fns in os.walk(ORIG):
        for fn in fns:
            src = os.path.join(dp, fn)
            shutil.copy2(src, os.path.join(ROOT, os.path.relpath(src, ORIG)))


if __name__ == '__main__':
    restore_all()
    print('원본 전량 원복')
    d = decompress(open(os.path.join(ORIG, REL), 'rb').read())
    pages = struct.unpack_from('<I', d, 4)[0]
    start = 0x20 if pages == 1 else 0x50
    head, body = d[:start], d[start:]
    planes = []
    for i in range(pages):
        pl = decode_alpha(body[i * PAGE_BYTES:(i + 1) * PAGE_BYTES], PAGE_W, PAGE_H)
        ink = sum(1 for v in pl if v)
        print('  페이지 %d 잉크 픽셀 %d -> 0 으로 지움' % (i, ink))
        planes.append(bytes(PAGE_W * PAGE_H))          # 전부 0
    newbody = b''.join(encode_alpha(p, PAGE_W, PAGE_H) for p in planes)
    assert len(newbody) == len(body)
    packed = pcmp_build(head + newbody)
    o = open(os.path.join(ORIG, REL), 'rb').read()
    print('  압축 %d B (원본 %d B)' % (len(packed), len(o)))
    assert len(packed) <= len(o)
    with open(os.path.join(ROOT, REL), 'wb') as f:
        f.write(packed + b'\x00' * (len(o) - len(packed)))
    print('%s 를 «완전 공백»으로 기록. 나머지 전부 원본.' % REL)
