"""공통 경로·상수. 원본 자산은 저장소에 두지 않는다."""
import os

# 원본 = extract-xiso 로 이미 풀린 디렉터리 (이름이 .xiso 지만 폴더다)
ROOT = r"C:\claude\roms\xbox\Panzer Dragoon Orta (USA).xiso"

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(REPO, 'work')
TRANS = os.path.join(REPO, 'trans')
DOCS = os.path.join(REPO, 'docs')

FONT_DIR = os.path.join(ROOT, 'sprite', 'Font')
MSG_DIRS = [os.path.join(ROOT, 'messageevent'),
            os.path.join(ROOT, 'menudata', 'TextData')]

# --- 폰트 상수 (docs/survey.md 「폰트」 참조) ---
GLYPH_W = 28
GLYPH_H = 28
ATLAS_W = 512
ATLAS_H = 1024          # 페이지 하나. z_tbl 헤더 [1] 이 페이지 수
ATLAS_BPP = 4           # ★추론값. PCMP 를 풀면 실측으로 확정할 것
CELLS_PER_PAGE = (ATLAS_W // GLYPH_W) * (ATLAS_H // GLYPH_H)   # 18*36 = 648

# SJIS 2바이트 리드 47개 (z_tbl 인덱스 = 리드순번*192 + (트레일-0x40))
LEADS = list(range(0x81, 0xa0)) + list(range(0xe0, 0xf0))
ZTBL_STRIDE = 192
ZTBL_ENTRIES = len(LEADS) * ZTBL_STRIDE     # 9024

# 장면 이름: Reisyo_<이름>_z_tbl.bin ↔ Zenkaku_<이름>.txb
SCENES = (['Stage%d' % i for i in range(1, 11)]
          + ['Menu', 'Movie', 'OpeningDemo', 'Tutorial']
          + ['Mission0%d' % i for i in range(1, 6)]
          + ['SubScenario0%d' % i for i in range(1, 8)])
COMMON_TBL = 'Reisyo_Cmn_z_tbl_cmn.bin'     # 공용(가나·기호). Zenkaku_Common.txb 와 짝
HANKAKU_TBL = 'Arial_h_tbl.bin'             # 반각 1바이트 표. font_hs_test_arial.txb 와 짝


def pristine(path):
    """★빌드가 제자리를 덮어쓰므로 «조사·예산»은 항상 work/orig 백업을 본다."""
    rel = os.path.relpath(path, ROOT)
    bak = os.path.join(WORK, 'orig', rel)
    return bak if os.path.exists(bak) else path


def scene_tbl(scene):
    return pristine(os.path.join(FONT_DIR, 'Reisyo_%s_z_tbl.bin' % scene))


def scene_atlas(scene):
    return pristine(os.path.join(FONT_DIR, 'Zenkaku_%s.txb' % scene))


def msg_files():
    """모든 .msg 를 (경로, 언어) 로. 언어는 'JP' / 'EN'."""
    out = []
    for d in MSG_DIRS:
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith('.msg'):
                continue
            lang = 'JP' if '_JP' in fn else ('EN' if '_EN' in fn else '??')
            out.append((os.path.join(d, fn), lang))
    return out
