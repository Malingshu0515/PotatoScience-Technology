# -*- coding: utf-8 -*-
u"""_zf168_pre.py —— ZF168 动手前备份（§10）。

⚠ 本轮开动时先改了代码才开始备份 ⇒ 改过的那些文件从 **git HEAD** 取（ZF157/ZF164 那条先例），
其余从盘上拷。落到 `C:\\PotatoST救援\\zf168_pre\\`，逐份核 sha1 + 回读。

跑法：python build\\zftools\\_zf168_pre.py
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

PROJ = r"E:\PotatoST"
DST = r"C:\PotatoST救援\zf168_pre"

FROM_HEAD = [
    r"src\main\java\com\potatost\mod\FluidConverterBlockEntity.java",
    r"src\main\java\com\potatost\mod\FluidConverterBlock.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"src\main\resources\assets\potato_s_t\lang\lzh.json",
]
FROM_DISK = [
    r"src\main\java\com\potatost\mod\FluidConverterMenu.java",
    r"src\main\java\com\potatost\mod\client\FluidConverterScreen.java",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.13.jar",
    r"release\PotatoST-0.13.jar.sha1",
    r"build\libs\potato_s_t-0.13.jar",
    r"build\zftools\_zf149_verify.py",
    r"build\zftools\_zf166_verify.py",
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
    fails, lines, total = [], [], 0
    for rel in FROM_DISK:
        src = os.path.join(PROJ, rel)
        if not os.path.isfile(src):
            fails.append(u"不在盘上：%s" % rel)
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
    # 整目录工具（门的跟平要用）
    import glob
    for p in sorted(glob.glob(os.path.join(PROJ, u"build", u"zftools", u"*.py"))):
        rel = os.path.relpath(p, PROJ)
        if rel in FROM_DISK:
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
    with io.open(os.path.join(DST, u"_manifest.txt"), "w", encoding="utf-8", newline=u"\n") as fh:
        fh.write(u"\n".join(lines) + u"\n")
    print(u"备份根：%s" % DST)
    print(u"备份成功 %d 份（清单 _manifest.txt；其中 %d 份取自 git HEAD）" % (total, len(FROM_HEAD)))
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
