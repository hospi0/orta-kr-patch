"""글리프 실측 — 28×28 칸 안에서 «잉크가 실제로 차지하는 범위»와 알파 계조.

한글을 덮어그리려면 원본이 칸의 어디를 쓰는지·몇 단계 알파를 쓰는지 알아야 한다.
★파생 수치 금지, 실측 (feedback_screen_limits_measure_not_derive).
"""
import os
import sys
from cells import atlas_alpha, COLS, ROWSC, PAGE_W
from ztbl import ZTbl
from project import FONT_DIR, COMMON_TBL, GLYPH_W, GLYPH_H, scene_tbl, scene_atlas


def cell_box(px, idx):
    """칸 idx 의 (x0,y0,x1,y1) 잉크 경계와 알파값 집합. 없으면 None."""
    r, c = divmod(idx % (COLS * ROWSC), COLS)
    xs, ys, vals = [], [], set()
    for y in range(GLYPH_H):
        base = (r * GLYPH_H + y) * PAGE_W + c * GLYPH_W
        row = px[base:base + GLYPH_W]
        for x, v in enumerate(row):
            if v:
                xs.append(x)
                ys.append(y)
                vals.add(v)
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys)), vals


def main(scene):
    if scene == 'Common':
        tbl, atl = os.path.join(FONT_DIR, COMMON_TBL), os.path.join(FONT_DIR, 'Zenkaku_Common.txb')
    else:
        tbl, atl = scene_tbl(scene), scene_atlas(scene)
    pages, px = atlas_alpha(atl)
    t = ZTbl(tbl)
    m = t.mapping(drop_sentinel=True)
    inv = {}
    for ch, g in m.items():
        inv.setdefault(g, ch)

    boxes, allvals = [], set()
    kana = []
    for g in sorted(inv):
        p = g // (COLS * ROWSC)
        if p >= pages:
            continue
        b = cell_box(px[p], g)
        if b is None:
            continue
        boxes.append(b[0])
        allvals |= b[1]
        ch = inv[g]
        if 0x3040 <= ord(ch) <= 0x30ff:
            kana.append((ch, g, b[0]))

    print('%s: 매핑문자 %d / 잉크칸 %d' % (scene, len(m), len(boxes)))
    print('  잉크 x 범위 %d~%d, y 범위 %d~%d  (칸 %dx%d)'
          % (min(b[0] for b in boxes), max(b[2] for b in boxes),
             min(b[1] for b in boxes), max(b[3] for b in boxes), GLYPH_W, GLYPH_H))
    ws = [b[2] - b[0] + 1 for b in boxes]
    hs = [b[3] - b[1] + 1 for b in boxes]
    print('  글리프 폭 최대 %d (평균 %.1f) / 높이 최대 %d (평균 %.1f)'
          % (max(ws), sum(ws) / len(ws), max(hs), sum(hs) / len(hs)))
    print('  알파 계조 %d종: %s' % (len(allvals), sorted(allvals)))
    print('  가나 %d자, 글리프 인덱스 %d~%d'
          % (len(kana), min(k[1] for k in kana), max(k[1] for k in kana)) if kana else '  가나 없음')
    if kana:
        print('  가나 예:', ' '.join('%s=%d' % (c, g) for c, g, _ in kana[:12]))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'Common')
