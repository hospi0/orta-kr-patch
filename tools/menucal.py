"""★★★Menu 아틀라스 «표값 -> 자리» 실측 실험 — 시험 빌드를 만든다.

## 왜

도감(Menu 장면)은 아틀라스 자리를 189개밖에 몰라 음절 426개가 ■ 로 나온다.
자리를 알아내는 오프라인 방법은 다 막혔다(머리에 격자 정보 없음 · 라스터 공식 16/191 ·
다른 아틀라스 글리프 사전으로는 189개가 한계).

## 그런데

실측한 189자리로 재 보면 «예측 라스터 번호 - 표값» 이 **0~5 안에 갇혀 있다**.
그러니 자리마다 «자리번호 mod 12» 를 라벨로 칠해 두고 값들을 순서대로 찍어 보면,
후보가 6칸뿐이라 라벨 하나로 자리가 **유일하게** 확정된다.

## 시험 빌드가 하는 일

1. 잉크 있는 자리 전부(1146개)에 라벨 한글을 칠한다 — 라벨 = 자리번호 % 12.
2. 도감 «드래곤» 계열 레코드에 값들을 순서대로 부르는 문자를 채운다.
   · 코드는 «공용 표에 없는 문자»만 쓴다(공용이 먼저 조회돼 엉뚱한 칸이 나오는 걸 막는다).
   · 레코드마다 앞 2글자는 «자리를 이미 아는 값»으로 만든 머리표다 — 스샷 순서가
     섞여도 어느 조각인지 알 수 있다.
3. 계획을 work/menucal.json 에 남긴다(스샷 판독용).

    python menucal.py            # 계획만 보고
    python menucal.py --apply    # 게임 트리에 시험 빌드 기록
    python menucal.py --restore  # work/orig 로 되돌린다
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, TRANS, WORK, pristine
from atlaswrite import Atlas
from msgrec import records
from ztbl import ZTbl
import build_all as B
import render3 as R

ORIG = os.path.join(WORK, 'orig')
PLAN = os.path.join(WORK, 'menucal.json')
LABELS = '가나다라마바사아자카파하'          # 12개 — 저해상도에서도 서로 안 헷갈리게
BASE = {0: 16, 1: 20, 2: 24, 3: 0}
DBREL = r'menudata\TextData\text_pdb_db_world_JP.msg'
# 드래곤 계열 레코드 — 화면 한 장 = 레코드 하나. 위에서부터 순서대로 채운다.
RECS = [76, 77, 78, 79, 80, 81, 82, 84, 85, 86, 87]


def positions(a):
    out = []
    for p in range(a.pages):
        for r in range(18):
            for c in range(18):
                x = BASE[p] + c * 28
                if x > 511:
                    continue
                out.append((x, p * 512 + r * 28))
    return [xy for xy in out if a.ink_xy(*xy) > 0]


def main():
    apply = '--apply' in sys.argv
    if '--restore' in sys.argv:
        n = 0
        for rel in (DBREL, os.path.join('sprite', 'Font', 'Zenkaku_Menu.txb')):
            src = os.path.join(ORIG, rel)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(ROOT, rel))
                n += 1
        print('원본으로 되돌린 파일 %d개' % n)
        return 0

    menu_tbl = ZTbl(pristine(B.tbl_path('Menu'))).mapping()
    cmn = ZTbl(pristine(B.tbl_path('Common'))).mapping()
    a = Atlas(pristine(B.atlas_path('Menu')))
    pos = positions(a)
    print('잉크 있는 자리 %d개 · 라벨 %d종' % (len(pos), len(LABELS)))

    # 값 -> 부를 문자 (공용 표에 없는 것 우선)
    byval = {}
    for ch, v in menu_tbl.items():
        cur = byval.get(v)
        if cur is None or (cur in cmn and ch not in cmn):
            byval[v] = ch
    vals = [v for v in sorted(byval) if byval[v] not in cmn]
    print('부를 수 있는 값 %d개 (공용 표에 없는 문자로)' % len(vals))

    # 머리표에 쓸 «자리를 이미 아는» 값
    known = {int(k): tuple(v) for k, v in json.load(
        open(os.path.join(WORK, 'gridmap_Menu.json'), encoding='utf-8')).items()}
    pidx = {xy: i for i, xy in enumerate(pos)}
    hdr_pool = [v for v in sorted(known) if v in byval and byval[v] not in cmn
                and known[v] in pidx]
    print('머리표에 쓸 수 있는 «자리 아는» 값 %d개' % len(hdr_pool))

    # --- 레코드에 나눠 담기 ---
    d = open(os.path.join(ORIG, DBREL), 'rb').read()
    rs = records(d)
    plan, vi = [], 0
    out = bytearray(d)
    for k, ri in enumerate(RECS):
        if ri >= len(rs):
            continue
        r = rs[ri]
        budget = r['bytes']
        # ★한 줄 16자 · 최대 12줄. 원본 항목이 12줄까지 쓰므로 그 안이면 안 잘린다.
        #   머리표 2글자는 «첫 줄 앞»에 붙인다(줄을 하나 더 쓰면 13줄이 되어 넘친다).
        # ★머리표 = «라벨 k» 가 나오는 자리를 가리키는 값을 두 번 -> 화면엔 「가가」「나나」…
        #   조각마다 라벨이 겹치지 않아 스샷 순서가 섞여도 구분된다.
        hv = next(v for v in sorted(known)
                  if v in byval and byval[v] not in cmn and known[v] in pidx
                  and pidx[known[v]] % len(LABELS) == k % len(LABELS))
        h = [hv, hv]
        body = [byval[v] for v in h]
        col = 2
        used = 2 * 2
        take = []
        while vi < len(vals):
            ch = byval[vals[vi]]
            nl = (col == 16)
            if nl and len(body) and body.count('\n') >= 11:
                break                                   # 12줄을 넘기지 않는다
            add = 2 + (1 if nl else 0)
            if used + add > budget:
                break
            if nl:
                body.append('\n')
                col = 0
            take.append(vals[vi])
            body.append(ch)
            col += 1
            used += add
            vi += 1
        txt = ''.join(body)
        enc = txt.encode('cp932')
        enc += b' ' * (budget - len(enc))
        out[r['off']:r['off'] + budget] = enc
        hlab = ''.join(LABELS[pidx[known[v]] % len(LABELS)] for v in h)
        plan.append({'chunk': k, 'rec': ri, 'bytes': budget,
                     'header': [h[0], h[1]], 'header_label': hlab,
                     'lines': body.count('\n') + 1, 'values': take})
        print('  조각 %-2d 레코드 %-4d %4dB · 값 %4d개 · %2d줄 · 머리표 「%s」'
              % (k, ri, budget, len(take), body.count('\n') + 1, hlab))
        if vi >= len(vals):
            break
    print('담은 값 %d / %d' % (vi, len(vals)))
    if vi < len(vals):
        print('★레코드가 모자란다 — RECS 에 항목을 더 넣어야 한다')

    # --- 아틀라스에 라벨 칠하기 ---
    R.calibrate(sorted(set(LABELS)))
    blob = None
    for levels in (0, 8, 6, 4):
        at = Atlas(os.path.join(ORIG, os.path.relpath(B.atlas_path('Menu'), ROOT)))
        for i, (x, y) in enumerate(pos):
            at.set_at(x, y, R.glyph(LABELS[i % len(LABELS)], levels=levels), color=True)
        try:
            blob = at.to_bytes(keep_size=True)
            print('아틀라스 %d B (계조 %s)' % (len(blob), levels or '전체'))
            break
        except ValueError:
            continue
    if blob is None:
        print('★아틀라스가 원본 크기를 넘는다 — 라벨을 더 단순하게 해야 한다')
        return 1

    if apply:
        open(os.path.join(ROOT, DBREL), 'wb').write(bytes(out))
        open(os.path.join(ROOT, os.path.relpath(B.atlas_path('Menu'), ROOT)),
             'wb').write(blob)
        with open(PLAN, 'w', encoding='utf-8') as f:
            json.dump({'labels': LABELS, 'positions': [list(p) for p in pos],
                       'chunks': plan}, f, ensure_ascii=False)
        print('시험 빌드 기록 · 계획 -> work/menucal.json')
        print('★다음: python hddcache.py  그리고 isopatch.py')
    else:
        print('※ 계획만. 기록하려면 --apply')
    return 0


if __name__ == '__main__':
    sys.exit(main())
