"""빈칸의 원인을 «한 빌드, 세 줄»로 가른다. 아틀라스는 이미 한글이므로 건드리지 않는다.

idx 4  원문 글자만 «순서만 바꿔» 넣는다 (반각 없음, 새 코드 없음)
        → 나오면 «.msg 제자리 편집»은 정상. 안 나오면 편집 자체가 깨진 것.
idx 3  한글 + 전각 마침표만 (반각 공백·마침표 **없음**)
        → 나오면 대체 코드는 정상이고 **반각 ASCII 가 범인**.
idx 0  ★제외 — 34/36B 라 널이 2개 늘어 그 뒤 색인을 다 밀어버렸다
        널 개수가 바뀌면 문자열 «전체»가 무너진다. 길이는 «정확히» 맞춰야 한다.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'trans'))
from project import ROOT, WORK
from budget_menu import entries
from check_menu import prepare

REL = os.path.join('menudata', 'TextData', 'Text_MenuInst_JP.msg')

CASES = {
    4: ('원문글자 재배열', 'ゲームを最初から開始します。'),
    3: ('한글+전각만', '설정을변경합니다。'),
}


def main():
    syl, st, short, smap = prepare(persist=False)

    def enc(t):
        out = bytearray()
        for c in t:
            if c == '\n':
                out.append(0x0A)
            elif 0xac00 <= ord(c) <= 0xd7a3:
                out += smap[c].encode('cp932')
            else:
                out += c.encode('cp932')
        return bytes(out)

    src = os.path.join(WORK, 'orig', REL)
    d = bytearray(open(src, 'rb').read())
    _, es = entries()
    for i, (tag, text) in CASES.items():
        e = es[i]
        b = enc(text)
        if len(b) > e['bytes']:
            raise SystemExit('★idx %d 예산 초과 %d > %d' % (i, len(b), e['bytes']))
        d[e['off']:e['off'] + e['bytes']] = b + b'\x00' * (e['bytes'] - len(b))
        print('idx %d [%s] %d/%d B  %s' % (i, tag, len(b), e['bytes'], text))
        print('   %s' % b.hex(' '))
    dst = os.path.join(ROOT, REL)
    o = open(src, 'rb').read()
    assert len(d) == len(o)
    with open(dst, 'wb') as f:
        f.write(bytes(d))
    print('기록 %s (%d B, 원본과 동일)' % (REL, len(d)))


if __name__ == '__main__':
    main()
