"""★★`default.xbe` 의 «진짜» 일본어 문자열만 추린다.

거르는 조건 (기계어 오탐을 걷어낸다):
  · 앞뒤가 NUL 로 끊긴 «C 문자열» 일 것
  · 전각 2자 이상
  · 글자가 전부 «상용 구역» — 가나 · 흔한 기호 · JIS 1수준 한자(0x889F~0x9872)
    ⇒ 기계어가 우연히 만드는 «희귀 한자» 를 배제한다

    python xbescan2.py [--json]
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, TRANS, WORK

ORIG = os.path.join(WORK, 'orig')
BODY = re.compile(rb'[\x20-\x7e\x81-\x9f\xe0-\xef\xa1-\xdf]{3,200}')


def sane(t):
    n_wide = 0
    for c in t:
        o = ord(c)
        if o < 0x80:
            continue
        n_wide += 1
        b = c.encode('cp932')
        v = (b[0] << 8) | b[1] if len(b) == 2 else 0
        # 가나·기호(0x8140~0x8396) · JIS 1수준 한자(0x889F~0x9872)
        if not (0x8140 <= v <= 0x8396 or 0x889f <= v <= 0x9872):
            return False
    return n_wide >= 2


def main():
    p = os.path.join(ORIG, 'default.xbe')
    if not os.path.exists(p):
        p = os.path.join(ROOT, 'default.xbe')
    d = open(p, 'rb').read()
    out = []
    for m in BODY.finditer(d):
        s, e = m.start(), m.end()
        if s > 0 and d[s - 1] != 0:
            continue
        if e < len(d) and d[e] != 0:
            continue
        raw = m.group()
        try:
            t = raw.decode('cp932')
        except Exception:
            continue
        if not sane(t):
            continue
        out.append({'off': s, 'bytes': len(raw), 'jp': t})
    print('XBE %d B · 진짜로 보이는 일본어 문자열 %d개' % (len(d), len(out)))
    for e in out:
        print('  %8d %4dB  %s' % (e['off'], e['bytes'], e['jp']))
    if '--json' in sys.argv:
        dst = os.path.join(TRANS, 'xbe_corpus.json')
        with open(dst, 'w', encoding='utf-8', newline='') as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print('-> %s' % dst)


if __name__ == '__main__':
    main()
