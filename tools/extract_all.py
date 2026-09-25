"""번역 대상 전체 추출 — 모든 `.msg` 를 훑어 코퍼스로 만든다.

산출물
  trans/corpus.json   {파일: [{idx, off, bytes, pad, jp}]}
  화면 요약표          파일별 항목수·글자수·바이트

★예산은 «원본»에서 잰다(work/orig 우선). 빌드가 제자리를 덮어쓰기 때문이다.
★번역문은 원문과 «정확히» 같은 바이트 수여야 한다
  → [[feedback_nul_padding_shifts_string_index]]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, TRANS, WORK, pristine
from msgrec import records   # ★레코드 파서. 휴리스틱 scan 은 항목을 놓친다


def msg_paths():
    out = []
    for dp, dn, fn in os.walk(ROOT):
        for f in sorted(fn):
            # ⛔영문판은 번역 대상이 아니다 — 코퍼스에 넣지 않는다.
            if f.lower().endswith('.msg') and '_JP' in f:
                out.append(os.path.join(dp, f))
    return sorted(out)


def entries_of(path):
    d = open(pristine(path), 'rb').read()
    out = []
    for i, r in enumerate(records(d)):
        out.append({'idx': i, 'off': r['off'], 'bytes': r['bytes'],
                    'pad': r['pad'], 'rec': r['rec'], 'jp': r['jp']})
    return out


def main():
    paths = msg_paths()
    corpus = {}
    rows = []
    for p in paths:
        rel = os.path.relpath(p, ROOT)
        try:
            es = entries_of(p)
        except Exception as e:
            rows.append((rel, -1, 0, 0, str(e)[:30]))
            continue
        corpus[rel] = es
        chars = sum(len(e['jp']) for e in es)
        by = sum(e['bytes'] for e in es)
        rows.append((rel, len(es), chars, by, ''))

    os.makedirs(TRANS, exist_ok=True)
    dst = os.path.join(TRANS, 'corpus.json')
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(corpus, f, ensure_ascii=False, indent=1)

    print('%-46s %6s %8s %8s' % ('파일(JP만)', '항목', '글자', '바이트'))
    for rel, n, c, b, err in sorted(rows):
        print('%-46s %6s %8s %8s %s' % (rel, n, c, b, err))
    print('    합계  파일 %d  항목 %d  글자 %d  바이트 %d'
          % (len(rows), sum(r[1] for r in rows), sum(r[2] for r in rows),
             sum(r[3] for r in rows)))
    print('\n코퍼스 -> %s' % dst)


if __name__ == '__main__':
    main()
