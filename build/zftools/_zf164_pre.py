# -*- coding: utf-8 -*-
u"""_zf164_pre.py —— ZF164 动手前备份（§10）。

⚠ 本轮开动时先改了三个文件才开始备份 ⇒ 它们的"改前件"从 **git HEAD** 取（ZF157/ZF159 那条先例），
其余从盘上拷。落到 `C:\\PotatoST救援\\zf164_pre\\`，逐份核 sha1 + 回读。

跑法：python build\\zftools\\_zf164_pre.py
"""
import glob
import hashlib
import io
import os
import shutil
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

PROJ = r"E:\PotatoST"
DST = r"C:\PotatoST救援\zf164_pre"

# 从 git HEAD 取（动手早于备份的那几份）
FROM_HEAD = [r"build.gradle", r"src\main\java\com\potatost\mod\FillingMachineBlockEntity.java"]
EXPLICIT = [
    r"src\main\java\com\potatost\mod\MekChemicalBridge.java",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"build\zftools\_zf162_verify.py",
    r"build\zftools\_zf149_verify.py",
    r"build\zftools\_zf149_jar.py",
    r"build\zftools\_zf156_jarcheck.py",
    r"build\zftools\_zf155_jarcheck.py",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.13.jar",
    r"release\PotatoST-0.13.jar.sha1",
    r"build\libs\potato_s_t-0.13.jar",
]


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def main():
    if not os.path.isdir(DST):
        os.makedirs(DST)
    fails, total, lines = [], 0, []
    for rel in sorted(set(EXPLICIT)):
        src = os.path.join(PROJ, rel)
        if not os.path.isfile(src):
            fails.append(u"改前件不在：%s" % rel)
            continue
        dst = os.path.join(DST, rel)
        d = os.path.dirname(dst)
        if not os.path.isdir(d):
            os.makedirs(d)
        shutil.copy2(src, dst)
        if sha(src) != sha(dst):
            fails.append(u"%s 回读不一致" % rel)
            continue
        total += 1
        lines.append(u"%s  %s" % (sha(src), rel))
    # 工具目录（整目录，门的跟平要用）
    for p in sorted(glob.glob(os.path.join(PROJ, u"build", u"zftools", u"*.py"))):
        rel = os.path.relpath(p, PROJ)
        if rel in EXPLICIT:
            continue
        dst = os.path.join(DST, rel)
        d = os.path.dirname(dst)
        if not os.path.isdir(d):
            os.makedirs(d)
        shutil.copy2(p, dst)
        if sha(p) != sha(dst):
            fails.append(u"%s 回读不一致" % rel)
            continue
        total += 1
        lines.append(u"%s  %s" % (sha(p), rel))
    # git HEAD 那两份
    for rel in FROM_HEAD:
        r = subprocess.run([u"git", u"-C", PROJ, u"show", u"HEAD:" + rel.replace(os.sep, u"/")],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if r.returncode != 0:
            fails.append(u"git HEAD 取不到 %s" % rel)
            continue
        dst = os.path.join(DST, rel)
        d = os.path.dirname(dst)
        if not os.path.isdir(d):
            os.makedirs(d)
        with open(dst, "wb") as fh:
            fh.write(r.stdout)
        total += 1
        lines.append(u"%s  %s  (git HEAD)" % (sha(dst), rel))
    with io.open(os.path.join(DST, u"_manifest.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(u"\n".join(lines) + u"\n")
    print(u"备份根：%s" % DST)
    print(u"备份成功 %d 份（清单 _manifest.txt；其中 2 份取自 git HEAD）" % total)
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
