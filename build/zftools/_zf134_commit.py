# -*- coding: utf-8 -*-
u"""_zf134_commit.py —— 按路径提交本轮（**绝不 `git add -A`**，§10.1）

本轮（星璨钢斧的合成配方）碰过的路径都在下面；另外带上两笔"顺手但必须一起进"的：

  · 29 份 `_zf*_verify.py` 的**语言键数跟平**（478 → 482）——
    ZF133 四语言各 +4 没跑重定目标，这条链全红，还挡住了本轮 `ZF104 falsify` 的"基线必须绿"；
  · `docs/UpdateAnnouncement_EN.md` 的 `(478 keys each)` → `(482 keys each)`。

跑法：
    python build/zftools/_zf134_commit.py            # 只列清单
    python build/zftools/_zf134_commit.py --write    # add + commit
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
MSG = os.path.join(ROOT, "build", "tmp", "zf134_commit_msg.txt")

# 语言键数跟平改到的那 29 份（478 → 482）
KEY_FIXED = [
    "_zf71_verify", "_zf73_verify", "_zf75_verify", "_zf78_verify", "_zf79_verify",
    "_zf80_verify", "_zf81_verify", "_zf82_verify", "_zf93_verify", "_zf96_verify",
    "_zf97_verify", "_zf98_verify", "_zf100_verify", "_zf101_verify", "_zf102_verify",
    "_zf103_verify", "_zf107_verify", "_zf109_verify", "_zf111_verify", "_zf112_verify",
    "_zf114_verify", "_zf117_verify", "_zf118_verify", "_zf119_verify", "_zf122_verify",
    "_zf125_verify", "_zf126_verify", "_zf127_verify", "_zf128_verify",
]

PATHS = [
    # ---- 本轮的正事：一张配方 ----
    "src/main/resources/data/potato_s_t/recipe/star_steel_axe.json",
    "build/zftools/_zf45_recipes.py",
    # ---- 本轮的工具与证据 ----
    "build/zftools/_zf134_survey.py",
    "build/zftools/_zf134_verify.py",
    "build/zftools/_zf134_falsify.py",
    "build/zftools/_zf134_live.py",
    "build/zftools/_zf134_keys.py",
    "build/zftools/_zf134_zf104falsify.txt",
    "build/zftools/_zf134_compile.log",
    # ---- 活体数字与门 ----
    "build/zftools/_zf100_recipe_guard.py",
    "build/zftools/_zf106_recipes_check.py",
    "build/zftools/_zf104_gates.ps1",
    "build/zftools/_zf104_gatecount.py",
    "build/zftools/_zf104_gates.txt",
    "build/zftools/_zf103_falsify_compile.log",
    "build/zftools/_zf120_falsify_compile.log",
    # ---- 文档 ----
    "docs/UpdateAnnouncement_EN.md",
    "docs/多会话协作交接.md",
] + ["build/zftools/%s.py" % n for n in KEY_FIXED]


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
    staged = [l for l in out.split(u"\n") if l[:2].strip() and not l.startswith(u"??")]
    print(u"\n已暂存 %d 项（前 12 条）：" % len(staged))
    for l in staged[:12]:
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
