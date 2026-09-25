"""★병합 전 번역에 있던 «띄어쓰기»가 지금 빠진 자리를 전부 찾는다.

layout_scan 의 «붙음» 검사는 `[가-힣]{6,}` 만 본다. 그래서
`Tutorial1-1드래곤` 처럼 **영숫자와 한글이 맞붙은 곳**을 놓친다(2026-08-31 실기).

판정: 공백만 지운 알맹이가 같은 «병합 전» 판본을 찾아, 그쪽에만 있는 경계를 센다.
      줄바꿈 자리(우리가 `\\n` 을 넣은 곳)는 정상이므로 뺀다.

    python gapscan.py            # 목록
    python gapscan.py --fix      # trans/jam_fix.json 으로 후보를 뽑는다
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS
import check_ko as K
import splitscan as S
import unjam

H = K.HALF_SP


def half(t):
    out = []
    for ln in t.split('\n'):
        i = 0
        while i < len(ln) and ln[i] == '　':
            i += 1
        out.append(ln[:i] + ln[i:].replace(' ', H).replace(' ', H))
    return '\n'.join(out)


def main():
    dofix = '--fix' in sys.argv
    ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
    # ★★출처는 «병합 전 조각»만 쓴다.
    #   ⛔ko.json 백업까지 섞으면, 낱말이 쪼개진 판본(`부탁한\n다`)이 «공백이 제일 많은
    #     판본»으로 뽑혀 그 자리에 공백이 들어간다 -> 「부탁한 다」·「좋 아」·「사람 이다」.
    #     2026-08-31 실기 직전에 실제로 그렇게 망가뜨렸다.
    srcs = [(n, r) for n, r in unjam.load_sources() if '병합전' in n]
    fix, n, judged = {}, 0, 0
    for rel in sorted(ko):
        base = os.path.basename(rel)
        rows_out = []
        for k, t in sorted(ko[rel].items(), key=lambda x: int(x[0])):
            cand = None
            for _nm, rows in srcs:
                s = rows.get(rel, {}).get(k) or rows.get(base, {}).get(k)
                if s and S.bare(s) == S.bare(t):
                    if cand is None or len(S.gaps(s)) > len(S.gaps(cand)):
                        cand = s
            if cand is None:
                continue
            judged += 1
            # ★출처의 «줄바꿈»은 공백으로 세지 않는다 — 우리가 줄을 합친 자리다.
            miss = S.gaps(cand, nl=False) - S.gaps(t) - set(S.breaks(t))
            if not miss:
                continue
            new = half(cand)
            rows_out.append((k, t, new, len(miss), K.nbytes(new) - K.nbytes(t)))
            fix.setdefault(base, {})[k] = new
            n += len(miss)
        if rows_out:
            print('== %s (%d항목)' % (base, len(rows_out)))
            for k, t, new, m, d in rows_out:
                print('  idx %-5s 빠진공백 %d  %+3dB' % (k, m, d))
                print('     지금 %s' % t.replace(H, ' ').replace('\n', ' / '))
                print('     복원 %s' % new.replace(H, ' ').replace('\n', ' / '))
    print()
    print('판정한 항목 %d개 · 빠진 띄어쓰기 %d곳 (%d항목)'
          % (judged, n, sum(len(v) for v in fix.values())))
    if dofix:
        with open(os.path.join(TRANS, 'jam_fix.json'), 'w', encoding='utf-8') as f:
            json.dump(fix, f, ensure_ascii=False, indent=1)
        print('-> trans/jam_fix.json. 반영은 jamfix.py --apply')


if __name__ == '__main__':
    main()
