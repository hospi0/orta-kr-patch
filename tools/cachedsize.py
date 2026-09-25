"""★★HDD 캐시에 올라간 파일은 «크기를 늘리면 안 된다» — 초과분을 잰다.

캐시는 같은 크기로만 제자리 덮어쓸 수 있다. 커지면 hddcache 가 건너뛰고,
그 구간은 «이전 빌드» 텍스트가 계속 나온다(2026-08-31 튜토리얼).

    python cachedsize.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, WORK

MAP = os.path.join(WORK, 'hdd', 'cache_map.json')
m = json.load(open(MAP, encoding='utf-8')) if os.path.exists(MAP) else {}
print('%-42s %9s %9s %s' % ('캐시된 파일', '원본', '현재', ''))
bad = 0
for rel in sorted(m):
    o = os.path.join(WORK, 'orig', rel)
    p = os.path.join(ROOT, rel)
    if not (os.path.exists(o) and os.path.exists(p)):
        continue
    so, sp = os.path.getsize(o), os.path.getsize(p)
    tag = ''
    if sp > so:
        tag = '  ★%+d B 초과 — 캐시 갱신 불가' % (sp - so)
        bad += 1
    print('%-42s %9d %9d%s' % (os.path.basename(rel), so, sp, tag))
print()
print('크기가 커진 파일 %d개' % bad)
