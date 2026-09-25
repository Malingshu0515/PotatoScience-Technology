# -*- coding: utf-8 -*-
u"""_zf109_backup.py —— ZF109 **动手前**的改前件（§10）

用户原话（2026 本轮）：
  「海洋油田可以利用起来了 加一个采油机（配方；【硬质钛合金】【耐热金属块】【硬质钛合金】，
    【油桶】【高压气罐】【油桶】，【流体泵】【流体泵】【流体泵】） 在海洋油田群系工作
    gui为一个大罐子25B储量（不是那种竖直的了 是一个横过来的矩形罐子）和一个工作指示灯
    能量条不需要 下方必须有水源方块 检测下方连接的 含水锁链的数量
    耗能公式为 80n*1/10n+80n FE/t 原油获取为 10n mb/s （n为下方含水锁链个数）
    每开采25~80桶原油 附近10*10的海洋油桶群系会变成符合旁边群系的海洋（冻洋 暖洋 温带海洋...）」
两个用户拍板的选项：
  · 耗能公式 = **B：8n² + 80n FE/t**（从左到右算 80×n×1÷10×n）
  · 群系转换范围 = **10×10 区块（以机器为中心 160×160 格）**

本轮会动到的：
  · Java **改** 5 个：`ModBlocks` / `ModMenus` / `PotatoST`（两个能力）/ `PotatoSTClient`（界面）
    / `client/gui/parts/StatusLampPart`（新状态码 15、16）
  · Java **新** 5 个：`OilPumpBlock` / `OilPumpBlockEntity` / `OilPumpMenu`
    / `client/OilPumpScreen` / `client/gui/parts/HorizontalFluidTankPart`
  · 资源**改** 5 个：四语言 + `data/minecraft/tags/block/mineable/pickaxe.json`（§4.52 老规矩）
  · 资源**新** 6 个：`blockstates/oil_pump.json`、`models/block/oil_pump.json`、
    `models/item/oil_pump.json`、`textures/block/oil_pump.png`（脚本画）、
    `recipe/oil_pump.json`、（机脚贴图不加 —— 方块六面同图）
  · 往轮校验器：**键数耦合的 16 份** + **配方清单耦合的 6 份** + 本轮新脚本
  · 工具：本轮新脚本；`_zf107_gatesnap.py` 是"快照"，本轮另起 `_zf109_gatesnap.py`（不动它）
  · 文档 3 份 + 旧成品 jar 与 `.sha1`

⚠ 备份根已存在就直接退出（绝不覆盖上一次的改前件）。
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
BK = r"C:\PotatoST救援\zf109_pre"
JAVA = r"src\main\java\com\potatost\mod"
CLIENT = JAVA + r"\client"
TOOLS = r"build\zftools"
DATA = r"src\main\resources\data"
RES = r"src\main\resources"

# ---- 本轮**会改**的既有文件（逐份抄下来；回退时照抄回去） ----
FILES = [
    # Java 汇合点（只加行，§4.7）
    JAVA + r"\ModBlocks.java",
    JAVA + r"\ModMenus.java",
    JAVA + r"\PotatoST.java",
    JAVA + r"\PotatoSTClient.java",
    JAVA + r"\client\gui\parts\StatusLampPart.java",
    # 资源：四语言 + 挖掘标签
    RES + r"\assets\potato_s_t\lang\zh_cn.json",
    RES + r"\assets\potato_s_t\lang\en_us.json",
    RES + r"\assets\potato_s_t\lang\ja_jp.json",
    RES + r"\assets\potato_s_t\lang\ru_ru.json",
    DATA + r"\minecraft\tags\block\mineable\pickaxe.json",
    # 文档 + 旧成品
    r"docs\开发档案.md",
    r"docs\贴图清单.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]

# ---- 键数耦合的 16 份（§4.x：加/删语言键要一起重定目标） ----
KEYCOUPLED = ["_zf71_verify.py", "_zf73_verify.py", "_zf75_verify.py", "_zf78_verify.py",
              "_zf79_verify.py", "_zf80_verify.py", "_zf81_verify.py", "_zf82_verify.py",
              "_zf93_verify.py", "_zf96_verify.py", "_zf97_verify.py", "_zf98_verify.py",
              "_zf100_verify.py", "_zf101_verify.py", "_zf102_verify.py", "_zf103_verify.py"]
# ---- 配方清单耦合的（加一份合成配方就要一起改） ----
RECIPECOUPLED = ["_zf73_repro.py", "_zf95_verify.py", "_zf100_recipe_guard.py", "_zf45_recipes.py"]

# ---- 本轮开始前"盘上还没有"的路径：回退时一律删除 ----
NEW = [
    JAVA + r"\OilPumpBlock.java",
    JAVA + r"\OilPumpBlockEntity.java",
    JAVA + r"\OilPumpMenu.java",
    CLIENT + r"\OilPumpScreen.java",
    CLIENT + r"\gui\parts\HorizontalFluidTankPart.java",
    RES + r"\assets\potato_s_t\blockstates\oil_pump.json",
    RES + r"\assets\potato_s_t\models\block\oil_pump.json",
    RES + r"\assets\potato_s_t\models\item\oil_pump.json",
    RES + r"\assets\potato_s_t\textures\block\oil_pump.png",
    DATA + r"\potato_s_t\recipe\oil_pump.json",
    TOOLS + r"\_zf109_verify.py",
    TOOLS + r"\_zf109_falsify.py",
    TOOLS + r"\_zf109_textures.py",
    TOOLS + r"\_zf109_lang.py",
    TOOLS + r"\_zf109_gatesnap.py",
    TOOLS + r"\_zf109_retarget.py",
]

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [STOP] 备份根已存在：%s" % BK)
        return 1
    lines, ok = [], 0

    # ① 明确清单
    todo = list(FILES)
    # ② 常驻校验脚本一律全抄（本轮会碰哪几份现在不必赌对；§4.77 的教训）
    for pat in ("_zf*_verify.py", "_zf*_repro.py", "_zf*_guard.py", "_zf*_falsify.py",
                "_zf*_gatesnap.py", "_zf*_gatecount.py", "_zf45_recipes.py"):
        for p in sorted(glob.glob(os.path.join(ROOT, TOOLS, pat))):
            rel = os.path.relpath(p, ROOT)
            if rel not in todo:
                todo.append(rel)

    for rel in todo:
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

    # ③ 本轮新文件的存在性（回退时：当时不存在的一律删除）
    pre = [u"%s  %s" % (u"存在(异常)" if os.path.exists(os.path.join(ROOT, p)) else u"不存在(正常)", p)
           for p in NEW]
    io.open(os.path.join(BK, u"_zf109_newfiles.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"本轮开始前，下列路径的**存在性**（回退时：不存在的一律删除；存在的别动）\n"
        + u"\n".join(pre) + u"\n")
    bad = [p for p in NEW if os.path.exists(os.path.join(ROOT, p))]
    if bad:
        fails.append(u"本轮要新建的文件已经有同名：%s" % bad)

    # ④ 两张目录改前清单
    for rel, out in ((r"src\main\resources\data\potato_s_t\recipe", u"_recipe_before.txt"),
                     (r"src\main\java\com\potatost\mod", u"_java_before.txt"),
                     (r"src\main\resources\assets\potato_s_t\textures\block", u"_textures_before.txt")):
        d = os.path.join(ROOT, rel)
        listing = sorted(os.listdir(d))
        io.open(os.path.join(BK, out), "w", encoding="utf-8", newline=u"\n").write(
            u"改前 %s 目录 %d 项：\n" % (rel, len(listing)) + u"\n".join(listing) + u"\n")
        print(u"  改前 %s：%d 项" % (rel, len(listing)))

    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
