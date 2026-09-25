"""★HDD 이미지 안에 «같은 파일의 사본이 몇 개» 있는지 세고, 각각의 내용을 판정한다.

2026-08-31: `MesData_Stage01_JP.msg` 가 **4곳**에서 needle 로 잡혔다.
hddcache.py 는 첫 곳만 고친다 — 게임이 다른 사본을 읽으면 번역이 반영 안 된다.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, WORK, pristine

HDD = r'D:\hospi\XEMU\XEMU FILES\Pre-built Xbox HDD image\xbox_hdd.qcow2'
ORIG = os.path.join(WORK, 'orig')
N = 48


def find_all(hdd, needle):
    out = []
    CH = 1 << 25
    with open(hdd, 'rb') as f:
        base, tail = 0, b''
        while True:
            b = f.read(CH)
            if not b:
                break
            buf = tail + b
            i = buf.find(needle)
            while i >= 0:
                out.append(base - len(tail) + i)
                i = buf.find(needle, i + 1)
            base += len(b)
            tail = buf[-N:]
    return out


def main():
    rels = sys.argv[1:] or [r'messageevent\MesData_Stage01_JP.msg',
                            r'messageevent\MesData_Tutorial_JP.msg']
    with open(HDD, 'rb') as f:
        for rel in rels:
            cur = open(os.path.join(ROOT, rel), 'rb').read()
            ori = open(os.path.join(ORIG, rel), 'rb').read()
            hits = sorted(set(find_all(HDD, ori[:N]) + find_all(HDD, cur[:N])))
            print('=== %s (%d B) — 후보 %d곳' % (os.path.basename(rel), len(cur), len(hits)))
            for off in hits:
                f.seek(off)
                blk = f.read(len(cur))
                tag = ('원본' if blk == ori else
                       '트리와 동일' if blk == cur else '★제3의 내용/부분일치')
                print('   @%-12d %s' % (off, tag))


if __name__ == '__main__':
    main()
