"""«내 빌드가 실제로 돌고 있는가» 를 눈으로 확인하는 표식(canary) 빌드.

`sprite/pdtex_gamefont.txb` **하나만** 픽셀 0 으로 만든다.
이 파일은 라틴 UI 폰트다 — 렌더해서 확인했다(`! ? % & ' . . / 0 1 2 … A B C … a b c …`).

판정
  타이틀의 `NEW GAME` `CONTINUE` `PANDORA'S BOX` `TUTORIAL` `OPTIONS` `MENU` 글자가
  **사라지거나 깨짐**  -> 내 빌드가 살아 있다. 이후 파괴 시험 결과를 믿어도 된다.
  그대로 멀쩡          -> 빌드가 반영이 안 되고 있다(에뮬 캐시·다른 ISO 등).
                          그럼 지금까지의 폰트 결론을 전부 다시 봐야 한다.
일본어 설명문은 이 폰트와 무관하므로 그대로 나와야 한다.
"""
import os
import shutil
from project import ROOT, WORK
from pcmp import decompress, build as pcmp_build

ORIG = os.path.join(WORK, 'orig')
REL = os.path.join('sprite', 'pdtex_gamefont.txb')


def restore_all():
    for dp, dn, fns in os.walk(ORIG):
        for fn in fns:
            src = os.path.join(dp, fn)
            shutil.copy2(src, os.path.join(ROOT, os.path.relpath(src, ORIG)))


if __name__ == '__main__':
    restore_all()
    print('원본 전량 원복')
    src = os.path.join(ORIG, REL)
    if not os.path.exists(src):
        os.makedirs(os.path.dirname(src), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, REL), src)
    o = open(src, 'rb').read()
    d = decompress(o)
    new = pcmp_build(d[:0x20] + bytes(len(d) - 0x20))
    assert len(new) <= len(o)
    new += b'\x00' * (len(o) - len(new))
    with open(os.path.join(ROOT, REL), 'wb') as f:
        f.write(new)
    print('%s 만 픽셀 0 (크기 %d 동일). 나머지 전부 원본.' % (REL, len(o)))
