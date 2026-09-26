# -*- coding: utf-8 -*-
u"""_zf128_commit.py —— ZF128 的提交（**只 add 本轮的路径**）

口径同 `_zf125/_zf126/_zf127_commit.py`：按清单逐条 `git add`，绝不用 `git add -A`；
`-c core.quotepath=false`；"清单外"只报告、不自动撤。

⚠ **本轮清单里刻意不含**素材线的东西（贴图/模型/`docs\\贴图清单.md`）：那是他们那条线的改动，
  我只把**自己的判据跟平**（`_zf127_verify.py` / `_zf128_verify.py` 里那几条）——
  同一棵树上两条线并行时，"别人的改动由别人提交"是既定口径。

跑法：
    python build\\zftools\\_zf128_commit.py
"""
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
GIT = r"C:\Program Files\Git\cmd\git.exe"
MSG = os.path.join(ROOT, r"build\zftools\_zf128_commit_msg.txt")
TOOLS = u"build/zftools/"

PATHS = [
    u"src/main/resources/data/potato_s_t/advancement/new_beginning.json",
    u"docs/开发档案.md",
    u"docs/多会话协作交接.md",
    u"docs/UpdateAnnouncement_EN.md",
    # 往轮门与生成器（跟平）
    TOOLS + u"_zf70_verify.py",
    TOOLS + u"_zf107_adv.py",
    TOOLS + u"_zf107_verify.py",
    TOOLS + u"_zf124_verify.py",
    TOOLS + u"_zf125_verify.py",
    TOOLS + u"_zf127_verify.py",
    TOOLS + u"_zf90_verify.py",
    TOOLS + u"_zf128_verify.py",
    # 本轮脚本 / 取证
    TOOLS + u"_zf128_backup.py",
    TOOLS + u"_zf128_json.py",
    TOOLS + u"_zf128_gatefix.py",
    TOOLS + u"_zf128_gatefix2.py",
    TOOLS + u"_zf128_artfix.py",
    TOOLS + u"_zf128_repair.py",
    TOOLS + u"_zf128_handfix.py",
    TOOLS + u"_zf128_docs.py",
    TOOLS + u"_zf128_docs2.py",
    TOOLS + u"_zf128_docs3.py",
    TOOLS + u"_zf128_mount.py",
    TOOLS + u"_zf128_unprobe.py",
    TOOLS + u"_zf128_falsify.py",
    TOOLS + u"_zf128_mkgatesnap.py",
    TOOLS + u"_zf128_gatesnap.py",
    TOOLS + u"_zf128_commit.py",
    TOOLS + u"_zf128_commit_msg.txt",
    TOOLS + u"_zf128_build.log",
    TOOLS + u"_zf128_probe.log",
    TOOLS + u"_zf128_probe_utf8.txt",
    TOOLS + u"_zf128_gatesnap.txt",
    TOOLS + u"_zf128_redlines.txt",
    TOOLS + u"_zf128_peek_state.txt",
    TOOLS + u"check/Zf128Check.java",
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
        notes.append(u"⚠ status 里没看到变化（可能已提交 / 或没改）：%s" % u"、".join(nochange))
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
        notes.append(u"提交成功：%s" % out.split(u"\n")[0][:140])
    notes.append(u"最近两条：\n" + run([u"log", u"--oneline", u"-2"]).stdout.decode(u"utf-8", u"replace").rstrip())

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
