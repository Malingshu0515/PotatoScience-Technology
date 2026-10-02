# -*- coding: utf-8 -*-
u"""_zf167_commit.py —— ZF167 提交（**显式列路径**，绝不 `git add -A`）

⚠ 工作树里同时有**别的线在途**的改动（Curios 桥、流体转化器、教程手册文案、配方…）
   ⇒ 只能一个路径一个路径地 add。本轮的文件清单：
     ① 新建：6 个 java + 机器/物品资源 + 四份配方 + 乙醇标签 + 我的 `_zf167_*` 脚本 + 探针
     ② 修改：ModItems / ModBlocks / ModMenus / PotatoST / PotatoSTClient / MachineRecipes /
             PotatoSTJeiPlugin / StatusLampPart / 五份 lang（别的线已代提交）/ `_zf153_verify.py` /
             `_zf149_verify.py` / `_zf149_jar.py` / **40 份跟平过的常驻门** / 四份文档
     ③ 「跟平过的门」用**内容判据**挑（含 `620`/`622` 的 `_zf*_verify.py` 与 `_zf*_jarcheck.py`），
        不靠手抄名单（手抄必漏）。

跑法：python build\\zftools\\_zf167_commit.py [--push]
"""
import glob
import io
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
MOD = r"src\main\java\com\potatost\mod"
ASSETS = r"src\main\resources\assets\potato_s_t"
MSG = os.path.join(TOOLS, "_zf167_commit_msg.txt")

PATHS = [
    MOD + r"\ColaItem.java", MOD + r"\CanningMachineRecipes.java",
    MOD + r"\BeverageCanningMachineBlock.java", MOD + r"\BeverageCanningMachineBlockEntity.java",
    MOD + r"\BeverageCanningMachineMenu.java", MOD + r"\client\BeverageCanningMachineScreen.java",
    MOD + r"\ModItems.java", MOD + r"\ModBlocks.java", MOD + r"\ModMenus.java",
    MOD + r"\PotatoST.java", MOD + r"\PotatoSTClient.java", MOD + r"\MachineRecipes.java",
    MOD + r"\client\jei\PotatoSTJeiPlugin.java", MOD + r"\client\gui\parts\StatusLampPart.java",
    ASSETS + r"\blockstates\beverage_canning_machine.json",
    ASSETS + r"\models\block\beverage_canning_machine.json",
    ASSETS + r"\models\item\beverage_canning_machine.json",
    ASSETS + r"\models\item\empty_aluminum_can.json",
    ASSETS + r"\models\item\cola.json",
    ASSETS + r"\textures\block\beverage_canning_machine_top.png",
    ASSETS + r"\textures\block\beverage_canning_machine_side.png",
    r"src\main\resources\data\potato_s_t\recipe\empty_aluminum_can.json",
    r"src\main\resources\data\potato_s_t\recipe\empty_aluminum_can_from_smelting.json",
    r"src\main\resources\data\potato_s_t\recipe\empty_aluminum_can_from_blasting.json",
    r"src\main\resources\data\potato_s_t\recipe\beverage_canning_machine.json",
    r"src\main\resources\data\c\tags\fluid\ethanol.json",
    r"docs\开发档案.md", r"docs\多会话协作交接.md", r"docs\贴图清单.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"build\zftools\_zf149_verify.py", r"build\zftools\_zf149_jar.py",
    r"build\zftools\_zf153_verify.py",
    r"build\zftools\check\Zf167Check.java",
    r"build\zftools\check\zf167_罐装机取证.log",
    r"build\zftools\check\zf167_after.log",
    r"build\zftools\check\zf167_PotatoST_noprobe.java",
    r"build\zftools\check\zf167_server.properties.bak",
]
# 跟平过的常驻门：按内容挑（含 620 或 622）
for pat in (u"_zf*_verify.py", u"_zf*_jarcheck.py"):
    for p in sorted(glob.glob(os.path.join(TOOLS, pat))):
        t = io.open(p, encoding="utf-8").read()
        if re.search(u"\\b(620|622)\\b", t):
            PATHS.append(os.path.relpath(p, ROOT))
PATHS += [os.path.relpath(p, ROOT) for p in sorted(glob.glob(os.path.join(TOOLS, u"_zf167*")))]


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")


def main():
    fails = []
    main_java = io.open(os.path.join(ROOT, MOD, "PotatoST.java"), encoding="utf-8").read()
    probes = [l.strip() for l in main_java.split(u"\n") if u"Check.register()" in l]
    print(u"① 探针摘干净了吗：%s" % (probes or u"（无）"))
    if probes:
        fails.append(u"源码树里还挂着探针")
    if os.path.exists(os.path.join(ROOT, MOD, "Zf167Check.java")):
        fails.append(u"src 下还有 Zf167Check.java")

    exist = [p for p in PATHS if os.path.exists(os.path.join(ROOT, p))]
    print(u"\n② add（%d 条，盘上有 %d 条）" % (len(PATHS), len(exist)))
    rc, out, err = git("add", "--", *exist)
    print(u"   git add exit=%d %s" % (rc, err.strip()[:200]))
    if rc != 0:
        fails.append(u"git add 失败")
    rc, out, _ = git("-c", "core.quotepath=false", "diff", "--cached", "--name-only")
    staged = [l for l in out.split(u"\n") if l.strip()]
    mine = set(p.replace(u"\\", u"/") for p in exist)
    extra = [p for p in staged if p not in mine]
    print(u"   暂存 %d 条；不在我清单里的 %d 条" % (len(staged), len(extra)))
    for p in extra[:8]:
        print(u"      " + p)
    if extra:
        fails.append(u"暂存区有多余：%s" % extra[:3])

    if fails:
        print(u"\n有失败项 ⇒ 不提交")
        for f in fails:
            print(u"  !! " + f)
        return 1

    print(u"\n③ commit")
    rc, out, err = git("commit", "-F", MSG)
    print((out or err).strip()[-400:])
    if rc != 0:
        fails.append(u"commit 失败")
    rc, out, _ = git("log", "--oneline", "-1")
    print(u"   最新提交：%s" % out.strip())
    if u"--push" in sys.argv and not fails:
        print(u"\n④ push")
        rc, out, err = git("push")
        print((out + err).strip()[-400:])
        if rc != 0:
            fails.append(u"push 失败")
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
