# -*- coding: utf-8 -*-
u"""_zf125_commit.py —— ZF125 的提交（**只 add 本轮的路径**；同一棵树上还有别的线在跑）

口径（照 `_zf120_commit.py` / `_zf121` / `_zf124` 那几份）：
  · 按**路径清单**逐条 `git add`，绝不用 `git add -A`（别人的素材/改动物一个字都不许带上）；
  · 提交前先 `git status --short` 核一遍清单里的路径**确实都变了**；
  · 提交信息从 `build\\zftools\\_zf125_commit_msg.txt` 读（UTF-8，`-F` 方式传）。

⚠ 本轮**没有** `release\\` 的改动（不重新打包）⇒ 不需要"作废 SHA1"的声明。

跑法：
    python build\\zftools\\_zf125_commit.py
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
MSG = os.path.join(ROOT, r"build\zftools\_zf125_commit_msg.txt")

JAVA = u"src/main/java/com/potatost/mod/"
LANG = u"src/main/resources/assets/potato_s_t/lang/"
ASSETS = u"src/main/resources/assets/potato_s_t/"
DATA = u"src/main/resources/data/"

PATHS = [
    # ---- 新增：机器本体（7 个 Java）----
    JAVA + u"DieselGeneratorStructure.java",
    JAVA + u"DieselGeneratorBlock.java",
    JAVA + u"DieselGeneratorBlockEntity.java",
    JAVA + u"DieselGeneratorPortBlock.java",
    JAVA + u"DieselGeneratorPortBlockEntity.java",
    JAVA + u"DieselGeneratorMenu.java",
    JAVA + u"client/DieselGeneratorScreen.java",
    # ---- 改动：接线（6 个既有 Java）----
    JAVA + u"ModBlocks.java",
    JAVA + u"ModItems.java",
    JAVA + u"ModMenus.java",
    JAVA + u"PotatoST.java",
    JAVA + u"PotatoSTClient.java",
    JAVA + u"client/gui/parts/StatusLampPart.java",
    # ---- 新增：资源与数据 ----
    ASSETS + u"blockstates/diesel_generator_controller.json",
    ASSETS + u"blockstates/diesel_generator_port.json",
    ASSETS + u"models/block/diesel_generator_controller.json",
    ASSETS + u"models/block/diesel_generator_port.json",
    ASSETS + u"models/item/diesel_generator_controller.json",
    ASSETS + u"textures/block/diesel_generator_controller.png",
    DATA + u"potato_s_t/recipe/diesel_generator_controller.json",
    DATA + u"potato_s_t/tags/item/copper_blocks.json",
    # ---- 改动：四语言 + 两张挖掘标签 ----
    LANG + u"zh_cn.json", LANG + u"en_us.json", LANG + u"ja_jp.json", LANG + u"ru_ru.json",
    DATA + u"minecraft/tags/block/mineable/pickaxe.json",
    DATA + u"minecraft/tags/block/needs_stone_tool.json",
    # ---- 改动：文档四份 ----
    u"docs/开发档案.md", u"docs/多会话协作交接.md",
    u"docs/UpdateAnnouncement_EN.md", u"docs/贴图清单.md",
    # ---- 改动：26 份往轮校验器的键数/清单 retarget ----
    u"build/zftools/_zf71_verify.py", u"build/zftools/_zf73_verify.py",
    u"build/zftools/_zf75_verify.py", u"build/zftools/_zf78_verify.py",
    u"build/zftools/_zf79_verify.py", u"build/zftools/_zf80_verify.py",
    u"build/zftools/_zf81_verify.py", u"build/zftools/_zf82_verify.py",
    u"build/zftools/_zf93_verify.py", u"build/zftools/_zf96_verify.py",
    u"build/zftools/_zf97_verify.py", u"build/zftools/_zf98_verify.py",
    u"build/zftools/_zf100_verify.py", u"build/zftools/_zf101_verify.py",
    u"build/zftools/_zf102_verify.py", u"build/zftools/_zf103_verify.py",
    u"build/zftools/_zf107_verify.py", u"build/zftools/_zf109_verify.py",
    u"build/zftools/_zf111_verify.py", u"build/zftools/_zf112_verify.py",
    u"build/zftools/_zf114_verify.py", u"build/zftools/_zf117_verify.py",
    u"build/zftools/_zf118_verify.py", u"build/zftools/_zf119_verify.py",
    u"build/zftools/_zf121_verify.py", u"build/zftools/_zf122_verify.py",
    # ---- 新增：本轮的工具与证据 ----
    u"build/zftools/_zf125_backup.py", u"build/zftools/_zf125_fixA.py",
    u"build/zftools/_zf125_java.py", u"build/zftools/_zf125_assets.py",
    u"build/zftools/_zf125_lang.py", u"build/zftools/_zf125_lang2.py",
    u"build/zftools/_zf125_retarget.py", u"build/zftools/_zf125_retarget2.py",
    u"build/zftools/_zf125_verify.py", u"build/zftools/_zf125_falsify.py",
    u"build/zftools/_zf125_unprobe.py", u"build/zftools/_zf125_docs.py",
    u"build/zftools/_zf125_docs2.py", u"build/zftools/_zf125_fixdocs.py",
    u"build/zftools/_zf125_gatesnap.py", u"build/zftools/_zf125_gatesnap.txt",
    u"build/zftools/_zf125_gatebrief.py", u"build/zftools/_zf125_gatesnap_summary.txt",
    u"build/zftools/_zf125_redlines.py", u"build/zftools/_zf125_redlines.txt",
    u"build/zftools/_zf125_probe.log", u"build/zftools/_zf125_probe2.log",
    u"build/zftools/_zf125_probe_utf8.txt", u"build/zftools/_zf125_build.log",
    u"build/zftools/_zf125_commit_msg.txt",
    u"build/zftools/check/Zf125Check.java",
]

fails, notes = [], []


def run(args, **kw):
    return subprocess.run([GIT] + args, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, **kw)


def main():
    # ① 清单里的路径必须真的存在（新增件也在），且 status 里确实有变化
    st = run([u"status", u"--short"]).stdout.decode(u"utf-8", u"replace")
    changed = set()
    for line in st.split(u"\n"):
        if len(line) > 3:
            p = line[3:].strip().strip(u'"')
            changed.add(p.replace(u"\\", u"/"))
    missing = [p for p in PATHS if not os.path.exists(os.path.join(ROOT, p.replace(u"/", os.sep)))]
    if missing:
        fails.append(u"这些路径不在盘上：%s" % u"、".join(missing))
    nochange = []
    for p in PATHS:
        if p in changed:
            continue
        # 未跟踪的新文件在 status 里是 `?? 目录/`，逐条比前缀
        if any(c.rstrip(u"/") and (p.startswith(c.rstrip(u"/") + u"/") or c.endswith(p))
               for c in changed):
            continue
        nochange.append(p)
    if nochange:
        notes.append(u"⚠ status 里没看到变化的 %d 条（可能已提交或未改）：%s"
                     % (len(nochange), u"、".join(nochange[:6])))
    if fails:
        print(u"\n".join(u"  !! " + f for f in fails))
        return 1

    # ② 逐条 add
    for p in PATHS:
        r = run([u"add", u"--", p])
        if r.returncode != 0:
            fails.append(u"git add 失败：%s（%s）" % (p, r.stdout.decode(u"utf-8", u"replace")[:120]))
    if fails:
        print(u"\n".join(u"  !! " + f for f in fails))
        return 1
    notes.append(u"已 add %d 条路径" % len(PATHS))

    # ③ 暂存区里不该有别人的东西：核一遍 staged 清单是否都在 PATHS 里
    staged = run([u"diff", u"--cached", u"--name-only"]).stdout.decode(u"utf-8", u"replace")
    staged_paths = [l.strip().replace(u"\\", u"/") for l in staged.split(u"\n") if l.strip()]
    stray = [p for p in staged_paths if p not in PATHS]
    if stray:
        fails.append(u"暂存区里有清单外的 %d 条：%s" % (len(stray), u"、".join(stray[:8])))
        for p in stray:
            run([u"restore", u"--staged", u"--", p])
        notes.append(u"已把清单外的路径撤出暂存区")
    notes.append(u"暂存区 %d 条，全部在清单内" % len(staged_paths))

    # ④ 提交
    msg = io.open(MSG, encoding="utf-8").read()
    r = run([u"commit", u"-F", MSG])
    out = r.stdout.decode(u"utf-8", u"replace")
    if r.returncode != 0:
        fails.append(u"git commit 失败：%s" % out[:400])
    else:
        notes.append(u"提交成功：%s" % out.split(u"\n")[0][:120])
    log = run([u"log", u"--oneline", u"-3"]).stdout.decode(u"utf-8", u"replace")
    notes.append(u"最近三条：\n" + log.rstrip())

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
