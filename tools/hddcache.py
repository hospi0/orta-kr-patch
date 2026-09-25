"""xemu HDD 이미지 안의 «캐시된 자산»을 게임 트리의 현재 파일로 갱신한다.

★★이걸 안 하면 ISO 를 새로 구워도 화면이 안 바뀐다.
  게임이 부팅 때 폰트 세트를 Xbox HDD 캐시 파티션에 복사해 두고 거기서 읽기 때문이다.
  4세션을 이걸 몰라서 태웠다 → [[feedback_game_caches_assets_to_xbox_hdd]]

사용:
    python hddcache.py            # 캐시된 파일을 전부 «게임 트리 현재본»으로 갱신
    python hddcache.py --status   # 갱신 안 하고 «지금 캐시에 뭐가 있나»만 본다
    python hddcache.py --restore  # 캐시를 원본(work/orig)으로 되돌린다

원리: 크기가 같아야만 제자리 덮어쓴다. qcow2 클러스터 구조를 안 건드리므로 안전하다.
찾은 오프셋은 work/hdd/cache_map.json 에 남긴다(캐시가 다시 만들어지면 위치가 바뀐다).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import FONT_DIR, ROOT, WORK, pristine

HDD = r'D:\hospi\XEMU\XEMU FILES\Pre-built Xbox HDD image\xbox_hdd.qcow2'
HDDDIR = os.path.join(WORK, 'hdd')
MAP = os.path.join(HDDDIR, 'cache_map.json')
NEEDLE = 48


def targets():
    """캐시에 올라갈 만한 파일 = sprite/Font 전체 + ★모든 `.msg`.

    ★★2026-08-31 정정 — `.msg` 도 캐시된다. 「`.msg` 는 캐시에 안 올라간다」는
      앞선 메모는 **틀렸다**. `MesData_Stage01_JP.msg` 와 `MesData_Tutorial_JP.msg`
      의 **원본**이 HDD 이미지에 그대로 들어 있었고, 그래서 인게임 대사가
      번역을 무시하고 «원본 일본어»로 나왔다(글리프만 우리 한글이라 「외계어」로 보였다).
      → [[feedback_game_caches_assets_to_xbox_hdd]]
    ★캐시는 «플레이한 구간»만 만들어진다. 새 구간을 진행하면 다시 돌려야 한다.
    """
    for f in sorted(os.listdir(FONT_DIR)):
        yield os.path.join(FONT_DIR, f)
    for sub in ('menudata\\TextData', 'messageevent'):
        d = os.path.join(ROOT, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.lower().endswith('.msg'):
                yield os.path.join(d, f)


def find_all(hdd, needles):
    """{키: [오프셋]} — 한 번의 훑기로 전부 찾는다."""
    hit = {k: [] for k in needles}
    CH = 1 << 25
    with open(hdd, 'rb') as f:
        base, tail = 0, b''
        while True:
            b = f.read(CH)
            if not b:
                break
            buf = tail + b
            for k, n in needles.items():
                i = buf.find(n)
                while i >= 0:
                    hit[k].append(base - len(tail) + i)
                    i = buf.find(n, i + 1)
            base += len(b)
            tail = buf[-NEEDLE:]
    return hit


def load_map():
    if os.path.exists(MAP):
        with open(MAP, encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_map(m):
    os.makedirs(HDDDIR, exist_ok=True)
    with open(MAP, 'w', encoding='utf-8') as f:
        json.dump(m, f, indent=1, ensure_ascii=False)


def locate(paths):
    """{rel: [오프셋...]}. ★★사본이 «여러 벌» 있을 수 있다.

    2026-08-31 실기: `MesData_Stage01_JP.msg` 가 HDD 에 **4벌** 있었고,
    첫 벌만 고쳐서 게임은 계속 «원본» 사본을 읽었다(튜토리얼은 1벌이라 잘 나왔다).
    ⇒ 찾은 자리는 **전부** 고쳐야 한다.
    """
    m = load_map()
    good, unknown = {}, []
    with open(HDD, 'rb') as f:
        for p in paths:
            rel = os.path.relpath(p, ROOT)
            ori = open(pristine(p), 'rb').read()
            cur = open(p, 'rb').read()
            offs = m.get(rel)
            if isinstance(offs, int):
                offs = [offs]
            # ★★저장된 자리는 «내용과 무관하게» 신뢰한다.
            #   앞선 빌드로 덮어쓴 캐시는 원본도 현재본도 아니다("제3의 내용").
            #   내용으로 거르면 그런 자리를 놓쳐 폰트가 낡은 채로 남는다(2026-08-31 실수).
            ok = []
            for off in (offs or []):
                f.seek(off)
                if len(f.read(len(ori))) == len(ori):
                    ok.append(off)
            if ok:
                good[rel] = ok
            # ★저장된 자리를 찾았더라도 «다른 사본»이 더 있을 수 있으므로 항상 다시 훑는다
            unknown.append((rel, p, ori, cur))
    if unknown:
        # ★★needle 은 «원본»만으로는 부족하다 — 패치된 ISO 로 처음 플레이한 구간은
        #   «그때 빌드»로 캐시된다. 원본·현재 둘 다로 훑는다.
        needles = {}
        for rel, p, ori, cur in unknown:
            needles[rel + '\0o'] = ori[:NEEDLE]
            if cur[:NEEDLE] != ori[:NEEDLE]:
                needles[rel + '\0c'] = cur[:NEEDLE]
        hit = find_all(HDD, needles)
        with open(HDD, 'rb') as f:
            for rel, p, ori, cur in unknown:
                offs = sorted(set(hit.get(rel + '\0o', []) +
                                  hit.get(rel + '\0c', []) +
                                  good.get(rel, [])))
                # ★저장된 자리는 «무조건» 유지한다(앞선 빌드 내용이라 needle 로 못 찾는다).
                #   새로 찾은 자리는 «원본 또는 현재본과 전체가 같을 때만» 받는다 —
                #   ⛔앞 48바이트만 우연히 맞은 자리를 덮으면 엉뚱한 데이터를 망친다.
                keep = list(good.get(rel, []))
                for off in offs:
                    if off in keep:
                        continue
                    f.seek(off)
                    blk = f.read(len(ori))
                    if len(blk) == len(ori) and blk in (ori, cur):
                        keep.append(off)
                if keep:
                    good[rel] = sorted(set(keep))
    m.update(good)
    save_map(m)
    return good


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--write'
    if not os.path.exists(HDD):
        print('★HDD 이미지 없음: %s' % HDD)
        return 1
    paths = list(targets())
    found = locate(paths)
    n_copy = sum(len(v) for v in found.values())
    print("검사 %d개 중 캐시에 있는 것 %d개 (사본 %d벌)"
          % (len(paths), len(found), n_copy))
    for rel, offs in sorted(found.items()):
        if len(offs) > 1:
            print('  ★%s 사본 %d벌 %s' % (os.path.basename(rel), len(offs), offs))

    os.makedirs(HDDDIR, exist_ok=True)
    changed = same = 0
    with open(HDD, 'r+b') as f:
        for p in paths:
            rel = os.path.relpath(p, ROOT)
            if rel not in found:
                continue
            ori = open(pristine(p), 'rb').read()
            want = ori if mode == '--restore' else open(p, 'rb').read()
            if len(want) != len(ori):
                print('  ★%s 크기가 달라 건너뜀 (%d != %d)' % (rel, len(want), len(ori)))
                continue
            for off in found[rel]:            # ★사본 전부
                f.seek(off)
                cur = f.read(len(ori))
                if mode == '--status':
                    tag = ('원본' if cur == ori else
                           '트리와 동일' if cur == want else '★제3의 내용')
                    print('  %-34s @%-12d %s' % (os.path.basename(rel), off, tag))
                    continue
                bak = os.path.join(HDDDIR, 'cache_%s.orig' % os.path.basename(rel))
                if not os.path.exists(bak) and cur == ori:
                    with open(bak, 'wb') as g:
                        g.write(cur)
                if cur == want:
                    same += 1
                    continue
                f.seek(off)
                f.write(want)
                changed += 1
        if mode != '--status':
            f.flush()
            os.fsync(f.fileno())

    if mode != '--status':
        # 되읽기 검산
        bad = 0
        with open(HDD, 'rb') as f:
            for p in paths:
                rel = os.path.relpath(p, ROOT)
                if rel not in found:
                    continue
                want = open(pristine(p) if mode == '--restore' else p, 'rb').read()
                for off in found[rel]:
                    f.seek(off)
                    if f.read(len(want)) != want:
                        bad += 1
                        print('  ★검산 실패: %s @%d' % (rel, off))
        print('갱신 %d / 이미 동일 %d / 검산실패 %d' % (changed, same, bad))
        print('★xemu 를 완전히 종료한 뒤에 실행해야 반영된다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
