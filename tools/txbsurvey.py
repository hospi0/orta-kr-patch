"""미조사 `.txb` 전수 조사 — 「가나를 담은 아틀라스」를 찾는다.

세션2 로 표적이 좁혀졌다: 찾는 폰트는 **히라가나·가타카나·장음부호**를 담고,
메뉴 설명문의 92 미수록자(一 左 右 表 示)까지 갖고 있다.
`sprite/Font` 는 아니다(Common 을 알파+컬러 다 바꿔도 화면이 안 변했다).

세션1 이 비운 건 `sprite`+`menudata` 230개뿐이고 디스크 전체 `.txb` 는 **527개**다.
여기서는 나머지 **297개**를 본다.

★검출기는 **컬러 채널도** 본다 — 알파만 보면 컬러에만 글자가 있는 폰트를 놓친다
  ([[feedback_dxt_color_channel_also_has_glyph]]).
"""
import os
import struct
import sys
from pcmp import decompress
from project import ROOT


def txb_files(scope='rest'):
    """scope: 'rest' = sprite/menudata 밖, 'all' = 전부."""
    out = []
    for dp, dn, fns in os.walk(ROOT):
        rel_dir = os.path.relpath(dp, ROOT)
        for fn in sorted(fns):
            if not fn.lower().endswith('.txb'):
                continue
            rel = os.path.normpath(os.path.join(rel_dir, fn))
            top = rel.split(os.sep)[0]
            if scope == 'rest' and top in ('sprite', 'menudata'):
                continue
            out.append(rel)
    return sorted(out)


def probe(rel):
    """(rel, 원본크기, 압축여부, magic, pages, 해제크기, 페이지당바이트) 또는 None."""
    p = os.path.join(ROOT, rel)
    raw = open(p, 'rb').read()
    packed = raw[:4] == b'PCMP'
    d = raw
    if packed:
        try:
            d = decompress(raw)
        except Exception as e:
            return dict(rel=rel, size=len(raw), packed=True, magic='PCMP?', err=str(e)[:40])
    magic = d[:4].decode('ascii', 'replace')
    pages = struct.unpack_from('<I', d, 4)[0] if len(d) >= 8 else 0
    start = 0x20 if pages == 1 else 0x50
    body = len(d) - start
    per = body // pages if 0 < pages <= 64 else 0
    return dict(rel=rel, size=len(raw), packed=packed, magic=magic,
                pages=pages, unpacked=len(d), per=per, err=None)


if __name__ == '__main__':
    scope = sys.argv[1] if len(sys.argv) > 1 else 'rest'
    rows = [probe(r) for r in txb_files(scope)]
    ok = [r for r in rows if not r.get('err')]
    bad = [r for r in rows if r.get('err')]
    print('%s 대상 %d개 (해제 실패 %d)' % (scope, len(rows), len(bad)))
    for r in bad[:5]:
        print('   ⚠', r['rel'], r['err'])

    import collections
    print('\n-- magic 분포 --')
    for m, c in collections.Counter(r['magic'] for r in ok).most_common():
        print('   %-8s %d' % (m, c))
    print('\n-- pages 분포 --')
    for m, c in collections.Counter(r['pages'] for r in ok).most_common(10):
        print('   pages=%-4s %d' % (m, c))
    print('\n-- 페이지당 바이트 분포(상위) --')
    for m, c in collections.Counter(r['per'] for r in ok).most_common(12):
        side = ''
        for w in (64, 128, 256, 512, 1024, 2048):
            if m == w * w:
                side = '  = %d x %d (1B/px)' % (w, w)
            if m == w * w // 2:
                side = '  = %d x %d (DXT1/4bpp)' % (w, w)
        print('   %-10s %4d%s' % (m, c, side))

    # 폰트다운 후보 = 512x512 DXT3(=262144 B/page) 인 것
    cand = [r for r in ok if r['per'] == 262144]
    print('\n-- 512x512 DXT3 페이지를 가진 파일 %d개 --' % len(cand))
    for r in cand[:40]:
        print('   %-52s pages=%d %8d B %s' % (r['rel'], r['pages'], r['size'],
                                              'PCMP' if r['packed'] else ''))
