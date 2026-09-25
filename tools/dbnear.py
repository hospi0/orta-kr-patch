"""★★■ 음절을 «비슷한 음절»로 갈아 끼우는 후보를 뽑는다.

낱말을 통째로 바꾸는 것보다 싸고, 고유명사도 표기만 살짝 바꿔 살릴 수 있다.
  플뤼게 -> 플리게 · 셸쿠프 -> 셀쿠프 · 카챠피 -> 카차피

가까운 순서(위쪽이 더 자연스럽다)
  1. 받침만 뗀다            껏 -> 거
  2. 겹받침·된받침을 홑으로  깝 -> 갑 · 았 -> 앗
  3. 이중모음을 단모음으로   챠 -> 차 · 셸 -> 셀 · 뤼 -> 리
  4. 비슷한 모음으로        뎌 -> 더 · 웠 -> 았

    python dbnear.py            # ■ 음절마다 «쓸 수 있는» 후보
    python dbnear.py --sub      # 바로 db_sub.json 에 넣을 낱말 치환으로 출력
"""
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS, WORK
import check_ko as K

CODE = re.compile(r'\$[cw]\d+|%[si]\d')
WORD = re.compile(r'[가-힣]+')
BASE = 0xAC00
JONG = 28
JUNG = 21

# 이중모음 -> 단모음 (자연스러운 순서)
VOWEL = {
    2: [0], 3: [0, 2],          # ㅑ->ㅏ, ㅒ->ㅐ,ㅑ
    6: [4], 7: [4, 5, 6],       # ㅕ->ㅓ, ㅖ->ㅔ
    9: [8, 0], 10: [8, 1], 11: [8, 5],   # ㅘ->ㅗ/ㅏ, ㅙ->ㅗ/ㅐ, ㅚ->ㅗ/ㅔ
    12: [8],                    # ㅛ->ㅗ
    14: [13, 4], 15: [13, 5], 16: [13, 20],  # ㅝ ㅞ ㅟ
    17: [13],                   # ㅠ->ㅜ
    19: [20, 18],               # ㅢ->ㅣ/ㅡ
}
# 된받침·겹받침 -> 홑받침
JONGS = {1: [0], 2: [1, 0], 3: [1, 0], 4: [0], 5: [4, 0], 6: [4, 0],
         7: [0], 8: [8, 0], 9: [8, 0], 10: [8, 0], 11: [8, 0], 12: [8, 0],
         13: [8, 0], 14: [8, 0], 15: [8, 0], 16: [16, 0], 17: [0],
         18: [0], 19: [19, 0], 20: [19, 0], 21: [0], 22: [0], 23: [0],
         24: [0], 25: [0], 26: [0], 27: [0]}


def parts(ch):
    c = ord(ch) - BASE
    return c // (JUNG * JONG), (c // JONG) % JUNG, c % JONG


def make(cho, jung, jong):
    return chr(BASE + (cho * JUNG + jung) * JONG + jong)


def cands(ch):
    """«표기만» 바뀌는 후보 — 모음만 갈아 끼운다.

    ⛔받침을 떼면 낱말이 깨진다(힘껏 -> 힘꺼). 그건 후보가 아니다.
      이 방식은 외래어·이름 표기를 살짝 바꿔 살리는 용도다(셸쿠프 -> 셀쿠프).
    """
    cho, jung, jong = parts(ch)
    out = []
    for v in VOWEL.get(jung, []):
        out.append(make(cho, v, jong))
    seen, res = set(), []
    for c in out:
        if c != ch and c not in seen:
            seen.add(c)
            res.append(c)
    return res


def main():
    ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
    nd = set(json.load(open(os.path.join(WORK, 'notdef.json'),
                            encoding='utf-8'))['Menu'])
    rels = [r for r in ko if K.scene_of(r) == 'Menu']
    have = set()
    words = collections.defaultdict(collections.Counter)
    cnt = collections.Counter()
    for rel in rels:
        for t in ko[rel].values():
            clean = CODE.sub('', t)
            have |= {c for c in clean if K.is_hangul(c)}
            for ch in clean:
                if ch in nd:
                    cnt[ch] += 1
            for m in WORD.finditer(clean.replace('\n', ' ')):
                for ch in set(m.group()) & nd:
                    words[ch][m.group()] += 1
    nd = {c for c in nd if cnt[c]}
    ok = have - nd
    hit, miss = [], []
    for ch in sorted(nd, key=lambda c: (cnt[c], c)):
        good = [c for c in cands(ch) if c in ok]
        (hit if good else miss).append((ch, good))
    print('남은 ■ %d개 · 비슷한 음절로 갈아 끼울 수 있는 것 %d개 / 낱말을 바꿔야 하는 것 %d개'
          % (len(nd), len(hit), len(miss)))
    print()
    if '--sub' in sys.argv:
        subs = []
        for ch, good in hit:
            for w, _n in words[ch].items():
                subs.append([w, w.replace(ch, good[0])])
        print(json.dumps(subs, ensure_ascii=False, indent=1))
        return
    print('■ %-3s %-4s %-14s %s' % ('', '횟수', '후보(쓸 수 있는 것)', '나오는 낱말'))
    for ch, good in hit:
        ws = ' '.join(list(words[ch])[:3])
        print('  %s %3d회  %-12s %s' % (ch, cnt[ch], ' '.join(good[:4]), ws))
    print()
    print('--- 비슷한 음절이 없어 낱말을 바꿔야 하는 것 %d개' % len(miss))
    for ch, _g in miss:
        ws = ' '.join(list(words[ch])[:3])
        print('  %s %3d회  %s' % (ch, cnt[ch], ws))


if __name__ == '__main__':
    main()
