"""★xemu HDD 이미지에 폰트 파일 사본이 «몇 개» 있는지 전수로 센다.

hddcache.py 는 첫 히트만 지도에 남긴다. 사본이 둘 이상이면 게임이 «우리가 안 고친 쪽»을
읽을 수 있다. 2026-08-31 hddcache 가 「제3의 내용」이라고 알린 파일이 바로 그 후보다.

원본(work/orig) 과 현재(트리) 두 판본의 앞부분을 각각 needle 로 훑는다.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, WORK

HDD = r'D:\hospi\XEMU\XEMU FILES\Pre-built Xbox HDD image\xbox_hdd.qcow2'
ORIG = os.path.join(WORK, 'orig')
N = 64

names = sys.argv[1:] or ['Zenkaku_Menu.txb', 'Reisyo_Menu_z_tbl.bin',
                         'Zenkaku_Stage1.txb', 'Reisyo_Stage1_z_tbl.bin',
                         'Zenkaku_Tutorial.txb', 'Reisyo_Tutorial_z_tbl.bin',
                         'Zenkaku_Common.txb', 'Reisyo_Cmn_z_tbl_cmn.bin']

needles = {}
for nm in names:
    cur = os.path.join(FONT_DIR, nm)
    old = os.path.join(ORIG, os.path.relpath(cur, ROOT))
    if os.path.exists(cur):
        needles[nm + ' [현재]'] = open(cur, 'rb').read()[:N]
    if os.path.exists(old):
        needles[nm + ' [원본]'] = open(old, 'rb').read()[:N]

hits = {k: [] for k in needles}
CH = 1 << 25
with open(HDD, 'rb') as f:
    base, tail = 0, b''
    while True:
        b = f.read(CH)
        if not b:
            break
        buf = tail + b
        for k, nd in needles.items():
            i = buf.find(nd)
            while i >= 0:
                hits[k].append(base - len(tail) + i)
                i = buf.find(nd, i + 1)
        base += len(b)
        tail = buf[-N:]

for k in sorted(hits):
    print('%-40s %d곳  %s' % (k, len(hits[k]), hits[k][:8]))
