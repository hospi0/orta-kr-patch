"""★도감 ■ 음절을 «어떤 낱말에 들어 있는지»로 분류한다 — 줄이기 작업용.

원칙(사용자 지시 2026-08-31): **고유명사는 되도록 건드리지 않는다.**
어간·어미·흔한 한자어 쪽에서 먼저 찾는다.

분류
  · 제목  : `＜…＞` 안 — 대개 고유명사다. 손대지 않는다.
  · 이름  : 원문이 가타카나였던 자리(음역어) — 고유명사일 가능성이 높다.
  · 본문  : 나머지. 여기서 고른다.

    python dbcut.py            # ■ 음절 목록(싼 순)
    python dbcut.py --words    # 음절마다 들어 있는 낱말까지
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
KATA = re.compile(r'[゠-ヿ]{2,}')


def load():
    ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
    corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
    nd = set(json.load(open(os.path.join(WORK, 'notdef.json'),
                            encoding='utf-8'))['Menu'])
    rows = []
    for rel in sorted(ko):
        if K.scene_of(rel) != 'Menu':
            continue
        jp = {e['idx']: e['jp'] for e in corpus[rel]}
        for k, t in ko[rel].items():
            rows.append((os.path.basename(rel), int(k), t, jp.get(int(k), '')))
    return nd, rows


def kind(t, jp, word):
    """그 낱말이 제목/이름/본문 중 무엇인가."""
    head = CODE.sub('', t).split('\n')[0]
    if word in head and ('＜' in head or '<' in head):
        return '제목'
    if KATA.search(jp or ''):
        # 원문에 가타카나가 많으면 음역 고유명사가 섞여 있다
        if len(KATA.findall(jp)) >= 2:
            return '이름?'
    return '본문'


def main():
    nd, rows = load()
    cnt = collections.Counter()
    words = collections.defaultdict(collections.Counter)
    kinds = collections.defaultdict(collections.Counter)
    for _f, _i, t, jp in rows:
        clean = CODE.sub('', t)
        for ch in clean:
            if ch in nd:
                cnt[ch] += 1
        for m in WORD.finditer(clean.replace('\n', ' ')):
            w = m.group()
            for ch in set(w) & nd:
                words[ch][w] += 1
                kinds[ch][kind(t, jp, w)] += 1
    # ★이미 치환으로 사라진 음절은 뺀다(빌드 없이도 남은 목록을 알 수 있어야 한다)
    nd = {c for c in nd if cnt[c]}
    print('아직 남은 ■ 음절 %d개 · 총 %d자' % (len(nd), sum(cnt[c] for c in nd)))
    print()
    show = '--words' in sys.argv
    body_only = []
    for ch in sorted(nd, key=lambda c: (cnt[c], c)):
        kk = kinds[ch]
        tag = '제목' if kk.get('제목') and not kk.get('본문') else (
            '이름?' if kk.get('이름?') and not kk.get('본문') else '본문')
        if tag == '본문':
            body_only.append(ch)
        if show:
            ws = ' '.join('%s×%d' % (w, n) if n > 1 else w
                          for w, n in words[ch].most_common(6))
            print('  %s %-5s %2d회 : %s' % (ch, tag, cnt[ch], ws))
    if not show:
        print('  ' + ' '.join('%s(%d)' % (c, cnt[c])
                              for c in sorted(nd, key=lambda c: (cnt[c], c))))
    print()
    print('본문에만 나오는(=고쳐도 고유명사를 안 건드리는) 음절 %d개 / %d'
          % (len(body_only), len(nd)))
    print('  누적 고칠 글자 %d자' % sum(cnt[c] for c in body_only))


if __name__ == '__main__':
    main()
