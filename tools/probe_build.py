"""변수 분리용 최소 시험 빌드. 폰트·압축은 **전혀 건드리지 않는다**.

지금까지 나온 사실 (실기 확인)
  시험1  idx2 «짧게+널»        -> 나옴 ✓
         idx4 «꽉 채움(널 없음)» -> **빈칸** ✗   내용 = ゲームを最初から開始します。
  시험2  idx3 «꽉 채움(널 없음)» -> 나옴 ✓
         idx4 «짧게+널»         -> 나옴 ✓
  ⇒ 「꽉 채우면 안 된다」는 규칙은 idx3 이 반증했다. 남은 갈래는 셋:
     (a) idx4 를 꽉 채우는 것만 실패   (b) 그 문장 내용이 문제   (c) 재현이 안 되는 현상

시험3 (지금) — 세 갈래를 한 번에 가른다. 전부 «꽉 채움(널 없음)».
  idx 4 : 시험1 과 **완전히 같은 내용**  -> 재현되는가
  idx 2 : 34B 꽉 채움                    -> 다른 항목에서 꽉 채우면?
  idx 5 : 43B 꽉 채움                    -> 또 다른 항목
  idx 3 : 원본 그대로 (대조군)

해석
  idx2·5 나오고 idx4 만 빈칸  -> (a) idx4 고유 문제. 그 레코드를 뜯는다.
  전부 빈칸                    -> 꽉 채우기가 문제. idx3 이 왜 됐는지 재확인.
  전부 나옴                    -> (c) 시험1 결과가 재현 안 됨. 원인을 다시 잡는다.
"""
import os
import shutil
from project import ROOT, WORK
from budget_menu import entries

ORIG = os.path.join(WORK, 'orig')
REL_MSG = os.path.join('menudata', 'TextData', 'Text_MenuInst_JP.msg')

PROBE = {
    4: 'ゲームを最初から開始します。',                     # 28B — 시험1 그대로
    2: 'わかりやすく操作方法を説明します。',               # 34B
    5: '前回、セーブしたエピソードから再開します。\n',      # 43B
}


def restore_all():
    for dp, dn, fns in os.walk(ORIG):
        for fn in fns:
            src = os.path.join(dp, fn)
            rel = os.path.relpath(src, ORIG)
            shutil.copy2(src, os.path.join(ROOT, rel))


if __name__ == '__main__':
    restore_all()
    print('원본 전량 원복 완료')
    d = bytearray(open(os.path.join(ORIG, REL_MSG), 'rb').read())
    _, es = entries()
    ok = True
    for i, t in sorted(PROBE.items()):
        e = es[i]
        b = t.encode('cp932')
        fill = '꽉 채움' if len(b) == e['bytes'] else '널 %d' % (e['bytes'] - len(b))
        if len(b) > e['bytes']:
            print('★ idx %d 예산 초과 %d > %d' % (i, len(b), e['bytes']))
            ok = False
            continue
        d[e['off']:e['off'] + e['bytes']] = b + b'\x00' * (e['bytes'] - len(b))
        print('idx %d @%05x  %dB / %dB  %-8s  %s' % (i, e['off'], len(b), e['bytes'], fill, t))
    assert ok
    o = open(os.path.join(ORIG, REL_MSG), 'rb').read()
    assert len(d) == len(o)
    with open(os.path.join(ROOT, REL_MSG), 'wb') as f:
        f.write(bytes(d))
    print('\n%s 만 수정.' % REL_MSG)
