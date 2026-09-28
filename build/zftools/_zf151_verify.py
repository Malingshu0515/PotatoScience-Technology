# -*- coding: utf-8 -*-
r'''_zf151_verify.py —— ZF151 **常驻校验**：挖掘口径（太阳能板掉落 / 全机器镐子标签 / 空手也掉）。

只读盘上文件，不开游戏。分区：
  A 太阳能板：`SolarPanelBlock` 必须覆写 `getDrops` 返回自己（本轮修的 bug）；
  B 镐子标签：`data/minecraft/tags/block/mineable/pickaxe.json` 必须含**每一台机器**
    （机器 = 有 BlockItem 的方块 + 四个结构件；矿与建材另算）；
  C 空手掉落：ModBlocks 里**只有**矿与建材家族带 `requiresCorrectToolForDrops`，
    机器一个都不许带；两个接线口必须已去掉；
  D 口径记录（§4.161）：档案里写着「标签只管速度、不管掉落」与那张实测表；
  E 文档：§5 行 / §9 小节 / 交接 / 英文公告。

跑法：python build\zftools\_zf151_verify.py
'''
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
RES = os.path.join(ROOT, "src", "main", "resources")
TAG = os.path.join(RES, "data", "minecraft", "tags", "block", "mineable", "pickaxe.json")
MODBLOCKS = os.path.join(JAVA, "ModBlocks.java")
SOLAR = os.path.join(JAVA, "SolarPanelBlock.java")
DOC = os.path.join(ROOT, "docs", "开发档案.md")
HAND = os.path.join(ROOT, "docs", "多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")

# 四个结构件（没有 BlockItem，但属于机器外壳/接线口）
PARTS = [u"electric_blast_furnace_part", u"alloy_smelter_part",
         u"alloy_smelter_port", u"diesel_generator_port"]
# 刻意学原版铁块/煤炭块的建材家族（**允许**要镐）
DECOR = [u"common_metal_block", u"advanced_metal_block", u"stable_metal_block",
         u"heat_resistant_metal_block", u"heater", u"heat_sink", u"wiring_block",
         u"asphalt_block"]

passed, failed, fails = 0, 0, []


def check(cond, label, detail=u""):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label if not detail else u"%s（%s）" % (label, detail))
        print(u"  [FAIL] " + label + (u" —— " + detail if detail else u""))


def read(p):
    return io.open(p, encoding=u"utf-8").read() if os.path.isfile(p) else u""


def block_items():
    """有 BlockItem 的方块 id（= 玩家能拿到手、能放下来的机器/建材）。

    ⚠ 判据是「同一个 `BLOCKS.register("X", …)` 段里紧接着又 `ITEMS.register(`」——
    不能拿 `X.toUpperCase() + "_ITEM"` 去猜：`diesel_generator_controller` 的物品叫
    `DIESEL_GENERATOR_ITEM`（名字不一样），第一版就是这么误报"漏了 diesel_generator"的。
    """
    t = read(MODBLOCKS)
    segs = re.split(r'BLOCKS\.register\(', t)[1:]
    ids = set()
    for seg in segs:
        m = re.match(r'\s*"([a-z0-9_]+)"', seg)
        if m and u"ITEMS.register(" in seg[:2000]:
            ids.add(m.group(1))
    return ids


