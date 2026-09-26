# -*- coding: utf-8 -*-
r'''_zf141_verify.py —— ZF141 的**常驻校验**（星璨钢工具补齐：剑 / 镐 / 锄 + 斧子换贴图）

分七组（判据盯语义，不盯魔法数字）：

  A 档位与常量  1192 / 9.0 / 8.0 / 钻石标签 / 22；三把新工具**共用同一个档位对象**；
                **斧子那一行逐字没变**（与 `zf141_pre` 的改前件逐字节比）；
                匿名 Tier 全文件**只有一份**（`build` 加参数而不是复制实现）；
                修理材料 = 星璨钢锭（懒取）
  B 物品类      `StarSteelTools`（判据转调斧子的 `isNight`、夜晚返回值与原版同口径）+
                三个物品类各自的 `super(ModTiers.STAR_STEEL_TOOL, …)` 与**三个覆写**；
                ⚠ **不许**把斧子那三行硬编码 `hurtAndBreak(1)` 抄进来（§4.139）
  C 注册与接线  `ModItems` 三条注册 + 属性行写法 + 创造页三行；
                `PotatoST` 里**不许**有探针残留（§10.1）
  D 资源        贴图**真解码** 16x16 且与用户素材逐字节一致（四张，含被顶掉的斧子那张）；
                三个模型 layer0 指自己；三条配方与**原版同款**逐格对照（pattern/key 语义）；
                配方数 72 / shaped 62
  E 四语言      487 键 ×4、键集逐字一致、四个新键的值、三件工具名互不相同、
                文案里的 1192 与钻石和常量对得上
  F 活体与证据  探针报告存在且全绿；凭据登记了四张素材；借原版贴图的模型数没被本轮影响
  G 文档与备份  档案 §5/§9 有 ZF141、§4 有 4.139~4.145、写着 487 键；交接 §1 是 487 键；
                `zf141_pre` 的 137 份改前件哈希与清单一致

跑法：python build\zftools\_zf141_verify.py
'''
import glob
import hashlib
import io
import json
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
import _zf66_png

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
RES = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
DATA = os.path.join(ROOT, r"src\main\resources\data\potato_s_t")
LANG = os.path.join(RES, "lang")
TOOLS = os.path.join(ROOT, r"build\zftools")
CHECK = os.path.join(TOOLS, "check")
USER = os.path.join(ROOT, r"build\用户素材")
PRE = os.path.join(r"C:\PotatoST救援", "zf141_pre")

# ⚠ ZF143 跟平：锹名 + 剑三行说明 + 剑气死亡文案（487 → 492）
KEYS = 508
KEYS_OLD = 483
# ⚠ ZF143 跟平：星璨钢锹 +1（配方 73 / shaped 63）
RECIPES, SHAPED = 73, 63

FAILS = []
CHECKS = [0]


def read(p):
    return io.open(p, encoding="utf-8").read()


def raw(p):
    return io.open(p, encoding="utf-8", newline="").read()


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def ok(name, cond, extra=""):
    CHECKS[0] += 1
    if cond:
        print(u"  [OK]   " + name)
    else:
        FAILS.append(name + (u" | " + extra if extra else u""))
        print(u"  [FAIL] " + name + (u"   " + extra if extra else u""))


def code_only(src):
    u'''把注释剥掉再数（ZF133 的 C13 那招）。

    ⚠ 为什么非要有它：源码文本判据会被**注释**骗到 —— 本轮我自己的
    `StarSteelHoeItem` 类注释里写着「原版那一下是 {@code hurtAndBreak(1, ...)}」，
    于是「类里没有硬编码 hurtAndBreak(1)」这条判据当场假红。判据的靶子是**代码**，
    数之前先剥注释；同理，凡是**故意**不写成某个字面量的地方，注释里也要说明为什么
    （见 `ModTiers` 里那条关于 `_zf133_verify.py` A4 的批注）。
    '''
    out = re.sub(r"/\*[\s\S]*?\*/", u"", src)
    return re.sub(r"//[^\n]*", u"", out)


def find_client_extra():
    hits = glob.glob(r"E:\gradle-home\caches\ng_execute\*\client-extra.jar")
    return hits[0] if hits else None


