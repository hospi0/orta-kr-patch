"""*.msg / *.mnu 안의 문자열 추출.

.msg 는 무압축이고 대사가 NUL 종단 문자열로 그대로 들어 있다.
레코드 문법(u32 ID + 0x24 헤더 + 줄엔트리)은 파일마다 줄엔트리 길이가 달라
★아직 완전히 확정되지 않았다 — 그래서 문자열은 「바이트 스캔」으로 뽑는다.
스캔은 오프셋을 그대로 돌려주므로 제자리 덮어쓰기에는 충분하다.

★검출기는 문자열 단위로 판정한다 (구간 비율로 거르면 진짜 데이터가 통째로
탈락한다 — feedback_detector_ratio_per_string_not_per_region).
"""


def _lead(b):
    return 0x81 <= b <= 0x9f or 0xe0 <= b <= 0xef


def _trail(b):
    return 0x40 <= b <= 0xfc and b != 0x7f


def _classify(seg):
    """NUL 종단 후보를 (종류, 문자열) 로. 아니면 None."""
    try:
        t = seg.decode('cp932')
    except Exception:
        return None
    if not t:
        return None
    jp = sum(1 for c in t if
             0x3040 <= ord(c) <= 0x30ff or 0x4e00 <= ord(c) <= 0x9fff
             or 0x3000 <= ord(c) <= 0x303f or 0xff01 <= ord(c) <= 0xff5e
             or ord(c) in (0x30fb, 0xb0))
    plain = sum(1 for c in t if (0x20 <= ord(c) < 0x7f) or c == '\n')
    if jp and jp + plain == len(t) and jp >= 2:
        return ('jp', t)
    if plain == len(t):
        letters = sum(1 for c in t if c.isalpha())
        if letters >= 4 and letters / len(t) > 0.5 and ' ' in t.strip():
            return ('en', t)
        if letters >= 6 and letters / len(t) > 0.8:
            return ('en', t)
    return None


def scan(data, minlen=2):
    """[(오프셋, 종류, 문자열)] — 종류는 'jp' / 'en'."""
    out, n, i = [], len(data), 0
    while i < n:
        start = j = i
        while j < n:
            c = data[j]
            if 0x20 <= c < 0x7f or c == 0x0a:
                j += 1
            elif _lead(c) and j + 1 < n and _trail(data[j + 1]):
                j += 2
            else:
                break
        if j > start and j < n and data[j] == 0 and (j - start) >= minlen:
            r = _classify(data[start:j])
            if r:
                out.append((start, r[0], r[1]))
            i = j + 1
        else:
            i = start + 1
    return out


def scan_file(path, minlen=2):
    with open(path, 'rb') as f:
        return scan(f.read(), minlen)


def data_end(data):
    """꼬리 널 패딩을 뺀 실사용 길이. 파일은 2048 배수로 패딩돼 있다."""
    i = len(data)
    while i > 0 and data[i - 1] == 0:
        i -= 1
    return i


if __name__ == '__main__':
    import os, sys, collections
    from project import msg_files, ROOT
    tot = collections.Counter()
    chars = collections.Counter()
    rows = []
    for p, lang in msg_files():
        d = open(p, 'rb').read()
        ss = scan(d)
        n, c = len(ss), sum(len(t) for _, _, t in ss)
        rows.append((os.path.relpath(p, ROOT), lang, n, c, len(d) - data_end(d)))
        tot[lang + '_str'] += n
        tot[lang + '_char'] += c
        tot[lang + '_slack'] += len(d) - data_end(d)
        if lang == 'JP':
            for _, _, t in ss:
                chars.update(t)
    for r in sorted(rows, key=lambda r: -r[3]):
        print('%-48s %-3s %5d 문자열 %7d 자  슬랙 %6d' % r)
    print()
    for k in sorted(tot):
        print('  %-10s %d' % (k, tot[k]))
    kana = {c for c in chars if 0x3040 <= ord(c) <= 0x30ff}
    kanji = {c for c in chars if 0x4e00 <= ord(c) <= 0x9fff}
    print('\nJP 고유문자 %d (가나 %d, 한자 %d, 기타 %d)'
          % (len(chars), len(kana), len(kanji), len(chars) - len(kana) - len(kanji)))
