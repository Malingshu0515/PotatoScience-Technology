# -*- coding: utf-8 -*-
r'''_zf145_pre.py —— ZF145 改前件（§10：动手前先备份）

本轮要做的事：**成就树补线**（ZF117 之后新加的内容一条进度都没有）。

备份清单（**本轮会动到的**，逐份抄 + 记 sha1）：
  · 四语言 `lang\*.json`（要 +16 键）
  · 所有 `_zf*_verify.py` + `_zf100_recipe_guard.py`（活体数字 492 → 508、进度 35 → 43 要跟平）
  · 三份文档（档案 / 交接 / 英文公告）
  · `_zf104_gates.ps1` / `_zf104_gatecount.py` / `_zf104_gates.txt`（要加 ZF144+ZF145 两段）
  · `PotatoST.java`（⚠ 要挂临时探针 —— §6 第 9/14/18 条三次漏账的教训：**先写进清单**）

⚠ 规矩（§4.147 撞号事故之后立的）：
  ① **目标目录已存在就停手**（绝不覆盖别人的备份根 —— ZF142 那次就是覆盖了别人的 `_sha1.txt`）；
  ② 先查盘上有没有人在用这个轮号。

跑法：python build\zftools\_zf145_pre.py
'''
import glob
import hashlib
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
DEST = os.path.join(r"C:\PotatoST救援", "zf145_pre")

FIXED = [
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"build\zftools\_zf104_gates.ps1",
    r"build\zftools\_zf104_gatecount.py",
    r"build\zftools\_zf104_gates.txt",
    r"build\zftools\_zf100_recipe_guard.py",
    r"build\zftools\_zf71_verify.py",
]

GLOBS = [
    r"build\zftools\_zf*_verify.py",
]


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.exists(DEST):
        print(u"!! 备份根已存在，停手（绝不覆盖别人的 / 自己的旧快照）：%s" % DEST)
        print(u"   里面现有 %d 个条目。" % len(os.listdir(DEST)))
        return 1

    files = set()
    for rel in FIXED:
        p = os.path.join(ROOT, rel)
        if os.path.isfile(p):
            files.add(rel)
        else:
            print(u"  [警告] 清单里的这份不在盘上：%s" % rel)
    for g in GLOBS:
        for p in glob.glob(os.path.join(ROOT, g)):
            files.add(os.path.relpath(p, ROOT))

    # 撞号检查：别人的在途文件（不在档案里也可能在盘上）
    busy = [os.path.basename(p) for p in glob.glob(os.path.join(ZT, u"_zf145_*"))
            if os.path.basename(p) != u"_zf145_pre.py"]
    os.makedirs(DEST, exist_ok=True)

    lines, n = [], 0
    for rel in sorted(files):
        src = os.path.join(ROOT, rel)
        dst = os.path.join(DEST, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        a, b = sha1(src), sha1(dst)
        assert a == b, rel
        lines.append(u"%s  %s" % (a, rel.replace(u"\\", u"/")))
        n += 1

    io.open(os.path.join(DEST, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"").write(u"\n".join(lines) + u"\n")

    note = u"""ZF145 改前件（成就树补线）

轮号：ZF145（开工前查过：build\\zftools 下没有别的 _zf145_*，C:\\PotatoST救援 下没有 zf145_pre）
本目录：%s
份数：%d
清单：见 _sha1.txt（格式 = sha1 + 两空格 + 相对路径，路径用 /）

为什么 PotatoST.java 在清单里：
  ⚠ 本轮要挂**临时探针** `Zf145Check.java`（runServer 里读真数据包）。§6 第 9/14/18 条
  记着三次「探针挂载点漏进备份清单」—— 这次**动手前**就写进来。

别人在途的 ZF145 文件（应为空）：%s
""" % (DEST, n, u"、".join(busy) if busy else u"（无）")
    io.open(os.path.join(DEST, u"_说明.txt"), "w", encoding="utf-8",
            newline=u"").write(note)

    print(u"备份根：%s" % DEST)
    print(u"份数：%d" % n)
    print(u"sha1 清单：_sha1.txt（%d 行）" % len(lines))
    print(u"别人在途的 ZF145 文件：%s" % (u"、".join(busy) if busy else u"（无）"))
    for rel in (r"src\main\java\com\potatost\mod\PotatoST.java",
                r"src\main\resources\assets\potato_s_t\lang\zh_cn.json"):
        print(u"  抽查 %s = %s" % (rel, sha1(os.path.join(ROOT, rel))))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
