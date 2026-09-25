"""빌드한 ISO 안에 «내 수정본»이 실제로 들어갔는지 바이트로 검산한다.

원본 파일의 고유 바이트열과, 수정본의 고유 바이트열을 각각 ISO 에서 찾는다.
  원본만 나옴 -> ISO 에 반영 안 됨 (빌드/경로 문제)
  수정본만 나옴 -> 반영됨
"""
import os
import sys
from project import ROOT, WORK

ISO = r"F:\hospi\roms\xbox roms\Panzer Dragoon Orta (KR test).xiso"
NEEDLE_AT = 0x1000
NEEDLE_LEN = 64


def needle(path, off=NEEDLE_AT, n=NEEDLE_LEN):
    d = open(path, 'rb').read()
    return d[off:off + n]


def find_in_iso(iso, needles, chunk=64 * 1024 * 1024):
    found = {k: False for k in needles}
    maxlen = max(len(v) for v in needles.values())
    prev = b''
    with open(iso, 'rb') as f:
        while True:
            buf = f.read(chunk)
            if not buf:
                break
            hay = prev + buf
            for k, v in needles.items():
                if not found[k] and v in hay:
                    found[k] = True
            if all(found.values()):
                break
            prev = hay[-maxlen:]
    return found


if __name__ == '__main__':
    rels = sys.argv[1:] or [
        os.path.join('sprite', 'pdtex_gamefont.txb'),
        os.path.join('sprite', 'Font', 'Zenkaku_Common.txb'),
        os.path.join('menudata', 'TextData', 'Text_MenuInst_JP.msg'),
    ]
    from pcmp import decompress, build as pcmp_build
    needles = {}
    for rel in rels:
        org = os.path.join(WORK, 'orig', rel)
        src = org if os.path.exists(org) else os.path.join(ROOT, rel)
        o = open(src, 'rb').read()
        needles['원본:' + rel] = o[NEEDLE_AT:NEEDLE_AT + NEEDLE_LEN]
        if o[:4] == b'PCMP':
            d = decompress(o)
            blank = pcmp_build(d[:0x20] + bytes(len(d) - 0x20))
            blank += b'\x00' * (len(o) - len(blank))
            needles['공백본:' + rel] = blank[NEEDLE_AT:NEEDLE_AT + NEEDLE_LEN]
    for k, v in needles.items():
        print('%-58s %s' % (k, v[:16].hex()))
    print('\nISO 훑는 중: %s (%.1f GB)' % (ISO, os.path.getsize(ISO) / 1024 ** 3))
    res = find_in_iso(ISO, needles)
    print()
    for k in sorted(res):
        print('  %-58s %s' % (k, '있음' if res[k] else '없음'))
