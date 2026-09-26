# -*- coding: utf-8 -*-
u"""_zf127_commit.py —— ZF127 的提交（**只 add 本轮的路径**）

口径同 `_zf125/_zf126_commit.py`：按清单逐条 `git add`，绝不用 `git add -A`；
`-c core.quotepath=false`（非 ASCII 路径），"清单外"只报告、不自动撤。

跑法：
    python build\\zftools\\_zf127_commit.py
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
MSG = os.path.join(ROOT, r"build\zftools\_zf127_commit_msg.txt")

JAVA = u"src/main/java/com/potatost/mod/"
RES = u"src/main/resources/"
TOOLS = u"build/zftools/"

# 本轮**被我改过/新增**的常驻门（retarget 27 份 + 两份被顶到的往轮门）
GATES = [
    u"_zf71_verify.py", u"_zf73_verify.py", u"_zf75_verify.py", u"_zf78_verify.py",
    u"_zf79_verify.py", u"_zf80_verify.py", u"_zf81_verify.py", u"_zf82_verify.py",
    u"_zf90_verify.py", u"_zf93_verify.py", u"_zf96_verify.py", u"_zf97_verify.py",
    u"_zf98_verify.py", u"_zf100_verify.py", u"_zf101_verify.py", u"_zf102_verify.py",
    u"_zf103_verify.py", u"_zf107_verify.py", u"_zf109_verify.py", u"_zf111_verify.py",
    u"_zf112_verify.py", u"_zf114_verify.py", u"_zf117_verify.py", u"_zf118_verify.py",
    u"_zf119_verify.py", u"_zf122_verify.py", u"_zf125_verify.py", u"_zf126_verify.py",
]

PATHS = [
    # ---- Java（4 份）----
    JAVA + u"ModItems.java",
    JAVA + u"TerminalBlock.java",
    JAVA + u"TerminalBlockEntity.java",
    JAVA + u"client/TerminalRenderer.java",
    # ---- 资源：两个模型 + 两条配方 ----
    RES + u"assets/potato_s_t/models/item/silver_wire.json",
    RES + u"assets/potato_s_t/models/item/silver_wire_spool.json",
    RES + u"data/potato_s_t/recipe/silver_wire.json",
    RES + u"data/potato_s_t/recipe/silver_wire_spool.json",
    # ---- 四语言 ----
    RES + u"assets/potato_s_t/lang/zh_cn.json",
    RES + u"assets/potato_s_t/lang/en_us.json",
    RES + u"assets/potato_s_t/lang/ja_jp.json",
    RES + u"assets/potato_s_t/lang/ru_ru.json",
    # ---- 文档 ----
    u"docs/开发档案.md",
    u"docs/多会话协作交接.md",
    u"docs/贴图清单.md",
    u"docs/UpdateAnnouncement_EN.md",
    # ---- 工具：配方表 + 本轮脚本 + 取证 ----
    TOOLS + u"_zf45_recipes.py",
    TOOLS + u"_zf127_backup.py",
    TOOLS + u"_zf127_mount.py",
    TOOLS + u"_zf127_java.py",
    TOOLS + u"_zf127_assets.py",
    TOOLS + u"_zf127_lang.py",
    TOOLS + u"_zf127_retarget.py",
    TOOLS + u"_zf127_gatefix.py",
    TOOLS + u"_zf127_gatefix2.py",
    TOOLS + u"_zf127_verify.py",
    TOOLS + u"_zf127_falsify.py",
    TOOLS + u"_zf127_unprobe.py",
    TOOLS + u"_zf127_docs.py",
    TOOLS + u"_zf127_docs2.py",
    TOOLS + u"_zf127_docs3.py",
    TOOLS + u"_zf127_gatesnap.py",
    TOOLS + u"_zf127_gatesnap.txt",
    TOOLS + u"_zf127_gatesnap_before.txt",
    TOOLS + u"_zf127_commit.py",
    TOOLS + u"_zf127_commit_msg.txt",
    TOOLS + u"_zf127_build.log",
    TOOLS + u"_zf127_probe.log",
    TOOLS + u"_zf127_probe_utf8.txt",
    TOOLS + u"_zf127_potatost_diff.txt",
    TOOLS + u"_zf127_peek476.txt",
    TOOLS + u"_zf127_redlines.txt",
    TOOLS + u"check/Zf127Check.java",
] + [TOOLS + g for g in GATES]

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
