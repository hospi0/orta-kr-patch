"""스샷에서 «글자 격자»를 실측 — 행 위치와 글자 전진폭.
→ [[feedback_measure_screenshot_pixels_before_fixing]] · [[feedback_measure_advance_by_difference]]
"""
import sys
import numpy as np
from PIL import Image

im = Image.open(sys.argv[1]).convert('L')
im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
a = 255.0 - np.asarray(im, dtype=np.float32)      # 잉크가 밝게
box = a[40:230, 70:580]                            # 텍스트 상자 대략
rows = box.mean(axis=1)
print('행 프로파일 (y는 원본 640x480 기준, +40):')
run = None
for i, v in enumerate(rows):
    on = v > rows.mean() * 1.15
    if on and run is None:
        run = i
    if not on and run is not None:
        if i - run >= 6:
            print('  줄 y %3d ~ %3d  (높이 %d)' % (run + 40, i + 40, i - run))
        run = None

y = int(sys.argv[2]) if len(sys.argv) > 2 else None
if y is not None:
    band = a[y:y + 26, :]
    cols = band.mean(axis=0)
    th = cols.max() * 0.18
    runs = []
    run = None
    for i, v in enumerate(cols):
        on = v > th
        if on and run is None:
            run = i
        if not on and run is not None:
            if i - run >= 3:
                runs.append((run, i))
            run = None
    print()
    print('y=%d 줄의 글자 덩어리 %d개:' % (y, len(runs)))
    for s, e in runs:
        print('   x %3d ~ %3d  (폭 %d)' % (s, e, e - s))
    if len(runs) > 1:
        d = [runs[i + 1][0] - runs[i][0] for i in range(len(runs) - 1)]
        print('   시작점 간격:', d)
