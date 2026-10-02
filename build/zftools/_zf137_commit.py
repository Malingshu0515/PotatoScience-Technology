# -*- coding: utf-8 -*-
u"""_zf137_commit.py —— 按路径提交本轮（**绝不 `git add -A`**，§10.1）

本轮（星璨钢头盔给夜视 I / 4 s）碰过的路径都在下面。
⚠ 其中两份是"我的改动与别的线在同一文件里"（拆不开，拆了仓库编译不过），提交信息里已点名：
  · `ModArmorMaterials.java` —— 我的 `hasStarSteelHelmet` + ZF136 那条"振金护甲值各 +1"；
  · 四语言 —— 我的星璨钢说明 + ZF136 的振金说明与那个新死因键。

跑法：
    python build/zftools/_zf137_commit.py            # 只列清单
    python build/zftools/_zf137_commit.py --write    # add + commit
"""
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
GIT = r"C:\Program Files\Git\bin\git.exe"
MSG = os.path.join(ROOT, "build", "tmp", "zf137_commit_msg.txt")

PATHS = [
    # ---- 本轮的正事 ----
    "src/main/java/com/potatost/mod/ModArmorSet.java",
    "src/main/java/com/potatost/mod/ModArmorMaterials.java",
    "src/main/resources/assets/potato_s_t/lang/zh_cn.json",
    "src/main/resources/assets/potato_s_t/lang/en_us.json",
    "src/main/resources/assets/potato_s_t/lang/ja_jp.json",
    "src/main/resources/assets/potato_s_t/lang/ru_ru.json",
    # ---- 本轮的工具与证据 ----
    "build/zftools/_zf137_verify.py",
    "build/zftools/_zf137_falsify.py",
    "build/zftools/_zf137_lang.py",
    "build/zftools/_zf137_rename.py",
    "build/zftools/_zf137_compile.log",
    "build/zftools/_zf137_falsify.txt",
    "build/zftools/_zf137_falsify_compile.log",
    # ---- 门与文档 ----
    "build/zftools/_zf104_gates.ps1",
    "build/zftools/_zf104_gatecount.py",
    "build/zftools/_zf104_gates.txt",
    "docs/开发档案.md",
]


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
    print(u"\ncommit rc=%d\n%s" % (rc, out.strip()[:900]))
    if rc != 0:
        return 1
    rc, out = git("log", "--oneline", "-3")
    print(u"\n最近三次提交：\n" + out.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
