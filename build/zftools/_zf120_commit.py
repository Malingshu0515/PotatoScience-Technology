# -*- coding: utf-8 -*-
u"""_zf120_commit.py —— 按路径提交本轮（**绝不 `git add -A`**）

规则（§10.1）：多会话并行时只加自己碰过的路径。这一轮碰过的路径在这里逐条列出，
另外带上两笔**为了仓库自洽**必须一起进的：

  · 25 份被清成 0 字节的 `_zf*_verify.py` —— 它们是本轮修回来的（HEAD 上还是空的）；
  · 4 个星璨钢模型 + 4 张星璨钢图标 —— 另一条线已落盘未提交，
    而本轮的 `_zf103_verify.py` 改锚点正好要用它（不然 HEAD 上那条断言与仓库不一致）。

跑法：
    python build/zftools/_zf120_commit.py            # 只列清单
    python build/zftools/_zf120_commit.py --write    # add + commit
"""
import io
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
GIT = r"C:\Program Files\Git\bin\git.exe"
MSG = os.path.join(ROOT, "build", "tmp", "zf120_commit_msg.txt")

PATHS = [
    # ---- 本轮自己的代码 ----
    "src/main/java/com/potatost/mod/ModArmorItems.java",
    "src/main/java/com/potatost/mod/ModArmorMaterials.java",
    "src/main/java/com/potatost/mod/ModVibraniumPiece.java",
    "src/main/java/com/potatost/mod/ModVibraniumSet.java",
    # ---- 本轮自己的资源 ----
    "src/main/resources/assets/potato_s_t/models/item/vibranium_helmet.json",
    "src/main/resources/assets/potato_s_t/models/item/vibranium_chestplate.json",
    "src/main/resources/assets/potato_s_t/models/item/vibranium_leggings.json",
    "src/main/resources/assets/potato_s_t/models/item/vibranium_boots.json",
    "src/main/resources/data/potato_s_t/recipe/vibranium_helmet_smithing.json",
    "src/main/resources/data/potato_s_t/recipe/vibranium_chestplate_smithing.json",
    "src/main/resources/data/potato_s_t/recipe/vibranium_leggings_smithing.json",
    "src/main/resources/data/potato_s_t/recipe/vibranium_boots_smithing.json",
    # ---- 本轮的工具与证据 ----
    "build/zftools/_zf120_src.py",
    "build/zftools/_zf120_lang.py",
    "build/zftools/_zf120_verify.py",
    "build/zftools/_zf120_falsify.py",
    "build/zftools/_zf120_falsify.txt",
    "build/zftools/_zf120_falsify_compile.log",
    "build/zftools/_zf120_falsify_k216.txt",
    "build/zftools/_zf120_zf104falsify.txt",
    "build/zftools/_zf120_guardfix.py",
    "build/zftools/_zf120_retarget.py",
    "build/zftools/_zf120_repair.py",
    "build/zftools/_zf120_compile.log",
    # ---- 本轮改过的共用门 ----
    "build/zftools/RecipeCheck.ps1",
    "build/zftools/_zf104_gates.ps1",
    "build/zftools/_zf104_gatecount.py",
    "build/zftools/_zf104_gates.txt",
    "build/zftools/_zf103_falsify_compile.log",
    "build/zftools/_zf45_recipes.py",
    "build/zftools/_zf100_recipe_guard.py",
    "build/zftools/_zf106_recipes_check.py",
    "build/zftools/_zf103_verify.py",
    "build/zftools/_zf71_verify.py",
    "build/zftools/_zf90_verify.py",
    "build/zftools/_zf122_live.py",
    # ---- 被清成 0 字节后由本轮修回来的那 24 份 ----
    "build/zftools/_zf100_verify.py", "build/zftools/_zf101_verify.py",
    "build/zftools/_zf102_verify.py", "build/zftools/_zf107_verify.py",
    "build/zftools/_zf109_verify.py", "build/zftools/_zf111_verify.py",
    "build/zftools/_zf112_verify.py", "build/zftools/_zf114_verify.py",
    "build/zftools/_zf117_verify.py", "build/zftools/_zf118_verify.py",
    "build/zftools/_zf119_verify.py", "build/zftools/_zf119_falsify.py",
    "build/zftools/_zf121_verify.py", "build/zftools/_zf73_verify.py",
    "build/zftools/_zf75_verify.py", "build/zftools/_zf78_verify.py",
    "build/zftools/_zf79_verify.py", "build/zftools/_zf80_verify.py",
    "build/zftools/_zf81_verify.py", "build/zftools/_zf82_verify.py",
    "build/zftools/_zf93_verify.py", "build/zftools/_zf96_verify.py",
    "build/zftools/_zf97_verify.py", "build/zftools/_zf98_verify.py",
    # ---- 仓库自洽要带上：另一条线已落盘未提交的星璨钢图标 ----
    "src/main/resources/assets/potato_s_t/models/item/star_steel_helmet.json",
    "src/main/resources/assets/potato_s_t/models/item/star_steel_chestplate.json",
    "src/main/resources/assets/potato_s_t/models/item/star_steel_leggings.json",
    "src/main/resources/assets/potato_s_t/models/item/star_steel_boots.json",
    "src/main/resources/assets/potato_s_t/textures/item/star_steel_helmet.png",
    "src/main/resources/assets/potato_s_t/textures/item/star_steel_chestplate.png",
    "src/main/resources/assets/potato_s_t/textures/item/star_steel_leggings.png",
    "src/main/resources/assets/potato_s_t/textures/item/star_steel_boots.png",
    # ---- 文档 ----
    "docs/贴图清单.md",
]


def git(*args):
    p = subprocess.run([GIT, "-C", ROOT] + list(args), stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def main(argv):
    write = "--write" in argv
    missing = [p for p in PATHS if not os.path.exists(os.path.join(ROOT, p.replace("/", os.sep)))]
    if missing:
        print(u"  [FAIL] 这些路径在盘上不存在：")
        for m in missing:
            print(u"     " + m)
        return 1
    print(u"清单 %d 个路径，全部存在 ✔" % len(PATHS))

    rc, out = git("add", "--", *PATHS)
    print(u"git add rc=%d %s" % (rc, out.strip()[:300]))
    if rc != 0:
        return 1

    rc, out = git("status", "--short")
    staged = [l for l in out.split(u"\n") if l[:2].strip() and not l.startswith(u"??")]
    print(u"\n已暂存 %d 项：" % len(staged))
    for l in staged:
        print(u"   " + l)

    if not write:
        print(u"\n（只列清单；加 --write 才真的 commit）")
        return 0

    rc, out = git("commit", "-F", MSG)
    print(u"\ncommit rc=%d\n%s" % (rc, out.strip()[:1500]))
    if rc != 0:
        return 1
    rc, out = git("log", "--oneline", "-3")
    print(u"\n最近三次提交：\n" + out.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
