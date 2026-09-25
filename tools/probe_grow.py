"""파일 «키우기» 시험 — `.msg` 를 2048B 늘려도 게임이 읽는가.

되면 예산이 파일마다 +2,048B 씩 늘어 도감 두 파일의 부족분이 한 번에 풀린다.

대상 = Text_MenuInst_JP.msg (14,336B, 본문 끝 14,154 -> 여백 182B)
  · 메인 메뉴라 부팅 직후 확인된다
  · 본문이 거의 꽉 차 있어 조금만 늘려도 **원래 파일 경계를 넘는다** (판정이 확실)

방법
  1. 0번 문자열 뒤에 300B 를 끼워 넣는다 -> 뒤 문자열이 전부 +300 밀린다
     (본문 끝 14,154 -> 14,454 로 **원래 크기 14,336 을 넘어선다**)
  2. 파일을 16,384B 로 키운다(뒤를 0 으로 채움)

판정
  메뉴 설명이 **끝 항목까지 정상** -> 파일 키우기 가능
  뒤쪽 항목이 깨지거나 게임이 멈춤 -> 불가. 예산은 파일 크기 그대로 유지
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, WORK, pristine
from msgrec import records

REL = os.path.join('menudata', 'TextData', 'Text_MenuInst_JP.msg')
NEWSIZE = 32768
ADD = 'オルタとドラゴンの物語を体験します。' * 400   # 그 줄이 이미 쓰는 글자만


def main():
    src = pristine(os.path.join(ROOT, REL))
    d = open(src, 'rb').read()
    rs = records(d)
    r = rs[0]
    add = ADD.encode('cp932')[:14000]
    s, L = r['off'], r['bytes']
    print('원본 %d B, 레코드 %d개, 본문 끝 0x%x'
          % (len(d), len(rs), max(x['off'] + x['bytes'] for x in rs)))
    print('idx0 off 0x%04x %dB  %r' % (s, L, r['jp']))
    print('덧붙일 %dB' % len(add))

    new = d[:s + L] + add + d[s + L:]
    end = max(x['off'] + x['bytes'] for x in records(new))
    print('밀어낸 뒤 본문 끝 0x%x (%d) — 원래 크기 %d %s'
          % (end, end, len(d), '★넘어섬' if end > len(d) else '아직 안 넘음'))
    if len(new) < NEWSIZE:
        new = new + bytes(NEWSIZE - len(new))
    else:
        raise SystemExit('★%d B 로 안 들어간다' % NEWSIZE)

    rs2 = records(new)
    print('레코드 %d -> %d  / 뒤 문자열 보존 %s'
          % (len(rs), len(rs2),
             '예' if all(a['jp'] == b['jp'] for a, b in zip(rs[1:], rs2[1:])) else '★아니오'))

    bak = os.path.join(WORK, 'orig', REL)
    os.makedirs(os.path.dirname(bak), exist_ok=True)
    if not os.path.exists(bak):
        shutil.copy2(os.path.join(ROOT, REL), bak)
    dst = os.path.join(ROOT, REL)
    open(dst, 'wb').write(new)
    print('기록 %s  %d B -> %d B' % (REL, len(d), len(new)))


if __name__ == '__main__':
    main()
