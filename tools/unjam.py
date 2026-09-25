"""★★붙어 버린 문장의 띄어쓰기·마침표를 «병합 전 원본»에서 되살린다.

배경: 예산이 빠듯한 줄 알고 공백과 줄 끝 마침표를 기계적으로 지운 판본이 지금 ko.json 이다.
      `my files/번역/part_*.json` (병합 전 조각)에는 **원래 문장이 그대로** 남아 있다.

안전 규칙(이것만 지키면 나중에 손본 것을 되돌리지 않는다):
  · «공백·줄바꿈·마침표를 모두 지운 알맹이»가 완전히 같을 때만 바꾼다.
    글자가 하나라도 다르면 그 뒤에 고친 것이므로 **건드리지 않는다**(예: 판저 -> 팬저).
  · 제어코드(`$c0` `$w0240`)도 같아야 한다.
  · 후보가 여럿이면 «공백이 가장 많은» 판본을 쓴다.

되살린 뒤에는 `reflow.py` 로 줄 수를 원문에 맞춘다.

    python unjam.py            # 검산만
    python unjam.py --apply
"""
import glob
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS

KO = os.path.join(TRANS, 'ko.json')
# ★1순위 출처 = «병합 전» 번역 조각
PARTS = os.path.join(os.path.dirname(TRANS), 'my files', '번역')
WS = re.compile(r'[\s 　]+')
CODE = re.compile(r'\$[cw]\d+|%[si]\d')
SP = (' ', ' ', '　')


def key(t):
    """공백·줄바꿈·마침표를 지운 «알맹이». 이게 같아야 같은 문장이다.

    ⛔마침표까지 지우는 이유 — 예산을 줄이려고 줄 끝 마침표를 지운 게 현재본이다.
      공백만 지우고 비교하면 그런 항목이 전부 «다른 문장»으로 잡혀 못 되살린다.
    """
    return WS.sub('', t).replace('.', '').replace('。', '')


def nsp(t):
    return sum(t.count(c) for c in SP)


def jammed(t, lo=None):
    # ★기준을 12자로 두면 「각하!휴지상태였던생명로가…」 같은 8~11자 붙음을 놓친다.
    #   그러면 줄바꿈할 자리가 없어 조판이 이상해진다. 기본 6자.
    if lo is None:
        lo = int(next((a.split('=')[1] for a in sys.argv if a.startswith('--min=')), 6))
    for ln in CODE.sub('', t).split('\n'):
        for m in re.finditer(r'[가-힣]+', ln):
            if len(m.group()) >= lo:
                return True
    return False


def load_sources():
    """[(이름, {파일: {idx: 번역}})] — 병합 전 조각을 앞에, 백업을 뒤에."""
    out = []
    rows = {}
    for p in sorted(glob.glob(os.path.join(PARTS, '*.json'))):
        try:
            data = json.load(open(p, encoding='utf-8'))
        except Exception:
            continue
        for e in data:
            ko = e.get('ko')
            if ko:
                rows.setdefault(e['file'], {})[str(e['idx'])] = ko
    if rows:
        out.append(('병합전 조각', rows))
    for p in sorted(glob.glob(KO + '.bak*')):
        try:
            out.append((os.path.basename(p), json.load(open(p, encoding='utf-8'))))
        except Exception:
            pass
    return out


def main():
    apply = '--apply' in sys.argv
    ko = json.load(open(KO, encoding='utf-8'))
    src = load_sources()
    print('출처 %d개: %s' % (len(src), ', '.join(s[0] for s in src)))

    n_fix = n_skip = 0
    used = {}
    for rel, d in ko.items():
        for k, t in list(d.items()):
            if not jammed(t):
                continue
            best, bestn, bestname = None, nsp(t), None
            for name, b in src:
                o = b.get(rel, {}).get(k)
                if o is None or key(o) != key(t):
                    continue
                if CODE.findall(o) != CODE.findall(t):
                    continue
                if nsp(o) > bestn:
                    best, bestn, bestname = o, nsp(o), name
            if best is None:
                n_skip += 1
                continue
            n_fix += 1
            used[bestname] = used.get(bestname, 0) + 1
            if apply:
                d[k] = best
    print('되살릴 수 있는 항목 %d개 · 못 찾은 항목 %d개' % (n_fix, n_skip))
    for k2, v2 in sorted(used.items(), key=lambda kv: -kv[1]):
        print('   %-16s %d건' % (k2, v2))
    if apply and n_fix:
        bak = KO + '.bak_unjam'
        i = 0
        while os.path.exists(bak):
            i += 1
            bak = KO + '.bak_unjam%d' % i
        shutil.copy2(KO, bak)
        with open(KO, 'w', encoding='utf-8', newline='') as f:
            json.dump(ko, f, ensure_ascii=False, indent=1)
        print('백업 %s · 적용 완료' % os.path.basename(bak))
    elif not apply:
        print('※ 검산만. 반영하려면 --apply')


if __name__ == '__main__':
    main()
