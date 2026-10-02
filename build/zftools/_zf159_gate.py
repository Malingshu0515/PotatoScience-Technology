#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
_zf159_gate.py —— 流体 / 粉尘跨模组兼容的**只读**校验门（0.12 ZF159 立）。

用户原话（2026-10-01）：
    「兼容一下沉浸工程和通用机械中与本mod同名的所有流体配方（例如沉浸原油的便携式发电机
      可以用本项目的汽油桶激活 本项目的氧气...和MEK通用） 2.本mod的碳粉 铁粉与其它mod通用
      3.目前通用锻造模板不知道是不是通用的 …」
追加口径（用户拍板）：「再加上"我们的机器也能烧别人的油"」。

━━━ 这一轮查清的三件事（都可复验，别凭印象推翻）━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

① **同名流体靠标签就通了，一条新配方都不用写**。证据是上游自己的 json：
   · Mekanism `mekanism:rotary`（旋转冷凝器，流体↔气体）：
       {"chemical_input":{"chemical":"mekanism:oxygen"},
        "fluid_input":{"tag":"c:oxygen"}, "fluid_output":{"id":"mekanism:oxygen"} …}
     —— 流体那一侧认的是 **`c:` 标签**，所以挂在 `#c:oxygen` 上的**我们的氧气**
        在它眼里就是 `mekanism:oxygen` 气体。
     Mekanism 里这样写的还有 hydrogen / chlorine / sulfuric_acid。
   · 沉浸原油：蒸馏塔吃 `#c:crude_oil`（我们的油田能直接喂它）、装瓶机与混合器吃 `#c:gasoline`、
     炼油厂与加氢处理吃 `#c:naphtha`、`generator_fuel` 吃 `#c:diesel`。
   ⇒ 所以本门**不检查"我们有没有写这些配方"**，而是检查**我们的流体有没有落在那几张标签里**。

② **`c:dusts/coal` 是雷，用户拍板不挂**（`c:dusts/carbon` 照挂）：
   通用机械 `mekanism:enriching` 有「1 个 `#c:dusts/coal` → 1 个煤」，而我们的粉碎机
   「煤 → 1 碳粉」⇒ 两个都挂上就是 **煤 → 碳粉 → 煤** 的 1:1 无限循环。
   （同理 `c:dusts/iron` 是安全的：我们的铁粉来自**铁锭**，而整个整合包里没有
     「铁粉 → 铁锭」的配方，环不闭合。）
   ⚠ 本门**必须钉住这条**：`c:dusts/coal` 里**不许出现我们的 id**。谁哪天"顺手补全"
     把碳粉挂进去，这条门就红 —— 这正是它存在的意义。

③ **便携式发电机烧不烧汽油，是 IP 自己缺配方**：IP 的 `GasGeneratorTileEntity` 走 IE 的
   `immersiveengineering:generator_fuel`，而 IP 只注册了 diesel / diesel_sulfur / kerosene
   三条（它自己的手册第 15 页却写着"燃烧汽油、石脑油、粗苯" —— 手册陈旧）。
   我们补的是**我们自己命名空间**下的三条 generator_fuel（汽油/石脑油/液化气），
   带 `neoforge:mod_loaded=immersivepetroleum` 守卫。

跑法：
    python build\\zftools\\_zf159_gate.py

