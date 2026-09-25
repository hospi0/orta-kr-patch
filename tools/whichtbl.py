"""★★각 `.msg` 의 «원문»이 어느 코드표에 «전부» 들어 있는지 전수로 가른다.

원리: 게임이 그 화면을 원본 상태로 «멀쩡히» 그리는 이상, 그 화면이 쓰는 표에는
원문의 모든 전각 문자가 있어야 한다. 한 글자라도 없으면 그 표가 아니다.
⇒ 「파일 이름이 Menu 니까 Menu 겠지」 같은 추측을 **증거로 바꾼다**
   → [[feedback_verify_which_asset_the_screen_uses]]

    python whichtbl.py            # 전 파일
    python whichtbl.py <파일조각>  # 이름에 그 조각이 든 파일만, 표별 상세
"""
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, WORK, COMMON_TBL, SCENES, pristine
from ztbl import ZTbl
from atlaswrite import Atlas, CELLS_PER_PAGE
from msgwalk import walk

ORIG = os.path.join(WORK, 'orig')


def tables():
    """{이름: (문자집합, 칸수)} — 전부 «무수정 원본»에서."""
    out = {}
    rows = [('Common', os.path.join(FONT_DIR, COMMON_TBL))]
    rows += [(s, os.path.join(FONT_DIR, 'Reisyo_%s_z_tbl.bin' % s)) for s in SCENES]
    for name, p in rows:
        po = os.path.join(ORIG, os.path.relpath(p, ROOT))
        src = po if os.path.exists(po) else p
        ap = os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % name)
        apo = os.path.join(ORIG, os.path.relpath(ap, ROOT))
        if not os.path.exists(src):
            continue
        t = ZTbl(src)
        n = None
        try:
            n = Atlas(apo if os.path.exists(apo) else ap).pages * CELLS_PER_PAGE
        except Exception:
            pass
        m = t.mapping()
        if n:
            m = {c: g for c, g in m.items() if g < n}
        out[name] = set(m)
    return out


def chars_of(path):
    d = open(path, 'rb').read()
    s = collections.Counter()
    for start, ident, off, ln in walk(d):
        for ch in d[off:off + ln].decode('cp932', 'replace'):
            if ord(ch) > 0x7f and ch != '�':
                s[ch] += 1
    return s


def main():
    pick = sys.argv[1] if len(sys.argv) > 1 else None
    tb = tables()
    files = []
    for dp, dn, fn in os.walk(ORIG):
        for f in sorted(fn):
            if f.endswith('.msg') and (pick is None or pick in f):
                files.append(os.path.join(dp, f))
    print('%-42s %6s  %s' % ('파일', '고유자', '원문을 «전부» 담은 표'))
    for p in files:
        s = chars_of(p)
        full = [n for n, cs in tb.items() if not (set(s) - cs)]
        # 가장 잘 덮는 표 3개
        best = sorted(((len(set(s) - cs), n) for n, cs in tb.items()))[:3]
        print('%-42s %6d  %s' % (os.path.basename(p), len(s),
              ', '.join(full) if full else
              '★없음 — 최선: ' + ' / '.join('%s(빠짐%d)' % (n, k) for k, n in best)))
        if pick:
            print('     상위: ' + ' / '.join('%s(빠짐%d)' % (n, k) for k, n in best))


if __name__ == '__main__':
    main()
