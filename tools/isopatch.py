"""★★원본 ISO 를 «제자리»로 패치한다 — 배포용 xdelta 를 작게 만들기 위해.

⛔`extract-xiso -c` 로 다시 구우면 파일 배치가 통째로 달라진다(섹터 99.86% 상이).
  그러면 xdelta 가 ISO 크기만큼 커져 배포가 불가능하다.
⇒ 원본 ISO 를 복사한 뒤, XISO 파일 표가 알려 주는 «그 파일 자리»에 직접 써넣는다.
  바뀐 섹터만 달라지므로 xdelta 가 작아진다.

★크기가 같아야만 제자리 쓰기가 된다. 커진 파일은 건너뛰고 경고한다
  (그런 파일은 HDD 캐시 동기화도 안 되므로, 애초에 원본 크기 안에 맞추는 게 맞다).

    python isopatch.py <원본ISO> <출력ISO>
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import ROOT, WORK
from xiso import Xiso

ORIG = os.path.join(WORK, 'orig')


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    src, dst = sys.argv[1], sys.argv[2]
    if os.path.abspath(src) == os.path.abspath(dst):
        print('★출력이 원본과 같다 — 원본을 덮어쓰면 안 된다')
        return 1

    # 바뀐 파일 목록 (work/orig 대비)
    changed = {}
    for dp, dn, fn in os.walk(ORIG):
        for f in fn:
            o = os.path.join(dp, f)
            rel = os.path.relpath(o, ORIG)
            p = os.path.join(ROOT, rel)
            if not os.path.exists(p):
                continue
            a = open(o, 'rb').read()
            b = open(p, 'rb').read()
            if a != b:
                changed[rel.replace('/', '\\')] = (len(a), b)
    print('원본 대비 바뀐 파일 %d개' % len(changed))

    print('원본 ISO 복사 중… (%.1f GB)' % (os.path.getsize(src) / 2 ** 30))
    shutil.copy2(src, dst)

    x = Xiso(dst)
    table = x.files()
    x.f.close()
    # 표의 키는 대소문자·구분자가 다를 수 있다 — 정규화해 맞춘다
    norm = {k.lower().replace('/', '\\'): v for k, v in table.items()}

    ok = miss = big = 0
    with open(dst, 'r+b') as f:
        for rel, (osize, data) in sorted(changed.items()):
            key = rel.lower()
            ent = norm.get(key)
            if ent is None:
                print('  ★ISO 표에 없음: %s' % rel)
                miss += 1
                continue
            off, size = ent
            if size != osize:
                print('  ★크기 불일치(표 %d vs 원본 %d): %s' % (size, osize, rel))
                miss += 1
                continue
            if len(data) != size:
                print('  ★커져서 제자리 못 씀 (%d -> %d): %s' % (size, len(data), rel))
                big += 1
                continue
            f.seek(off)
            f.write(data)
            ok += 1
        f.flush()
        os.fsync(f.fileno())

    print()
    print('제자리로 쓴 파일 %d개 · 못 찾음 %d · 커서 제외 %d' % (ok, miss, big))
    if big:
        print('★커진 파일은 반영되지 않았다 — 원본 크기 안으로 줄여야 한다.')
    # 검산
    bad = 0
    x2 = Xiso(dst)
    t2 = x2.files()
    with open(dst, 'rb') as f:
        for rel, (osize, data) in changed.items():
            ent = {k.lower(): v for k, v in t2.items()}.get(rel.lower())
            if not ent or len(data) != ent[1]:
                continue
            f.seek(ent[0])
            if f.read(ent[1]) != data:
                bad += 1
                print('  ★검산 실패: %s' % rel)
    x2.f.close()
    print('검산 실패 %d건' % bad)
    return 0


if __name__ == '__main__':
    sys.exit(main())
