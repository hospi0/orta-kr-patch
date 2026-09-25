"""왕복 검증. ★인코더가 디코더보다 잘 깨진다 — 빌드 전에 항상 이걸 돌린다."""
import os
import sys
import struct
from pcmp import decompress, build, lzss_decode, lzss_encode
from ztbl import ZTbl
from project import ROOT, FONT_DIR, SCENES, COMMON_TBL, HANKAKU_TBL, scene_tbl, scene_atlas


def t_pcmp_roundtrip(paths):
    ok = bad = 0
    for p in paths:
        raw = open(p, 'rb').read()
        dec = decompress(raw)
        rebuilt = build(dec)
        again = decompress(rebuilt)
        if again == dec:
            ok += 1
        else:
            bad += 1
            print('  ✗ 왕복 불일치:', os.path.relpath(p, ROOT))
        print('    %-40s 원본 %7d -> 내 압축 %7d (%.1f%%)'
              % (os.path.basename(p), len(raw), len(rebuilt), 100.0 * len(rebuilt) / len(raw)))
    print('PCMP 왕복: 성공 %d / 실패 %d' % (ok, bad))
    return bad == 0


def t_ztbl_roundtrip():
    ok = bad = 0
    paths = [os.path.join(FONT_DIR, COMMON_TBL), os.path.join(FONT_DIR, HANKAKU_TBL)]
    paths += [scene_tbl(s) for s in SCENES]
    for p in paths:
        t = ZTbl(p)
        if t.to_bytes() == t.raw:
            ok += 1
        else:
            bad += 1
            print('  ✗', os.path.basename(p))
    print('z_tbl 무편집 재기록: 성공 %d / 실패 %d' % (ok, bad))
    return bad == 0


if __name__ == '__main__':
    sample = [os.path.join(FONT_DIR, 'font_hs_test_arial.txb'),
              os.path.join(FONT_DIR, 'Zenkaku_Common.txb'),
              scene_atlas('Stage1'),
              scene_atlas('Menu')]
    a = t_pcmp_roundtrip(sample)
    b = t_ztbl_roundtrip()
    sys.exit(0 if (a and b) else 1)
