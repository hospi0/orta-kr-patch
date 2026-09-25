import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS, WORK
from msgwalk import walk

ORIG = os.path.join(WORK, 'orig')
corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
rel = sys.argv[1] if len(sys.argv) > 1 else r'menudata\TextData\Text_OpeningDemo_JP.msg'
d = open(os.path.join(ORIG, rel), 'rb').read()
w = walk(d)
recoff = {e['off']: e for e in corpus[rel]}
print('--- walk %d items ---' % len(w))
for start, ident, off, ln in w:
    t = d[off:off + ln].decode('cp932', 'replace').replace('\n', '/')
    mark = 'rec%-4d' % recoff[off]['idx'] if off in recoff else '  --  '
    print('%08X id=%-9s off=%-6d len=%-4d %s  %s'
          % (start, ident if ident is not None else '', off, ln, mark, t[:70]))
