"""한글 음절 -> **Common 아틀라스** 글리프 칸 배정.

★★2026-08-12 시험1 실패로 확정된 사실:
  메인 메뉴 설명 상자는 **`Zenkaku_Common` 으로 그린다.**
  근거 = 원문 「最初からゲームを開始します。」의 `最` 는 **Common 표에만 있고
  Menu 표에는 없는데** 원본에서 정상 출력됐다.
  1차 시험에서 Menu 표에만 있는 코드로 바꿨더니 **상자가 통째로 비었다**(전부 미매핑).
  ⇒ 대체 코드는 반드시 **Common 표에 있는 문자**여야 한다.

전략
  - Common 의 기존 매핑을 그대로 쓰고 **아틀라스 칸만 다시 그린다** → z_tbl 무편집.
  - 대체 문자가 **Menu 표에도 있으면** Menu 아틀라스의 그 칸도 **똑같이 칠한다.**
    렌더러가 어느 표를 먼저 보든 한글이 나온다.
  - 번역문에 실제로 쓰는 기호(「」（）／：・ＮＯＲＭＡＬ …)가 걸린 칸은 **보호**한다.
  - ★가나·한자·안 쓰는 기호 칸은 전부 덮어쓴다 ([[feedback_jp_kr_overwrite_all_slots]]).

★배정표 `work/slots.json` 은 바뀌면 넣은 텍스트가 다 깨진다. 새 음절은 뒤에 덧붙인다.
"""
import os
import sys
import json
from ztbl import ZTbl
from cells import atlas_alpha, filled_cells
from project import FONT_DIR, COMMON_TBL, WORK, pristine, scene_tbl, scene_atlas

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'trans'))

SLOTS = os.path.join(WORK, 'slots.json')
CMN_ATLAS = os.path.join(FONT_DIR, 'Zenkaku_Common.txb')


def _cls(ch):
    o = ord(ch)
    return '가나' if 0x3040 <= o <= 0x30ff else (
        '한자' if 0x4e00 <= o <= 0x9fff else '기호')


def protected_chars():
    """번역문이 그대로 쓰는 «한글 아닌 전각 문자» — 이 칸은 못 건드린다.

    ★빌더가 반각 ASCII 를 전각으로 바꿔 넣으므로(check_menu.to_full),
      여기서도 «변환한 뒤» 모아야 한다. 안 그러면 Ｈ·Ｖ 처럼 변환으로 새로 생기는
      글자의 칸이 한글로 덮여 화면에 엉뚱한 글자가 나온다.
    """
    from Text_MenuInst_ko import KO
    from check_menu import to_full
    keep = set()
    for t in KO.values():
        if not t:
            continue
        t = ''.join(to_full(c) if c != '\n' else c for c in t)
        for c in t:
            if c == '\n' or ord(c) < 0x80 or 0xac00 <= ord(c) <= 0xd7a3:
                continue
            keep.add(c)
    return keep


def build_pool():
    """[(대체SJIS문자, Common칸, Menu칸 or -1, 갈래)]"""
    cm = ZTbl(pristine(os.path.join(FONT_DIR, COMMON_TBL))).mapping(drop_sentinel=False)
    mm = ZTbl(scene_tbl('Menu')).mapping(drop_sentinel=False)
    pages, px = atlas_alpha(pristine(CMN_ATLAS))
    ink = [i for i, (p, r, c, k) in enumerate(filled_cells(px)) if k]
    nglyph = ink[-1] + 1 if ink else 0
    keep = protected_chars()

    bycell = {}
    blocked = set()
    for ch, g in cm.items():
        if g >= nglyph:
            continue
        if ch in keep:
            blocked.add(g)
        bycell.setdefault(g, []).append(ch)

    pool, used_menu = [], set()
    for g, chars in sorted(bycell.items()):
        if g in blocked or g == 0:          # 0 = 전각 스페이스, 남겨둔다
            continue
        # Menu 에 없는 문자를 우선(추가 작업 없음), 없으면 Menu 칸도 같이 칠한다
        pick = next((c for c in chars if c not in mm), None)
        mcell = -1
        if pick is None:
            for c in chars:
                if mm[c] not in used_menu:
                    pick, mcell = c, mm[c]
                    used_menu.add(mm[c])
                    break
        if pick is None:
            continue
        pool.append((pick, g, mcell, _cls(pick)))
    pool.sort(key=lambda p: ({'가나': 0, '한자': 1}.get(p[3], 2), p[1]))
    return pool


def load():
    if os.path.exists(SLOTS):
        with open(SLOTS, encoding='utf-8') as f:
            return json.load(f)
    return {'map': {}, 'pool': [list(p) for p in build_pool()]}


def save(st):
    os.makedirs(WORK, exist_ok=True)
    with open(SLOTS, 'w', encoding='utf-8') as f:
        json.dump(st, f, ensure_ascii=False, indent=1)


def allocate(syllables, persist=True):
    st = load()
    taken = {v[0] for v in st['map'].values()}
    free = [tuple(p) for p in st['pool'] if p[0] not in taken]
    short = []
    for s in syllables:
        if s in st['map']:
            continue
        if not free:
            short.append(s)
            continue
        ch, g, mcell, kind = free.pop(0)
        st['map'][s] = [ch, g, mcell, kind]
    if persist:
        save(st)
    return st, short


if __name__ == '__main__':
    pool = build_pool()
    k = {}
    for ch, g, m, c in pool:
        k[c] = k.get(c, 0) + 1
    dual = sum(1 for p in pool if p[2] >= 0)
    print('Common 슬롯 풀 %d개  %s  (Menu 칸도 같이 칠할 것 %d개)' % (len(pool), k, dual))
    print('보호 문자:', ''.join(sorted(protected_chars())))
