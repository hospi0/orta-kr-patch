"""빌드 결과 검산 — 되읽기로 원문 복원, 아틀라스 렌더."""
import os
import sys
import struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'trans'))
from Text_MenuInst_ko import KO                  # noqa: E402
from project import ROOT, WORK                   # noqa: E402
from pcmp import decompress                      # noqa: E402
from dxt import decode_alpha                     # noqa: E402
from atlas import write_png                      # noqa: E402
from cells import PAGE_W, PAGE_H, PAGE_BYTES     # noqa: E402
from budget_menu import entries                  # noqa: E402
from check_menu import prepare, is_hangul        # noqa: E402

rel_msg = os.path.join('menudata', 'TextData', 'Text_MenuInst_JP.msg')
rel_atl = os.path.join('sprite', 'Font', 'Zenkaku_Common.txb')

syl, st, short, smap = prepare(persist=False)
rev = {v[0]: k for k, v in st['map'].items()}     # 대체SJIS -> 음절

d = open(os.path.join(ROOT, rel_msg), 'rb').read()
_, es = entries()
bad = 0
shown = 0
for i, e in enumerate(es):
    t = KO.get(i)
    if not t:
        continue
    raw = d[e['off']:e['off'] + e['bytes']].rstrip(b'\x00')
    try:
        dec = raw.decode('cp932')
    except Exception:
        print('%3d 디코드 실패' % i)
        bad += 1
        continue
    back = ''.join(rev.get(c, c) for c in dec)
    if back != t:
        print('%3d ★불일치\n    기대 %r\n    실제 %r' % (i, t, back))
        bad += 1
    elif shown < 8:
        print('%3d OK  %s' % (i, back.replace('\n', ' / ')))
        shown += 1
print('\n되읽기 불일치 %d건 / 검사 %d건' % (bad, sum(1 for i in range(len(es)) if KO.get(i))))

# 아틀라스 렌더
a = decompress(open(os.path.join(ROOT, rel_atl), 'rb').read())
pages = struct.unpack_from('<I', a, 4)[0]
start = 0x20 if pages == 1 else 0x50
body = a[start:]
outdir = os.path.join(WORK, 'atlas')
# 새로 채운 칸은 4페이지 뒤쪽(빈 칸)과 앞쪽 한자 칸에 흩어져 있다
p0 = decode_alpha(body[0:PAGE_BYTES], PAGE_W, PAGE_H)
write_png(os.path.join(outdir, 'built_Common.png'), PAGE_W, 504, p0[:PAGE_W * 504])
print('아틀라스 PNG -> work/atlas/built_Common.png')
