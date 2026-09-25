"""PCMP LZSS 인코더 개선 — `Zenkaku_Menu.txb` 를 크기 안에 넣기 위해.

기존 `pcmp.lzss_tokens` 는 **그리디 + 후보 체인 48개 제한**이라 원본 인코더보다
나쁘다. 실측: 무수정 왕복인데도 Menu 만 **+2578 B**(나머지 27개는 전부 원본보다 작다).
그 2578 B 때문에 「메뉴 폰트」인 `Zenkaku_Menu` 를 **한 번도 시험 못 했다**.

개선 두 가지
  1. 후보 체인 제한을 크게 (48 -> chain)
  2. **lazy matching** — 지금 자리의 매치보다 한 칸 뒤 매치가 더 길면 리터럴로 흘린다

토큰 문법·플래그 배치는 `pcmp.py` 그대로 쓴다(★거긴 이미 실기로 검증됐다).
"""
import struct
import sys
from pcmp import lzss_encode, lzss_decode, decompress


def tokens_lazy(raw, max_off=4096, max_len=18, chain=4096, lazy=True):
    toks = []
    i, n = 0, len(raw)
    table = {}

    def find(at):
        """(길이, 오프셋). 없으면 (0,0)."""
        if at + 3 > n:
            return 0, 0
        bl, bo = 0, 0
        for cand in reversed(table.get(raw[at:at + 3], ())):
            off = at - cand
            if off > max_off:
                break
            L = 0
            while L < max_len and at + L < n and raw[cand + L] == raw[at + L]:
                L += 1
            if L > bl:
                bl, bo = L, off
                if L == max_len:
                    break
        return bl, bo

    def add(at, cnt):
        for k in range(cnt):
            j = at + k
            if j + 3 <= n:
                lst = table.setdefault(raw[j:j + 3], [])
                lst.append(j)
                if len(lst) > chain:
                    del lst[0]

    while i < n:
        bl, bo = find(i)
        if bl >= 3 and lazy and bl < max_len and i + 1 < n:
            # 한 칸 뒤가 더 길면 지금은 리터럴로 흘린다
            add(i, 1)
            nl, _ = find(i + 1)
            # add() 한 것을 되돌린다 (i 를 후보 목록에서 뺀다)
            key = raw[i:i + 3] if i + 3 <= n else None
            if key is not None and table.get(key) and table[key][-1] == i:
                table[key].pop()
            if nl > bl:
                toks.append((False, raw[i:i + 1]))
                add(i, 1)
                i += 1
                continue
        if bl >= 3:
            v = (bo - 1) & 0xFFF
            toks.append((True, bytes(((v & 0x0F) << 4 | (bl - 3), (v >> 4) & 0xFF))))
            step = bl
        else:
            toks.append((False, raw[i:i + 1]))
            step = 1
        add(i, step)
        i += step
    return toks


def encode(raw, **kw):
    import pcmp
    old = pcmp.lzss_tokens
    pcmp.lzss_tokens = lambda r, **k: tokens_lazy(r, **kw)
    try:
        return lzss_encode(raw)
    finally:
        pcmp.lzss_tokens = old


def build(raw, **kw):
    comp = encode(raw, **kw)
    hdr = bytearray(0x20)
    hdr[0:4] = b'PCMP'
    struct.pack_into('<I', hdr, 0x10, 1)
    struct.pack_into('<I', hdr, 0x14, len(raw))
    struct.pack_into('<I', hdr, 0x18, len(comp))
    return bytes(hdr) + comp


if __name__ == '__main__':
    import os
    import time
    from project import FONT_DIR, pristine
    import pcmp as P
    name = sys.argv[1] if len(sys.argv) > 1 else 'Zenkaku_Menu.txb'
    p = pristine(os.path.join(FONT_DIR, name))
    raw = open(p, 'rb').read()
    d = decompress(raw)
    print('%s  원본 파일 %d B / 풀림 %d B' % (name, len(raw), len(d)))
    t = time.time()
    old = P.build(d)
    print('  기존 인코더      %8d B  (%+d)   %.1fs' % (len(old), len(old) - len(raw), time.time() - t))
    for chain, lazy in ((4096, False), (4096, True)):
        t = time.time()
        new = build(d, chain=chain, lazy=lazy)
        ok = lzss_decode(new[0x20:], len(d)) == d
        print('  chain=%-5d lazy=%-5s %8d B  (%+d)  왕복%s  %.1fs'
              % (chain, lazy, len(new), len(new) - len(raw), 'OK' if ok else '★실패',
                 time.time() - t))