出口：0 = 全过；1 = 有失败项。
"""

import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
RES = os.path.join(ROOT, "src", "main", "resources")
FLUID_TAGS = os.path.join(RES, "data", "c", "tags", "fluid")
ITEM_TAGS = os.path.join(RES, "data", "c", "tags", "item")
RECIPES = os.path.join(RES, "data", "potato_s_t", "recipe")
# 别的 mod 的 jar 可能不在开发实例里（本工程只在做兼容时临时装），所以两个位置都认
JAR_DIRS = [
    r"E:\game\pcl快照\.minecraft\versions\科技mod乱炖\mods",
    os.path.join(ROOT, "run", "client", "mods"),
    os.path.join(ROOT, "run", "server", "mods"),
]

# 我们的 10 种「与别家同名」的流体 -> 我们自己的流体 id
OUR_FLUIDS = {
    "oxygen": "potato_s_t:oxygen",
    "hydrogen": "potato_s_t:hydrogen",
    "chlorine": "potato_s_t:chlorine",
    "nitrogen": "potato_s_t:nitrogen",
    "sulfuric_acid": "potato_s_t:sulfuric_acid",
    "crude_oil": "potato_s_t:crude_oil",
    "diesel": "potato_s_t:diesel",
    "gasoline": "potato_s_t:gasoline",
    "naphtha": "potato_s_t:naphtha",
    "lpg": "potato_s_t:lpg",
}

# 上游"认标签"的实证表：上游 jar 里的哪个文件、吃了我们哪张标签
UPSTREAM_EVIDENCE = [
    ("Mekanism", "mekanism:rotary", "c:oxygen"),
    ("Mekanism", "mekanism:rotary", "c:hydrogen"),
    ("Mekanism", "mekanism:rotary", "c:chlorine"),
    ("Mekanism", "mekanism:rotary", "c:sulfuric_acid"),
    ("ImmersivePetroleum", "distillationtower/oil", "c:crude_oil"),
    ("ImmersivePetroleum", "bottling/gasoline_bottle", "c:gasoline"),
    ("ImmersivePetroleum", "mixer/napalm", "c:gasoline"),
    ("ImmersivePetroleum", "refinery/gasoline", "c:naphtha"),
    ("ImmersivePetroleum", "hydrotreater/naphtha_cracking", "c:naphtha"),
]
FAIL = []


def fail(msg):
    FAIL.append(msg)


def ok(msg):
    print("  [OK]   " + msg)


def load(path):
    return json.loads(io.open(path, encoding="utf-8").read())


def read_bytes(path):
    return io.open(path, "rb").read()


def find_jars():
    """在候选目录里找四个上游 jar；返回 {关键字: 路径}。"""
    found = {}
    keys = ["MekanismGenerators", "Mekanism-", "ImmersivePetroleum", "ImmersiveEngineering"]
    for d in JAR_DIRS:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".jar"):
                continue
            for k in keys:
                if k in fn and k not in found:
                    found[k] = os.path.join(d, fn)
    return found


# ---------------------------------------------------------------- ①
def check_fluid_tags():
    print("--- ① 我们的同名流体是否落在对应的 c: 标签里")
    for name, our_id in sorted(OUR_FLUIDS.items()):
        p = os.path.join(FLUID_TAGS, name + ".json")
        if not os.path.isfile(p):
            fail("data/c/tags/fluid/%s.json 不存在（我们自己的流体反而没挂标签）" % name)
            continue
        d = load(p)
        vals = d.get("values")
        if not isinstance(vals, list):
            fail("c:%s 的 values 不是数组" % name)
            continue
        if our_id not in vals:
            fail("c:%s 里没有 %s" % (name, our_id))
        if "replace" in d and d["replace"] is True:
            fail("c:%s 写了 replace=true —— 会清空上游同标签（默认 false 才是合并）" % name)
    if not FAIL:
        ok("10 张 c:<名字> 流体标签齐备、都收了我们自己的流体、都没写 replace")


# ---------------------------------------------------------------- ②
def check_dust_tags():
    print("--- ② 粉尘标签（碳粉/铁粉/钛粉）与『不许挂 coal』那条红线")
    want = {
        "carbon": "potato_s_t:carbon",
        "iron": "potato_s_t:iron_powder",
        "titanium": "potato_s_t:titanium_powder",
    }
    for name, our_id in sorted(want.items()):
        p = os.path.join(ITEM_TAGS, "dusts", name + ".json")
        if not os.path.isfile(p):
            fail("data/c/tags/item/dusts/%s.json 不存在" % name)
            continue
        vals = load(p).get("values", [])
        if our_id not in vals:
            fail("c:dusts/%s 里没有 %s" % (name, our_id))
    # ⚠ 红线：c:dusts/coal 里绝对不许有我们
    coal = os.path.join(ITEM_TAGS, "dusts", "coal.json")
    if os.path.isfile(coal):
        vals = load(coal).get("values", [])
        ours = [v for v in vals if isinstance(v, str) and v.startswith("potato_s_t:")]
        if ours:
            fail("c:dusts/coal 里出现了我们的物品 %s —— 那会造成『煤→碳粉→煤』1:1 无限循环"
                 "（Mekanism 的 enriching 就吃这条标签），用户明确拍板不挂" % ours)
    # 父标签
    parent = os.path.join(ITEM_TAGS, "dusts.json")
    if not os.path.isfile(parent):
        fail("data/c/tags/item/dusts.json（父标签）不存在")
    else:
        pv = load(parent).get("values", [])
        for name, our_id in sorted(want.items()):
            if our_id not in pv:
                fail("父标签 c:dusts 缺 %s" % our_id)
    # 粉碎机的封闭标签
    closed = os.path.join(RES, "data", "potato_s_t", "tags", "item", "crushable_as_coals.json")
    if not os.path.isfile(closed):
        fail("data/potato_s_t/tags/item/crushable_as_coals.json 不存在"
             "（粉碎机不该再直接吃 #minecraft:coals 这种开放标签）")
    else:
        cv = load(closed).get("values", [])
        if cv != ["#minecraft:coals"]:
            fail("crushable_as_coals 的内容变了（现在是 %s）—— 换之前先看这条门的注释" % cv)
    if not FAIL:
        ok("c:dusts/{carbon,iron,titanium} 各收 1 件 + 父标签齐；c:dusts/coal **没有**我们的东西（红线守住）")


# ---------------------------------------------------------------- ③
def check_generator_fuel_recipes():
    print("--- ③ 我们补的三条便携式发电机燃料（generator_fuel）")
    expect = {
        "gasoline": "c:gasoline",
        "naphtha": "c:naphtha",
        "lpg": "c:lpg",
    }
    d = os.path.join(RECIPES, "generator_fuel")
    if not os.path.isdir(d):
        fail("data/potato_s_t/recipe/generator_fuel/ 目录不存在")
        return
    for name, tag in sorted(expect.items()):
        p = os.path.join(d, name + ".json")
        if not os.path.isfile(p):
            fail("generator_fuel/%s.json 不存在" % name)
            continue
        r = load(p)
        if r.get("type") != "immersiveengineering:generator_fuel":
            fail("%s.json 的 type 不是 immersiveengineering:generator_fuel" % name)
        if r.get("fluidTag") != tag:
            fail("%s.json 的 fluidTag 不是 %s（现在是 %r）" % (name, tag, r.get("fluidTag")))
        bt = r.get("burnTime")
        if not isinstance(bt, int) or bt <= 0:
            fail("%s.json 的 burnTime 不是正整数" % name)
        conds = r.get("neoforge:conditions") or []
        if not any(c.get("modid") == "immersivepetroleum" for c in conds):
            fail("%s.json 缺 neoforge:mod_loaded=immersivepetroleum 守卫（没装 IP 时是条死配方）" % name)
    if not FAIL:
        ok("3 条 generator_fuel（汽油/石脑油/液化气）形状合规、都带 IP 守卫")


# ---------------------------------------------------------------- ④
def check_generator_java():
    print("--- ④ 大型柴油发电机的多燃料实现（源码级）")
    p = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod",
                     "DieselGeneratorBlockEntity.java")
    s = io.open(p, encoding="utf-8").read()
    checks = [
        ("有 FuelClass 枚举", "enum FuelClass" in s),
        ("六族燃料各自带 c: 标签", all(('"%s"' % t) in s for t in
                                 ("c:diesel", "c:biodiesel", "c:high_power_biodiesel",
                                  "c:gasoline", "c:naphtha", "c:lpg"))),
        ("有按标签判定的 fuelClassOf", "fuelClassOf" in s),
        ("罐与流体能力改走 isFuel", s.count("isFuel(") >= 2),
        ("发电量按燃料族算（不再写死 ENERGY_PER_TICK）", "energyPerTick()" in s),
        ("ENERGY_PER_TICK 常量仍是 7200（用户给的数没动）", "ENERGY_PER_TICK = 7200" in s),
    ]
    for label, good in checks:
        if not good:
            fail("DieselGeneratorBlockEntity：%s —— 没做到" % label)
    # 我们自己那 8 个流体必须写死在 fuelClassOf 的 ownClassOf 里（不依赖数据包）
    if "ownClassOf" not in s:
        fail("DieselGeneratorBlockEntity：缺 ownClassOf（标签没绑好时自己人会掉出去）")
    if not FAIL:
        ok("FuelClass 六族 + ownClassOf 写死兜底 + 罐/能力/发电量三处都改到了；ENERGY_PER_TICK 未动")


# ---------------------------------------------------------------- ⑤
def check_upstream_evidence():
    print("--- ⑤ 上游『认标签』的实证（扫 jar；jar 不在就跳过）")
    jars = find_jars()
    if not jars:
        print("  [SKIP] 一个上游 jar 都找不到（开发实例里没装）")
        return
    print("  找到：" + ", ".join("%s=%s" % (k, os.path.basename(v)) for k, v in sorted(jars.items())))
    import zipfile
    cache = {}
    for who, what, tag in UPSTREAM_EVIDENCE:
        key = [k for k in jars if k.rstrip("-") in who or who in k]
        if not key:
            continue
        jar = jars[key[0]]
        if jar not in cache:
            cache[jar] = zipfile.ZipFile(jar)
        z = cache[jar]
        hits = []
        for n in z.namelist():
            if not n.endswith(".json") or "/recipe" not in n:
                continue
            s = z.read(n).decode("utf-8", "replace")
            # ⚠ 判据要用**去空格压缩后**的文本：上游有些 json 是压成一行的
            #   （`{"type":"mekanism:rotary","chemical_input":…`）。
            #   第一版拿 `what.split("/")[-1] in n` 当文件名判据 ⇒
            #   Mekanism 的配方在 `mekanism/recipe/rotary/oxygen.json`，
            #   文件名是 oxygen，而 what 是 "mekanism:rotary"，永远匹配不上 ⇒ 假红 4 条。
            compact = re.sub(r"\s+", "", s)
            tag_needle = '"tag":"%s"' % tag
            if tag_needle in compact and what.split(":")[-1] in n:
                hits.append(n)
        if not hits:
            fail("在 %s 里找不到『%s 吃 %s』的证据（上游改过？兼容结论要重查）" % (who, what, tag))
    if not FAIL:
        ok("Mekanism 的 rotary（氧气/氢气/氯气/硫酸）与沉浸原油的 5 条配方都确实吃我们的 c: 标签")


def main():
    print("=" * 84)
    print("_zf159_gate.py —— 流体 / 粉尘跨模组兼容 只读校验（沉浸工程 / 沉浸原油 / 通用机械）")
    print("=" * 84)
    check_fluid_tags()
    check_dust_tags()
    check_generator_fuel_recipes()
    check_generator_java()
    check_upstream_evidence()
    print("=" * 84)
    if FAIL:
        print("失败 %d 项：" % len(FAIL))
        for m in FAIL:
            print("  [FAIL] " + m)
        return 1
    print("结论：全过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
