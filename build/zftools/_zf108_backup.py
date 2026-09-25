# -*- coding: utf-8 -*-
u"""_zf108_backup.py —— ZF108 **动手前**的改前件（§10）

用户原话：
  「你看看您不能发挥一下 简单画一下合金冶炼炉的材质（不用太好 凑活都可以）现在的太丑了谢谢啦」

本轮要动的（都是"画/接"这件事）：
  · 贴图：`textures/block/alloy_smelter.png`（主控 + 外壳 + 物品图标都用它）**重画**
          + 新增 `textures/block/alloy_smelter_formed.png`（成型后的多方块机体）
  · 模型：`models/block/alloy_smelter_{north,east,south,west}.obj` 的 **vt 表**
          （现在整个模型只有 **4 个唯一 vt** ⇒ 4×4 像素的贴图被放大铺满每一个面）
          + `alloy_smelter.mtl` 的 `map_Kd`（现在借的是 `heat_resistant_metal_block`）
  · 文档：`docs\贴图清单.md`（那三行写的是"合金冶炼炉 ← alloy_smelter.png"）
          + `docs\开发档案.md`（§4/§5/§9）+ 英文公告（如果提到借贴图）

⚠ 备份根已存在就直接退出（绝不覆盖上一次的改前件）。
"""
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
BK = r"C:\PotatoST救援\zf108_pre"
ASSETS = r"src\main\resources\assets\potato_s_t"
TOOLS = r"build\zftools"

FILES = [
    ASSETS + r"\textures\block\alloy_smelter.png",
    ASSETS + r"\models\block\alloy_smelter.mtl",
    ASSETS + r"\models\block\alloy_smelter_north.obj",
    ASSETS + r"\models\block\alloy_smelter_east.obj",
    ASSETS + r"\models\block\alloy_smelter_south.obj",
    ASSETS + r"\models\block\alloy_smelter_west.obj",
    ASSETS + r"\models\block\alloy_smelter.json",
    ASSETS + r"\models\block\alloy_smelter_part.json",
    ASSETS + r"\models\block\alloy_smelter_port.json",
    # 工具：贴图体检查（本轮会跑它；它里面有一张"我们的贴图"名单，可能要跟）
    TOOLS + r"\TextureCheck.py",
    TOOLS + r"\_zf107_gatesnap.py",
    # 文档 + 旧成品
    r"docs\贴图清单.md",
    r"docs\开发档案.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]

# 本轮开始前"盘上还没有"的路径（回退时一律删除）
NEW = [
    ASSETS + r"\textures\block\alloy_smelter_formed.png",
    TOOLS + r"\_zf108_textures.py",
    TOOLS + r"\_zf108_reuv.py",
    TOOLS + r"\_zf108_verify.py",
    TOOLS + r"\_zf108_falsify.py",
]
# ⚠ 补账（§10 第四条先例，照 ZF100/ZF107）：`_zf108_palette.py`（量现有贴图调色板的**只读**脚本）
#   是**先写的、后建的快照** —— 它不改任何资源、不进 jar，但它确实早于本快照存在。
#   所以它不进 NEW（否则"存在(异常)"会误报），改为在 `_补说明.txt` 里连哈希一起记下来。
LATE = [TOOLS + r"\_zf108_palette.py"]

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [STOP] 备份根已存在：%s" % BK)
        return 1
    lines, ok = [], 0
    for rel in FILES:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            fails.append(u"缺文件：%s" % rel)
            lines.append(u"MISSING  %s" % rel)
            continue
        dst = os.path.join(BK, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        before = sha1(src)
        shutil.copy2(src, dst)
        after = sha1(dst)
        if before != after:
            fails.append(u"%s：拷贝后哈希不一致" % rel)
        else:
            ok += 1
            lines.append(u"%s  %10d  %s" % (after, os.path.getsize(dst), rel))
    pre = [u"%s  %s" % (u"存在(异常)" if os.path.exists(os.path.join(ROOT, p)) else u"不存在(正常)", p)
           for p in NEW]
    io.open(os.path.join(BK, u"_zf108_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(
        u"本轮开始前，下列路径的**存在性**（回退时：不存在的一律删除；存在的别动）\n"
        + u"\n".join(pre) + u"\n")
    bad = [p for p in NEW if os.path.exists(os.path.join(ROOT, p))]
    if bad:
        fails.append(u"本轮要新建的文件已经有同名的：%s" % bad)
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    late = []
    for rel in LATE:
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            late.append(u"%s  %10d  %s" % (sha1(p), os.path.getsize(p), rel))
    if late:
        io.open(os.path.join(BK, u"_补说明.txt"), "w", encoding="utf-8",
                newline=u"\n").write(
            u"ZF108 改前件补账（照 ZF100 / ZF107 先例）\n"
            u"原因：下面这些文件在**建快照之前**就已经存在 —— 它们是本轮用到的**只读**分析脚本，\n"
            u"      不改任何资源、不进 jar，但仍然如实记账（回退时**不要**删）。\n\n"
            + u"\n".join(late) + u"\n")
        print(u"  补账 %d 份（只读脚本，回退时保留）" % len(late))
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
