"""메뉴 화면 대사에 쓰인 글자가 어느 표에서 오는지 확인."""
import os
from ztbl import ZTbl
from project import FONT_DIR, COMMON_TBL, scene_tbl

TEXT = '最初からゲームを開始します。'

menu = ZTbl(scene_tbl('Menu'))
cmn = ZTbl(os.path.join(FONT_DIR, COMMON_TBL))
mm = menu.mapping(drop_sentinel=False)
cm = cmn.mapping(drop_sentinel=False)

print('%-4s %-8s %-8s' % ('글자', 'Menu', 'Common'))
for ch in dict.fromkeys(TEXT):
    print('%-4s %-8s %-8s' % (ch, mm.get(ch, '-'), cm.get(ch, '-')))

kana = [c for c in cm if 0x3040 <= ord(c) <= 0x30ff]
kana_menu = [c for c in mm if 0x3040 <= ord(c) <= 0x30ff]
print('\nCommon 가나 %d자, Menu 가나 %d자' % (len(kana), len(kana_menu)))
print('Common 가나 글리프 인덱스 범위:',
      min(cm[c] for c in kana), '~', max(cm[c] for c in kana))
