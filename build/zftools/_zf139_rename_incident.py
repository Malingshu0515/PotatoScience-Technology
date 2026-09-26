# -*- coding: utf-8 -*-
u"""_zf139_rename.py —— 把本轮从 **ZF136 改号成 ZF139**

为什么改号（查证之后才动的手）：
  本轮开工时我问过盘上最新的号（那时最新是 ZF135、我取了 ZF136）。
  但在本轮进行到一半时，另一条线提交了 `8ed549a ZF137`，那一笔**同时**往
  `docs/开发档案.md` 的 §5 表里塞了一行 `| ZF136 |`（他们是"换掉旧 star_steel_ingot.png"
  那件事）⇒ **ZF136 被占了**，而 ZF137 也是他们的。
  ⇒ 本轮改用 **ZF139**（交接文档 §6 里点名过这条：别让读者看到两节同号）。

这个脚本做四件事（都能重复跑，第二次会报"已经改过"）：
  ① `build/zftools/_zf136_*` → `_zf139_*`（脚本、txt 证据、日志）；
  ② 这些文件**内容**里的 `136` → `139`（只动我自己写的 .py/.java；`.log` 只改名不动内容）；
  ③ `src/main/java/com/potatost/mod/Zf136Check.java` → `Zf139Check.java`，
     连 `PotatoST.java` 那行挂载一起改；
  ④ 救援目录 `zf136_pre` → `zf139_pre`（备份根也要跟着改名，
     否则下一轮按"zf139_pre"去找会找不到）。
"""
import io
import os
import re
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
SRC = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
RESCUE = r"C:\PotatoST救援"
OLD, NEW = u"136", u"139"

notes, fails = [], []


def rename_path(old_path, new_path, rewrite=True):
    if not os.path.exists(old_path):
        if os.path.exists(new_path):
            notes.append(u"  [已改过] %s" % os.path.basename(new_path))
            return
        fails.append(u"两边都不在：%s" % old_path)
        return
    if rewrite and old_path.endswith((u".py", u".java", u".txt", u".md")):
        raw = open(old_path, "rb").read()
        text = raw.decode("utf-8")
        n = text.count(OLD)
        if n:
            open(old_path, "wb").write(text.replace(OLD, NEW).encode("utf-8"))
            notes.append(u"  [改内容 %2d 处] %s" % (n, os.path.basename(old_path)))
        else:
            notes.append(u"  [无内容改动]   %s" % os.path.basename(old_path))
    else:
        notes.append(u"  [只改名]       %s" % os.path.basename(old_path))
    shutil.move(old_path, new_path)


def main():
    print(u"===== ① build/zftools 里的本轮文件 =====")
    if os.path.isdir(ZT):
        for name in sorted(os.listdir(ZT)):
            if u"zf136" in name:
                rename_path(os.path.join(ZT, name),
                            os.path.join(ZT, name.replace(u"zf136", u"zf139")),
                            rewrite=not name.endswith(u".log"))
    check = os.path.join(ZT, u"check")
    if os.path.isdir(check):
        for name in sorted(os.listdir(check)):
            if u"zf136" in name or u"Zf136" in name:
                rename_path(os.path.join(check, name),
                            os.path.join(check, name.replace(u"zf136", u"zf139")
                                         .replace(u"Zf136", u"Zf139")))

    print(u"===== ② 探针类与挂载点 =====")
    rename_path(os.path.join(SRC, u"Zf136Check.java"), os.path.join(SRC, u"Zf139Check.java"))
    pot = os.path.join(SRC, u"PotatoST.java")
    text = io.open(pot, encoding=u"utf-8", newline=u"").read()
    if u"Zf136Check" in text:
        text = text.replace(u"Zf136Check", u"Zf139Check").replace(u"ZF136", u"ZF139")
        io.open(pot, u"w", encoding=u"utf-8", newline=u"").write(text)
        notes.append(u"  [改内容] PotatoST.java 的探针挂载行 → Zf139Check")
    else:
        notes.append(u"  [已改过] PotatoST.java 里没有 Zf136Check")

    print(u"===== ③ 备份根 =====")
    old_bk, new_bk = os.path.join(RESCUE, u"zf136_pre"), os.path.join(RESCUE, u"zf139_pre")
    if os.path.isdir(old_bk):
        # 备份里那两份清单的文件名也一起改（内容里记的是"本轮开始前这些路径应当不存在"）
        for name in (u"_zf136_newfiles.txt",):
            if os.path.exists(os.path.join(old_bk, name)):
                os.rename(os.path.join(old_bk, name),
                          os.path.join(old_bk, name.replace(u"zf136", u"zf139")))
        os.rename(old_bk, new_bk)
        note = (u"\n【改号说明】本轮原本取 ZF136，进行到一半时另一条线提交 8ed549a（ZF137）\n"
                u"并同时在开发档案 §5 塞了一行 | ZF136 |（换 star_steel_ingot.png 那件事）\n"
                u"⇒ ZF136 被占，本轮改用 **ZF139**。备份根随之改名 zf136_pre → zf139_pre。\n")
        with io.open(os.path.join(new_bk, u"_说明.txt"), u"a", encoding=u"utf-8",
                     newline=u"\n") as f:
            f.write(note)
        notes.append(u"  [改名] zf136_pre → zf139_pre（并追加改号说明）")
    else:
        notes.append(u"  [已改过] zf139_pre 已在盘上")

    print(u"\n".join(notes))
    # ---- 自检：不许再有 zf136 残留 ----
    left = []
    for base in (ZT, os.path.join(ZT, u"check"), SRC):
        if not os.path.isdir(base):
            continue
        for name in os.listdir(base):
            if u"zf136" in name or u"Zf136" in name:
                left.append(os.path.join(base, name))
    if left:
        fails.append(u"还有残留：%s" % u"、".join(left))
    if os.path.isdir(os.path.join(RESCUE, u"zf136_pre")):
        fails.append(u"救援目录 zf136_pre 还在")
    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
