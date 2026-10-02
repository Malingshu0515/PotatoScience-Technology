# -*- coding: utf-8 -*-
u"""_zf137_commit3.py —— 按路径提交"夜视 III / 13 s（不闪）"这一笔（**绝不 `git add -A`**，§10.1）

第三笔改口（4 s → 5 s → **III / 13 s 且不闪**），仍然不占新号，提交信息写 `ZF137 补二`。

跑法：
    python build/zftools/_zf137_commit3.py            # 只列清单
    python build/zftools/_zf137_commit3.py --write    # add + commit
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
MSG = os.path.join(ROOT, "build", "tmp", "zf137c_commit_msg.txt")

PATHS = [
    "src/main/java/com/potatost/mod/ModArmorSet.java",
    "src/main/resources/assets/potato_s_t/lang/zh_cn.json",
    "src/main/resources/assets/potato_s_t/lang/en_us.json",
    "src/main/resources/assets/potato_s_t/lang/ja_jp.json",
    "src/main/resources/assets/potato_s_t/lang/ru_ru.json",
    "build/zftools/_zf137_verify.py",
    "build/zftools/_zf137_falsify.py",
    "build/zftools/_zf137_nv3.py",
    "build/zftools/_zf137_compile.log",
    "build/zftools/_zf137_falsify.txt",
    "build/zftools/_zf137_falsify_compile.log",
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
    print(u"\ncommit rc=%d\n%s" % (rc, out.strip()[:800]))
    if rc != 0:
        return 1
    rc, out = git("log", "--oneline", "-3")
    print(u"\n最近三次提交：\n" + out.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
