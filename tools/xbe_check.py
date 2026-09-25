"""XBE 번역문 검산 — 바이트 예산·제어코드·불가문자.

XBE 문자열은 **NUL 종단**이라 «원본보다 짧거나 같으면» 제자리 치환이 된다.
바이트 셈법은 빌더와 같다: 한글/전각 2 · 반각 1 · `\\n` 1.
★`%s0` `%s1` `%i0` 은 게임이 읽는 제어코드다 — 개수와 값이 원문과 같아야 한다.
★`%s0…%s1` 사이의 «여백»은 반각 공백(U+00A0 표식)이어야 한다. 전각이면 폭이 2배가 된다.

    python xbe_check.py [--fix]
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS
import check_ko as K

CODE = re.compile(r'%[si]\d')
FW = {' ': '　', '.': '。'}


def nbytes(t):
    n = 0
    for c in t:
        if c == '\n' or c == K.HALF_SP:
            n += 1
        elif ord(c) < 0x80 and c not in FW:
            n += 1
        elif K.is_hangul(c):
            n += 2                      # 대체 코드(전각 SJIS)로 나간다
        else:
            n += len(FW.get(c, c).encode('cp932'))
    return n


def main():
    fix = '--fix' in sys.argv
    corpus = json.load(open(os.path.join(TRANS, 'xbe_corpus.json'), encoding='utf-8'))
    ko = json.load(open(os.path.join(TRANS, 'xbe_ko.json'), encoding='utf-8'))
    by = {str(e['off']): e for e in corpus}
    bad = 0
    changed = False
    print('%-10s %5s %5s  %s' % ('오프셋', '원본', '번역', ''))
    for off, t in sorted(ko.items(), key=lambda kv: int(kv[0])):
        e = by.get(off)
        if e is None:
            print('★%s : 코퍼스에 없는 오프셋' % off)
            bad += 1
            continue
        # ★%s0…%s1 사이 여백을 반각으로
        t2 = re.sub(r'(?<=%s0) {2,}(?=%s1)', lambda m: K.HALF_SP * len(m.group()), t)
        if t2 != t:
            changed = True
            ko[off] = t2
            t = t2
        n = nbytes(t)
        c1 = sorted(CODE.findall(e['jp']))
        c2 = sorted(CODE.findall(t))
        msg = ''
        if n > e['bytes']:
            msg += '  ★넘침 %d' % (n - e['bytes'])
            bad += 1
        if c1 != c2:
            msg += '  ★제어코드 %s -> %s' % (c1, c2)
            bad += 1
        for ch in t:
            if not K.is_hangul(ch) and ch not in ('\n', K.HALF_SP):
                try:
                    FW.get(ch, ch).encode('cp932')
                except Exception:
                    msg += '  ★cp932 불가 %r' % ch
                    bad += 1
        print('%-10s %5d %5d%s' % (off, e['bytes'], n, msg))
    print()
    print('문제 %d건 · 항목 %d개' % (bad, len(ko)))
    if fix and changed:
        with open(os.path.join(TRANS, 'xbe_ko.json'), 'w',
                  encoding='utf-8', newline='') as f:
            json.dump(ko, f, ensure_ascii=False, indent=1)
        print('★반각 여백으로 고쳐 저장했습니다.')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
