"""한글 글리프 렌더 v2 — 원본 글꼴의 «획 두께·알파 계조»에 맞춘다.

실측 기준값 (tools/strokes.py, OpeningDemo 200글리프)
    수평 런 최빈 3 / 중앙값 4.0
    잉크 픽셀 중 알파 240+ 비율 35%   ← 원본이 오히려 더 부드럽다

v1(malgun 24px)은 런 최빈 2 / 알파 240+ 76.5% 라 획이 1px 가늘고 딱딱했다.
실기에서 자막의 한글이 «점선처럼 끊겨» 나온 원인이 이것이다.

방법: 큰 크기로 렌더해서 축소(supersampling)하면 계조가 자연스럽고,
      볼드체 + 필요하면 팽창으로 두께를 맞춘다.
"""
import os
from PIL import Image, ImageFont, ImageDraw, ImageFilter
from project import GLYPH_W, GLYPH_H

FONTS = {
    'regular': r'C:\Windows\Fonts\malgun.ttf',
    'bold': r'C:\Windows\Fonts\malgunbd.ttf',
}
SS = 8              # supersampling 배율
_cache = {}


def _font(weight, size):
    key = (weight, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(FONTS[weight], size)
    return _cache[key]


def glyph(ch, weight='bold', size=24, dilate=0, box=(GLYPH_W, GLYPH_H)):
    """28x28 그레이 bytes.

    weight  'regular' | 'bold'
    size    28칸 기준 글자 크기 (실제로는 size*SS 로 그려 축소한다)
    dilate  축소 «전» 에 굵히는 픽셀 수(고해상도 기준) — 0.5px 단위 조절용
    """
    w, h = box
    f = _font(weight, size * SS)
    big = Image.new('L', (w * SS, h * SS), 0)
    d = ImageDraw.Draw(big)
    bb = d.textbbox((0, 0), ch, font=f)
    x = (w * SS - (bb[2] - bb[0])) // 2 - bb[0]
    y = (h * SS - (bb[3] - bb[1])) // 2 - bb[1]
    d.text((x, y), ch, font=f, fill=255)
    if dilate:
        big = big.filter(ImageFilter.MaxFilter(int(dilate) * 2 + 1))
    small = big.resize((w, h), Image.BOX)      # BOX = 면적 평균 → 자연스러운 계조
    return small.tobytes()


def font_desc(weight='bold', size=24, dilate=0):
    return '%s %dpx ss%d dilate%d' % (os.path.basename(FONTS[weight]), size, SS, dilate)


if __name__ == '__main__':
    from strokes import stats, orig_cells
    SAMPLE = '강산진수해별봄여름가을겨울처음부터게임시작합니다'
    med, solid = stats(orig_cells('OpeningDemo'), '원본 OpeningDemo (목표)')
    print()
    import render as v1
    stats([v1.glyph(c) for c in SAMPLE], 'v1  malgun 24px (실기에서 끊긴 것)')
    print()
    for weight, size, dil in [('regular', 24, 0), ('bold', 24, 0),
                              ('bold', 25, 0), ('bold', 24, 2), ('bold', 25, 2)]:
        print()
        stats([glyph(c, weight, size, dil) for c in SAMPLE],
              'v2  ' + font_desc(weight, size, dil))
