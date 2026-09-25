"""★★★빌드된 `.msg` 의 «모든 코드»가 화면에서 어떻게 나올지 분류한다.

2026-08-31 실기로 확정된 세 갈래:
  ① 그 장면 표에 있고 + 그 장면 «원문»에도 있는 글자 -> 아틀라스 글리프(우리 한글) ✔
  ② 그 장면 표에 있고 + 원문엔 없는 글자           -> ■ (안 나옴)
  ③ 어느 표에도 없는 글자                          -> ★게임이 «시스템 폰트»로 그 한자를 그린다
     (도감에 界·往·偉·海·樂·握·奧·塊 가 뜬 원인. ■ 보다 훨씬 나쁘다.)

그러니 ③이 0 이어야 한다.

    python codecheck.py
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, TRANS, pristine
from msgrec import records
from ztbl import ZTbl
import build_all as B
import check_ko as K


def main():
    corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
    ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
    # ★★«빌드된» 표를 읽어야 한다 — 빌더가 새 코드를 표에 써넣는다.
    #   원본 표로 보면 그 코드들이 전부 «표에 없음»으로 잡혀 오탐이 된다.
    cmn = ZTbl(B.tbl_path('Common')).mapping()
    orig = collections.defaultdict(set)
    for rel in corpus:
        sc = K.scene_of(rel)
        for e in corpus[rel]:
            orig[sc].update(c for c in e['jp'] if ord(c) > 0x7f)
    xc = os.path.join(TRANS, 'xbe_corpus.json')
    if os.path.exists(xc):
        for e in json.load(open(xc, encoding='utf-8')):
            orig['Common'].update(c for c in e['jp'] if ord(c) > 0x7f)

    tot = collections.Counter()
    worst = collections.Counter()
    for rel in sorted(corpus):
        sc = K.scene_of(rel)
        tp = B.tbl_path(sc)
        if not os.path.exists(tp):
            continue
        tbl = ZTbl(tp).mapping()
        d = open(os.path.join(ROOT, rel), 'rb').read()
        rs = records(d)
        a = b = c = 0
        for i, r in enumerate(rs):
            if str(i) not in ko.get(rel, {}):
                continue
            src = ko[rel][str(i)]
            raw = d[r['off']:r['off'] + r['bytes']]
            j = 0
            for ch in src:
                # ★build_all.encode 와 «똑같이» 세야 자리가 안 어긋난다.
                #   ⛔'.' 과 ' ' 는 전각으로 바뀌어 2바이트다 — ASCII 로 세면 다 밀린다.
                if ch == '\n' or ch == K.HALF_SP:
                    j += 1
                    continue
                if not K.is_hangul(ch):
                    j += len(B.FW.get(ch, ch).encode('cp932', 'replace'))
                    continue
                code = raw[j:j + 2].decode('cp932', 'replace')
                j += 2
                if code in tbl or code in cmn:
                    # ★표에 있으면서 원문 밖인 코드는 «빌더가 표에 새로 써넣은» 것이다.
                    #   1쪽 장면은 표를 고칠 수 있어 정상으로 그려진다(실기 확인).
                    #   ⛔도감(Menu, 4쪽)만 표를 못 고쳐서 그런 코드가 ■ 가 된다.
                    if code in orig[sc] or sc != 'Menu':
                        a += 1
                    else:
                        b += 1
                else:
                    c += 1
                    worst[(os.path.basename(rel), ch, code)] += 1
        tot['글리프'] += a
        tot['■'] += b
        tot['★한자'] += c
        if c:
            print('  ★%-34s 글리프 %5d · ■ %5d · ★한자로 나옴 %4d'
                  % (os.path.basename(rel), a, b, c))
    print()
    print('합계 : 제대로 %d · ■ %d · ★시스템폰트 한자 %d'
          % (tot['글리프'], tot['■'], tot['★한자']))
    for (f, ch, code), n in worst.most_common(10):
        print('   %s  %s -> %r ×%d' % (f, ch, code, n))
    return 0 if not tot['★한자'] else 1


if __name__ == '__main__':
    sys.exit(main())
