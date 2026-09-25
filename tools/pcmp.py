"""PCMP 컨테이너 — LZSS 압축. 해독 완료.

    0x00 'PCMP'
    0x04..0x0f  0
    0x10 u32 blobs   항상 1
    0x14 u32 dec     압축해제 크기
    0x18 u32 enc     압축 크기
    0x1c u32 0
    0x20 ...         LZSS 스트림. 풀면 'TXRB' / 'RSBN' / 'EESB' 등으로 시작

LZSS 문법:
    플래그 바이트를 **MSB 부터** 한 비트씩 쓴다.
      0 = 리터럴 1바이트
      1 = 매치 2바이트   off = ((b0 >> 4) | (b1 << 4)) + 1
                         len = (b0 & 0x0F) + 3
    ★★off 가 지금까지 낸 출력보다 크면 **0을 채운다**(윈도가 0으로 초기화된 셈).
      이 처리가 없으면 파일 첫 매치에서 바로 터진다 — 내가 처음에 여기서 막혔다.
      풀린 데이터 앞부분이 헤더의 널 밭이라 이 경로를 아주 많이 탄다.

출처: reshax.com/topic/17944 (Rabatini). 이 저장소에서 전 PCMP 200개 왕복 검증함.
"""
import struct


class PcmpError(Exception):
    pass


def decompress(data):
    """PCMP 파일 전체 바이트 -> 풀린 바이트."""
    if data[:4] != b'PCMP':
        raise PcmpError('PCMP 매직이 아니다: %r' % data[:4])
    out_size, comp_size = struct.unpack_from('<II', data, 0x14)
    avail = len(data) - 0x20
    if comp_size == 0 or comp_size > avail:
        comp_size = avail
    return lzss_decode(data[0x20:0x20 + comp_size], out_size)


def lzss_decode(comp, out_size):
    out = bytearray()
    idx, ilen = 0, len(comp)
    if ilen == 0:
        raise PcmpError('스트림이 비었다')
    b, bits = comp[idx], 8
    idx += 1
    while len(out) < out_size:
        if idx > ilen:
            raise PcmpError('스트림이 일찍 끝났다 (%d/%d)' % (len(out), out_size))
        op = b & 0x80
        b = (b << 1) & 0xff
        bits -= 1
        if bits == 0:
            if idx >= ilen:
                break
            b, bits = comp[idx], 8
            idx += 1
        if op:
            if idx + 1 >= ilen:
                raise PcmpError('매치 토큰이 잘렸다')
            off = ((comp[idx] >> 4) | (comp[idx + 1] << 4)) + 1
            cnt = (comp[idx] & 0x0F) + 3
            idx += 2
            for _ in range(cnt):
                if len(out) >= out_size:
                    break
                out.append(0 if off > len(out) else out[-off])
        else:
            if idx >= ilen:
                raise PcmpError('리터럴이 잘렸다')
            out.append(comp[idx])
            idx += 1
    return bytes(out)


def lzss_tokens(raw, max_off=4096, max_len=18, chain=48):
    """[(매치인가, 데이터바이트)] 로 쪼갠다."""
    toks = []
    i, n = 0, len(raw)
    table = {}
    while i < n:
        best_len, best_off = 0, 0
        if i + 3 <= n:
            key = raw[i:i + 3]
            for cand in reversed(table.get(key, ())):
                off = i - cand
                if off > max_off:
                    break
                L = 0
                while L < max_len and i + L < n and raw[cand + L] == raw[i + L]:
                    L += 1
                if L > best_len:
                    best_len, best_off = L, off
                    if L == max_len:
                        break
        if best_len >= 3:
            v = (best_off - 1) & 0xFFF
            toks.append((True, bytes(((v & 0x0F) << 4 | (best_len - 3), (v >> 4) & 0xFF))))
            step = best_len
        else:
            toks.append((False, raw[i:i + 1]))
            step = 1
        for k in range(step):
            j = i + k
            if j + 3 <= n:
                lst = table.setdefault(raw[j:j + 3], [])
                lst.append(j)
                if len(lst) > chain:
                    del lst[0]
        i += step
    return toks


def lzss_encode(raw, **kw):
    """되감기 검증·재빌드용 인코더.

    ★★디코더가 **8번째 토큰의 데이터를 읽기 전에** 다음 플래그 바이트를 먼저
      집어간다. 그래서 스트림은 이렇게 흐른다:
          F0 d0 d1 d2 d3 d4 d5 d6 | F1 | d7 | d8 ... d14 | F2 | d15 | ...
      즉 F(g+1) 이 d(8g+6) 과 d(8g+7) **사이**에 낀다.
      이걸 놓쳐서 첫 인코더가 「리터럴이 잘렸다」로 터졌다.
      ★인코더가 디코더보다 잘 깨진다 (reference_custom_codec_playbook) —
      selftest.py 의 왕복 대조를 반드시 통과시킬 것.
    """
    toks = lzss_tokens(raw, **kw)
    out = bytearray()
    flags = []                      # (스트림 위치, 플래그값)
    pos = len(out)
    out.append(0)
    flag = 0
    for i, (is_match, data) in enumerate(toks):
        bit = i % 8
        if is_match:
            flag |= 0x80 >> bit
        if bit == 7:
            flags.append((pos, flag))
            flag = 0
            pos = len(out)          # 다음 플래그 칸을 d7 **앞**에 낸다
            out.append(0)
        out += data
    if len(toks) % 8:
        flags.append((pos, flag))
    for p, v in flags:
        out[p] = v
    return bytes(out)


def build(raw):
    """풀린 바이트 -> PCMP 파일 바이트."""
    comp = lzss_encode(raw)
    hdr = bytearray(0x20)
    hdr[0:4] = b'PCMP'
    struct.pack_into('<I', hdr, 0x10, 1)
    struct.pack_into('<I', hdr, 0x14, len(raw))
    struct.pack_into('<I', hdr, 0x18, len(comp))
    return bytes(hdr) + comp


def encode_decode_ok(raw):
    return lzss_decode(lzss_encode(raw), len(raw)) == raw


if __name__ == '__main__':
    import os, sys
    from project import ROOT
    only = sys.argv[1] if len(sys.argv) > 1 else None
    ok = bad = 0
    fails = []
    for dp, dn, fns in os.walk(ROOT):
        for fn in fns:
            p = os.path.join(dp, fn)
            if os.path.getsize(p) < 32:
                continue
            with open(p, 'rb') as f:
                head = f.read(4)
            if head != b'PCMP':
                continue
            rel = os.path.relpath(p, ROOT)
            if only and only.lower() not in rel.lower():
                continue
            data = open(p, 'rb').read()
            want = struct.unpack_from('<I', data, 0x14)[0]
            try:
                d = decompress(data)
            except PcmpError as e:
                bad += 1
                fails.append((rel, str(e)))
                continue
            if len(d) != want:
                bad += 1
                fails.append((rel, '크기 %d != %d' % (len(d), want)))
            else:
                ok += 1
                if only:
                    print('%-52s %s dec=%d' % (rel, d[:4].decode('latin1'), len(d)))
    print('\n해제 성공 %d / 실패 %d' % (ok, bad))
    for r, e in fails[:20]:
        print('  ✗ %-52s %s' % (r, e))
