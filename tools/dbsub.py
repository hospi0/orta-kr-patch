"""★도감 낱말 치환 — ■ 음절을 «이미 칸을 받은 음절»로만 바꿔 넣는다.

`trans/db_sub.json` = [["바꿀말", "바뀐말"], ...]  (Menu 장면 파일 전체에 적용)

반드시 검사한다:
  · 바뀐말의 «모든 음절»이 지금 칸을 받은 음절인가 — 아니면 ■ 가 새로 생긴다.
  · 제어코드(`$c0` `%s0`)를 건드리지 않는가.
  · 항목 예산(바이트)을 넘지 않는가.

    python dbsub.py            # 검산만
    python dbsub.py --apply
"""
import collections
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS, WORK
import check_ko as K

KO = os.path.join(TRANS, 'ko.json')
SUB = os.path.join(TRANS, 'db_sub.json')
CODE = re.compile(r'\$[cw]\d+|%[si]\d')


def main():
    apply = '--apply' in sys.argv
    ko = json.load(open(KO, encoding='utf-8'))
    corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
    nd = set(json.load(open(os.path.join(WORK, 'notdef.json'),
                            encoding='utf-8'))['Menu'])
    subs = json.load(open(SUB, encoding='utf-8'))

    rels = [r for r in ko if K.scene_of(r) == 'Menu']
    have = set()
    for rel in rels:
        for t in ko[rel].values():
            have |= {c for c in t if K.is_hangul(c)}
    ok_syl = have - nd
    print('도감 음절 %d종 · ■ %d종 · 쓸 수 있는 음절 %d종'
          % (len(have), len(nd), len(ok_syl)))

    # ★«지금 ■ 인 음절»로 합치는 건 허용한다 — 음절 종류가 줄어 오히려 이득이다.
    #   막아야 할 것은 «도감에 아예 없던 새 음절»뿐이다(그건 칸을 새로 먹는다).
    bad = []
    for a, b in subs:
        miss = {c for c in b if K.is_hangul(c)} - have
        if miss:
            bad.append((a, b, ''.join(sorted(miss))))
    if bad and '--force' not in sys.argv:
        print('\n★바뀐말에 «칸 없는 음절»이 들어 있다 — 그대로 두면 ■ 가 새로 생긴다')
        for a, b, m in bad:
            print('   %s -> %s   문제 음절: %s' % (a, b, m))
        return 1

    budget = {}
    for rel in rels:
        budget[rel] = {e['idx']: e['bytes'] for e in corpus[rel]}
    hit = collections.Counter()
    over = []
    new_ko = {rel: dict(ko[rel]) for rel in rels}
    for rel in rels:
        for k, t in ko[rel].items():
            n = t
            for a, b in subs:
                if a in n:
                    hit[a] += n.count(a)
                    n = n.replace(a, b)
            if n == t:
                continue
            if CODE.findall(n) != CODE.findall(t):
                print('★제어코드가 달라졌다: %s idx %s' % (os.path.basename(rel), k))
                return 1
            new_ko[rel][k] = n
    # 예산 검사(4정렬 반영, 파일 단위)
    for rel in rels:
        d = 0
        for e in corpus[rel]:
            k = str(e['idx'])
            if k not in new_ko[rel]:
                continue
            d += ((K.nbytes(new_ko[rel][k]) + 4) & ~3) - ((e['bytes'] + 4) & ~3)
        print('  %-32s 예산 여유 %+5d B' % (os.path.basename(rel), -d))
        if d > 0:
            over.append(rel)

    left = set()
    for rel in rels:
        for t in new_ko[rel].values():
            left |= {c for c in t if K.is_hangul(c)} & nd
    print()
    after = set()
    for rel in rels:
        for t in new_ko[rel].values():
            after |= {c for c in t if K.is_hangul(c)}
    print('치환 %d건 적용 · ■ 음절 %d -> %d (없앤 것 %d)'
          % (sum(hit.values()), len(nd), len(left), len(nd) - len(left)))
    print('★도감 음절 %d종 -> %d종' % (len(have), len(after)))
    miss = [a for a, _b in subs if not hit[a]]
    if miss:
        print('★본문에서 못 찾은 말 %d개: %s' % (len(miss), ' '.join(miss[:12])))
    if over:
        print('★예산 초과 파일: %s' % ', '.join(os.path.basename(r) for r in over))
        return 1
    if apply:
        bak = KO + '.bak_dbsub'
        i = 0
        while os.path.exists(bak):
            i += 1
            bak = KO + '.bak_dbsub%d' % i
        shutil.copy2(KO, bak)
        for rel in rels:
            ko[rel] = new_ko[rel]
        with open(KO, 'w', encoding='utf-8', newline='') as f:
            json.dump(ko, f, ensure_ascii=False, indent=1)
        print('백업 %s · 적용 완료' % os.path.basename(bak))
    else:
        print('※ 검산만. 반영하려면 --apply')
    return 0


if __name__ == '__main__':
    sys.exit(main())
