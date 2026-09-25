"""번역된 조각을 모아 `trans/ko.json` 하나로 병합한다.

사용:
    python merge_ko.py "..\\my files\\번역"        # 그 폴더의 part_*.json 을 병합
    python merge_ko.py <폴더> --replace           # 기존 ko.json 을 버리고 새로 만든다

`trans/ko.json` = { 파일경로: { "항목번호": "번역문" } }   ← 빌더·검사기의 유일한 원본

★대조 검사
  · (file, idx) 가 코퍼스에 실제로 있는가
  · 조각의 `jp` 가 코퍼스의 원문과 «같은가» — 다르면 낡은 조각이다
  · 같은 항목이 두 번 나오면서 번역이 다르면 경고
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS

CORPUS = os.path.join(TRANS, 'corpus.json')
OUT = os.path.join(TRANS, 'ko.json')


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    src = sys.argv[1]
    replace = '--replace' in sys.argv

    corpus = json.load(open(CORPUS, encoding='utf-8'))
    index = {(rel, e['idx']): e for rel in corpus for e in corpus[rel]}

    ko = {} if replace or not os.path.exists(OUT) else json.load(
        open(OUT, encoding='utf-8'))

    # ★폴더 대신 «파일 여러 개»도 받는다.
    #   이미 병합·보정한 조각을 다시 넣으면 fix_ko 의 예산 조정이 되돌아가므로,
    #   새로 온 조각만 골라 넣을 수 있어야 한다.
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    files = []
    for a in args:
        if os.path.isdir(a):
            files += sorted(glob.glob(os.path.join(a, 'part_*.json')))
        elif os.path.isfile(a):
            files.append(a)
    if not files:
        print('조각을 못 찾았습니다: %s' % ' '.join(args))
        return 1

    added = skipped = mismatch = missing = conflict = 0
    for p in files:
        data = json.load(open(p, encoding='utf-8'))
        n = 0
        for it in data:
            key = (it['file'], it['idx'])
            if key not in index:
                missing += 1
                continue
            if index[key]['jp'] != it['jp']:
                mismatch += 1
                continue
            t = it.get('ko')
            if not t:
                skipped += 1
                continue
            slot = ko.setdefault(it['file'], {})
            k = str(it['idx'])
            if k in slot and slot[k] != t:
                conflict += 1
            slot[k] = t
            n += 1
            added += 1
        print('%-16s 항목 %4d  반영 %4d' % (os.path.basename(p), len(data), n))

    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        json.dump(ko, f, ensure_ascii=False, indent=1)

    total = sum(len(v) for v in ko.values())
    print('\n병합 %d건 / 미번역 %d / 코퍼스에 없음 %d / 원문 불일치 %d / 충돌 %d'
          % (added, skipped, missing, mismatch, conflict))
    print('%s  누적 %d항목 / 전체 %d항목 (%.1f%%)'
          % (OUT, total, len(index), 100.0 * total / len(index)))
    print('\n파일별 진행:')
    for rel in sorted(corpus):
        got = len(ko.get(rel, {}))
        if got:
            print('  %-42s %4d / %4d' % (os.path.basename(rel), got, len(corpus[rel])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
