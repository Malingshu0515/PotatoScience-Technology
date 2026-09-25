# -*- coding: utf-8 -*-
u"""_zf113_backup.py —— ZF113 **动手前**的改前件（§10）

用户原话（附了酸性反应室的界面截图）：
  「这个gui可以改一下 有些重叠 然后合金冶炼炉的jei配方箭头也向左移5个像素」

量出来的两处重叠（都是坐标算出来的，不是感觉）：
  ① 状态灯 (174,25) 8×8 —— 它的框画在 173..183，而**硫槽**在 (160,25)、框到 177 ⇒ 压住 4 px
     （截图里槽右上角那个黄色小方块就是灯）；
  ② 「物品栏」标签由 `MachineScreen` 按 `imageHeight-93` 算 ⇒ 216-93 = **123**，
     而四个配方按钮在 y=110..**124** ⇒ 压住 1~2 px。

本轮会动到的：`client/AcidicReactionChamberScreen.java`、`client/jei/MachineRecipeCategory.java`
+ `_zf102_verify.py`（它钉着 `new StatusLampPart(174`）+ 全部常驻校验脚本 + 文档 + 旧成品。
"""
import glob
import hashlib
import io
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
BK = r"C:\PotatoST救援\zf113_pre"
JAVA = r"src\main\java\com\potatost\mod"
TOOLS = r"build\zftools"

FILES = [
    JAVA + r"\client\AcidicReactionChamberScreen.java",
    JAVA + r"\client\jei\MachineRecipeCategory.java",
    JAVA + r"\AcidicReactionChamberMenu.java",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]
NEW = [TOOLS + r"\_zf113_verify.py", TOOLS + r"\_zf113_docs.py", TOOLS + r"\_zf113_gatesnap.py"]

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [STOP] 备份根已存在：%s" % BK)
        return 1
    lines, ok = [], 0
    todo = list(FILES)
    for pat in ("_zf*_verify.py", "_zf*_repro.py", "_zf*_guard.py", "_zf*_falsify.py",
                "_zf*_gatesnap.py"):
        for p in sorted(glob.glob(os.path.join(ROOT, TOOLS, pat))):
            rel = os.path.relpath(p, ROOT)
            if rel not in todo:
                todo.append(rel)
    for rel in todo:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            fails.append(u"缺文件：%s" % rel)
            continue
        dst = os.path.join(BK, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        before = sha1(src)
        shutil.copy2(src, dst)
        if before != sha1(dst):
            fails.append(u"%s：拷贝后哈希不一致" % rel)
        else:
            ok += 1
            lines.append(u"%s  %10d  %s" % (sha1(src), os.path.getsize(dst), rel))
    io.open(os.path.join(BK, u"_zf113_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"本轮开始前这些路径应当不存在：\n" + u"\n".join(NEW) + u"\n")
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
