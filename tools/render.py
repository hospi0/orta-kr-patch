"""한글 글리프를 28x28 알파 비트맵으로 렌더."""
import os
from PIL import Image, ImageDraw, ImageFont
from project import GLYPH_W, GLYPH_H

FONT_CANDIDATES = [
    r'C:\Windows\Fonts\malgun.ttf',
    r'C:\claude\project\terra-kr-patch\assets\GalmuriMono11.ttf',
]
SIZE = 24          # 28칸 안에 여백 2px
_cache = {}


def _font():
    if 'f' not in _cache:
        for p in FONT_CANDIDATES:
            if os.path.exists(p):
                _cache['f'] = ImageFont.truetype(p, SIZE)
                _cache['path'] = p
                break
        else:
            raise RuntimeError('한글 폰트를 못 찾았다')
    return _cache['f']


def glyph(ch):
    """28x28 그레이스케일 bytes. 값 0~255 (DXT3 알파는 4비트로 줄인다)."""
    f = _font()
    img = Image.new('L', (GLYPH_W, GLYPH_H), 0)
    d = ImageDraw.Draw(img)
    box = d.textbbox((0, 0), ch, font=f)
    w, h = box[2] - box[0], box[3] - box[1]
    x = (GLYPH_W - w) // 2 - box[0]
    y = (GLYPH_H - h) // 2 - box[1]
    d.text((x, y), ch, font=f, fill=255)
    return img.tobytes()


def font_path():
    _font()
    return _cache['path']
