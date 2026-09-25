# -*- coding: utf-8 -*-
u"""_zf90_backup.py —— ZF90 **动手前**的改前件（§10）

用户：「**其它锭板子贴图都换成铁板的**」。
还在用通用 `textures/item/plate.png` 的正是四件：**银板 / 铝板 / 镍板 / 钴板**
（铁/钢/铜三件 ZF83/ZF86 已经有自己的图了）。

做法沿用 ZF83 那套（用户当时原话是「换一下 然后删除原来的贴图」）：
  · 四个模型指向 `potato_s_t:item/iron_plate`；
  · **删掉通用 `plate.png`**（删之前先抄进本快照；成品里也还留着一份，可回退）。

改前件 = 会被这一轮动到的全部文件。
"""
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
BK = r"C:\PotatoST救援\zf90_pre"
MODELI = r"src\main\resources\assets\potato_s_t\models\item"
TEXI = r"src\main\resources\assets\potato_s_t\textures\item"
FILES = [
    MODELI + r"\aluminum_plate.json",
    MODELI + r"\cobalt_plate.json",
    MODELI + r"\nickel_plate.json",
    MODELI + r"\silver_plate.json",
    TEXI + r"\plate.png",
    TEXI + r"\iron_plate.png",
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"build\zftools\_zf83_verify.py",
    r"build\zftools\_zf78_falsify.py",
    r"docs\开发档案.md",
    r"docs\贴图清单.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    # ⚠ 0.11 ZF90 修一个真陷阱：原来的写法是「根已存在就打印 [SKIP]，然后**照样往下拷**」——
    #   等于重跑一次就把**改后**的内容覆盖进快照，改前件当场变成改后件（静默、看不出来）。
    #   现在改成：根已存在就直接**中止**，一个字节都不写。
    if os.path.isdir(BK):
        print(u"  [STOP] 备份根已存在：%s" % BK)
        print(u"         重跑会把手改后的内容覆盖进快照 ⇒ 直接中止，不写任何文件。")
        print(u"         要补文件请用单独的补账脚本（照 ZF78/ZF83 先例，逐个核哈希）。")
        return 1
    lines = []
    ok = 0
    for rel in FILES:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            fails.append(u"缺文件：%s" % rel)
            lines.append(u"MISSING  %s" % rel)
            continue
        dst = os.path.join(BK, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        before = sha1(src)
        shutil.copy2(src, dst)
        after = sha1(dst)
        if before != after:
            fails.append(u"%s：拷贝后哈希不一致" % rel)
        else:
            ok += 1
            lines.append(u"%s  %10d  %s" % (after, os.path.getsize(dst), rel))
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
