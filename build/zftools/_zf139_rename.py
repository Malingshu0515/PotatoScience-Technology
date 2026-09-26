# -*- coding: utf-8 -*-
u"""_zf139_rename.py —— 收拾我 22:31 那次改号造成的误伤，并把本轮定到 **ZF139**

## 出了什么事（如实记）

22:31 我跑了 `_zf138_rename.py`（当时想把本轮从 ZF136 改成 ZF138，因为档案 §5 里
ZF136 那一行已经被另一条线占了）。那个脚本的做法是"**凡是 `build/zftools` 里名字带
`zf136` 的，一律改名成 `zf138` 并把内容里的 136 换成 138**" —— 这是**错的做法**：

  · 那条线自己那时**已经在用 `_zf138_*` 这个名字**了（`_zf138_look.txt` 22:14、
    `_zf138_diff.png` 22:16 就是他们的产物）；
  · 于是我的改名把他们**同一件事的两套稿子**（`_zf136_*` 旧稿 与 `_zf138_*` 新稿）
    撞在了一起：`shutil.move` 在 Windows 上目标存在时会**覆盖** ⇒
    他们 `_zf138_*.py` 的内容被替换成了他们自己的 `_zf136_*.py` 旧稿（只差号码）。

**能救的**：他们那 9 个件 + `zf136_pre/` 的**内容**完好（我的替换只碰了号码，
逐个查过：所有 `138` 都出现在 `ZF138`/`zf138` 这类号码位置，没有一个是数据值
—— 见本脚本的"写前自检"）。⇒ **把它们逐字节还原回 `_zf136_*`**，
与档案里那一行 `| ZF136 |` 和 `zf136_pre` 对齐。

**救不回的**：他们 `_zf138_*.py`（新稿）若与旧稿有差别，那部分已丢。这条写进交接 §6，
请他们核对/重生成。

## 本轮定号

ZF136（他们的档案行）、ZF137（他们的提交）、ZF138（他们正在用的文件名）**都占着**
⇒ 本轮改 **ZF139**。我自己的全部产物从 `_zf138_*` 改名成 `_zf139_*`。
"""
import io
import os
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

# 另一条线的件（当前叫 138，要还原成 136）
THEIRS = [u"_zf138_apply.py", u"_zf138_diff.py", u"_zf138_diff.png", u"_zf138_docs.py",
          u"_zf138_look.py", u"_zf138_look.txt", u"_zf138_row.txt", u"_zf138_section.md",
          u"_zf138_shape.py"]
THEIRS_DIR = u"zf138_pre"

notes, fails = [], []


def swap(path_from, path_to, a, b):
    u"""把 path_from 里的 a 换成 b 再写到 path_to（两个都指同一份文件时就是原地改）。

    ⚠ 二进制件（png）**只改名、不解码** —— 第一版对 PNG 也 decode("utf-8")，
    当场 UnicodeDecodeError（0x89 = PNG 魔数）。
    """
    textual = path_from.endswith((u".py", u".md", u".txt"))
    n = 0
    if textual:
        raw = open(path_from, "rb").read()
        text = raw.decode("utf-8")
        n = text.count(a)
        if n:
            open(path_from, "wb").write(text.replace(a, b).encode("utf-8"))
    if path_from != path_to:
        if os.path.exists(path_to):
            fails.append(u"目标已存在，不敢覆盖：%s" % path_to)
            return
        shutil.move(path_from, path_to)
    notes.append(u"  [还原] %-24s 改了 %d 处号码" % (os.path.basename(path_to), n))


def main():
    print(u"===== 写前自检：他们那些件里的 138 是不是全在号码位置 =====")
    bad = []
    for name in THEIRS:
        p = os.path.join(ZT, name)
        if not os.path.exists(p):
            fails.append(u"找不到：%s" % name)
            continue
        if name.endswith((u".png",)):
            continue
        for i, line in enumerate(io.open(p, encoding=u"utf-8").read().split(u"\n")):
            j = 0
            while True:
                k = line.find(u"138", j)
                if k < 0:
                    break
                j = k + 3
                ctx = line[max(0, k - 6):k + 8]
                if not any(t in ctx for t in (u"zf138", u"ZF138", u"Zf138", u"A138")):
                    bad.append(u"%s:%d  %s" % (name, i + 1, ctx))
    if bad:
        print(u"  !! 有 138 不在号码位置，停手：")
        for b in bad:
            print(u"     " + b)
        return 1
    print(u"  [OK] 逐个查过：全是号码（ZF138 / zf138 / _zf138），没有数据值被误伤")
    print(u"")
    print(u"===== ① 还原另一条线的件（138 → 136）=====")
    for name in THEIRS:
        p = os.path.join(ZT, name)
        if not os.path.exists(p):
            notes.append(u"  [已还原] %s（原名已在）" % name.replace(u"138", u"136"))
            continue
        swap(p, os.path.join(ZT, name.replace(u"zf138", u"zf136")), u"138", u"136")
    d = os.path.join(ZT, THEIRS_DIR)
    if os.path.isdir(d):
        shutil.move(d, os.path.join(ZT, u"zf136_pre"))
        notes.append(u"  [还原] zf138_pre/ → zf136_pre/（1 份 star_steel_ingot.png，逐字节）")

    print(u"===== ② 我自己的件：138 → 139 =====")
    skip = set(THEIRS)
    for name in sorted(os.listdir(ZT)):
        if name in skip or u"zf138" not in name:
            continue
        p = os.path.join(ZT, name)
        swap(p, os.path.join(ZT, name.replace(u"zf138", u"zf139")),
             u"138", u"139") if name.endswith((u".py", u".md", u".txt")) \
            else swap(p, os.path.join(ZT, name.replace(u"zf138", u"zf139")), u"138", u"139")

    print(u"===== ③ 探针类与挂载点 =====")
    swap(os.path.join(SRC, u"Zf138Check.java"), os.path.join(SRC, u"Zf139Check.java"),
         u"138", u"139")
    pot = os.path.join(SRC, u"PotatoST.java")
    text = io.open(pot, encoding=u"utf-8", newline=u"").read()
    if u"Zf138Check" in text:
        io.open(pot, u"w", encoding=u"utf-8", newline=u"").write(
            text.replace(u"Zf138Check", u"Zf139Check").replace(u"ZF138", u"ZF139"))
        notes.append(u"  [改] PotatoST.java 的挂载行 → Zf139Check")

    print(u"===== ④ 救援备份根 =====")
    old_bk, new_bk = os.path.join(RESCUE, u"zf138_pre"), os.path.join(RESCUE, u"zf139_pre")
    if os.path.isdir(old_bk):
        for name in (u"_zf138_newfiles.txt",):
            if os.path.exists(os.path.join(old_bk, name)):
                os.rename(os.path.join(old_bk, name),
                          os.path.join(old_bk, name.replace(u"zf138", u"zf139")))
        os.rename(old_bk, new_bk)
        with io.open(os.path.join(new_bk, u"_说明.txt"), u"a", encoding=u"utf-8",
                     newline=u"\n") as f:
            f.write(u"\n【再次改号】本轮最终定 **ZF139**（ZF136 被另一条线的档案行占了、\n"
                    u"ZF137 是他们的提交、ZF138 是他们在用的文件名）⇒ 备份根 zf138_pre → zf139_pre。\n")
        notes.append(u"  [改名] 救援目录 zf138_pre → zf139_pre")
    else:
        notes.append(u"  [已改过] zf139_pre 已在盘上")

    print(u"\n".join(notes))
    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