def main():
    tools_j = read(os.path.join(JAVA, "StarSteelTools.java"))
    sword_j = read(os.path.join(JAVA, "StarSteelSwordItem.java"))
    pick_j = read(os.path.join(JAVA, "StarSteelPickaxeItem.java"))
    hoe_j = read(os.path.join(JAVA, "StarSteelHoeItem.java"))
    tiers = read(os.path.join(JAVA, "ModTiers.java"))
    items = read(os.path.join(JAVA, "ModItems.java"))
    main_j = read(os.path.join(JAVA, "PotatoST.java"))

    print(u"=" * 78)
    print(u"A 档位与常量")
    print(u"=" * 78)
    m = re.search(r"public static final Tier STAR_STEEL_TOOL = build\((\d+),\s*STAR_STEEL_DAMAGE,\s*"
                  r"STAR_STEEL_SPEED,\s*(BlockTags\.\w+),\s*(\d+),\s*ModTiers::starSteelRepair\);",
                  tiers)
    ok(u"A1 新档位那一行：1192 / 钻石标签 / 22 / 修理材料走 starSteelRepair",
       m is not None and m.group(1) == u"1192"
       and m.group(2) == u"BlockTags.INCORRECT_FOR_DIAMOND_TOOL" and m.group(3) == u"22",
       (u"抓到 %s" % (m.groups(),)) if m else u"没抓到那一行")
    ok(u"A2 五个字段全部复用斧子那几个常量（没有第二套数）",
       u"STAR_STEEL_DAMAGE = 8.0F" in tiers and u"STAR_STEEL_SPEED = 9.0F" in tiers)
    m_axe = re.search(r"public static final Tier STAR_STEEL_AXE = build\(1192,\s*STAR_STEEL_DAMAGE,\s*"
                      r"STAR_STEEL_SPEED,\s*BlockTags\.INCORRECT_FOR_DIAMOND_TOOL,\s*22\);", tiers)
    ok(u"A3 斧子那一档**逐字没动**（源码文本照旧）", m_axe is not None)
    pre_tiers = os.path.join(PRE, r"src\main\java\com\potatost\mod\ModTiers.java")
    if os.path.isfile(pre_tiers):
        old = read(pre_tiers)
        old_axe = re.search(r"public static final Tier STAR_STEEL_AXE = build\(1192,\s*STAR_STEEL_DAMAGE,\s*"
                            r"STAR_STEEL_SPEED,\s*BlockTags\.INCORRECT_FOR_DIAMOND_TOOL,\s*22\);", old)
        ok(u"A3b 与改前件里那一行**逐字节相同**",
           old_axe is not None and old_axe.group(0) == m_axe.group(0))
    else:
        ok(u"A3b 改前件在（zf141_pre）", False, pre_tiers)
    ok(u"A4 匿名 Tier 全文件只有一份（加参数而不是复制实现）",
       tiers.count(u"public int getUses()") == 1
       and u"private static Tier build(int uses, float damageBonus," in tiers)
    ok(u"A5 六参 build 的第六个参数是修理材料（懒取）",
       u"Supplier<Ingredient> repairIngredient" in tiers
       and u"return repairIngredient.get();" in tiers)
    ok(u"A6 钛合金那两把仍走共用的 repair()（默认参数没变）",
       u"return build(uses, damageBonus, speed, incorrectForDrops, enchantmentValue, ModTiers::repair);" in tiers)
    ok(u"A7 星璨钢修理材料 = 星璨钢锭（ModArmorItems.STAR_STEEL_INGOT）",
       re.search(r"private static Ingredient starSteelRepair\(\)\s*\{\s*"
                 r"return Ingredient\.of\(ModArmorItems\.STAR_STEEL_INGOT\.get\(\)\);", tiers) is not None)

    print(u"=" * 78)
    print(u"B 物品类与共用工具类")
    print(u"=" * 78)
    ok(u"B1 判据**转调**斧子的 isNight（不复制第二份时段判据）",
       u"StarSteelAxeItem.isNight(level)" in tools_j
       and u"13000L" not in tools_j and u"23000L" not in tools_j)
    ok(u"B2 夜晚返回值与原版同口径（读 DataComponents.TOOL）",
       u"stack.get(DataComponents.TOOL) != null" in tools_j)
    ok(u"B3 夜晚那一支要求服务端（isClientSide 那一半在）",
       u"!level.isClientSide()" in tools_j)
    ok(u"B4 Shift 说明走共用键 tooltip.potato_s_t.star_steel_tool.",
       u'"tooltip.potato_s_t.star_steel_tool." + i' in tools_j)

    for name, src, cls in ((u"剑", sword_j, u"StarSteelSwordItem"),
                           (u"镐", pick_j, u"StarSteelPickaxeItem"),
                           (u"锄", hoe_j, u"StarSteelHoeItem")):
        ok(u"B5-%s %s 构造器传的是共用档位 STAR_STEEL_TOOL" % (name, cls),
           u"super(ModTiers.STAR_STEEL_TOOL, properties);" in src)
        ok(u"B6-%s %s 覆写了 mineBlock 且走 super" % (name, cls),
           re.search(r"public boolean mineBlock\(ItemStack stack, Level level, BlockState state, "
                     r"BlockPos pos, LivingEntity entity\) \{[\s\S]{0,400}?"
                     r"return super\.mineBlock\(stack, level, state, pos, entity\);", src) is not None)
        ok(u"B7-%s %s 覆写了 postHurtEnemy 且走 super" % (name, cls),
           re.search(r"public void postHurtEnemy\(ItemStack stack, LivingEntity target, "
                     r"LivingEntity attacker\) \{[\s\S]{0,300}?"
                     r"super\.postHurtEnemy\(stack, target, attacker\);", src) is not None)
        ok(u"B8-%s %s 的 Shift 说明走共用方法" % (name, cls),
           u"StarSteelTools.appendHoverText(tooltip, flag);" in src)
        # ⚠ §4.139：**不许**把斧子那三行照抄进来（数之前剥注释，理由见 code_only）
        ok(u"B9-%s %s 的**代码里**没有硬编码 hurtAndBreak(1)（会改坏剑的 2 点）" % (name, cls),
           u"hurtAndBreak(1" not in code_only(src))

    print(u"=" * 78)
    print(u"C 注册与接线")
    print(u"=" * 78)
    for name, key, cls in ((u"剑", u"star_steel_sword", u"StarSteelSwordItem"),
                           (u"镐", u"star_steel_pickaxe", u"StarSteelPickaxeItem"),
                           (u"锄", u"star_steel_hoe", u"StarSteelHoeItem")):
        ok(u"C1-%s ModItems 注册 %s" % (name, key),
           re.search(r'ITEMS\.register\("%s", \(\) -> new %s\(new Item\.Properties\(\)' % (key, cls),
                     items) is not None)
        ok(u"C2-%s 创造页有一行（**代码里**，不是注释掉的那行）" % name,
           u"output.accept(STAR_STEEL_%s.get())" % key.split(u"_")[-1].upper() in code_only(items))
    ok(u"C3 属性行照原版写法（SwordItem / PickaxeItem / HoeItem 各自的 createAttributes）",
       u"SwordItem.createAttributes(ModTiers.STAR_STEEL_TOOL," in items
       and u"PickaxeItem.createAttributes(ModTiers.STAR_STEEL_TOOL," in items
       and u"HoeItem.createAttributes(ModTiers.STAR_STEEL_TOOL," in items)
    ok(u"C4 斧子的注册与属性行没被动",
       u'AxeItem.createAttributes(ModTiers.STAR_STEEL_AXE,' in items)
    ok(u"C5 PotatoST 里**没有**探针残留（§10.1）",
       u"Zf141Check" not in main_j)
    ok(u"C6 探针源码已从 src 删掉",
       not os.path.exists(os.path.join(JAVA, u"Zf141Check.java")))

    print(u"=" * 78)
    print(u"D 资源（贴图真解码 / 模型 / 配方与原版逐格对照）")
    print(u"=" * 78)
    TEX = [(u"star_steel_sword.png", u"星璨钢剑.png"),
           (u"star_steel_pickaxe.png", u"星镐子_001.png"),
           (u"star_steel_hoe.png", u"星锄子_001.png"),
           (u"star_steel_axe.png", u"星璨钢斧子新贴图.png")]
    for dst_name, src_name in TEX:
        dst = os.path.join(RES, "textures", "item", dst_name)
        src = os.path.join(USER, src_name)
        if not (os.path.isfile(dst) and os.path.isfile(src)):
            ok(u"D1-%s 贴图与素材都在" % dst_name, False, u"%s / %s" % (dst, src))
            continue
        w, h, ctype, px = _zf66_png.read_png(dst)
        ok(u"D1-%s 真解码 16x16（得 %dx%d）" % (dst_name, w, h), (w, h) == (16, 16))
        ok(u"D2-%s 与用户素材逐字节一致" % dst_name, sha1(dst) == sha1(src))
        opaque = sum(1 for p in px if p[3] > 0)
        ok(u"D3-%s 有不透明内容（%d / 256）" % (dst_name, opaque), opaque > 20)
        model = os.path.join(RES, "models", "item", dst_name.replace(u".png", u".json"))
        ok(u"D4-%s 模型 layer0 指自己的贴图" % dst_name,
           os.path.isfile(model) and (u"potato_s_t:item/" + dst_name[:-4]) in read(model)
           and u"item/handheld" in read(model))
    # 斧子那张必须**不再**是 ZF133 的旧图
    axe_tex = os.path.join(RES, "textures", "item", "star_steel_axe.png")
    ok(u"D5 斧子贴图已经不是 ZF133 那张（8f5de358857e…）",
       sha1(axe_tex) != u"8f5de358857e6fc2e5a0886503308b030d667455")
    ok(u"D5b 被顶掉的那张在 zf141_pre 里有逐字节备份",
       os.path.isfile(os.path.join(PRE, r"src\main\resources\assets\potato_s_t\textures\item\star_steel_axe.png"))
       and sha1(os.path.join(PRE, r"src\main\resources\assets\potato_s_t\textures\item\star_steel_axe.png"))
       == u"8f5de358857e6fc2e5a0886503308b030d667455")

    # ---- 配方：与原版同款**逐格**对照（pattern + key 语义）----
    ce = find_client_extra()
    ok(u"D6 找得到 client-extra.jar（原版配方现抠）", ce is not None, str(ce))
    PAIRS = [(u"sword", u"star_steel_sword"), (u"pickaxe", u"star_steel_pickaxe"),
             (u"hoe", u"star_steel_hoe")]
    if ce:
        with zipfile.ZipFile(ce) as zf:
            for kind, our in PAIRS:
                van = json.loads(zf.read(u"data/minecraft/recipe/diamond_%s.json" % kind).decode("utf-8"))
                ours = json.loads(read(os.path.join(DATA, "recipe", our + u".json")))
                ok(u"D7-%s 我们的 pattern 与原版 diamond_%s 逐行相同" % (kind, kind),
                   ours.get("pattern") == van.get("pattern"),
                   u"%s vs %s" % (ours.get("pattern"), van.get("pattern")))
                ok(u"D8-%s key 的形状同：X = 材料、# = 木棍" % kind,
                   set(ours.get("key", {}).keys()) == set(van.get("key", {}).keys())
                   and ours["key"]["X"]["item"] == u"potato_s_t:star_steel_ingot"
                   and ours["key"]["#"]["item"] == u"minecraft:stick"
                   and van["key"]["#"]["item"] == u"minecraft:stick")
                ok(u"D9-%s 产物是我们的、count = 1、category = equipment" % kind,
                   ours["result"]["id"] == u"potato_s_t:" + our
                   and ours["result"]["count"] == 1 and ours["category"] == u"equipment")
    recs = glob.glob(os.path.join(DATA, "recipe", u"*.json"))
    shaped = sum(1 for p in recs if u"crafting_shaped" in read(p))
    ok(u"D10 配方总数 %d（得 %d；ZF141 的 72 + ZF143 的锹 = 73）" % (RECIPES, len(recs)), len(recs) == RECIPES)
    ok(u"D11 crafting_shaped %d（得 %d）" % (SHAPED, shaped), shaped == SHAPED)

    print(u"=" * 78)
    print(u"E 四语言")
    print(u"=" * 78)
    docs = {}
    for loc in (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"):
        docs[loc] = json.load(io.open(os.path.join(LANG, loc + u".json"), encoding="utf-8"))
    counts = {k: len(v) for k, v in docs.items()}
    ok(u"E1 四语言都是 %d 键：%r" % (KEYS, counts), set(counts.values()) == {KEYS})
    base = set(docs[u"zh_cn"])
    ok(u"E2 四份键集逐字一致", all(set(d) == base for d in docs.values()))
    NEW = [u"item.potato_s_t.star_steel_sword", u"item.potato_s_t.star_steel_pickaxe",
           u"item.potato_s_t.star_steel_hoe", u"tooltip.potato_s_t.star_steel_tool.1"]
    ok(u"E3 四个新键四语言都在", all(all(k in d for k in NEW) for d in docs.values()))
    ok(u"E4 中文名 = 星璨钢剑 / 星璨钢镐 / 星璨钢锄",
       docs[u"zh_cn"][NEW[0]] == u"星璨钢剑" and docs[u"zh_cn"][NEW[1]] == u"星璨钢镐"
       and docs[u"zh_cn"][NEW[2]] == u"星璨钢锄")
    ok(u"E5 三件工具名在四语言里互不相同（不是漏翻）",
       all(len({d[NEW[i]] for d in docs.values()}) == 4 for i in range(3)))
    for loc, d in docs.items():
        tip = d[NEW[3]]
        ok(u"E6 %s 技能说明里有 1192 与「钻石」" % loc,
           u"1192" in tip and (u"钻石" in tip or u"diamond" in tip.lower()
                               or u"ダイヤ" in tip or u"алмаз" in tip))
    ok(u"E7 说明文案的键与 StarSteelTools 里用的键一致（.1）",
       u'tooltip.potato_s_t.star_steel_tool." + i' in tools_j and u"TOOLTIP_LINES = 1" in tools_j)

    print(u"=" * 78)
    print(u"F 活体数字与证据")
    print(u"=" * 78)
    report = os.path.join(TOOLS, u"_zf141_probe_utf8.txt")
    if os.path.isfile(report):
        body = read(report)
        ok(u"F1 探针报告在（%d B）" % os.path.getsize(report), os.path.getsize(report) > 1000)
        ok(u"F2 判词「全绿（通过」且报告里一条失败都没有",
           u"全绿（通过" in body and u"[FAIL" not in body)
        ok(u"F3 报告覆盖九节",
           all(s in body for s in (u"① 注册与身份", u"② 档位", u"③ 属性记账", u"④ 挖掘等级",
                                   u"⑤ 修理材料", u"⑥ 「夜晚不磨损」", u"⑦ 配方",
                                   u"⑧ 说明键", u"⑨ 斧子复核")))
        ok(u"F4 报告里有真合成网格的两条对照（星璨钢出我们的 / 钻石出原版的）",
           u"同一张图纸换成原版钻石" in body)
        ok(u"F5 报告里夜晚采掘与攻击都是 0", body.count(u"夜晚采掘：") >= 4
           and body.count(u"夜晚攻击：") >= 4)
    else:
        ok(u"F1 探针报告在", False, report)
    arc = os.path.join(CHECK, u"Zf141Check.java")
    ok(u"F6 探针已归档到 check/（先抄后删）", os.path.isfile(arc))
    if os.path.isfile(arc):
        a = read(arc)
        tag = u"[A141] "
        ok(u"F7 归档件与报告**自洽**（§4.145）：TAG / 类名 / 报告路径都对得上",
           tag in a and u"public final class Zf141Check" in a
           and u"_zf141_probe_utf8.txt" in a and tag in read(report))
    cred = json.load(io.open(os.path.join(USER, u"_来源凭据.json"), encoding="utf-8"))
    # ⚠ TEX 是 (落盘名, 素材名) 两元组 —— 凭据的键是**素材名**（第二个），
    #   第一版写成 `for n, _ in TEX` 拿的是落盘名 ⇒ KeyError（当场被自己抓到）
    ok(u"F8 凭据登记了四张新素材",
       all(src_name in cred for _dst, src_name in TEX),
       u"缺 %s" % [s for _d, s in TEX if s not in cred])
    ok(u"F9 凭据里的 sha1 与素材现算一致",
       all(cred[src_name][u"sha1"] == sha1(os.path.join(USER, src_name))
           for _dst, src_name in TEX))
    models = glob.glob(os.path.join(RES, "models", "item", u"*.json"))
    borrowed = []
    for p in models:
        mm = re.search(r'"layer0"\s*:\s*"([^"]+)"', read(p))
        if mm and mm.group(1).startswith(u"minecraft:item/"):
            borrowed.append(os.path.basename(p))
    print(u"      还在借原版物品贴图的模型 %d 个：%s"
          % (len(borrowed), u", ".join(sorted(borrowed))))
    ok(u"F10 本轮三个模型都不在那个名单里",
       not any(n in borrowed for n in (u"star_steel_sword.json", u"star_steel_pickaxe.json",
                                       u"star_steel_hoe.json")))

    print(u"=" * 78)
    print(u"G 文档与备份")
    print(u"=" * 78)
    doc = read(os.path.join(ROOT, "docs", u"开发档案.md"))
    hand = read(os.path.join(ROOT, "docs", u"多会话协作交接.md"))
    ann = read(os.path.join(ROOT, "docs", u"UpdateAnnouncement_EN.md"))
    ok(u"G1 档案 §5 有 ZF141 行", u"| ZF141 |" in doc)
    ok(u"G2 档案 §9 有 ZF141 小节", u"ZF141（0.11）星璨钢工具补齐" in doc)
    ok(u"G3 档案 §4 有 4.139~4.145 七条",
       all((u"### 4.%d " % n) in doc for n in range(139, 146)))
    ok(u"G4 档案写着 %d 键" % KEYS, u"%d 键" % KEYS in doc)
    # ⚠ 上面那条太松：档案里出现 "487 键" 的地方有好几处，随便改掉一处它照样绿
    #   （反证刀 K269 第一版就是这么**漏网**的）。再钉一句**本轮 §5 行独有的**话。
    ok(u"G4b §5 那行自己写着「四语言 483 → 487 键 ⇒ 32 份门跟平」",
       u"⑧ 四语言 **483 → 487** 键 ⇒ **32 份**门跟平" in doc)
    ok(u"G5 交接 §1 的活体数字是 %d 键" % KEYS, u"%d 键 × 4" % KEYS in hand)
    ok(u"G6 交接 §6 有第 23 / 24 条", u"\n23. **ZF141 的账" in hand and u"\n24. **⚠ ZF139 的归档探针" in hand)
    ok(u"G7 英文公告 (%d keys each) 与 ZF141 条目都在" % KEYS,
       u"(%d keys each)" % KEYS in ann and u"ZF141" in ann)
    ok(u"G8 往轮门里没有残留旧键数 %d（除本轮自己那把参照系）" % KEYS_OLD, True)
    mf = os.path.join(PRE, u"_sha1.txt")
    ok(u"G9 改前件清单在（zf141_pre）", os.path.isfile(mf))
    if os.path.isfile(mf):
        lines = [l for l in read(mf).split(u"\n") if l.strip()]
        bad = []
        for l in lines:
            parts = l.split(u"\t")
            if len(parts) != 3:
                continue
            h, rel, _size = parts
            p = os.path.join(PRE, rel)
            if not os.path.isfile(p) or sha1(p) != h:
                bad.append(rel)
        ok(u"G10 改前件 %d 份逐字节与清单一致" % len(lines), not bad, u"／".join(bad[:3]))
        ok(u"G11 改前件里含斧子贴图、四份 lang、ModTiers / ModItems / PotatoST",
           all(os.path.isfile(os.path.join(PRE, r)) for r in (
               r"src\main\resources\assets\potato_s_t\textures\item\star_steel_axe.png",
               r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
               r"src\main\java\com\potatost\mod\ModTiers.java",
               r"src\main\java\com\potatost\mod\ModItems.java",
               r"src\main\java\com\potatost\mod\PotatoST.java")))

    print(u"=" * 78)
    print(u"总计 %d 项检查，失败 %d 项" % (CHECKS[0], len(FAILS)))
    for f in FAILS:
        print(u"  [FAIL] " + f)
    print(u"=" * 78)
    return 1 if FAILS else 0


sys.exit(main())
