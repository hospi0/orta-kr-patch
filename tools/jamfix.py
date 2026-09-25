"""붙은 줄의 «띄어쓰기 복원»을 반영한다.

`trans/jam_fix.json` = {파일명조각: {idx: 고친문장}}  (파일명은 basename 으로 찾는다)

반영 전에 검사한다:
  · 제어코드(`$c0` `$w0240`)가 원문과 같은가
  · cp932 로 못 넣는 문자가 없는가
  · Common 장면이면 «음절 수요»가 칸 수를 넘지 않는가
반영 뒤에는 `reflow.py` 로 줄을 다시 맞추면 된다.

    python jamfix.py            # 검산만
    python jamfix.py --apply
"""
import json
import os
import re
import shutil
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS
import check_ko as K

KO = os.path.join(TRANS, 'ko.json')
FIX = os.path.join(TRANS, 'jam_fix.json')
CODE = re.compile(r'\$[cw]\d+|%[si]\d')
CAP_COMMON = 274


def main():
    apply = '--apply' in sys.argv
    corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
    ko = json.load(open(KO, encoding='utf-8'))
    fix = json.load(open(FIX, encoding='utf-8'))

    bykey = {}
    for rel in corpus:
        bykey[os.path.basename(rel)] = rel

    n = bad = 0
    for frag, d in fix.items():
        rel = bykey.get(frag) or next((r for r in corpus if frag in r), None)
        if rel is None:
            print('★파일 못 찾음: %s' % frag)
            bad += 1
            continue
        jp = {str(e['idx']): e['jp'] for e in corpus[rel]}
        for k, t in d.items():
            old = ko.get(rel, {}).get(k)
            if old is None:
                print('★%s idx%s : 기존 번역 없음' % (frag, k))
                bad += 1
                continue
            if sorted(CODE.findall(t)) != sorted(CODE.findall(jp.get(k, ''))):
                print('★%s idx%s : 제어코드 불일치 %s vs 원문 %s'
                      % (frag, k, CODE.findall(t), CODE.findall(jp.get(k, ''))))
                bad += 1
                continue
            bc = K.bad_chars(t)
            if bc:
                print('★%s idx%s : 쓸 수 없는 문자 %s' % (frag, k, bc))
                bad += 1
                continue
            n += 1
            if apply:
                ko[rel][k] = t
    print('고칠 항목 %d개 · 문제 %d건' % (n, bad))

    # 반영본 기준으로 Common 수요 재계산
    tmp = json.loads(json.dumps(ko))
    if not apply:
        for frag, d in fix.items():
            rel = bykey.get(frag) or next((r for r in corpus if frag in r), None)
            if rel:
                for k, t in d.items():
                    if k in tmp.get(rel, {}):
                        tmp[rel][k] = t
    cnt = collections.Counter()
    for rel in corpus:
        if K.scene_of(rel) != 'Common':
            continue
        for e in corpus[rel]:
            t = tmp.get(rel, {}).get(str(e['idx']))
            if t:
                cnt.update(c for c in t if K.is_hangul(c))
    xk = os.path.join(TRANS, 'xbe_ko.json')
    if os.path.exists(xk):
        for t in json.load(open(xk, encoding='utf-8')).values():
            cnt.update(c for c in t if K.is_hangul(c))
    print('Common 음절 수요 %d / 칸 %d%s'
          % (len(cnt), CAP_COMMON,
             '  ★%d개 초과' % (len(cnt) - CAP_COMMON) if len(cnt) > CAP_COMMON else ''))

    if apply and not bad:
        bak = KO + '.bak_jam'
        i = 0
        while os.path.exists(bak):
            i += 1
            bak = KO + '.bak_jam%d' % i
        shutil.copy2(KO, bak)
        with open(KO, 'w', encoding='utf-8', newline='') as f:
            json.dump(ko, f, ensure_ascii=False, indent=1)
        print('백업 %s · 적용 완료' % os.path.basename(bak))
    elif not apply:
        print('※ 검산만. 반영하려면 --apply')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
