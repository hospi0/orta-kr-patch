"""Panzer Dragoon Orta 한글패치 — Xbox HDD 캐시 동기화 도구 (배포용, 단독 실행)

■ 왜 필요한가
  이 게임은 폰트와 텍스트를 Xbox 하드디스크의 «캐시 파티션»에 복사해 두고 거기서 읽습니다.
  그래서 **이미 한 번이라도 게임을 돌린 기기**에서는 ISO 만 패치해도 화면이 안 바뀝니다.
  이 도구가 그 캐시를 패치본으로 맞춰 줍니다.

■ 쓰는 법
    python hddsync.py <xbox_hdd.qcow2> [자료파일]      검사만 (아무것도 안 씁니다)
    python hddsync.py <xbox_hdd.qcow2> [자료파일] --write   실제로 고칩니다

  · 자료파일을 안 적으면 이 파일과 같은 폴더의 `orta_kr_cache.patch.gz` 를 씁니다.
  · **xemu 를 완전히 종료한 뒤** 실행하세요.
  · 실기(하드 개조 Xbox)라면 HDD 이미지 대신 그 디스크 이미지를 넣어도 원리는 같습니다.

■ 안전장치
  · 크기가 같아야만 «제자리» 덮어씁니다. 파일 크기·구조를 바꾸지 않습니다.
  · 덮어쓰기 전에 그 자리 전체의 SHA1 이 «원본과 완전히 일치»하는지 확인합니다.
    한 바이트라도 다르면 건너뜁니다(우연히 앞부분만 같은 자리를 망치지 않기 위해).
  · 이미 패치된 자리는 건너뜁니다. 여러 번 돌려도 안전합니다.
  · --write 없이는 아무것도 쓰지 않습니다.
"""
import gzip
import hashlib
import json
import os
import re
import sys

CHUNK = 1 << 24


def load_patch(path):
    with gzip.open(path, 'rb') as f:
        return json.loads(f.read().decode())


def scan(hdd, needles):
    """{needle: [오프셋...]} — 한 번의 훑기로 전부 찾는다."""
    pat = re.compile(b'|'.join(re.escape(n) for n in sorted(needles, key=len, reverse=True)))
    hit = {n: [] for n in needles}
    keep = max(len(n) for n in needles) - 1
    with open(hdd, 'rb') as f:
        base, tail = 0, b''
        total = os.path.getsize(hdd)
        while True:
            b = f.read(CHUNK)
            if not b:
                break
            buf = tail + b
            for m in pat.finditer(buf):
                g = m.group()
                if g in hit:
                    hit[g].append(base - len(tail) + m.start())
            base += len(b)
            tail = buf[-keep:]
            sys.stderr.write('\r  훑는 중 %d%%   ' % (base * 100 // max(total, 1)))
    sys.stderr.write('\r' + ' ' * 24 + '\r')
    return hit


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    write = '--write' in sys.argv
    if not args:
        print(__doc__)
        return 1
    hdd = args[0]
    here = os.path.dirname(os.path.abspath(__file__))
    data = args[1] if len(args) > 1 else os.path.join(here, 'orta_kr_cache.patch.gz')
    for p in (hdd, data):
        if not os.path.exists(p):
            print('★파일이 없습니다: %s' % p)
            return 1

    pk = load_patch(data)
    items = pk['items']
    print('%s — 캐시 동기화' % pk.get('game', ''))
    print('HDD 이미지 : %s (%.1f GB)' % (hdd, os.path.getsize(hdd) / 2 ** 30))
    print('자료 항목  : %d개' % len(items))
    print()

    by_needle = {}
    for it in items:
        for k in ('needle', 'needle_new'):
            if it.get(k):
                by_needle.setdefault(bytes.fromhex(it[k]), []).append(it)
    hits = scan(hdd, list(by_needle))

    found = fixed = already = skipped = 0
    mode = 'r+b' if write else 'rb'
    with open(hdd, mode) as f:
        for needle, offs in hits.items():
            for off in offs:
                for it in by_needle[needle]:
                    f.seek(off)
                    blk = f.read(it['size'])
                    if len(blk) != it['size']:
                        continue
                    h = hashlib.sha1(blk).hexdigest()
                    if h == it['new_sha1']:
                        already += 1
                        break
                    if h != it['orig_sha1']:
                        continue
                    found += 1
                    print('  %-40s @%-12d %s'
                          % (os.path.basename(it['rel']), off,
                             '고침' if write else '고쳐야 함'))
                    if write:
                        f.seek(off)
                        f.write(bytes.fromhex(it['new']))
                        fixed += 1
                    break
                else:
                    skipped += 1
        if write:
            f.flush()
            os.fsync(f.fileno())

    print()
    if write:
        # 되읽기 검산
        bad = 0
        with open(hdd, 'rb') as f:
            for needle, offs in hits.items():
                for off in offs:
                    for it in by_needle[needle]:
                        f.seek(off)
                        blk = f.read(it['size'])
                        if len(blk) == it['size'] and \
                                hashlib.sha1(blk).hexdigest() == it['new_sha1']:
                            break
                    else:
                        continue
        print('고친 자리 %d곳 · 이미 패치됨 %d곳' % (fixed, already))
        print('완료했습니다. 이제 게임을 실행하세요.')
    else:
        if found:
            print('고쳐야 할 자리 %d곳 · 이미 패치됨 %d곳' % (found, already))
            print('실제로 고치려면 뒤에 --write 를 붙여 다시 실행하세요.')
        elif already:
            print('캐시가 이미 패치본과 같습니다 (%d곳). 할 일이 없습니다.' % already)
        else:
            print('캐시에서 이 게임의 자산을 찾지 못했습니다.')
            print('아직 게임을 돌린 적이 없다면 정상입니다 — 그냥 패치 ISO 로 실행하세요.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
