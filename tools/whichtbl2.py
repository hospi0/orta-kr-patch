"""★★어느 «표»가 그 화면을 그리는가 — 원문 문자 커버리지로 가른다.

모집단은 `trans/corpus.json`(검증된 원문). walk 은 흔들리는 구간에서 잡음을 내므로 안 쓴다.
표는 전부 **무수정 원본**(work/orig)에서 읽는다.

    python whichtbl2.py           # 파일별: 단독 최선 / Common 합집합 / 전체 합집합
    python whichtbl2.py <조각>    # 그 파일의 «어느 표에도 없는» 문자를 나열
"""
import json
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, TRANS, WORK, COMMON_TBL, SCENES
from ztbl import ZTbl
from atlaswrite import Atlas, CELLS_PER_PAGE

ORIG = os.path.join(WORK, 'orig')


def orig_of(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


def tables(limit_to_atlas=True):
    out = {}
    rows = [('Common', os.path.join(FONT_DIR, COMMON_TBL))]
    rows += [(s, os.path.join(FONT_DIR, 'Reisyo_%s_z_tbl.bin' % s)) for s in SCENES]
    for name, p in rows:
        if not os.path.exists(p):
            continue
        m = ZTbl(orig_of(p)).mapping()
        if limit_to_atlas:
            ap = os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % name)
            if os.path.exists(ap):
                n = Atlas(orig_of(ap)).pages * CELLS_PER_PAGE
                m = {c: g for c, g in m.items() if g < n}
        out[name] = set(m)
    return out


def main():
    pick = sys.argv[1] if len(sys.argv) > 1 else None
    tb = tables()
    allc = set().union(*tb.values())
    corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
    print('표 %d개 · 전체 합집합 문자 %d개' % (len(tb), len(allc)))
    print()
    print('%-42s %6s %-22s %-22s %s'
          % ('파일', '고유자', '단독 최선', 'Common+장면', '전체합집합 빠짐'))
    for rel in sorted(corpus):
        if pick and pick not in rel:
            continue
        s = set()
        for e in corpus[rel]:
            s |= {c for c in e['jp'] if ord(c) > 0x7f}
        best = sorted(((len(s - cs), n) for n, cs in tb.items()))
        b0 = '%s(빠짐%d)' % (best[0][1], best[0][0])
        cm = tb['Common']
        best2 = sorted(((len(s - (cm | cs)), n) for n, cs in tb.items() if n != 'Common'))
        b2 = '%s(빠짐%d)' % (best2[0][1], best2[0][0])
        miss = s - allc
        print('%-42s %6d %-22s %-22s %d'
              % (os.path.basename(rel), len(s), b0, b2, len(miss)))
        if pick:
            print('   어느 표에도 없는 문자: %s' % ''.join(sorted(miss)))
            print('   Common 단독 빠짐 %d · %s 단독 빠짐 %d'
                  % (len(s - cm), best2[0][1], len(s - tb[best2[0][1]])))


if __name__ == '__main__':
    main()
