"""ID 머리 판정식 후보를 비교 — 원본에서 «몇 개를 찾고 얼마나 덜 흔들리는가»."""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import WORK
import msgwalk

ORIG = os.path.join(WORK, 'orig')

CANDS = {
    'c==10': lambda d, p: struct.unpack_from('<I', d, p + 4)[0] == 1
             and struct.unpack_from('<I', d, p + 8)[0] == 10,
    'dist==60': lambda d, p: struct.unpack_from('<I', d, p + 4)[0] == 1
                and struct.unpack_from('<I', d, p + 0x20)[0] == 60,
    'c%10, dist': lambda d, p: struct.unpack_from('<I', d, p + 4)[0] == 1
                  and 0 < struct.unpack_from('<I', d, p + 8)[0] <= 100
                  and struct.unpack_from('<I', d, p + 8)[0] % 10 == 0
                  and struct.unpack_from('<I', d, p + 0x20)[0] == 60,
    'c%10만': lambda d, p: struct.unpack_from('<I', d, p + 4)[0] == 1
              and 0 < struct.unpack_from('<I', d, p + 8)[0] <= 100
              and struct.unpack_from('<I', d, p + 8)[0] % 10 == 0,
}

files = []
for dp, dn, fn in os.walk(ORIG):
    for f in sorted(fn):
        if f.endswith('.msg'):
            files.append(os.path.join(dp, f))

orig_is = msgwalk.is_id_head
for name, fn in CANDS.items():
    def mk(fn):
        def g(d, p):
            if p + 60 > len(d):
                return False
            return fn(d, p)
        return g
    msgwalk.is_id_head = mk(fn)
    ids = items = junk = 0
    for p in files:
        d = open(p, 'rb').read()
        try:
            w = msgwalk.walk(d)
        except ValueError:
            junk += 999
            continue
        items += len(w)
        ids += sum(1 for _, i, _, _ in w if i is not None)
        # «쓰레기 항목» = 길이 0~4 이면서 ID 가 없는 것 → 걷기가 흔들린 지문
        junk += sum(1 for _, i, _, ln in w if i is None and ln <= 4)
    print('%-12s 항목 %5d · ID %4d · 쓰레기 %4d' % (name, items, ids, junk))
msgwalk.is_id_head = orig_is
