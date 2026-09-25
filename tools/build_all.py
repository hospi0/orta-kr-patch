"""전체 빌드 — `trans/ko.json` 으로 `.msg` 32개 + 장면별 폰트/표를 다시 쓴다.

  python build_all.py            # 검산만
  python build_all.py --apply    # 게임 트리에 기록

## 설계

1. 장면별로 필요한 한글 음절을 모은다(파일 -> 장면은 `check_ko.SCENE`).
2. 장면마다 «그 장면 아틀라스»의 칸에 음절을 배정한다.
   · 번역문이 그대로 쓰는 전각 기호의 칸은 **보존**한다.
   · 대체 SJIS 코드는 **장면끼리 겹치지 않게** 전역에서 잘라 나눠 준다.
   · ★코드는 **공용(Cmn) 표에 없는 것**만 쓴다. 그래야 공용 조회가 빗나가고
     그 장면 표가 쓰인다(공용이 먼저 이기면 엉뚱한 글자가 나온다).
3. 아틀라스 칸을 한글로 다시 그리고, 그 장면 `z_tbl` 에 코드->칸 을 써넣는다.
4. `.msg` 는 «레코드 사이 바이트를 그대로 두고 텍스트만» 교체한다.
   ★★널 개수를 바꾸면 그 뒤 레코드 경계가 어긋나 화면이 통째로 빈칸이 된다
     → [[feedback_nul_padding_shifts_string_index]]
   ★파일이 모자라면 2048 배수로 키운다(실기 확인됨 → [[reference_orta_msg_format]]).

★폰트·표 파일은 **크기를 유지**해야 한다(HDD 캐시가 같은 크기로만 교체된다).
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import FONT_DIR, ROOT, TRANS, WORK, COMMON_TBL, pristine
from atlaswrite import Atlas, CELLS_PER_PAGE
from msgrec import records
from msgwalk import walk
from ztbl import ZTbl, LEADS, ZTBL_STRIDE
import check_ko as K
import render3 as R

ORIG = os.path.join(WORK, 'orig')
# ★HDD 캐시에 올라가는 폰트 — 크기를 «반드시» 유지해야 한다(hddcache.py --status 실측)
CACHED = {'Common', 'Menu', 'Stage1', 'Tutorial'}
FW = {' ': '　', '.': '。'}

# ★★★«글자 없음»(notdef) 글리프의 칸은 절대 덮으면 안 된다.
#   2026-08-31 판도라 도감이 통째로 「갈」로 나온 원인이 이것이었다.
#   Common 칸 40 = ■ 가 notdef 인데 거기에 한글을 칠했더니, 표에서 «못 찾은 모든 글자»가
#   그 한글로 나왔다. 「메시지 코드와 상관없이 같은 글자가 반복」이 그 지문이다.
#   → [[feedback_never_paint_over_notdef_glyph]]
SYSTEM_GLYPHS = '■□◆◇●○※〓＊★☆'


def backup(rel):
    dst = os.path.join(ORIG, rel)
    if not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, rel), dst)
    return dst


def tbl_path(scene):
    return os.path.join(FONT_DIR, COMMON_TBL if scene == 'Common'
                        else 'Reisyo_%s_z_tbl.bin' % scene)


def atlas_path(scene):
    return os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % scene)


# ★★대체 코드는 «한자 구역»에서만 고른다.
#   2026-08-30 실기: 리드 0x8D~0x9F 를 쓴 무비 자막은 한글이 정상으로 나왔는데,
#   리드 0x84(키릴)를 쓴 메뉴는 아무것도 안 나왔다. 원본 표 27개를 통틀어
#   0x84~0x87 구역은 한 번도 안 쓰인다 — 게임의 색인 계산이 그 구역에선 다른 듯하다.
#   ⛔0xEB~0xEF 는 공용 표가 통째로 «센티널»로 채워 둔 NEC/IBM 중복 구역이라 뺀다.
SAFE_LEADS = [l for l in LEADS if 0x88 <= l <= 0x9F or 0xE0 <= l <= 0xEA]


def all_sjis():
    """대체 코드로 쓸 수 있는 전각 SJIS 문자(안전한 한자 구역만)."""
    out = []
    for li, lead in enumerate(SAFE_LEADS):
        for ti in range(ZTBL_STRIDE):
            trail = 0x40 + ti
            if trail == 0x7f or trail > 0xfc:
                continue
            try:
                out.append(bytes([lead, trail]).decode('cp932'))
            except Exception:
                pass
    return out


def encode(t, smap):
    out = bytearray()
    for c in t:
        if c == '\n':
            out.append(0x0A)
        elif c == K.HALF_SP:
            out.append(0x20)
        elif K.is_hangul(c):
            out += smap[c].encode('cp932')
        else:
            out += FW.get(c, c).encode('cp932')
    return bytes(out)


def rebuild_msg(rel, ko_of_idx, smap):
    """레코드 사이 바이트를 그대로 두고 텍스트만 교체. (새 바이트, 원본 크기)"""
    src = backup(rel)
    d = open(src, 'rb').read()
    rs = records(d)
    # ★★★msgrec 은 «레코드 머리»를 텍스트로 오인하는 가짜 항목을 만든다.
    #   거기에 번역을 써넣으면 머리가 깨져 그 뒤 항목을 못 찾는다 -> 화면에 `NO TEXT`.
    #   2026-08-31 실기: `text_pdb_db_world` idx83(off 6716, ' 跋')이 idx84 머리 한복판이었고,
    #   도감 카테고리 5개가 통째로 `NO TEXT` 였다.
    #   ⇒ walk(진짜 구조)이 «머리»라고 아는 구간과 겹치면 **건드리지 않는다.**
    header_bytes = set()
    try:
        for st, _id, toff, _ln in walk(d):
            header_bytes.update(range(st, toff))
    except ValueError:
        pass
    out = bytearray()
    prev = 0
    odd = 0
    skipped = 0
    for i, r in enumerate(rs):
        out += d[prev:r['off']]                       # 레코드 헤더·앞 바이트 그대로
        t = ko_of_idx.get(i)
        # ⛔오프셋이 4의 배수가 아닌 «레코드»는 파서의 가짜 항목이다.
        #   진짜 레코드는 전부 4바이트 경계에 있다. 여길 건드리면 텍스트가 아닌
        #   자리를 덮어써서 구조가 깨진다(OpeningDemo 의 'c.' 조각이 그랬다).
        if r['off'] % 4:
            t = None
        raw = d[r['off']:r['off'] + r['bytes']]
        # ★가짜 항목의 지문 = «4바이트 이하 + ASCII 로 시작».
        #   레코드 머리의 포인터 꼬리를 텍스트로 오인한 것이다(' 跋' · '8槫' · 'P鰥' …).
        #   진짜 짧은 대사(加速·上昇·敵？)는 전부 전각으로 시작하므로 안 걸린다.
        #   ⛔이걸 안 막으면 그 자리에 한글을 써 머리가 깨지고, 그 뒤가 `NO TEXT` 가 된다.
        if t and len(raw) <= 4 and raw and raw[0] < 0x80 and raw[0] != 0x0A:
            t = None
            skipped += 1
        # ★긴 가짜는 «머리 구간과 겹치는가»로 한 번 더 거른다(8바이트 이하만).
        elif t and len(raw) <= 8 and any(
                x in header_bytes for x in range(r['off'], r['off'] + r['bytes'])):
            t = None
            skipped += 1
        if t:
            b = encode(t, smap)
            # ★★★채움은 «종단 NUL 앞»에 — 텍스트의 일부로 넣는다.
            #   게임은 «NUL 다음 바이트를 4로 올린 자리»에서 다음 항목을 찾는다
            #   (2026-08-31 `NO DATA ID=3100` 화면으로 확정 → tools/msgwalk.py).
            #   ⛔예전처럼 NUL 을 찍고 그 «뒤»에 채우면 게임이 센 다음 항목 자리가
            #     실제보다 앞이 되어 그 뒤 전부가 어긋난다.
            #   ★반각 공백 0x20 은 안전하다 — 원본 텍스트가 실제로 쓴다
            #     (`$c0ドラゴン ` 의 끝 바이트가 `93 20 00`).
            need = (-(len(b) - r['bytes'])) % 4
            b += b' ' * need
            if need:
                odd += 1
            out += b
        else:
            out += d[r['off']:r['off'] + r['bytes']]
        prev = r['off'] + r['bytes']                  # ★종단 NUL 부터는 원본 그대로
    out += d[prev:]
    return bytes(out), len(d), odd, skipped


def fit_size(data, orig):
    """꼬리 0 을 잘라 원본 크기로. 모자라면 2048 배수로 키운다."""
    body = len(data.rstrip(b'\x00'))
    size = orig
    while body > size:
        size += 2048
    return data[:body] + bytes(size - body), size


def main():
    apply = '--apply' in sys.argv
    # ★--only=<장면> : 그 장면과 그 장면이 쓰는 .msg 만 바꾼다(최소 빌드로 원인 좁히기)
    only = None
    for a in sys.argv[1:]:
        if a.startswith('--only='):
            only = a.split('=',1)[1]
    corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
    ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))

    # --- 장면별 수요 + ★그 장면 «원문이 실제로 쓰는» 문자 ---
    need, keepch, files, used, used_f, freq = {}, {}, {}, {}, {}, {}
    for rel in corpus:
        sc = K.scene_of(rel)
        files.setdefault(sc, []).append(rel)
        for e in corpus[rel]:
            cs = {c for c in e['jp'] if ord(c) > 0x7f}
            used.setdefault(sc, set()).update(cs)
            used_f.setdefault(rel, set()).update(cs)
            t = ko.get(rel, {}).get(str(e['idx']))
            if not t:
                continue
            need.setdefault(sc, set()).update(c for c in t if K.is_hangul(c))
            for _c in t:
                if K.is_hangul(_c):
                    freq.setdefault(sc, {})[_c] = freq.setdefault(sc, {}).get(_c, 0) + 1
            keepch.setdefault(sc, set()).update(
                FW.get(c, c) for c in t
                if not K.is_hangul(c) and c not in ('\n', K.HALF_SP) and ord(c) > 0x7f)
    # ★★`default.xbe` 안의 하드코딩 문자열도 «공용 폰트»로 그려진다.
    #   수요(음절)와 원문 문자를 Common 장면에 합산해야 그 화면이 안 깨진다.
    xc0 = os.path.join(TRANS, 'xbe_corpus.json')
    xk0 = os.path.join(TRANS, 'xbe_ko.json')
    if os.path.exists(xc0) and os.path.exists(xk0):
        _c = json.load(open(xc0, encoding='utf-8'))
        _k = json.load(open(xk0, encoding='utf-8'))
        for e in _c:
            used.setdefault('Common', set()).update(
                c for c in e['jp'] if ord(c) > 0x7f)
            t = _k.get(str(e['off']))
            if not t:
                continue
            need.setdefault('Common', set()).update(
                c for c in t if K.is_hangul(c))
            keepch.setdefault('Common', set()).update(
                FW.get(c, c) for c in t
                if not K.is_hangul(c) and c not in ('\n', K.HALF_SP) and ord(c) > 0x7f)

    keep_all = set().union(*keepch.values()) if keepch else set()

    cmn_map = ZTbl(pristine(tbl_path('Common'))).mapping()
    pool = [c for c in all_sjis() if c not in cmn_map and c not in keep_all]
    print('대체 코드 풀 %d개 / 보존 문자 %d개' % (len(pool), len(keep_all)))

    R.calibrate(sorted(set().union(*need.values())))
    print('폰트 %s' % R.desc())

    # ═══ ★★★2026-08-31 실기 확정 규칙 ═══════════════════════════════════
    #  게임은 «그 화면의 원문이 실제로 쓰는 글자»만 폰트에 올린다.
    #  우리가 지어낸 코드는 그 집합 밖이라 **notdef(■)** 가 된다.
    #  판도라 도감 실기에서 19/19 일치: 화면에 나온 코드 5개는 전부 원문에 있고,
    #  ■ 로 나온 14개는 전부 원문에 없었다(`圧`=88B3 나옴 / 바로 옆 `梓`=88B2 안 나옴).
    #  ⇒ 대체 코드는 **그 장면 원문이 쓰는 문자**에서 고른다.
    #    부수 효과: 그 문자는 «이미» 그 칸을 가리키므로 **표를 안 건드려도 된다.**
    # ══════════════════════════════════════════════════════════════════
    n_cmn = Atlas(pristine(atlas_path('Common'))).pages * CELLS_PER_PAGE
    sys_cmn = {cmn_map[c] for c in SYSTEM_GLYPHS if c in cmn_map}
    keep_cmn = {cmn_map[c] for c in keep_all if c in cmn_map}

    def usable(g, n, bad):
        return g is not None and 0 < g < n and g not in bad

    # 공용 칸 -> {장면: 그 장면 원문이 쓰는 «그 칸을 가리키는» 문자}
    cmn_opt = {}
    for sc in need:
        for c in used.get(sc, ()):
            if c in keep_all:
                continue
            g = cmn_map.get(c)
            if usable(g, n_cmn, sys_cmn | keep_cmn):
                cmn_opt.setdefault(g, {}).setdefault(sc, c)

    # ★★★다중 페이지 아틀라스(Menu)는 «칸 번호 -> 위치» 공식이 우리 모델과 다르다.
    #   x 시작점이 페이지마다 달라(0->16 1->20 2->24 3->0) 28px 격자에 안 맞는다.
    #   ⇒ 실측한 위치표(work/gridmap_<장면>.json)를 쓴다. 없으면 칸 번호 그대로.
    #     만드는 법: tools/menupos.py (오라클 대조) -> tools/interp_pos.py (앵커 보간)
    posmap = {}
    for sc in list(need):
        pth = os.path.join(WORK, 'gridmap_%s.json' % sc)
        if os.path.exists(pth):
            posmap[sc] = {int(k): tuple(v) for k, v in
                          json.load(open(pth, encoding='utf-8')).items()}
            print('★%s 는 실측 위치표를 쓴다 (%d자리)' % (sc, len(posmap[sc])))

    def slot(sc, g, n):
        """표값 -> «쓸 수 있는 자리». 위치표가 있으면 (x,y), 없으면 칸 번호."""
        pm = posmap.get(sc)
        if pm is None:
            return g if (g is not None and 0 < g < n) else None
        return pm.get(g)

    def ink_of(a, sl):
        return a.ink_xy(*sl) if isinstance(sl, tuple) else a.ink(sl)

    # 장면 전용 칸 -> 문자 (원문이 쓰고, 공용엔 없고, 장면표에 있는 문자)
    sc_opt, sc_n, sc_tbl = {}, {}, {}
    for sc in need:
        tp0, ap0 = tbl_path(sc), atlas_path(sc)
        if not (os.path.exists(tp0) and os.path.exists(ap0)):
            continue
        m0 = ZTbl(pristine(tp0)).mapping()
        n0 = Atlas(pristine(ap0)).pages * CELLS_PER_PAGE
        bad = {slot(sc, m0[c], n0) for c in SYSTEM_GLYPHS if c in m0}
        bad |= {slot(sc, m0[c], n0) for c in keep_all if c in m0}
        bad.discard(None)
        d = {}
        for c in used.get(sc, ()):
            if c in cmn_map or c in keep_all:
                continue
            sl = slot(sc, m0.get(c), n0)
            if sl is not None and sl not in bad:
                d.setdefault(sl, c)
        sc_opt[sc], sc_n[sc], sc_tbl[sc] = d, n0, m0

    # --- 전역 공용 배정 (공용 칸은 전 장면이 같은 음절을 본다) ---
    tightness = {sc: len(need[sc]) - len(sc_opt.get(sc, {})) for sc in need}
    score = {}
    for sc in need:
        w = 10 if tightness[sc] > 0 else 1
        for s in need[sc]:
            score[s] = score.get(s, 0) + w
    # ★★공용 아틀라스는 «Common 장면(메인 메뉴)»이 통째로 쓴다 — 다른 칸이 없다.
    #   그래서 Common 의 수요를 «먼저» 채우고, 남는 칸만 다른 장면에 나눠 준다.
    #   ⛔안 그러면 Common 이 배정 실패해서 메인 메뉴가 통째로 깨진다.
    #  칸마다 «그 칸을 볼 수 있는 장면»이 다르다. 그래서 «집합 덮기» 로 푼다:
    #  칸을 «많은 장면이 볼 수 있는» 순으로 돌며, 그 칸의 장면들이 가장 많이 필요로 하는
    #  음절을 준다. ⛔단 Common 장면은 다른 칸이 없으므로 «자기 몫»을 남겨 둬야 한다.
    n_free_cmn = n_cmn - len(
        {0} | sys_cmn | keep_cmn
        | {cmn_map[c] for c in keepch.get('Common', ()) if c in cmn_map})
    scenes_of = {}
    for sc in need:
        for s in need[sc]:
            scenes_of.setdefault(s, set()).add(sc)
    need_cmn = need.get('Common', set())
    slack = max(0, n_free_cmn - len(need_cmn))   # Common 이 «원문 밖» 코드로 쓸 여유 칸
    # ★★칸이 모자란 장면이 «볼 수 있는» 칸을 먼저 배정한다.
    #   공용 칸은 Common 수요(274)와 칸 수(274)가 딱 맞아 여유가 0 이다. 그래서
    #   «어떤 음절을 넣느냐»가 아니라 «어느 칸에 넣느냐»가 유일한 자유도다.
    #   도감이 볼 수 있는 칸을 나중에 돌면, 거기에 도감이 안 쓰는 음절이 이미 들어간다.
    def urgency(g):
        return max((tightness.get(sc, 0) for sc in cmn_opt[g]), default=0)
    order = sorted(cmn_opt, key=lambda g: (-urgency(g), -len(cmn_opt[g])))
    cand = sorted(scenes_of, key=lambda s: (-len(scenes_of[s]), s))
    cmn_assign, taken_s, cov_c = {}, set(), 0
    for g in order:
        S = set(cmn_opt[g])
        # Common 이 못 보는 칸을 너무 많이 쓰면 Common 이 배정 실패한다
        only_common = (len(cmn_assign) - cov_c) >= slack
        best, bestk = None, 0
        for s in cand:
            if s in taken_s:
                continue
            if only_common and (s not in need_cmn or 'Common' not in S):
                continue
            # ★★«칸이 모자란 장면»의 수요를 무겁게 센다.
            #   ⛔장면 수만 세면(모두 1점), 도감처럼 자기 칸이 턱없이 모자란 장면이
            #     밀려 공용 칸을 164개밖에 못 받는다(닿을 수 있는 칸은 235개인데).
            k = sum(1 + max(0, tightness.get(sc, 0))
                    for sc in S & scenes_of[s])
            if k > bestk:
                best, bestk = s, k
        if best is None:
            continue
        cmn_assign[g] = best
        taken_s.add(best)
        if best in need_cmn and 'Common' in S:
            cov_c += 1
    # ⛔«공용 칸을 도감이 더 가져가기»는 하면 안 된다 — 공용 아틀라스는 여유가 0 이라
    #   가져간 만큼 주메뉴가 그대로 ■ 가 된다(2026-08-31 실측: 19칸 -> ■ 19개).
    print('전역 공용 칸 배정 %d개 (Common 몫 %d · 후보 칸 %d · 쓸 수 있는 칸 %d)'
          % (len(cmn_assign), cov_c, len(cmn_opt), n_free_cmn))

    pi = 0
    smaps, plans, syl_cell, notdef = {}, {}, {}, {}
    for sc in sorted(need):
        if only and sc != only:
            continue
        ap, tp = atlas_path(sc), tbl_path(sc)
        if not (os.path.exists(ap) and os.path.exists(tp)):
            print('★%s 아틀라스/표 없음 — 건너뜀' % sc)
            continue
        a = Atlas(pristine(ap))
        n = a.pages * CELLS_PER_PAGE
        m = ZTbl(pristine(tp)).mapping()
        prot = {slot(sc, m[c], n) for c in keepch.get(sc, ()) if c in m}
        # ★notdef·시스템 글리프 칸 보호 (자기 표 + 공용 표 둘 다에서)
        prot |= {slot(sc, m[c], n) for c in SYSTEM_GLYPHS if c in m}
        if sc == 'Common':
            prot |= {cmn_map[c] for c in SYSTEM_GLYPHS
                     if c in cmn_map and cmn_map[c] < n}
            prot |= {cmn_map[c] for c in keep_all if c in cmn_map and cmn_map[c] < n}
        prot.discard(None)
        if sc not in posmap:
            prot.add(0)
        # ★잉크가 «많은» 칸부터 덮는다.
        #   단순한 기호·가나 칸부터 덮으면 복잡한 한자가 그대로 남아
        #   PCMP 재압축이 원본 크기를 넘는다(Common 에서 +6,213 B 났다).
        # ★위치표를 쓰는 장면은 «실측한 자리»만 후보다. 나머지는 손대지 않는다.
        allslots = (sorted(set(posmap[sc].values())) if sc in posmap
                    else list(range(n)))
        cells = sorted((g for g in allslots if g not in prot),
                       key=lambda g: -ink_of(a, g))
        # ★★자주 쓰는 음절부터 칸을 준다.
        #   ⛔가나다순으로 주면 칸이 모자랄 때 «많이 쓰는 글자»가 밀려 ■ 가 된다
        #     (2026-08-31 실기: 주메뉴의 「체험」이 「체■」으로 나왔다).
        syl = sorted(need[sc], key=lambda c: (-freq.get(sc, {}).get(c, 0), c))
        # ⛔칸이 모자라도 멈추지 않는다 — 못 덮는 음절은 «표에 없는 코드»로 내보내
        #   화면에 정직하게 ■(notdef) 로 나오게 한다. 틀린 글자보다 낫다.
        # ★★칸에 «이미 붙어 있는» 코드를 우선 재사용한다.
        #   2026-08-30 실기: 표를 안 건드리고 기존 코드만 쓴 빌드는 메뉴가 정상이었는데,
        #   새 코드를 만들어 표에 써넣은 빌드는 메뉴가 빈칸이었다.
        #   기존 (코드->칸) 쌍은 게임이 실제로 쓰는 게 증명된 것이다.
        #   ★단 «Common 이 아닌» 장면은 공용 표에 없는 코드를 써야 한다.
        #     흔한 가나·한자는 공용 표에도 있어서, 게임이 공용을 먼저 조회하면
        #     공용 쪽 칸이 나와 «외계어»가 된다(2026-08-30 인게임 실기).
        bycell = {}
        for ch0, g0 in m.items():
            if ch0 in keep_all:
                continue
            if sc != 'Common' and ch0 in cmn_map:
                continue
            sl0 = slot(sc, g0, n)
            if sl0 is None:
                continue
            bycell.setdefault(sl0, []).append(ch0)
        smap, plan = {}, {}
        # ★공용 아틀라스에는 «전역 배정»을 통째로 칠한다(다른 장면이 그 칸을 본다).
        if sc == 'Common':
            for g, s in cmn_assign.items():
                plan[g] = (s, next(iter(cmn_opt[g].values())))

        # (a) 1순위 — 전역 공용 칸. 그 장면 «원문이 쓰는» 문자로 조회한다.
        cmn_here = {}
        for g, s in cmn_assign.items():
            c0 = cmn_opt.get(g, {}).get(sc)
            if c0 is not None:
                cmn_here.setdefault(s, c0)
        # (b) 2순위 — 그 장면 원문이 쓰는 «장면 전용» 문자.
        opts = {g: c for g, c in sc_opt.get(sc, {}).items() if g not in prot}
        free_text = sorted(opts, key=lambda g: -ink_of(a, g))

        nc = ns = fb = 0
        rest = []
        cell_of = {}                    # 음절 -> ('Common'|장면, 칸)
        cmn_cell_of = {s: g for g, s in cmn_assign.items()}
        for s in syl:
            if s in cmn_here:
                smap[s] = cmn_here[s]
                cell_of[s] = ('Common', cmn_cell_of[s])
                nc += 1
            else:
                rest.append(s)
        left = []
        for s in rest:
            if free_text:
                g = free_text.pop(0)
                smap[s] = opts[g]
                plan[g] = (s, opts[g])
                cell_of[s] = (sc, g)
                ns += 1
            else:
                left.append(s)
        # (c) 마지막 수단 — 원문 밖 코드. 그 화면에서 ■ 로 나올 수 있다.
        if left:
            taken = set(plan) | prot
            spare = sorted((g for g in allslots if g not in taken),
                           key=lambda g: -ink_of(a, g))
            # ★위치표 장면(Menu)은 «칸 번호»를 몰라 표를 못 고친다.
            #   그래서 그 칸을 이미 가리키는 코드가 있어야만 쓸 수 있다.
            #   없는 칸에 새 코드를 붙이면 그 코드는 표에 없어 ■ 가 되고,
            #   칠한 칸은 헛수고가 된다.
            # ★칸을 가리키는 «기존 코드»가 있는 칸만 쓴다.
            #   ⛔새 코드(pool)를 지어 붙이면 그 코드는 어느 표에도 없어 게임이
            #     시스템 폰트로 그 한자를 그린다(2026-08-31 실기, 254곳).
            #   ★★단 «원문에 있는 코드만» 쓰게 조이면 안 된다 — 공용 장면이 그 길로
            #     93음절을 그리고 있었고, 막았더니 주메뉴에 ■ 가 떴다(실기 19:22).
            #     기존 코드는 그 장면 표에 있으므로 최악이라야 ■ 다.
            # ★★칸 번호가 «정수»인 장면(1쪽짜리)은 표를 고칠 수 있으므로 새 코드를 붙여도
            #   그 코드가 표에 들어가 정상으로 그려진다(실기: 무비·스테이지·주메뉴).
            #   ⛔반면 «좌표»로 다루는 장면(도감/Menu, 4쪽)은 칸 번호를 몰라 표를 못 고친다.
            #     거기에 새 코드를 붙이면 어느 표에도 없어 시스템 폰트 한자가 튀어나온다.
            #     그래서 도감만 «이미 그 칸을 가리키는 코드»가 있는 칸으로 제한한다.
            spare = [g for g in spare if isinstance(g, int) or bycell.get(g)]
            for s, g in zip(left, spare):
                have = [c for c in bycell.get(g, ()) if c in used.get(sc, ())] \
                    or bycell.get(g)
                ch = have[0] if have else pool[pi]
                if not have:
                    pi += 1
                smap[s] = ch
                plan[g] = (s, ch)
                cell_of[s] = (sc, g)
                fb += 1
            left = left[len(spare):]
        # ★자리를 못 받은 음절 — 어느 표에도 없는 코드를 줘서 ■ 로 나오게 한다.
        # ★★★풀은 «공용 표»만 피해서는 안 된다 — 그 장면 «자기 표»도 피해야 한다.
        #   2026-08-31 실기: 도감에 各·液·扱·偉·案·央·關·衛 같은 한자가 그대로 떴다.
        #   Menu 표에 있는 코드를 골라 준 탓이다(그 칸은 위치를 몰라 못 칠한다).
        #   ⇒ 두 표 어디에도 없는 코드라야 진짜 notdef(■) 로 나온다.
        # ★★★2026-08-31 실기로 확정 — «화면에 안 나오게» 하는 코드는 이것뿐이다:
        #     그 장면 «표에는 있고» · 그 장면 «원문에는 없는» 글자.
        #   ⛔어느 표에도 없는 글자를 쓰면 게임이 **시스템 폰트로 그 한자를 그린다**
        #     (도감에 界·往·偉·海·樂·握·奧·塊 가 뜬 원인).
        #   ⛔그 장면 표에 있으면서 원문에도 있는 글자는 «진짜 글리프»가 나온다.
        #   근거: 시험 빌드 1107표본 — 원문에 있음 389/394 나옴, 원문에 없음 690/713 ■.
        my_tbl = sc_tbl.get(sc, {})
        my_used = used.get(sc, set())
        #   ★가장 확실한 코드는 «■» 그 자체다 — 공용 표에서 notdef 칸(40)을 가리키고,
        #     그 칸은 절대 칠하지 않게 보호돼 있다. 장면을 안 가리고 늘 ■ 로 나온다.
        #   ⛔장면 표에서 고르면 장면마다 후보 수가 들쭉날쭉하다(Stage4 는 2개뿐이었고,
        #     keep_all 을 빼면 0 이 되어 아무 코드나 쓰다 한자가 튀어나왔다).
        nd_code = '■' if '■' in cmn_map else None
        nd_pool = [c for c in my_tbl
                   if c not in my_used and (sc == 'Common' or c not in cmn_map)
                   and c not in keep_all and c not in SYSTEM_GLYPHS]
        if nd_code:
            nd_pool = [nd_code]
        elif not nd_pool:
            nd_pool = pool
        # ★■ 코드는 «겹쳐 써도» 된다 — 어차피 다 안 보인다.
        #   ⛔하나씩 소비하면 풀이 말라 남은 음절이 시스템 폰트 한자로 튀어나온다.
        none_n, qi = 0, 0
        for s in syl:
            if s not in smap:
                smap[s] = nd_pool[qi % len(nd_pool)]
                qi += 1
                none_n += 1
        smaps[sc] = smap
        plans[sc] = plan
        syl_cell[sc] = cell_of
        # ★칸을 못 받아 화면에 ■ 로 나올 음절을 파일로 남긴다(도감 줄이기 계획용).
        notdef[sc] = sorted(s for s in smap if s not in cell_of)
        print('  %-16s 음절 %4d : 공용 %4d · 장면원문 %4d · 원문밖 %3d · ■ %3d'
              % (sc, len(syl), nc, ns, fb, none_n))

    # --- 폰트·표 ---
    print('\n폰트/표')
    for sc, plan in plans.items():
        ap, tp = atlas_path(sc), tbl_path(sc)
        rel_a = os.path.relpath(ap, ROOT)
        rel_t = os.path.relpath(tp, ROOT)
        backup(rel_a)
        backup(rel_t)
        # ★재압축이 원본 크기를 넘으면 «알파 계조»를 줄여 다시 시도한다.
        #   폰트 파일은 HDD 캐시 때문에 크기를 못 늘린다.
        blob, lv = None, None
        for levels in (0, 8, 6, 4):
            a = Atlas(os.path.join(ORIG, rel_a))
            for g, (s, ch) in plan.items():
                gl = R.glyph(s, levels=levels)
                if isinstance(g, tuple):
                    a.set_at(g[0], g[1], gl, color=True)
                else:
                    a.set_cell(g, gl, color=True)
            try:
                blob = a.to_bytes(keep_size=True)
                lv = levels
                break
            except ValueError:
                continue
        if blob is None:
            # ★HDD 캐시에 올라가는 아틀라스만 크기를 못 바꾼다(캐시는 같은 크기로만 교체).
            #   나머지는 2048 배수로 키워도 된다.
            if sc in CACHED:
                print('  ★%s 는 HDD 캐시 대상이라 크기를 못 늘린다 — 실패' % sc)
                return 1
            a = Atlas(os.path.join(ORIG, rel_a))
            for g, (s, ch) in plan.items():
                gl = R.glyph(s)
                if isinstance(g, tuple):
                    a.set_at(g[0], g[1], gl, color=True)
                else:
                    a.set_cell(g, gl, color=True)
            raw = a.to_bytes(keep_size=False)
            orig_len = len(open(os.path.join(ORIG, rel_a), 'rb').read())
            size = orig_len
            while len(raw) > size:
                size += 2048
            blob, lv = raw + bytes(size - len(raw)), -1
            print('  %-16s ★파일 확장 %d -> %d B' % (sc, orig_len, size))
        t = ZTbl(os.path.join(ORIG, rel_t))
        for g, (s, ch) in plan.items():
            if isinstance(g, int):
                t.set(ch, g)
        tb = t.to_bytes()
        print('  %-16s 아틀라스 %6d B · 표 %6d B · 칸 %4d%s'
              % (sc, len(blob), len(tb), len(plan),
                 '' if lv in (0, -1) else '  (계조 %d단계로 압축)' % lv))
        if apply:
            open(os.path.join(ROOT, rel_a), 'wb').write(blob)
            open(os.path.join(ROOT, rel_t), 'wb').write(tb)

    # --- .msg ---
    print('\n.msg')
    grown = 0
    # ★HDD 캐시에 올라간 `.msg` 목록 — 크기를 늘리면 그 구간이 갱신 안 된다
    cached_msg = set()
    _cm = os.path.join(WORK, 'hdd', 'cache_map.json')
    if os.path.exists(_cm):
        cached_msg = {r for r in json.load(open(_cm, encoding='utf-8'))
                      if r.lower().endswith('.msg')}
    for sc, rels in files.items():
        if sc not in smaps:
            continue
        sc_m = sc_tbl.get(sc, {})
        for rel in rels:
            # ★★코드는 «그 파일 원문이 쓰는 문자»로 고른다 — 화면은 파일 단위로 글자를 올린다.
            sm = dict(smaps[sc])
            by = {}
            for c in used_f.get(rel, ()):
                if c in keep_all:
                    continue
                gc = cmn_map.get(c)
                if gc is not None:
                    by.setdefault(('Common', gc), c)
                elif sc_m.get(c) is not None:
                    by.setdefault((sc, sc_m[c]), c)
            hit = 0
            for s0, key in syl_cell.get(sc, {}).items():
                if key in by:
                    sm[s0] = by[key]
                    hit += 1
            ko_idx = {int(k): v for k, v in ko.get(rel, {}).items()}
            data, orig, odd, skipped = rebuild_msg(rel, ko_idx, sm)
            data, size = fit_size(data, orig)
            tag = ''
            if size != orig:
                grown += 1
                tag = '  ★%d -> %d B' % (orig, size)
            # ★★HDD 캐시에 올라간 `.msg` 는 «크기를 늘리면 안 된다».
            #   캐시는 같은 크기로만 제자리 덮어쓸 수 있어서, 커지면 hddcache 가 건너뛰고
            #   그 구간은 «이전 빌드» 텍스트가 계속 나온다(2026-08-31 튜토리얼 +55B).
            if size != orig and rel in cached_msg:
                tag += '  ★★캐시된 파일이라 크기를 늘리면 반영 안 된다 (%d 초과)' % (
                    len(data.rstrip(b'\x00')) - orig)
            print('  %-42s %6d B%s%s' % (os.path.basename(rel), size, tag,
                  ('  (정렬 %d곳)' % odd if odd else '')
                  + ('  ★머리와 겹쳐 건너뜀 %d곳' % skipped if skipped else '')))
            if apply:
                open(os.path.join(ROOT, rel), 'wb').write(data)
    print('\n키운 파일 %d개' % grown)

    # --- ★★default.xbe 안의 «하드코딩» 문자열 ---
    #   2026-08-31 발견 — 일시정지 메뉴·시스템 대화상자·도감 라벨이 `.msg` 가 아니라
    #   실행 파일 안에 있다. 공용 폰트 칸을 덮으면 이 화면들이 같이 깨진다.
    #   NUL 종단이라 «원본보다 짧거나 같으면» 제자리 치환이 된다. 크기는 안 바뀐다.
    xc = os.path.join(TRANS, 'xbe_corpus.json')
    xk = os.path.join(TRANS, 'xbe_ko.json')
    if os.path.exists(xc) and os.path.exists(xk) and 'Common' in smaps:
        corp = json.load(open(xc, encoding='utf-8'))
        kor = json.load(open(xk, encoding='utf-8'))
        # ★코드는 «XBE 원문이 쓰는 문자» 를 우선한다(그 화면이 반드시 찾는 집합)
        uf = set()
        for e in corp:
            uf |= {c for c in e['jp'] if ord(c) > 0x7f}
        sm = dict(smaps['Common'])
        by = {}
        for c in uf:
            if c in keep_all:
                continue
            g0 = cmn_map.get(c)
            if g0 is not None:
                by.setdefault(('Common', g0), c)
        for s0, key in syl_cell.get('Common', {}).items():
            if key in by:
                sm[s0] = by[key]
        d = bytearray(open(backup('default.xbe'), 'rb').read())
        n_ok = n_over = 0
        for e in corp:
            t = kor.get(str(e['off']))
            if not t:
                continue
            try:
                b = encode(t, sm)
            except KeyError as ex:
                print('  ★%d : 폰트에 없는 음절 %s' % (e['off'], ex))
                n_over += 1
                continue
            if len(b) > e['bytes']:
                print('  ★%d : %d > %d B 넘침' % (e['off'], len(b), e['bytes']))
                n_over += 1
                continue
            d[e['off']:e['off'] + len(b)] = b
            d[e['off'] + len(b)] = 0          # ★종단자
            n_ok += 1
        print('default.xbe : %d개 치환 (넘침/불가 %d)' % (n_ok, n_over))
        if apply:
            open(os.path.join(ROOT, 'default.xbe'), 'wb').write(bytes(d))

    if apply:
        snap = {sc: {s: [ch, list(g) if isinstance(g, tuple) else g]
                     for g, (s, ch) in plan.items()}
                for sc, plan in plans.items()}
        with open(os.path.join(WORK, 'charmap_all.json'), 'w',
                  encoding='utf-8', newline='') as f:
            json.dump(snap, f, ensure_ascii=False, indent=1)
        print('배정표 -> work/charmap_all.json')
        with open(os.path.join(WORK, 'notdef.json'), 'w',
                  encoding='utf-8') as f:
            json.dump(notdef, f, ensure_ascii=False, indent=1)
        print('■ 로 나올 음절 -> work/notdef.json')
        print('\n★다음: python hddcache.py  그리고 ISO 재빌드')
    else:
        print('\n※ 검산만 했습니다. 기록하려면 --apply')
    return 0


if __name__ == '__main__':
    sys.exit(main())
