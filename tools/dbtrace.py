"""★번역문의 «한 글자»가 실제로 어떤 코드로 나갔고, 어느 칸을 가리키는지 추적한다.

빌드된 `.msg` 를 번역문과 «글자 단위로 정렬»해서 본다.
⛔한글만 뽑아 코드와 zip 하면 안 된다 — 문장부호·따옴표도 코드 한 자리를 먹는다.

    python dbtrace.py <파일조각> <idx> [보고 싶은 음절...]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, TRANS, WORK, pristine
from msgrec import records
from ztbl import ZTbl
import build_all as B
import check_ko as K


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    frag, idx = args[0], int(args[1])
    want = set(''.join(args[2:])) if len(args) > 2 else None
    corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
    ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
    rel = [r for r in corpus if frag in r][0]
    sc = K.scene_of(rel)
    d = open(os.path.join(ROOT, rel), 'rb').read()
    r = records(d)[idx]
    raw = d[r['off']:r['off'] + r['bytes']]
    src = ko[rel][str(idx)]

    menu = ZTbl(pristine(B.tbl_path(sc))).mapping()
    cmn = ZTbl(pristine(B.tbl_path('Common'))).mapping()
    grid = {}
    p = os.path.join(WORK, 'gridmap_%s.json' % sc)
    if os.path.exists(p):
        grid = {int(k): tuple(v) for k, v in
                json.load(open(p, encoding='utf-8')).items()}
    orig = set()
    for e in corpus[rel]:
        orig.update(c for c in e['jp'] if ord(c) > 0x7f)
    for r0 in corpus:
        if K.scene_of(r0) == sc:
            for e in corpus[r0]:
                orig.update(c for c in e['jp'] if ord(c) > 0x7f)
    safe = set(B.SAFE_LEADS)

    i = 0
    seen = {}
    for ch in src:
        if ch == '\n':
            i += 1
            continue
        if ch == K.HALF_SP:
            i += 1
            continue
        if ch.isascii():
            i += 1
            continue
        code = raw[i:i + 2].decode('cp932', 'replace')
        i += 2
        if K.is_hangul(ch) and ch not in seen:
            seen[ch] = code
    print('%s idx %d · 장면 %s · 음절 %d종' % (os.path.basename(rel), idx, sc, len(seen)))
    for ch, code in seen.items():
        if want and ch not in want:
            continue
        b = code.encode('cp932', 'replace')
        g = menu.get(code)
        print('  %s -> %r %s · 원문 %-5s 안전리드 %-5s %s표 %-6s 공용표 %-6s 자리 %s'
              % (ch, code, b.hex(), code in orig, b[0] in safe, sc,
                 g if g is not None else '없음',
                 cmn.get(code, '없음'),
                 grid.get(g, '(모름)') if g is not None else '-'))


if __name__ == '__main__':
    main()