def main():
    print(u"================ ZF151 常驻校验：挖掘口径 ================")

    # ---------------- A 太阳能板 ----------------
    print(u"\n---- A 太阳能板：挖了要掉 -------------")
    solar = read(SOLAR)
    check(u"public List<ItemStack> getDrops(" in solar,
          u"A1 SolarPanelBlock 覆写了 getDrops（本轮修的就是这个）")
    check(u"return List.of(new ItemStack(this));" in solar,
          u"A2 返回值是 List.of(new ItemStack(this))（与另外 29 台机器逐字一致）")
    check(u"import net.minecraft.world.level.storage.loot.LootParams;" in solar
          and u"import java.util.List;" in solar,
          u"A3 两个 import 都在（LootParams / java.util.List）")
    loot = os.path.join(RES, "data", "potato_s_t", "loot_table", "blocks", "solar_panel.json")
    check(True, u"A4 记录：太阳能板走的是 Java getDrops（loot_table 里有/无都不影响）：%s"
          % (u"有" if os.path.isfile(loot) else u"无"))

    # ---------------- B 镐子标签 ----------------
    print(u"\n---- B 镐子标签：每一台机器都在里面 ----")
    tag = set(json.loads(read(TAG))[u"values"])
    tag = set(x.split(u":", 1)[1] if x.startswith(u"potato_s_t:") else x for x in tag)
    have_item = block_items()
    machines = sorted(have_item - set(DECOR))
    missing = [m for m in machines + PARTS if u"potato_s_t:" + m not in
               [u"potato_s_t:" + x for x in tag]]
    check(len(tag) >= 57, u"B1 标签条数 ≥ 57（本轮 54 → 57）", u"实际 %d" % len(tag))
    check(not missing, u"B2 每一台机器（%d 个有物品的 + %d 个结构件）都在标签里"
          % (len(machines), len(PARTS)), u"漏 %s" % missing)
    for extra in (u"fluid_exchanger", u"electric_blast_furnace_part", u"alloy_smelter_part"):
        check(extra in tag, u"B3 本轮补的那一项在标签里：%s" % extra)
    check(u"solar_panel" in tag, u"B4 太阳能板仍在标签里（镐子加速）")

    # ---------------- C 空手掉落 ----------------
    print(u"\n---- C 空手掉落：机器一个都不许要工具 ----")
    t = read(MODBLOCKS)
    # 逐条目扫：拿到每个 register(...) 段，看它带不带 requiresCorrectToolForDrops
    segs = re.split(r'BLOCKS\.register\(', t)[1:]
    offenders = []
    decor_with = []
    for seg in segs:
        m = re.match(r'\s*"([a-z0-9_]+)"', seg)
        if not m:
            continue
        name = m.group(1)
        body = seg[:1200]
        if u"requiresCorrectToolForDrops()" not in body:
            continue
        if name in DECOR:
            decor_with.append(name)
        elif name.endswith(u"_ore") or name.startswith(u"deepslate_"):
            pass
        else:
            offenders.append(name)
    check(not offenders, u"C1 除矿与建材外，没有方块带 requiresCorrectToolForDrops",
          u"越界：%s" % offenders)
    check(u"alloy_smelter_port" not in decor_with and u"alloy_smelter_port" not in offenders,
          u"C2 合金炉接线口已去掉 requiresCorrectToolForDrops")
    check(u"diesel_generator_port" not in offenders,
          u"C3 柴油机接线口已去掉 requiresCorrectToolForDrops")
    # ⚠ 建材家族的需求工具标志写在**共享 helper** 里（`decorativeMetalBlock()`），
    #   逐条目正则扫不到 ⇒ 改成验 helper 本身 + 沥青块那条直写 + 运行期矩阵（探针报告）。
    check(u"private static Block decorativeMetalBlock()" in t
          and u"requiresCorrectToolForDrops()" in t.split(u"private static Block decorativeMetalBlock()")[1][:400],
          u"C4 建材家族的 requiresCorrectToolForDrops 写在 decorativeMetalBlock() helper 里")
    check(u"asphalt_block" in decor_with, u"C5 沥青块照旧需要镐（与煤炭块同款）")
    rep = read(os.path.join(ROOT, "build", "zftools", u"_zf151_probe_utf8.txt"))
    check(u"判词：ALL OK" in rep, u"C6 运行期矩阵（探针报告）是全绿")
    check(u"A1 每一台机器都在 mineable/pickaxe 里（镐子加速）—— 漏 0" in rep
          and u"A2 每一台机器都不需要正确工具（空手也掉）—— 例外 0" in rep,
          u"C7 探针实盘：机器漏标签 0 个、要工具的例外 0 个")

    # ---------------- D 文档 ----------------
    print(u"\n---- D 文档 ----")
    doc, hand, ann = read(DOC), read(HAND), read(ANN)
    check(u"### 4.160 " in doc, u"D1 档案有 §4.160（标签只管速度 / 探针看不见新实体）")
    check(u"| ZF151 |" in doc, u"D2 档案 §5 有 ZF151 行")
    check(u"### ZF151" in doc, u"D3 档案 §9 有 ZF151 小节")
    check(u"## New in 0.12 ZF151" in ann, u"D4 英文公告里有 ZF151 那一条（逐字标题）")
    check(u"mineable/pickaxe" in ann or u"pickaxe" in ann, u"D5 公告讲了镐子标签那件事")
    check(u"ZF151" in hand, u"D6 交接文档里有本轮那一条")

    print(u"")
    print(u"================ 通过 %d / 失败 %d ================" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == u"__main__":
    sys.exit(main())
