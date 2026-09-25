"""★배포용 «HDD 캐시 동기화» 자료 파일을 만든다.

왜 필요한가:
  게임을 한 번이라도 돌린 기기는 폰트·텍스트를 Xbox HDD 캐시 파티션에 복사해 두고
  거기서 읽는다. 그래서 ISO 를 패치해도 **이미 플레이한 사람에게는 안 먹는다**
  → [[feedback_game_caches_assets_to_xbox_hdd]]
  배포 패치에는 «캐시도 같이 고쳐 주는 도구»가 있어야 한다.

자료 파일 = {항목: 원본 앞부분(needle) · 원본 크기 · 원본 SHA1 · 패치본 전체}
  · 크기가 같아야만 제자리 덮어쓸 수 있으므로 «크기가 변한 파일»은 담지 않는다.
  · 실제로 캐시에 뭐가 올라갈지는 기기마다 다르므로 **후보를 전부** 담는다.

    python mkcachepatch.py [출력경로]
"""
import gzip
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import FONT_DIR, ROOT, WORK

ORIG = os.path.join(WORK, 'orig')
NEEDLE = 64


def candidates():
    """캐시에 올라갈 수 있는 파일 = sprite/Font 전체 + 모든 `.msg`."""
    for f in sorted(os.listdir(FONT_DIR)):
        yield os.path.join(FONT_DIR, f)
    for sub in ('menudata\\TextData', 'messageevent'):
        d = os.path.join(ROOT, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.lower().endswith('.msg'):
                yield os.path.join(d, f)


def main():
    dst = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(ROOT), 'orta_kr_cache.patch.gz')
    rows, skip, same = [], 0, 0
    for p in candidates():
        rel = os.path.relpath(p, ROOT)
        o = os.path.join(ORIG, rel)
        if not os.path.exists(o):
            continue
        a = open(o, 'rb').read()
        b = open(p, 'rb').read()
        if a == b:
            same += 1
            continue
        if len(a) != len(b):
            print('  ★%s 크기가 달라 캐시 동기화 불가 (%d -> %d)' % (rel, len(a), len(b)))
            skip += 1
            continue
        rows.append({
            'rel': rel.replace('\\', '/'),
            'size': len(a),
            # ★needle 은 «원본»과 «패치본» 둘 다 담는다.
            #   원본만 담으면 이미 패치된 자리를 못 찾아 «다시 돌리기»가 안 된다.
            'needle': a[:NEEDLE].hex(),
            'needle_new': b[:NEEDLE].hex(),
            'orig_sha1': hashlib.sha1(a).hexdigest(),
            'new_sha1': hashlib.sha1(b).hexdigest(),
            'new': b.hex(),
        })
    blob = json.dumps({'game': 'Panzer Dragoon Orta (KR)', 'items': rows}).encode()
    with gzip.open(dst, 'wb', compresslevel=9) as f:
        f.write(blob)
    print('항목 %d개 (변경 없음 %d · 크기 달라 제외 %d)' % (len(rows), same, skip))
    print('자료 %d B -> 압축 %d B' % (len(blob), os.path.getsize(dst)))
    print('-> %s' % dst)


if __name__ == '__main__':
    main()
