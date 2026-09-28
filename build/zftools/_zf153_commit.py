# -*- coding: utf-8 -*-
u"""_zf153_commit.py —— ZF153 提交（**显式列路径**，绝不 `git add -A`）

纪律（§10 / ZF114 的教训）：
  · 工作树里**同时有别的线在途的改动**（本轮开工期间就有：`AlloySmelterBlockEntity` /
    `DieselGeneratorBlockEntity` / `SolarPanelBlock` / `ModBlocks` / `sound/ModSounds` …）
    ⇒ 只能一个路径一个路径地 add，多 add 一个就是把别人没写完的东西提交了。
  · 提交前先自己核三件事：① 源码树里**没有**任何 `*Check.register()`（探针必须摘干净）；
    ② `git diff --cached --name-only` 的条数与我的清单**逐条对得上**；③ 提交消息从文件读。

跑法：python build\\zftools\\_zf153_commit.py [--push]
"""
import glob
import io
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
T = os.path.join(ROOT, "build", "zftools")
MSG = os.path.join(T, "_zf153_commit_msg.txt")

# ① 本轮改过的常驻门（33 份重定靶 + _zf145 的 E6 跟平）
VERIFY = [
    u"_zf71_verify.py", u"_zf73_verify.py", u"_zf75_verify.py", u"_zf78_verify.py",
    u"_zf79_verify.py", u"_zf80_verify.py", u"_zf82_verify.py", u"_zf93_verify.py",
    u"_zf96_verify.py", u"_zf97_verify.py", u"_zf98_verify.py", u"_zf100_verify.py",
    u"_zf101_verify.py", u"_zf102_verify.py", u"_zf103_verify.py", u"_zf107_verify.py",
    u"_zf109_verify.py", u"_zf111_verify.py", u"_zf112_verify.py", u"_zf114_verify.py",
    u"_zf117_verify.py", u"_zf118_verify.py", u"_zf119_verify.py", u"_zf122_verify.py",
    u"_zf125_verify.py", u"_zf126_verify.py", u"_zf127_verify.py", u"_zf128_verify.py",
    u"_zf139_verify.py", u"_zf141_verify.py", u"_zf145_verify.py", u"_zf148_verify.py",
    u"_zf150_verify.py",
]

PATHS = [
    # 产品
    r"src\main\java\com\potatost\mod\VibraniumSwordItem.java",
    r"src\main\java\com\potatost\mod\ModTiers.java",
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"src\main\resources\assets\potato_s_t\textures\item\vibranium_sword.png",
    r"src\main\resources\assets\potato_s_t\models\item\vibranium_sword.json",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"src\main\resources\assets\potato_s_t\lang\lzh.json",
    # 素材与凭据
    r"build\用户素材\振金剑_001.png",
    r"build\用户素材\_来源凭据.json",
    # 文档
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\贴图清单.md",
    r"docs\UpdateAnnouncement_EN.md",
    # ⚠ 成品**不入库**：`release/` 在 .gitignore 里（往轮也一样，实测 git add 会直接报
    #   "paths are ignored"）⇒ 这里**不能**列它，否则 git add 整条命令返回 1。
    #   成品是本地产物，靠 `.sha1` 与公告里的哈希对外对账。
    # 探针与取证
    r"build\zftools\check\Zf153Check.java",
    r"build\zftools\check\zf153_振金剑取证.log",
    r"build\zftools\check\zf153_after.log",
    r"build\zftools\check\zf153_PotatoST_noprobe.java",
    r"build\zftools\check\zf153_server.properties.bak",
]
PATHS += [os.path.join(r"build\zftools", v) for v in VERIFY]
PATHS += [os.path.relpath(p, ROOT) for p in sorted(glob.glob(os.path.join(T, u"_zf153*")))]


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")


def main():
    fails = []
    print(u"① 探针摘干净了吗")
    main_java = io.open(os.path.join(ROOT, r"src\main\java\com\potatost\mod\PotatoST.java"),
                        encoding="utf-8").read()
    probes = [l.strip() for l in main_java.split(u"\n") if u"Check.register()" in l]
    print(u"   PotatoST.java 里的 *Check.register()：%s" % (probes or u"（无）"))
    if probes:
        fails.append(u"源码树里还挂着探针：%s" % probes)
    if os.path.exists(os.path.join(ROOT, r"src\main\java\com\potatost\mod\Zf153Check.java")):
        fails.append(u"src 下还有 Zf153Check.java")

    print(u"\n② add（显式路径，共 %d 条）" % len(PATHS))
    missing = [p for p in PATHS if not os.path.exists(os.path.join(ROOT, p))]
    if missing:
        print(u"   ⚠ 盘上不存在的路径 %d 条（跳过）：" % len(missing))
        for p in missing[:8]:
            print(u"      " + p)
    exist = [p for p in PATHS if os.path.exists(os.path.join(ROOT, p))]
    rc, out, err = git("add", "--", *exist)
    print(u"   git add exit=%d %s" % (rc, err.strip()[:200]))
    if rc != 0:
        fails.append(u"git add 失败")
    # ⚠ 取暂存清单时必须 **core.quotepath=false**：默认会把中文路径写成八进制转义
    #   （`"build/\347\224\250..."`）⇒ 与我的清单逐条比对会全被判成"多余文件"（第一版就栽了）。
    rc, out, _ = git("-c", "core.quotepath=false", "diff", "--cached", "--name-only")
    staged = [l for l in out.split(u"\n") if l.strip()]
    print(u"   暂存区共 %d 个文件" % len(staged))
    mine = set(p.replace(u"\\", u"/") for p in exist)
    extra = [p for p in staged if p not in mine]
    if extra:
        print(u"   [!!] 暂存区里有**不在我清单里**的 %d 条（要么是我漏写、要么是别人在途）：" % len(extra))
        for p in extra[:10]:
            print(u"      " + p)
        fails.append(u"暂存区有多余文件：%s" % extra[:3])
    else:
        print(u"   [OK] 暂存区的每一条都在清单里")

    if fails:
        print(u"\n有失败项 ⇒ **不提交**")
        for f in fails:
            print(u"  !! " + f)
        return 1

    print(u"\n③ commit")
    rc, out, err = git("commit", "-F", MSG)
    print(out.strip()[-800:] or err.strip()[:400])
    if rc != 0:
        fails.append(u"commit 失败")
    rc, out, _ = git("log", "--oneline", "-1")
    print(u"   最新提交：%s" % out.strip())

    if u"--push" in sys.argv and not fails:
        print(u"\n④ push")
        rc, out, err = git("push")
        print((out + err).strip()[-500:])
        if rc != 0:
            fails.append(u"push 失败")
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
