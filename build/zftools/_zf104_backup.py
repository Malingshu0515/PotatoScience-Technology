# -*- coding: utf-8 -*-
u"""_zf104_backup.py —— ZF104 **动手前**的改前件（§10）

用户原话（两套盔甲 + 三条追加答复）：

  「minecraftmod 加两套盔甲 物品栏贴图先用铁套的
    1.钛合金套（附魔权重比金高一些）… 2.星璨钢套 … 每件效果；夜晚时获得抗性提升1（不可叠加）
    装备耐久不消耗 套装效果：末地维度盔甲不消耗耐久 … 当收到虚空伤害时 传送到最近
    （20x20 y轴范围无限高）的方块上 如果没有方块则每件装备消耗999点耐久 与附近的一个生物交换位置 …」
  「效果须满套装 耐久夜晚不消耗 虚空优先找方块 找不到就换位」
  「钛合金用轻质钛合金 星璨钢用星璨钢（贴图放item材质文件夹里了 星璨钢这个金属的配方先不做）」
  「我等你文件」→ 随后 `build\用户素材\star_steel.png`（160×160，3975 B）到位

会动到的：
  · Java：3 个新类（ModArmorMaterials / ModArmorItems / ModArmorPiece）+ ModArmorSet（事件）
    + 两处汇合点文件**只加行**（`PotatoST` 登记材料注册表、`ModItems` 创造页加 9 行）
  · 资源：`textures/item/star_steel_ingot.png`（用户素材缩放）+ `models/item/*.json` × 9
    + 四语言各 +14 键 + `data/c/tags/item/{ingots/star_steel,star_steel_ingots}.json`
    + `data/c/tags/item/ingots.json`（重生成）
  · 工具：`GenCommonTags.py`（ALLOYS 加 star_steel）+ 本轮 4 个新脚本
    + 下一轮门的模板 `_zf104_gates.ps1` / `_zf104_gatecount.py`
  · 3 份文档 + 旧成品 jar 与 `.sha1`
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
BK = r"C:\PotatoST救援\zf104_pre"
JAVA = r"src\main\java\com\potatost\mod"
TOOLS = r"build\zftools"
RES = r"src\main\resources"
FILES = [
    # ---- 只加行的两个汇合点文件（§4.7）
    JAVA + r"\PotatoST.java",
    JAVA + r"\ModItems.java",
    # ---- 工具（会被本轮的 tag 生成 / 门脚本碰到）
    TOOLS + r"\GenCommonTags.py",
    TOOLS + r"\_zf102_gates.ps1",
    TOOLS + r"\_zf102_gatecount.py",
    # ---- 资源里的"活体数字"基线
    RES + r"\assets\potato_s_t\lang\zh_cn.json",
    RES + r"\assets\potato_s_t\lang\en_us.json",
    RES + r"\assets\potato_s_t\lang\ja_jp.json",
    RES + r"\assets\potato_s_t\lang\ru_ru.json",
    RES + r"\data\c\tags\item\ingots.json",
    # ---- 用户本轮给的素材（原样留档，§4.17 等级①）
    r"build\用户素材\star_steel.png",
    # ---- 文档 + 旧成品
    r"docs\开发档案.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"docs\贴图清单.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]
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
    # 基线快照：本轮开始前"盘上还没有"的东西一并记下来（回退时按这张表删）
    probe = [
        JAVA + r"\ModArmorMaterials.java",
        JAVA + r"\ModArmorItems.java",
        JAVA + r"\ModArmorPiece.java",
        JAVA + r"\ModArmorSet.java",
        RES + r"\assets\potato_s_t\textures\item\star_steel_ingot.png",
        RES + r"\data\c\tags\item\ingots\star_steel.json",
        RES + r"\data\c\tags\item\star_steel_ingots.json",
    ]
    probe += [RES + r"\assets\potato_s_t\models\item\%s.json" % n for n in (
        "star_steel_ingot", "titanium_alloy_helmet", "titanium_alloy_chestplate",
        "titanium_alloy_leggings", "titanium_alloy_boots",
        "star_steel_helmet", "star_steel_chestplate", "star_steel_leggings", "star_steel_boots")]
    pre = [u"%s  %s" % (u"存在(异常)" if os.path.exists(os.path.join(ROOT, p)) else u"不存在(正常)", p)
           for p in probe]
    io.open(os.path.join(BK, u"_zf104_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(
        u"本轮开始前，下列路径的**存在性**（回退时：不存在的一律删除；存在的别动）\n"
        + u"\n".join(pre) + u"\n")
    lines.append(u"（附）_zf104_newfiles.txt：%d 个新路径的存在性基线" % len(probe))
    print(u"  新路径基线 %d 条（本轮开始前全部应显示 不存在(正常)）" % len(probe))
    print(u"    " + u"，".join(p.split(u"\\")[-1] for p in probe[:4]))
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
