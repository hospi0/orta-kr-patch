"""★★`default.xbe` 안에 «하드코딩된» 일본어 문자열을 훑는다.

2026-08-31 발견: 일시정지 메뉴(続ける / リトライ / ゲーム終了)가 `.msg` 가 아니라
**실행 파일 안**에 있었다. 우리가 그 글자들의 폰트 칸을 한글로 덮어써서
그 화면이 깨졌다(원문은 그대로인데 글리프만 바뀐 것).

    python xbestrings.py            # 목록
    python xbestrings.py --json     # trans/xbe_corpus.json 으로 저장
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, TRANS, WORK, pristine

ORIG = os.path.join(WORK, 'orig')
# 전각 SJIS 2바이트: 리드 0x81~0x9F / 0xE0~0xEF, 트레일 0x40~0xFC (0x7F 제외)
PAIR = rb'(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc])'
RUN = re.compile((rb'(?:' + PAIR + rb'|[\x20-\x7e])*' + PAIR +
                  rb'(?:' + PAIR + rb'|[\x20-\x7e])*'))


def main():
    p = os.path.join(ROOT, 'default.xbe')
    o = os.path.join(ORIG, 'default.xbe')
    d = open(o if os.path.exists(o) else p, 'rb').read()
    out = []
    for m in RUN.finditer(d):
        raw = m.group()
        if len(raw) < 4:
            continue
        try:
            t = raw.decode('cp932')
        except Exception:
            continue
        # 전각이 2자 이상인 것만 (오탐 제거)
        n_wide = sum(1 for c in t if ord(c) > 0x7f)
        if n_wide < 2:
            continue
        out.append({'off': m.start(), 'bytes': len(raw), 'jp': t})
    print('XBE %d B · 전각 문자열 후보 %d개' % (len(d), len(out)))
    for e in out[:80]:
        print('  %8d %4dB  %s' % (e['off'], e['bytes'], e['jp'][:50]))
    if len(out) > 80:
        print('  ... 외 %d개' % (len(out) - 80))
    if '--json' in sys.argv:
        dst = os.path.join(TRANS, 'xbe_corpus.json')
        with open(dst, 'w', encoding='utf-8', newline='') as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print('-> %s' % dst)


if __name__ == '__main__':
    main()
