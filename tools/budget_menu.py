"""Text_MenuInst_JP.msg 의 문자열별 «제자리 예산»(원문 바이트 수)을 잰다.

파일 크기를 고정하고 제자리 덮어쓰기만 하므로 번역문 바이트 <= 원문 바이트여야 한다.
"""
import os
import json
from msgfile import scan, data_end
from project import ROOT, TRANS

TD = os.path.join(ROOT, 'menudata', 'TextData')
SRC = os.path.join(TD, 'Text_MenuInst_JP.msg')
# ★빌드가 제자리를 덮어쓰므로 예산은 «백업된 원본»에서 재야 한다.
_BAK = os.path.join(TRANS, '..', 'work', 'orig', 'menudata', 'TextData',
                    'Text_MenuInst_JP.msg')


def source():
    return _BAK if os.path.exists(_BAK) else SRC


def entries():
    d = open(source(), 'rb').read()
    out = []
    for off, kind, t in scan(d):
        raw = t.encode('cp932')
        # 원문 뒤 널 패딩까지가 실제 쓸 수 있는 자리
        end = off + len(raw)
        pad = 0
        while end + pad < len(d) and d[end + pad] == 0:
            pad += 1
        out.append({'off': off, 'jp': t, 'bytes': len(raw), 'pad': pad})
    return d, out


if __name__ == '__main__':
    d, es = entries()
    print('파일 %d B, 실사용 %d B' % (len(d), data_end(d)))
    tot = 0
    for i, e in enumerate(es):
        tot += e['bytes']
        print('%3d @%05x  %3dB (+pad %d)  %s'
              % (i, e['off'], e['bytes'], e['pad'], e['jp'].replace('\n', '\\n')))
    print('\n합계 %d B / 문자열 %d개' % (tot, len(es)))
