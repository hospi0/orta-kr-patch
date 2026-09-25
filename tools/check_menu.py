"""번역문 검사 — 음절 수요, 슬롯, 문자열별 바이트 예산. ★빌드 전 필수."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'trans'))
from Text_MenuInst_ko import KO                      # noqa: E402
from budget_menu import entries                      # noqa: E402
from alloc import allocate, build_pool               # noqa: E402
from ztbl import ZTbl                                # noqa: E402
from project import FONT_DIR, COMMON_TBL, scene_tbl  # noqa: E402


def is_hangul(c):
    return 0xac00 <= ord(c) <= 0xd7a3


def syllables():
    """등장 순서대로 고유 음절."""
    s = []
    for i in sorted(KO):
        if not KO[i]:
            continue
        for c in KO[i]:
            if is_hangul(c) and c not in s:
                s.append(c)
    return s


# ★원문 실측: 반각 영문자·문장부호(E O I S A D P N R H Y L " T , V G B 6 /)는
#   원문 17줄이 실제로 쓴다 ⇒ 그대로 써도 안전하다.
#   딱 하나 **반각 공백(0x20)만 원문에 한 번도 안 나온다** ⇒ 전각 공백으로 바꾼다.
_FW = {' ': '　', '.': '。'}   # ★반각 마침표는 앞 글자에 달라붙어 «찌꺼기 점»처럼 보인다


def to_full(c):
    return _FW.get(c, c)


HALF_SP = ' '       # 본문에 쓰는 «반각 공백» 표식 (1바이트로 나간다)


def _enc(t, smap):
    out = bytearray()
    for c in t:
        if c == '\n':
            out.append(0x0A)
        elif c == HALF_SP:
            out.append(0x20)
        elif is_hangul(c):
            out += smap[c].encode('cp932')
        else:
            out += to_full(c).encode('cp932')
    return bytes(out)


def encode(t, smap, width=None):
    """번역문 -> 기록할 바이트.

    ★★width 를 주면 «정확히» 그 길이로 맞춘다.
      짧게 쓰고 널로 패딩하면 널 개수가 늘어 **그 뒤 문자열 색인이 전부 밀린다**
      → [[feedback_nul_padding_shifts_string_index]]
    ★★채움 공백은 «마지막 줄의 앞뒤로 나눠» 넣는다.
      뒤에만 붙이면 게임이 그 공백까지 세어 가운데 맞춤을 하므로 그 줄만 왼쪽으로 밀린다.
    """
    out = _enc(t, smap)
    if width is None:
        return out
    gap = width - len(out)
    if gap < 0:
        raise ValueError('예산 초과: %d > %d' % (len(out), width))
    n_full, odd = divmod(gap, 2)
    lead = n_full // 2
    trail = n_full - lead
    lines = t.split('\n')
    lines[-1] = '　' * lead + lines[-1] + '　' * trail
    out = _enc('\n'.join(lines), smap)
    if odd:
        out += b'\x20'
    return out


def raw_len(t, smap):
    return len(encode(t, smap))


def fit(t, budget, smap):
    """예산에 맞을 때까지 «순서대로» 줄인다. 줄인 내용을 함께 돌려준다.

    ★규칙([[feedback_no_space_after_punct]]): 지우는 건 «줄 끝»만.
      문장 «중간»의 부호는 지우지 않는다 — 지우면 낱말이 붙어 못 읽는다.
      ① 줄 끝 마침표(1B)  ② 부호 뒤 공백(2B)  ③ 뒤에서부터 공백(2B)
    """
    log = []
    if raw_len(t, smap) <= budget:
        return t, log

    lines = t.split('\n')
    for i in range(len(lines) - 1, -1, -1):          # ① 줄 끝 마침표
        if raw_len('\n'.join(lines), smap) <= budget:
            break
        if lines[i].endswith(('.', '。')):
            lines[i] = lines[i][:-1]
            log.append('마침표')
    t = '\n'.join(lines)

    # ② ★공백을 «지우지 말고» 전각(2B) -> 반각(1B) 으로 바꾼다. 낱말은 그대로 떨어진다.
    #    원문이 반각 영문자를 쓰므로 반각 경로 자체는 안전하다.
    while raw_len(t, smap) > budget:
        j = t.rfind(' ')
        if j < 0:
            break
        t = t[:j] + HALF_SP + t[j + 1:]
        log.append('반각공백')

    while raw_len(t, smap) > budget:                 # ③ 최후 수단 — 공백 삭제
        j = t.rfind(HALF_SP)
        if j < 0:
            break
        t = t[:j] + t[j + 1:]
        log.append('공백삭제')
    return t, log


def prepare(persist=False):
    syl = syllables()
    st, short = allocate(syl, persist=persist)
    smap = {s: v[0] for s, v in st['map'].items()}
    return syl, st, short, smap


if __name__ == '__main__':
    d, es = entries()
    pool = build_pool()
    syl, st, short, smap = prepare(persist=False)
    nf = sum(1 for s, v in st['map'].items() if v[2] == 'free')
    print('필요 음절 %d / 슬롯 풀 %d  (배정: 빈 칸 %d, 한자 칸 %d)  부족 %d'
          % (len(syl), len(pool), nf, len(st['map']) - nf, len(short)))

    cm = ZTbl(os.path.join(FONT_DIR, COMMON_TBL)).mapping(drop_sentinel=False)
    mm = ZTbl(scene_tbl('Menu')).mapping(drop_sentinel=False)
    missing = set()
    for i in sorted(KO):
        if not KO[i]:
            continue
        for c in KO[i]:
            if c == '\n' or is_hangul(c) or ord(c) < 0x80:
                continue
            if c not in cm and c not in mm:
                missing.add(c)
    print('폰트에 없는 전각 문자: %s' % (''.join(sorted(missing)) or '없음'))

    over = []
    for i, e in enumerate(es):
        t = KO.get(i)
        if not t:
            continue
        b = encode(t, smap)
        if len(b) > e['bytes']:
            over.append((i, len(b), e['bytes'], t.replace('\n', '\\n')))
    print('\n예산 초과 %d건' % len(over))
    for i, got, cap, t in over:
        print('  %3d  %3d > %3d  %s' % (i, got, cap, t))
    sys.exit(1 if (over or short or missing) else 0)
