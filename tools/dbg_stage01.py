import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRANS, WORK
from build_all import rebuild_msg, fit_size
from msgwalk import walk
import check_ko as K

ORIG = os.path.join(WORK, 'orig')
rel = r'messageevent\MesData_Stage01_JP.msg'
corpus = json.load(open(os.path.join(TRANS, 'corpus.json'), encoding='utf-8'))
ko = json.load(open(os.path.join(TRANS, 'ko.json'), encoding='utf-8'))
cm = json.load(open(os.path.join(WORK, 'charmap_all.json'), encoding='utf-8'))
smap = {s: v[0] for s, v in cm[K.scene_of(rel)].items()}
ko_idx = {int(k): v for k, v in ko.get(rel, {}).items()}
data, orig, odd = rebuild_msg(rel, ko_idx, smap)
data, size = fit_size(data, orig)
o = open(os.path.join(ORIG, rel), 'rb').read()

wo, wn = walk(o), walk(data)
print('%-4s %-10s %-8s %-6s %s' % ('#', 'ID', 'start', 'len', 'text'))
for tag, d, w in (('원본', o, wo), ('새', data, wn)):
    print('===', tag, len(w), '항목')
    for i, (start, ident, off, ln) in enumerate(w[:22]):
        t = d[off:off + ln].decode('cp932', 'replace').replace('\n', '/')
        print('%-4d %-10s %-8X %-6d %s' % (i, ident if ident is not None else '', start, ln, t[:50]))
