# -*- coding: utf-8 -*-
u"""_zf107_eol.py —— §4.8：本轮碰过的文件换行风格必须与原样式一致（只读，不改）

`.gitattributes` 是 `* -text`（不做任何换行转换）⇒ **盘上是什么，仓库里就是什么**。
所以本轮新建/追加的每个文件都要自己交代清楚是 LF 还是 CRLF。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ADIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\advancement")
LANGS = [os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang", n + u".json")
         for n in ("zh_cn", "en_us", "ja_jp", "ru_ru")]
EXTRA = [
    os.path.join(ROOT, r"build\zftools\check\Zf107Check.java"),
    os.path.join(ROOT, r"docs\开发档案.md"),
    os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md"),
    os.path.join(ROOT, r"build\zftools\_zf107_adv.py"),
    os.path.join(ROOT, r"build\zftools\_zf107_verify.py"),
    os.path.join(ROOT, r"build\zftools\_zf107_falsify.py"),
    os.path.join(ROOT, r"build\zftools\_zf107_probe_archive.py"),
]
NEW_NODES = ["crushing", "pressing", "wiring", "first_power", "capacitor",
             "blast_furnace", "steel", "titanium", "electrolyzer", "gas_handling",
             "alloy_smelter", "light_alloy", "hard_alloy", "stable_block",
             "titanium_tools", "oil", "distillation", "fuel", "sulfur", "ammonia",
             "combustion", "acid", "music_disc_anvil", "music_disc_jasmine"]


def eol(path):
    b = open(path, "rb").read()
    crlf = b.count(b"\r\n")
    lf = b.count(b"\n") - crlf
    cr = b.count(b"\r") - crlf
    return crlf, lf, cr


def main():
    bad = 0
    files = [os.path.join(ADIR, n + u".json") for n in NEW_NODES] + LANGS + EXTRA
    print(u"%-46s %6s %6s %4s  %s" % (u"文件", u"CRLF", u"LF", u"裸CR", u"判定"))
    for p in files:
        if not os.path.exists(p):
            print(u"  [MISS] %s" % p)
            bad += 1
            continue
        crlf, lf, cr = eol(p)
        rel = p.replace(ROOT + "\\", "")
        if cr or (crlf and lf):
            verdict = u"**混合！**"
            bad += 1
        elif crlf:
            verdict = u"CRLF（原样式？）"
        else:
            verdict = u"LF"
        print(u"%-46s %6d %6d %4d  %s" % (rel[-46:], crlf, lf, cr, verdict))
    print(u"")
    print(u"混合/异常文件 = %d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
