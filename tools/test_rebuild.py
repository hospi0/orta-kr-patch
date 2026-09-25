"""재조립 규칙 검증 — 새 `.msg` 를 «게임처럼» 걸어서 원본과 ID 목록이 같은지 본다.

게임 트리에 아무것도 쓰지 않는다. 빌드 허락 없이 돌려도 안전하다.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS, WORK
from build_all import rebuild_msg, fit_size
from msgwalk import walk
import check_ko as K

ORIG = os.path.join(WORK, 'orig')
corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
cm = json.load(open(os.path.join(WORK, 'charmap_all.json'), encoding='utf-8'))
smaps = {sc: {s: v[0] for s, v in d.items()} for sc, d in cm.items()}

bad = 0
pad_items = 0
print('%-42s %6s %6s %8s %s' % ('파일', '원본ID', '새ID', '크기', ''))
for rel in sorted(corpus):
    sc = K.scene_of(rel)
    smap = smaps.get(sc, {})
    ko_idx = {int(k): v for k, v in ko.get(rel, {}).items()}
    data, orig, odd, skipped = rebuild_msg(rel, ko_idx, smap)
    data, size = fit_size(data, orig)
    pad_items += odd
    o = open(os.path.join(ORIG, rel), 'rb').read()
    try:
        wo = [i for _, i, _, _ in walk(o) if i is not None]
    except ValueError as e:
        wo = ['ERR', str(e)]
    try:
        wn = [i for _, i, _, _ in walk(data) if i is not None]
    except ValueError as e:
        wn = ['ERR', str(e)]
    mark = ''
    if wo != wn:
        mark = '  ★★불일치'
        bad += 1
        # 첫 어긋난 자리
        for j in range(min(len(wo), len(wn))):
            if wo[j] != wn[j]:
                mark += ' (ID #%d: %s -> %s)' % (j, wo[j], wn[j])
                break
        else:
            mark += ' (개수 %d -> %d)' % (len(wo), len(wn))
    print('%-42s %6d %6d %8d%s' % (os.path.basename(rel), len(wo), len(wn), size, mark))

print()
print('불일치 파일 %d개 · 채움을 넣은 항목 %d개' % (bad, pad_items))
