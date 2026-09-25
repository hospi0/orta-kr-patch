"""번역문의 «낱말 사이 공백»을 전각(2B) -> 반각(1B) 으로 바꿨을 때의 효과를 잰다.

★반각 공백 0x20 은 안전하다 — 원본 텍스트가 실제로 쓴다(`$c0ドラゴン ` 끝이 `93 20 00`).
★문단 첫머리의 전각 공백(　)은 «들여쓰기»이므로 건드리지 않는다.

    python halfsp.py            # 파일별 효과만
    python halfsp.py --apply [파일조각...]   # 반영 (조각을 주면 그 파일만)
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS
import check_ko as K

KO = os.path.join(TRANS, 'ko.json')
HALF = K.HALF_SP          # U+00A0 = 본문 안 «반각 공백» 표식


def convert(t):
    """줄 첫머리의 전각 공백(들여쓰기)은 남기고, 낱말 사이 ' ' 만 반각으로."""
    out = []
    for ln in t.split('\n'):
        i = 0
        while i < len(ln) and ln[i] == '　':
            i += 1
        out.append(ln[:i] + ln[i:].replace(' ', HALF))
    return '\n'.join(out)


def main():
    apply = '--apply' in sys.argv
    picks = [a for a in sys.argv[1:] if not a.startswith('--')]
    corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
    ko = json.load(open(KO, encoding='utf-8'))
    print('%-42s %7s %7s %8s' % ('파일', '공백', '절약B', '적용'))
    tot = 0
    for rel in sorted(corpus):
        kk = ko.get(rel, {})
        n = sum(v.count(' ') for v in kk.values())
        hit = (not picks) or any(p in rel for p in picks)
        if n:
            print('%-42s %7d %7d %8s'
                  % (os.path.basename(rel), n, n, 'O' if hit else ''))
        if hit:
            tot += n
            if apply:
                for k in list(kk):
                    kk[k] = convert(kk[k])
    print()
    print('절약 합계 %d B' % tot)
    if apply:
        bak = KO + '.bak_halfsp'
        i = 0
        while os.path.exists(bak):
            i += 1
            bak = KO + '.bak_halfsp%d' % i
        shutil.copy2(KO, bak)
        with open(KO, 'w', encoding='utf-8', newline='') as f:
            json.dump(ko, f, ensure_ascii=False, indent=1)
        print('백업 %s · 적용 완료' % os.path.basename(bak))
    else:
        print('※ 계산만. 반영하려면 --apply')


if __name__ == '__main__':
    main()
