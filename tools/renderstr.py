"""문자열을 «표 + 아틀라스»로 조판해 PNG 로 뽑는다 — 화면과 대조하는 양성 대조용.

    python renderstr.py <장면> <원본|현재> <파일> <idx> <출력.png>
예)
    python renderstr.py Menu 원본 menudata\TextData\text_pdb_db_world_JP.msg 76 a.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from project import ROOT, FONT_DIR, WORK, COMMON_TBL, pristine
from ztbl import ZTbl
from atlaswrite import Atlas
from msgrec import records

ORIG = os.path.join(WORK, 'orig')


def tbl_path(scene):
    return os.path.join(FONT_DIR, COMMON_TBL if scene == 'Common'
                        else 'Reisyo_%s_z_tbl.bin' % scene)


def draw(text, scene, use_orig, out, cols=34):
    tp, ap = tbl_path(scene), os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % scene)
    if use_orig:
        tp = os.path.join(ORIG, os.path.relpath(tp, ROOT))
        ap = os.path.join(ORIG, os.path.relpath(ap, ROOT))
    m = ZTbl(tp).mapping(drop_sentinel=False)
    a = Atlas(ap)
    n = a.pages * 324
    lines = text.split('\n')
    W = cols * 28
    H = len(lines) * 28
    img = Image.new('L', (W, H), 0)
    miss = []
    for y, ln in enumerate(lines):
        x = 0
        for ch in ln:
            if ord(ch) < 0x80:
                x += 14
                continue
            g = m.get(ch)
            if g is None or g >= n:
                miss.append((ch, g))
                x += 28
                continue
            cell = Image.frombytes('L', (28, 28), bytes(a.cell_alpha(g)))
            img.paste(cell, (x, y * 28))
            x += 28
    img.save(out)
    print('%s  글자 %d · 표에 없거나 범위밖 %d개 %s'
          % (out, sum(len(l) for l in lines), len(miss), miss[:8]))


if __name__ == '__main__':
    scene, which, rel, idx, out = sys.argv[1:6]
    p = os.path.join(ORIG if which == '원본' else ROOT, rel)
    d = open(p, 'rb').read()
    t = records(d)[int(idx)]['jp']
    draw(t, scene, which == '원본', out)
