"""화면에 «보이는» 한글 음절 집합으로 그 화면이 쓰는 아틀라스를 가린다.

판도라 도감 <드래곤> 화면에서 읽어낸 음절들. 우리가 어느 장면에 칠한 것인지 본다.
한 장면이 이걸 «전부» 갖고 있으면 그 장면 아틀라스가 그 화면의 폰트다.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import WORK

seen = list('입갈벌잖춘석쪽린면알실맨탑이도')
cm = json.load(open(os.path.join(WORK, 'charmap_all.json'), encoding='utf-8'))

print('화면에서 읽은 음절 %d개: %s' % (len(seen), ''.join(seen)))
print()
print('%-16s %5s %6s  %s' % ('장면', '배정', '없는것', ''))
for sc in sorted(cm):
    d = cm[sc]
    miss = [s for s in seen if s not in d]
    mark = '  ★★전부 있음' if not miss else ''
    print('%-16s %5d %6d  %s%s' % (sc, len(d), len(miss), ''.join(miss), mark))

print()
print('«갈» 이 각 장면에서 차지한 칸:')
for sc in sorted(cm):
    if '갈' in cm[sc]:
        print('  %-16s 코드 %s · 칸 %d' % (sc, cm[sc]['갈'][0], cm[sc]['갈'][1]))
