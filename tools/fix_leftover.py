"""ko.json 에 남은 «미번역 일본어 낱말» 손보기. 한 번만 돌리면 되고, 멱등이다."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS

P = os.path.join(TRANS, 'ko.json')
ko = json.load(open(P, encoding='utf-8'))

FIX = [
    (r'menudata\TextData\Text_OpeningDemo_JP.msg', '2', '亞人', '아인'),
    (r'menudata\TextData\Text_OpeningDemo_JP.msg', '7', '亞人', '아인'),
    (r'menudata\TextData\Text_SubScenarioDemo_JP.msg', '134', '男', '남자'),
    (r'menudata\TextData\text_pdb_db_empire_JP.msg', '164',
     '부트 改(개량형)', '부트 개량형'),
]

n = 0
for rel, idx, a, b in FIX:
    v = ko.get(rel, {}).get(idx)
    if v is None:
        print('★없음 %s %s' % (os.path.basename(rel), idx))
        continue
    if a not in v:
        print('   이미 반영 %s %s' % (os.path.basename(rel), idx))
        continue
    ko[rel][idx] = v.replace(a, b)
    n += v.count(a)
    print('%-34s %-4s %r -> %r' % (os.path.basename(rel), idx, a, b))

if n:
    with open(P, 'w', encoding='utf-8', newline='') as f:
        json.dump(ko, f, ensure_ascii=False, indent=1)
print('%d곳 고쳤습니다.' % n)
