"""Text_MenuInst 의 JP/EN 을 나란히 뽑는다."""
import os
import json
from msgfile import scan
from project import ROOT, TRANS

TD = os.path.join(ROOT, 'menudata', 'TextData')
jp = scan(open(os.path.join(TD, 'Text_MenuInst_JP.msg'), 'rb').read())
en = scan(open(os.path.join(TD, 'Text_MenuInst_EN.msg'), 'rb').read())
print('JP %d / EN %d' % (len(jp), len(en)))
rows = []
for i, (off, kind, t) in enumerate(jp):
    e = en[i][2] if i < len(en) else ''
    rows.append({'i': i, 'off': off, 'jp': t, 'en': e, 'ko': ''})
    print('%3d @%05x  %s' % (i, off, t.replace('\n', '\\n')))
    print('           %s' % e.replace('\n', '\\n'))
os.makedirs(TRANS, exist_ok=True)
p = os.path.join(TRANS, 'Text_MenuInst.json')
if not os.path.exists(p):
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print('\n->', p)
chars = set()
for r in rows:
    chars.update(c for c in r['jp'] if c != '\n')
print('\nJP 고유문자 %d' % len(chars))
