# -*- coding: utf-8 -*-
u"""_zf126_commit.py —— ZF126 的提交（**只 add 本轮的路径**）

口径同 `_zf125_commit.py`：按清单逐条 `git add`，绝不用 `git add -A`。
⚠ ZF125 那次踩过一个小坑：`git status` 对非 ASCII 路径会输出**八进制转义**，
   我的"清单外路径"检测因此误判、把三份文档当成清单外的撤了暂存 ——
   这次改成 **`-c core.quotepath=false`**，并且"清单外"只报告、**不再自动撤**。

跑法：
    python build\\zftools\\_zf126_commit.py
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
GIT = r"C:\Program Files\Git\cmd\git.exe"
MSG = os.path.join(ROOT, r"build\zftools\_zf126_commit_msg.txt")

JAVA = u"src/main/java/com/potatost/mod/"
TOOLS = u"build/zftools/"

PATHS = [
    JAVA + u"DieselGeneratorBlockEntity.java",
    JAVA + u"DieselGeneratorMenu.java",
    JAVA + u"client/DieselGeneratorScreen.java",
    TOOLS + u"_zf125_verify.py",
    TOOLS + u"_zf126_backup.py",
    TOOLS + u"_zf126_backfill.py",
    TOOLS + u"_zf126_backfill2.py",
    TOOLS + u"_zf126_verify.py",
    TOOLS + u"_zf126_falsify.py",
    TOOLS + u"_zf126_unprobe.py",
    TOOLS + u"_zf126_docs.py",
    TOOLS + u"_zf126_commit.py",
    TOOLS + u"_zf126_commit_msg.txt",
    TOOLS + u"_zf126_build.log",
    TOOLS + u"_zf126_probe.log",
    TOOLS + u"_zf126_probe_utf8.txt",
    TOOLS + u"check/Zf126Check.java",
    u"docs/开发档案.md",
    u"docs/多会话协作交接.md",
]

fails, notes = [], []


def run(args):
    return subprocess.run([GIT, u"-c", u"core.quotepath=false"] + args, cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def main():
    st = run([u"status", u"--short"]).stdout.decode(u"utf-8", u"replace")
    changed = set()
    for line in st.split(u"\n"):
        if len(line) > 3:
            changed.add(line[3:].strip().strip(u'"').replace(u"\\", u"/"))
    missing = [p for p in PATHS if not os.path.exists(os.path.join(ROOT, p.replace(u"/", os.sep)))]
    if missing:
        fails.append(u"这些路径不在盘上：%s" % u"、".join(missing))
    nochange = [p for p in PATHS if p not in changed]
    if nochange:
        notes.append(u"⚠ status 里没看到变化（可能已提交）：%s" % u"、".join(nochange))
    if fails:
        print(u"\n".join(u"  !! " + f for f in fails))
        return 1

    for p in PATHS:
        r = run([u"add", u"--", p])
        if r.returncode != 0:
            fails.append(u"git add 失败：%s（%s）" % (p, r.stdout.decode(u"utf-8", u"replace")[:120]))
    if fails:
        print(u"\n".join(u"  !! " + f for f in fails))
        return 1
    notes.append(u"已 add %d 条路径" % len(PATHS))

    staged = run([u"diff", u"--cached", u"--name-only"]).stdout.decode(u"utf-8", u"replace")
    staged_paths = [l.strip().replace(u"\\", u"/") for l in staged.split(u"\n") if l.strip()]
    stray = [p for p in staged_paths if p not in PATHS]
    if stray:
        # ⚠ 只报告、**不自动撤**（ZF125 那次就是自动撤把非 ASCII 路径误伤了）
        fails.append(u"暂存区里有清单外的 %d 条（**没有自动撤**，请人工确认）：%s"
                     % (len(stray), u"、".join(stray[:8])))
    else:
        notes.append(u"暂存区 %d 条，全部在清单内" % len(staged_paths))

    if fails:
        print(u"\n".join(u"  [OK] " + n for n in notes))
        print(u"\n".join(u"  !! " + f for f in fails))
        return 1

    r = run([u"commit", u"-F", MSG])
    out = r.stdout.decode(u"utf-8", u"replace")
    if r.returncode != 0:
        fails.append(u"git commit 失败：%s" % out[:400])
    else:
        notes.append(u"提交成功：%s" % out.split(u"\n")[0][:120])
    notes.append(u"最近两条：\n" + run([u"log", u"--oneline", u"-2"]).stdout.decode(u"utf-8", u"replace").rstrip())

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
