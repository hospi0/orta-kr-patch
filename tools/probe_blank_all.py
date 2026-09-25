"""파괴 시험 — 디스크의 **모든 `.txb` 픽셀을 0 으로** (`sprite/Font` 제외).

목적: 「메뉴 설명문·가나를 그리는 제3의 폰트가 `.txb` 안에 있는가」를 **1회 빌드로** 가른다.

    메뉴 설명문이 깨진다  -> `.txb` 안에 있다. 디렉터리 단위 이분 탐색으로 좁힌다.
    멀쩡하다              -> **`.txb` 가 아니다.** `.spr`(98) / XBE 내장 / 실시간 생성으로
                             후보가 확 줄어든다.

★세션1 `probe_blank3.py` 의 결함을 고쳤다 — 그건 데이터를 **0x20 부터** 지웠는데,
  `pages>1` 인 TXRB 는 데이터가 **0x20 + pages*0x0C** 부터다. 즉 **서브텍스처 표를
  뭉갠** 것이라 게임이 텍스처를 아예 못 읽고 폴백했을 수 있다. 그 결과는 못 믿는다.
★알파뿐 아니라 **컬러까지** 0 으로 만든다 — 컬러 채널에도 글자가 있다
  ([[feedback_dxt_color_channel_also_has_glyph]]).
★`sprite/Font` 는 제외한다. 거기는 이미 판정이 끝났다(Common 을 한글로 바꿔도
  메뉴·자막의 가나가 안 변했다).
"""
import os
import shutil
import sys
from pcmp import decompress, build as pcmp_build
from txrb import Txrb
from project import ROOT, WORK

ORIG = os.path.join(WORK, 'orig')
SKIP = os.path.join('sprite', 'Font')


def restore_all():
    n = 0
    for dp, dn, fns in os.walk(ORIG):
        for fn in fns:
            src = os.path.join(dp, fn)
            shutil.copy2(src, os.path.join(ROOT, os.path.relpath(src, ORIG)))
            n += 1
    return n


def targets():
    for dp, dn, fns in os.walk(ROOT):
        for fn in sorted(fns):
            if not fn.lower().endswith('.txb'):
                continue
            rel = os.path.relpath(os.path.join(dp, fn), ROOT)
            if rel.startswith(SKIP):
                continue
            yield rel


def blank_one(rel, dry):
    """헤더·서브텍스처 표는 그대로, 픽셀만 0. 크기는 원본과 같게."""
    src = os.path.join(ORIG, rel)
    if not os.path.exists(src):                     # 백업이 없으면 지금 떠 둔다
        os.makedirs(os.path.dirname(src), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, rel), src)
    raw = open(src, 'rb').read()
    t = Txrb(src)
    if not t.ok:
        return None, 'TXRB 아님'
    d = t.data
    new = d[:t.start] + bytes(len(d) - t.start)     # ★t.start = 서브텍스처 표 뒤
    out = pcmp_build(new) if t.packed else new
    if len(out) > len(raw):
        return None, '재압축 초과 %+d' % (len(out) - len(raw))
    out = out + bytes(len(raw) - len(out))
    if not dry:
        with open(os.path.join(ROOT, rel), 'wb') as f:
            f.write(out)
    return len(out), None


if __name__ == '__main__':
    dry = '--dry' in sys.argv
    print('원본 전량 원복: %d개' % restore_all())
    rels = list(targets())
    print('대상 .txb %d개 (sprite/Font 제외)\n' % len(rels))
    okn, fails = 0, []
    for i, rel in enumerate(rels):
        n, err = blank_one(rel, dry)
        if err:
            fails.append((rel, err))
        else:
            okn += 1
        if (i + 1) % 100 == 0:
            print('   %d/%d …' % (i + 1, len(rels)))
    print('\n비움 %d개 / 실패 %d개' % (okn, len(fails)))
    for rel, err in fails[:20]:
        print('   ⚠ %-48s %s' % (rel, err))
    if dry:
        print('\n[미리보기만 — 게임 트리는 원본 그대로다]')
