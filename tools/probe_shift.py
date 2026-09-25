"""밀어쓰기 시험 — 문자열을 «원문보다 길게» 쓰고 뒤를 밀어도 되는가.

되면 예산이 파일 꼬리 여백만큼 늘어난다(전체 +35%).
안 되면 번역문은 영원히 «원문과 정확히 같은 바이트»여야 한다.

대상 = Text_OpeningDemo_JP.msg
  · 부팅하자마자 오프닝 자막으로 보여서 확인이 싸다
  · 꼬리 여백이 1,543B 라 넉넉하다
방법 = 0번 문자열 뒤에 20바이트를 끼워 넣고, 파일 꼬리의 0 을 그만큼 잘라
       **파일 크기를 그대로** 유지한다. 뒤 문자열은 전부 +20 만큼 밀린다.

판정
  오프닝 1번째 줄이 길어지고 **나머지 줄이 멀쩡** -> 밀어쓰기 가능
  2번째 줄부터 깨짐/빈칸                          -> 절대 오프셋을 쓴다. 불가
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, WORK, pristine
from msgrec import records

REL = os.path.join('menudata', 'TextData', 'Text_OpeningDemo_JP.msg')
ADD = '栄華を誇った文明が滅'          # 20 B — 그 줄에 이미 쓰인 글자만 쓴다


def main():
    src = pristine(os.path.join(ROOT, REL))
    d = open(src, 'rb').read()
    rs = records(d)
    r = rs[0]
    add = ADD.encode('cp932')
    s, L = r['off'], r['bytes']
    print('대상 idx0 off 0x%04x  %dB  %r' % (s, L, r['jp']))
    print('덧붙일 %dB  %r' % (len(add), ADD))

    tail = len(d) - len(d.rstrip(b'\x00'))
    if tail < len(add):
        raise SystemExit('꼬리 여백 부족 %d < %d' % (tail, len(add)))
    new = d[:s + L] + add + d[s + L:len(d) - len(add)]
    assert len(new) == len(d), '크기가 달라졌다'

    rs2 = records(new)
    print('레코드 수 %d -> %d' % (len(rs), len(rs2)))
    print('idx0 %dB -> %dB' % (rs[0]['bytes'], rs2[0]['bytes']))
    print('idx1 오프셋 0x%04x -> 0x%04x (%+d)'
          % (rs[1]['off'], rs2[1]['off'], rs2[1]['off'] - rs[1]['off']))
    ok = all(a['jp'] == b['jp'] for a, b in zip(rs[1:], rs2[1:]))
    print('뒤 문자열 내용 보존: %s' % ('예' if ok else '★아니오'))

    dst = os.path.join(ROOT, REL)
    bak = os.path.join(WORK, 'orig', REL)
    os.makedirs(os.path.dirname(bak), exist_ok=True)
    if not os.path.exists(bak):
        open(bak, 'wb').write(d)
    open(dst, 'wb').write(new)
    print('기록 %s (%d B, 원본과 동일)' % (REL, len(new)))


if __name__ == '__main__':
    main()
