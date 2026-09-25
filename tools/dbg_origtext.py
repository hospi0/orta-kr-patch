"""★가설: 게임이 «원본 일본어 텍스트»를 읽고, 우리가 덮어쓴 칸 때문에 한글이 섞여 보인다.

원문 글자 -> (원본 표의 칸) -> (우리가 그 칸에 칠한 음절) 을 만들어
실제 화면과 대조한다. 맞으면 «.msg 가 반영이 안 되고 있다»는 뜻이다.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, FONT_DIR, TRANS, WORK, COMMON_TBL
from ztbl import ZTbl, SENTINEL
from atlaswrite import Atlas, CELLS_PER_PAGE

ORIG = os.path.join(WORK, 'orig')


def oo(p):
    o = os.path.join(ORIG, os.path.relpath(p, ROOT))
    return o if os.path.exists(o) else p


cm = json.load(open(os.path.join(WORK, 'charmap_all.json'), encoding='utf-8'))


def show(jp, scene):
    cto = ZTbl(oo(os.path.join(FONT_DIR, COMMON_TBL))).mapping(drop_sentinel=False)
    sto = ZTbl(oo(os.path.join(FONT_DIR, 'Reisyo_%s_z_tbl.bin' % scene))).mapping(drop_sentinel=False)
    nC = Atlas(oo(os.path.join(FONT_DIR, 'Zenkaku_Common.txb'))).pages * CELLS_PER_PAGE
    nS = Atlas(oo(os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % scene))).pages * CELLS_PER_PAGE
    inv_c = {v[1]: s for s, v in cm['Common'].items()}
    inv_s = {v[1]: s for s, v in cm[scene].items()}
    out = []
    print('%-3s %-8s %-8s %-8s %-8s' % ('원문자', '공용칸', '거기음절', '장면칸', '거기음절'))
    for ch in jp:
        if ch == '\n':
            out.append('/')
            continue
        cg, sg = cto.get(ch), sto.get(ch)
        pc = inv_c.get(cg) if cg is not None and cg < nC else None
        ps = inv_s.get(sg) if sg is not None and sg < nS else None
        print('%-4s %-8s %-8s %-8s %-8s'
              % (ch, cg if cg is not None else '-', pc or '-',
                 sg if sg is not None else '-', ps or '-'))
        out.append(pc or ps or ch)
    print()
    print('예상 화면: %s' % ''.join(out))


if __name__ == '__main__':
    jp = sys.argv[1]
    show(jp, sys.argv[2] if len(sys.argv) > 2 else 'Stage1')
