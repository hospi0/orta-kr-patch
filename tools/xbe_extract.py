"""★★`default.xbe` 에 하드코딩된 «시스템 문자열»을 추출한다.

2026-08-31 발견 — 일시정지 메뉴·시스템 대화상자·도감 라벨이 `.msg` 가 아니라
**실행 파일 안**에 있었다. `.msg` 만 훑던 코퍼스에는 한 번도 안 잡혔고,
우리가 공용 폰트 칸을 한글로 덮으면서 그 화면들이 깨졌다.

거르는 법(기계어 오탐 배제):
  · 앞뒤가 NUL 로 끊긴 C 문자열
  · **가나가 하나 이상** — 실제 UI 문구는 거의 다 가나를 쓴다. 기계어 오탐은 안 쓴다
  · 글자가 전부 가나·기호·JIS 1수준 한자 구역

    python xbe_extract.py [--json]   -> trans/xbe_corpus.json
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, TRANS, WORK

ORIG = os.path.join(WORK, 'orig')
XBE = 'default.xbe'
# 본문에 쓰이는 바이트: 반각 인쇄가능 · 개행 · 전각 리드/트레일
# ⛔트레일 바이트는 0x80 과 0xF0~0xFC 도 온다(「ム」= 0x83 **0x80**).
#   바이트 클래스에서 빼먹으면 문자열이 한복판에서 잘린다.
BODY = re.compile(rb'[\x0a\x20-\x7e\x80-\xfc]{4,400}')


def kana_ok(t):
    kana = 0
    for c in t:
        o = ord(c)
        if o < 0x80:
            continue
        b = c.encode('cp932')
        if len(b) != 2:
            return False, 0
        v = (b[0] << 8) | b[1]
        if 0x829f <= v <= 0x82f1 or 0x8340 <= v <= 0x8396:
            kana += 1
        elif not (0x8140 <= v <= 0x8396 or 0x889f <= v <= 0x9872):
            return False, 0
    return True, kana


def xbe_path():
    o = os.path.join(ORIG, XBE)
    return o if os.path.exists(o) else os.path.join(ROOT, XBE)


# ★문자열 표가 모여 있는 구역 — 여기 밖은 전부 기계어 오탐이다.
#   3,229,000 ~ 3,241,000 (도감 라벨 · 일시정지 메뉴 · 시스템 대화상자)
REGION = (3229000, 3241200)


def extract():
    d = open(xbe_path(), 'rb').read()
    out = []
    for m in BODY.finditer(d, *REGION):
        s, e = m.start(), m.end()
        if e < len(d) and d[e] != 0:
            continue
        raw = m.group()
        try:
            t = raw.decode('cp932')
        except Exception:
            continue
        ok, kana = kana_ok(t)
        # ★가나가 없는 라벨도 진짜다(「危険度：」「振動」). 구역을 좁혔으니 전각 2자면 받는다.
        if not ok or sum(1 for c in t if ord(c) > 0x7f) < 2:
            continue
        out.append({'off': s, 'bytes': len(raw), 'jp': t})
    return out


def main():
    out = extract()
    print('XBE 하드코딩 문자열 %d개' % len(out))
    for e in out:
        print('  %8d %4dB  %s' % (e['off'], e['bytes'], e['jp'].replace('\n', '/')))
    if '--json' in sys.argv:
        dst = os.path.join(TRANS, 'xbe_corpus.json')
        with open(dst, 'w', encoding='utf-8', newline='') as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print('-> %s' % dst)


if __name__ == '__main__':
    main()
