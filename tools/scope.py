"""번역 범위를 넓혀가며 «누적 고유 음절 수»를 본다. 슬롯 상한에 맞춰 범위를 정한다."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'trans'))
from Text_MenuInst_ko import KO          # noqa: E402
from alloc import kana_pool              # noqa: E402


def is_hangul(c):
    return 0xac00 <= ord(c) <= 0xd7a3


cap = len(kana_pool())
seen = set()
print('가나 슬롯 %d' % cap)
for i in sorted(KO):
    t = KO[i]
    if not t:
        continue
    new = {c for c in t if is_hangul(c)} - seen
    seen |= new
    mark = ' <<< 여기서 초과' if len(seen) > cap and len(seen) - len(new) <= cap else ''
    print('%3d 누적 %3d (+%2d)%s' % (i, len(seen), len(new), mark))
print('\n전체 %d' % len(seen))
