"""원본 vs 패치본 바이트 대조 — 어디를 건드렸는지 정확히 본다."""
import os
from project import ROOT, WORK
from budget_menu import entries

REL = os.path.join('menudata', 'TextData', 'Text_MenuInst_JP.msg')
a = open(os.path.join(WORK, 'orig', REL), 'rb').read()
b = open(os.path.join(ROOT, REL), 'rb').read()
_, es = entries()

print('크기 %d / %d' % (len(a), len(b)))
diff = [i for i in range(len(a)) if a[i] != b[i]]
print('다른 바이트 %d개, 구간 %05x~%05x' % (len(diff), diff[0], diff[-1]))


def dump(tag, d, s, n):
    print('  %s' % tag)
    for r in range(s, s + n, 16):
        row = d[r:r + 16]
        print('    %05x %s' % (r, ' '.join('%02x' % x for x in row)))


for i in (2, 4):
    e = es[i]
    print('\n=== idx %d  @%05x  원문 %dB  pad %d  %r'
          % (i, e['off'], e['bytes'], e['pad'], e['jp']))
    s = e['off'] - 16
    n = e['bytes'] + 48
    dump('원본', a, s, n)
    dump('패치', b, s, n)
    # 종단자 확인
    end = e['off'] + e['bytes']
    print('    원본 종단 위치 %05x = %02x   패치 %05x = %02x'
          % (end, a[end], end, b[end]))
    za = a.find(b'\x00', e['off'])
    zb = b.find(b'\x00', e['off'])
    print('    첫 널: 원본 %05x (길이 %d)   패치 %05x (길이 %d)'
          % (za, za - e['off'], zb, zb - e['off']))
