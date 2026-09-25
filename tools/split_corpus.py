"""코퍼스를 29KB 조각으로 쪼갠다 — 번역을 나눠서 하기 위한 작업 단위.

산출물  trans/corpus_parts/part_001.json ...
각 조각은 «자체 완결»이다. 항목마다 file/idx 를 달고 있어서, 번역 후
(file, idx) 로 원위치에 도로 합칠 수 있다.

★budget = 그 항목에 쓸 수 있는 «정확한» 바이트 수.
  번역문은 이보다 길면 안 되고, 짧으면 전각 공백으로 채운다.
  → [[feedback_nul_padding_shifts_string_index]]
★파일을 쓸 때 newline='' 을 반드시 줄 것. 안 그러면 Windows 가 줄바꿈을
  2바이트로 바꿔 조각이 한도를 넘는다(실제로 1,170B 넘쳤다).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS

LIMIT = 29 * 1024
SRC = os.path.join(TRANS, 'corpus.json')
DST = os.path.join(TRANS, 'corpus_parts')


def dump(chunk):
    return json.dumps(chunk, ensure_ascii=False, indent=1)


def main():
    with open(SRC, encoding='utf-8') as f:
        corpus = json.load(f)

    items = []
    for rel in sorted(corpus):
        for e in corpus[rel]:
            if not e['jp'].strip():
                continue
            items.append({'file': rel, 'idx': e['idx'], 'budget': e['bytes'],
                          'jp': e['jp'], 'ko': None})

    os.makedirs(DST, exist_ok=True)
    for old in os.listdir(DST):
        if old.startswith('part_') and old.endswith('.json'):
            os.remove(os.path.join(DST, old))

    parts, cur = [], []
    for it in items:
        cur.append(it)
        if len(dump(cur).encode('utf-8')) > LIMIT:
            cur.pop()
            parts.append(cur)
            cur = [it]
    if cur:
        parts.append(cur)

    for i, chunk in enumerate(parts, 1):
        p = os.path.join(DST, 'part_%03d.json' % i)
        with open(p, 'w', encoding='utf-8', newline='') as f:
            f.write(dump(chunk))
        files = sorted({c['file'] for c in chunk})
        tag = os.path.basename(files[0])
        if len(files) > 1:
            tag += ' 외 %d' % (len(files) - 1)
        print('part_%03d.json  %6d B  항목 %4d  글자 %5d  %s'
              % (i, os.path.getsize(p), len(chunk),
                 sum(len(c['jp']) for c in chunk), tag))

    print('\n조각 %d개 -> %s' % (len(parts), DST))
    print('항목 합계 %d  글자 합계 %d'
          % (sum(len(c) for c in parts),
             sum(len(x['jp']) for c in parts for x in c)))


if __name__ == '__main__':
    main()
