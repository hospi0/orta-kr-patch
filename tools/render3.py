"""한글 글리프 렌더 v3 — 궁서체 + «공통 변환»으로 간격을 균일하게.

v2 의 문제: 글자마다 **잉크 bbox 를 재서 가운데 맞춤**을 했다. 그러면 좁은 음절
(처·음)은 양옆 여백이 커져 칸 간격이 일정한데도 **띄엄띄엄** 보인다.
실기 스샷에서 `처 음 부터게 임을시작 합니다` 로 나온 원인이 이것이다.

v3: 음절 집합 전체의 **잉크 합집합 상자**를 한 번만 구하고, 모든 글자에 **같은
변환**(같은 배율·같은 원점)을 적용한다. 글자마다 다르게 움직이지 않으므로 간격이 고르다.

원본 실측 (Zenkaku_Common 한자 57자, 28x28 칸)
    잉크 상자 x 1..26 (폭 26) / y 4..23 (높이 20)  ← 가로로 넓고 납작하다(예서체)
    수평 런 중앙값 4.0
그래서 한글도 **26x20 상자**에 넣는다. 정사각형으로 그리면 원본과 안 어울린다.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import GLYPH_W, GLYPH_H

FONT_PATH = r'C:\Windows\Fonts\batang.ttc'
FONT_INDEX = 2            # 0 Batang / 1 BatangChe / 2 Gungsuh / 3 GungsuhChe
BIG = 160                 # 큰 크기로 그려서 축소(계조가 자연스럽다)

# 원본 실측 상자
BOX_L, BOX_R = 1, 26
BOX_T, BOX_B = 4, 23
BOX_W = BOX_R - BOX_L + 1     # 26
BOX_H = BOX_B - BOX_T + 1     # 20

_font = None
_norm = None                  # (x0, y0, w, h) — 음절 집합 공통 잉크 상자


def font():
    global _font
    if _font is None:
        _font = ImageFont.truetype(FONT_PATH, BIG, index=FONT_INDEX)
    return _font


def _draw_big(ch):
    """BIG 크기 캔버스에 «고정 원점»으로 그린다. 글자마다 위치를 안 바꾼다."""
    f = font()
    pad = BIG // 2
    im = Image.new('L', (BIG * 2, BIG * 2), 0)
    d = ImageDraw.Draw(im)
    asc, _desc = f.getmetrics()
    d.text((pad, pad + asc), ch, font=f, fill=255, anchor='ls')
    return im


def calibrate(chars):
    """음절 집합 전체의 잉크 합집합 상자를 구한다. ★한 번만 호출하면 된다."""
    global _norm
    box = None
    for ch in chars:
        bb = _draw_big(ch).getbbox()
        if bb is None:
            continue
        box = bb if box is None else (min(box[0], bb[0]), min(box[1], bb[1]),
                                      max(box[2], bb[2]), max(box[3], bb[3]))
    if box is None:
        raise ValueError('그릴 글자가 없다')
    _norm = (box[0], box[1], box[2] - box[0], box[3] - box[1])
    return _norm


def _despeckle(px, w, h, minpx=3):
    """획에서 떨어진 «찌꺼기 점»을 지운다.

    궁서체의 붓끝이 20px 로 줄면서 조각으로 떨어져 나온다(오 밑의 점).
    """
    seen = [False] * (w * h)
    ink = [v > 8 for v in px]
    for s in range(w * h):
        if not ink[s] or seen[s]:
            continue
        comp, stack = [], [s]
        seen[s] = True
        while stack:
            i = stack.pop()
            comp.append(i)
            y, x = divmod(i, w)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w:
                        j = ny * w + nx
                        if ink[j] and not seen[j]:
                            seen[j] = True
                            stack.append(j)
        if len(comp) < minpx:
            for i in comp:
                px[i] = 0
    return px


def glyph(ch, dilate=0, center=True, minpx=3, fill=False, levels=0):
    """28x28 그레이 bytes. ★calibrate() 를 먼저 부를 것.

    center=True  칸 안에서 글자를 «가로 가운데»에 놓는다.
      ★안 하면 글자가 칸 왼쪽에 붙고 여백이 오른쪽에만 몰려, 낱말 사이 간격이
        앞 글자 폭에 따라 들쭉날쭉해 보인다(실기에서 확인).
    """
    if _norm is None:
        raise RuntimeError('calibrate() 를 먼저 호출해야 간격이 균일해진다')
    x0, y0, w, h = _norm
    im = _draw_big(ch)
    if dilate:
        im = im.filter(ImageFilter.MaxFilter(int(dilate) * 2 + 1))
    im = im.crop((x0, y0, x0 + w, y0 + h)).resize((BOX_W, BOX_H), Image.BOX)
    dx = 0
    if fill:
        # ★★글자마다 «잉크 폭»을 같게 만든다.
        # ⛔2026-08-30 실기 결과: 간격은 «전혀 안 고쳐지고» 글자만 늘어나 보기 나빴다.
        #   기본값 False 로 되돌렸다. 전진 폭 규칙은 여전히 미상이다.
        bb = im.getbbox()
        if bb and bb[2] > bb[0]:
            core = im.crop((bb[0], 0, bb[2], BOX_H)).resize((BOX_W, BOX_H), Image.BOX)
            im = core
    elif center:
        bb = im.getbbox()
        if bb:
            dx = (BOX_W - (bb[2] - bb[0])) // 2 - bb[0]
    out = Image.new('L', (GLYPH_W, GLYPH_H), 0)
    out.paste(im, (BOX_L + dx, BOX_T))
    px = bytearray(out.tobytes())
    if levels:
        # ★계조를 줄이면 PCMP 재압축이 원본 크기 안에 들어간다.
        #   폭을 통일하면 잉크가 늘어 무양자화로는 +971B 넘쳤다.
        #   0 과 255 는 보존한다(투명·불투명이 어긋나면 획이 흐려진다).
        n = levels - 1
        px = bytearray(int(round(round(v / 255 * n) * 255 / n)) for v in px)
    if minpx:
        px = _despeckle(px, GLYPH_W, GLYPH_H, minpx)
    return bytes(px)


def desc(dilate=0):
    return 'Gungsuh(batang.ttc#%d) big%d box%dx%d 가운데정렬' % (
        FONT_INDEX, BIG, BOX_W, BOX_H)


if __name__ == '__main__':
    import numpy as np
    S = '처음부터게임을시작합니다'
    calibrate(S)
    print('공통 상자', _norm, '->', (BOX_W, BOX_H))
    for dl in (0, 2, 4, 6):
        runs = []
        for ch in S:
            g = np.frombuffer(glyph(ch, dl), np.uint8).reshape(GLYPH_H, GLYPH_W) > 8
            for row in g:
                n = 0
                for v in row:
                    if v:
                        n += 1
                    elif n:
                        runs.append(n)
                        n = 0
                if n:
                    runs.append(n)
        runs.sort()
        print('  dilate %d: 수평런 중앙값 %.1f  잉크 %.3f'
              % (dl, runs[len(runs) // 2], sum(
                  np.frombuffer(glyph(c, dl), np.uint8).astype(bool).sum()
                  for c in S) / (len(S) * 784)))
