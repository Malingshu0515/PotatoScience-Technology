# -*- coding: utf-8 -*-
r"""_zf118_backup.py —— ZF118 **动手前**的改前件（§10）

用户原话：「星轨坠配方；中间一个下界之星 上下左右各一个星璨钢 四角放岩浆块」

本轮 = **一个合成配方**（走生成器表 `_zf45_recipes.py`，不手写 JSON）。会被碰到的东西：
  · 生成器表 `_zf45_recipes.py`（加一条）
  · **新**配方 JSON `data\potato_s_t\recipe\starfall_pendant.json`（本轮开始前**不该存在**）
  · 三份文档（档案 §5/§9、交接文档的活体数字、英文公告里那句「no recipe yet」）
  · 全部常驻校验脚本（配方的活体数字：59 份 / 53 条 crafting_shaped 会变 60 / 54）
  · 旧成品 jar 与 .sha1

⚠ 顺手把**盘上现有 59 份配方**全抄一份 —— 用来证明"本轮只新增、没改旧"
  （`_zf118_verify.py` 会拿内嵌 sha1 表逐份比）。
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
BK = r"C:\PotatoST救援\zf118_pre"
TOOLS = r"build\zftools"
CHECK = TOOLS + r"\check"
RDIR = r"src\main\resources\data\potato_s_t\recipe"

FILES = [
    TOOLS + r"\_zf45_recipes.py",
    TOOLS + r"\_zf69_verify.py",
    TOOLS + r"\_zf73_repro.py",
    TOOLS + r"\_zf73_verify.py",
    TOOLS + r"\_zf95_verify.py",
    TOOLS + r"\_zf96_verify.py",
    TOOLS + r"\_zf97_verify.py",
    TOOLS + r"\_zf100_verify.py",
    TOOLS + r"\_zf100_recipe_guard.py",
    TOOLS + r"\_zf101_verify.py",
    TOOLS + r"\_zf102_verify.py",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]
# 盘上 59 份配方全抄（"只加不改"的证据）
FILES += [RDIR + "\\" + n for n in sorted(os.listdir(os.path.join(ROOT, RDIR)))
          if n.endswith(".json")]

NEW = [RDIR + r"\starfall_pendant.json",
       CHECK + r"\Zf118Check.java"] + \
      [TOOLS + r"\_zf118_%s.py" % s for s in
       ("backup", "recipe", "verify", "falsify", "docs", "gatesnap", "unprobe")]

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [STOP] 备份根已存在：%s" % BK)
        return 1
    lines, ok = [], 0
    todo = list(FILES)
    for pat in ("_zf*_verify.py", "_zf*_falsify.py", "_zf*_gatesnap.py", "_zf*gates.ps1"):
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
        b = sha1(src)
        shutil.copy2(src, dst)
        if b != sha1(dst):
            fails.append(u"%s：哈希不一致" % rel)
        else:
            ok += 1
            lines.append(u"%s  %10d  %s" % (b, os.path.getsize(dst), rel))
    io.open(os.path.join(BK, u"_zf118_newfiles.txt"), "w", encoding="utf-8",
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
