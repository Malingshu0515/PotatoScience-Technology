# -*- coding: utf-8 -*-
"""_zf201_commit.py —— 按路径提交 0.16 ZF201（钢套 + 钢制工具），**绝不 `git add -A`**（§10.1）

只 add 本轮碰过的路径。Forge 1.20.1 工程**没有 .git**，那边同批改动不在本仓库里。

跑法：
    python build/zftools/_zf201_commit.py            # 只列清单
    python build/zftools/_zf201_commit.py --write    # add + commit
"""
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
GIT = r"C:\Program Files\Git\bin\git.exe"
MSG = os.path.join(ROOT, "build", "tmp", "zf201_commit_msg.txt")

A = r"src\main\resources\assets\potato_s_t"
IDS = ["helmet", "chestplate", "leggings", "boots", "pickaxe", "sword", "axe"]

PATHS = [
    "src/main/java/com/potatost/mod/ModTiers.java",
    "src/main/java/com/potatost/mod/ModArmorMaterials.java",
    "src/main/java/com/potatost/mod/ModArmorItems.java",
    "src/main/java/com/potatost/mod/ModItems.java",
    "src/main/java/com/potatost/mod/SteelSwordItem.java",
    "src/main/resources/assets/potato_s_t/lang/zh_cn.json",
    "src/main/resources/assets/potato_s_t/lang/en_us.json",
    "src/main/resources/assets/potato_s_t/lang/ja_jp.json",
    "src/main/resources/assets/potato_s_t/lang/lzh.json",
    "src/main/resources/assets/potato_s_t/lang/ru_ru.json",
    "build/zftools/_zf45_recipes.py",
    "build/zftools/_zf201_assets.py",
    "build/zftools/_zf201_lang.py",
    "build/zftools/_zf201_forge_recipes.py",
    "build/zftools/_zf201_verify.py",
    "build/zftools/_zf201_docs.py",
    "build/zftools/_zf201_compile.log",
    "build/zftools/_zf201_compile2.log",
    "build/zftools/_zf201_docs2.py",
    "build/zftools/_zf201_falsify.py",
    "build/zftools/_zf201_falsify_compile.log",
    "docs/开发档案.md",
    "docs/多会话协作交接.md",
]
PATHS += ["src/main/resources/assets/potato_s_t/textures/item/steel_%s.png" % i for i in IDS]
PATHS += ["src/main/resources/assets/potato_s_t/models/item/steel_%s.json" % i for i in IDS]
PATHS += ["src/main/resources/data/potato_s_t/recipe/steel_%s.json" % i for i in IDS]


def git(*args):
    p = subprocess.run([GIT, "-C", ROOT] + list(args), stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def main(argv):
    write = "--write" in argv
    missing = [p for p in PATHS
               if not os.path.exists(os.path.join(ROOT, p.replace("/", os.sep)))]
    if missing:
        print(u"  [FAIL] 这些路径在盘上不存在：")
        for m in missing:
            print(u"     " + m)
        return 1
    print(u"清单 %d 个路径，全部存在 ✔" % len(PATHS))

    rc, out = git("add", "--", *PATHS)
    if rc != 0:
        print(u"git add 失败：%s" % out[:400])
        return 1
    rc, out = git("status", "--short")
    staged = [l for l in out.split(u"\n") if l and l[0] not in (u" ", u"?")]
    print(u"\n已暂存 %d 项：" % len(staged))
    for l in staged:
        print(u"   " + l)
    if not write:
        print(u"\n（只列清单；加 --write 才真的 commit）")
        return 0
    rc, out = git("commit", "-F", MSG)
    print(u"\ncommit rc=%d\n%s" % (rc, out.strip()[:700]))
    if rc != 0:
        return 1
    rc, out = git("log", "--oneline", "-3")
    print(u"\n最近三次提交：\n" + out.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
