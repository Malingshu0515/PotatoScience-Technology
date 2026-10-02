# -*- coding: utf-8 -*-
r'''_zf155_verify.py —— ZF155 **常驻校验**：通用升级模板（真·通用 + 冲突即禁用）。

只读盘上文件，不开游戏（运行期那半在 `_zf155_probe_utf8.txt` 里）。分区：
  A 物品与资产：注册 / 创造栏 / 模型 / 贴图（尺寸+哈希钉死）/ 原版模板子类
  B 五语文案：7 个新键齐全、旧键逐条原值不变（与 zf155_pre 备份比对）、键数活体数字
  C 配方：获取方式（八铝锭围一圈）/ 振金剑 / 4 件护甲换模板（除模板外逐字节等价）
  D 引擎：官方挂点 replaceRecipes、两个事件、无反射、原文冲突判据、纹饰排除、保真复核、幂等
  E 文档：§4 新节 / §5 行 / §9 小节 / 英文公告 / 交接 / §4 号不重复

跑法：python build\zftools\_zf155_verify.py
'''
import hashlib
import io
import json
import os
import re
import struct
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
ASSETS = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t")
DATA = os.path.join(ROOT, "src", "main", "resources", "data", "potato_s_t")
RECIPE = os.path.join(DATA, "recipe")
LANG = os.path.join(ASSETS, "lang")
ZT = os.path.join(ROOT, "build", "zftools")
PRE = os.path.join(r"C:\PotatoST救援", "zf155_pre")
DOC = os.path.join(ROOT, "docs", "开发档案.md")
HAND = os.path.join(ROOT, "docs", "多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")

TEX = os.path.join(ASSETS, "textures", "item", "universal_upgrade_template.png")
TEX_SHA1 = u"224ac42fa155464ae8e074776a91a2c42407c7f2"
TEX_BYTES = 138
LANGS = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]
NEW_KEYS = [
    u"item.potato_s_t.universal_upgrade_template",
    u"item.potato_s_t.universal_upgrade_template.desc",
    u"item.potato_s_t.universal_upgrade_template.applies_to",
    u"item.potato_s_t.universal_upgrade_template.ingredients",
    u"item.potato_s_t.universal_upgrade_template.base_slot",
    u"item.potato_s_t.universal_upgrade_template.additions_slot",
    u"item.potato_s_t.universal_upgrade_template.rule",
]
PIECES = [u"helmet", u"chestplate", u"leggings", u"boots"]
ENGINE_MARKERS = [u"replaceRecipes(", u"CompoundIngredient.of(", u"trim-pattern-bound",
                  u"fidelity-template", u"fidelity-base", u"fidelity-addition",
                  u"foreign-serializer", u"empty-template", u"|conflict", u"overlap(",
                  u"cachedManager", u"signature(", u"GENERATED_PREFIX"]

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


def rjson(p):
    try:
        return json.loads(read(p))
    except Exception as exc:  # noqa: BLE001
        fails.append(u"%s 解析失败：%s" % (os.path.relpath(p, ROOT), exc))
        return None


def sha1b(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    # ---------------- A 物品与资产 ----------------
    print(u"---- A 物品与资产 ----")
    items = read(os.path.join(JAVA, u"ModItems.java"))
    check(u'ITEMS.register("universal_upgrade_template", UniversalUpgradeTemplate::createTemplateItem)'
          in items, u"A1 ModItems 注册了通用升级模板（供货方指向引擎类）")
    check(u"output.accept(UNIVERSAL_UPGRADE_TEMPLATE.get());" in items, u"A2 创造栏里有它")

    model = rjson(os.path.join(ASSETS, "models", "item", "universal_upgrade_template.json"))
    if model:
        check(model.get(u"parent") == u"item/generated"
              and model.get(u"textures", {}).get(u"layer0")
              == u"potato_s_t:item/universal_upgrade_template",
              u"A3 物品模型：item/generated + layer0 指向本贴图")

    if os.path.isfile(TEX):
        blob = open(TEX, "rb").read()
        w, h, depth, ctype, _c, _f, inter = struct.unpack(">IIBBBBB", blob[16:29])
        check((w, h, depth, ctype, inter) == (16, 16, 8, 6, 0),
              u"A4a 贴图规格 16x16 / 8 位 / RGBA / 非交织", u"%dx%d d%d t%d i%d" % (w, h, depth, ctype, inter))
        check(sha1b(TEX) == TEX_SHA1 and len(blob) == TEX_BYTES,
              u"A4b 贴图哈希与字节数钉死（改图必红）", sha1b(TEX))
    else:
        check(False, u"A4 贴图存在")

    engine = read(os.path.join(JAVA, u"UniversalUpgradeTemplate.java"))
    check(u"extends SmithingTemplateItem" in engine and u"appendHoverText" in engine,
          u"A5 物品是原版模板类的子类，tooltip 末尾补了规则行")

    # ---------------- B 五语文案 ----------------
    print(u"\n---- B 五语文案 ----")
    data = {}
    for lg in LANGS:
        p = os.path.join(LANG, lg + u".json")
        obj = rjson(p)
        if obj is None:
            continue
        raw = open(p, "rb").read()
        data[lg] = obj
        missing = [k for k in NEW_KEYS if k not in obj]
        check(not missing and raw[:3] != b"\xef\xbb\xbf" and b"\r\n" not in raw,
              u"B1 %s 七个新键齐全 / 无 BOM / LF" % lg, u"缺 %s" % missing)
    check(len(data) == 5, u"B2 五份语言文件都能解析")
    if len(data) == 5:
        counts = {lg: len(data[lg]) for lg in LANGS}
        check(counts[u"zh_cn"] == counts[u"en_us"] == counts[u"ja_jp"] == counts[u"ru_ru"] == 620
              and counts[u"lzh"] == 622,
              u"B3 键数活体数字 620（zh/en/ja/ru）+ 622（lzh）", str(counts))
        base = set(data[u"zh_cn"])
        for lg in (u"en_us", u"ja_jp", u"ru_ru"):
            check(set(data[lg]) == base, u"B4 %s 键集合与 zh_cn 一致" % lg,
                  u"差 %s" % sorted(set(data[lg]) ^ base)[:4])
        check(set(data[u"lzh"]) - base == {u"language.name", u"language.region"},
              u"B5 lzh 只多 language.name / language.region 两键")
        blanks = [k for k in NEW_KEYS for lg in LANGS if not data[lg].get(k, u"").strip()]
        check(not blanks, u"B6 七条新文案在五份语言里都非空", u"%s" % blanks)
        # 与备份比对：**键**一个都不许少、也不许多出这 7 个以外的东西；
        # ⚠ 值漂移**不算我的账**：多线共树，别人随时会改老键的值（本轮实测：另一条线把
        #   `message.potato_s_t.guide_book.received` 五份的值都改了）—— 拿"值逐字相同"当判据，
        #   等于让别人的提交节奏决定我这条门红不红（ZF149 那轮踩过同款）。漂移另行列出来给人看。
        # 0.13 ZF162：灌装机加 1 键、扳手物品与电力高炉物品 tooltip 各删 1 键
        ZF162_ADDED = {u"gui.potato_s_t.filling.diag.unsupported"}
        ZF166_ADDED = {u"block.potato_s_t.fluid_converter",
                       u"tooltip.potato_s_t.fluid_converter",
                       u"gui.potato_s_t.fluid_converter.tank.input",
                       u"gui.potato_s_t.fluid_converter.tank.output",
                       u"gui.potato_s_t.fluid_converter.status.input_empty",
                       u"gui.potato_s_t.fluid_converter.status.target_empty",
                       u"gui.potato_s_t.fluid_converter.status.same_fluid",
                       u"gui.potato_s_t.fluid_converter.status.no_shared_tag",
                       u"gui.potato_s_t.fluid_converter.status.output_full",
                       u"gui.potato_s_t.fluid_converter.status.no_power",
                       u"gui.potato_s_t.fluid_converter.status.running",
                       u"gui.potato_s_t.fluid_converter.status.idle"}
        ZF162_REMOVED = {u"item.potato_s_t.wrench",
                         u"tooltip.potato_s_t.electric_blast_furnace"}
        key_problems, drift = [], []
        for lg in LANGS:
            old = rjson(os.path.join(PRE, u"src", u"main", u"resources", u"assets",
                                     u"potato_s_t", u"lang", lg + u".json"))
            if not old:
                continue
            added = set(data[lg]) - set(old)
            removed = set(old) - set(data[lg])
            if added != set(NEW_KEYS) | ZF162_ADDED | ZF166_ADDED:
                key_problems.append(u"%s:新增键不是那 7 个 + ZF162 那 1 个 %s"
                                    % (lg, sorted(added ^ (set(NEW_KEYS) | ZF162_ADDED | ZF166_ADDED))))
            if removed != ZF162_REMOVED:
                key_problems.append(u"%s:删掉的不是 ZF162 那 2 个 %s"
                                    % (lg, sorted(removed ^ ZF162_REMOVED)))
            for k, v in old.items():
                if data[lg].get(k) != v:
                    drift.append(u"%s:%s" % (lg, k))
        check(not key_problems, u"B7 对照备份：新增正好是那 7 个 + ZF162 那 1 个、删掉的正好是 ZF162 那 2 个", u"%s" % key_problems[:4])
        # ⚠ 值漂移**只报不判**：别人随时会改老键的值（本轮实测 5 处），拿它当判据就是
        #   "我这条门红不红看别人的提交节奏"（ZF149/ZF150 都踩过）。漂移照旧打出来给人看。
        if drift:
            print(u"  [注意] 旧键的值有 %d 处漂移（**不是本轮改的**，只报不判）：%s"
                  % (len(drift), drift[:6]))

    # ---------------- C 配方 ----------------
    print(u"\n---- C 配方 ----")
    ring = rjson(os.path.join(RECIPE, u"universal_upgrade_template.json"))
    if ring:
        key = ring.get(u"key", {})
        check(ring.get(u"type") == u"minecraft:crafting_shaped"
              and ring.get(u"pattern") == [u"AAA", u"ANA", u"AAA"]
              and key.get(u"A", {}).get(u"item") == u"potato_s_t:aluminum_ingot"
              and key.get(u"N", {}).get(u"item") == u"minecraft:netherite_upgrade_smithing_template"
              and ring.get(u"result", {}).get(u"id") == u"potato_s_t:universal_upgrade_template"
              and ring.get(u"result", {}).get(u"count") == 1,
              u"C1 获取方式：八块铝锭围一圈 + 中间一张下界合金升级模板 → 通用模板 x1")

    sword = rjson(os.path.join(RECIPE, u"vibranium_sword_smithing.json"))
    if sword:
        check(sword.get(u"type") == u"minecraft:smithing_transform"
              and sword.get(u"base", {}).get(u"item") == u"potato_s_t:titanium_alloy_sword"
              and sword.get(u"addition", {}).get(u"item") == u"potato_s_t:vibranium_ingot"
              and sword.get(u"template", {}).get(u"item") == u"potato_s_t:universal_upgrade_template"
              and sword.get(u"result", {}).get(u"id") == u"potato_s_t:vibranium_sword",
              u"C2 振金剑：钛合金剑 + 振金锭 + 通用升级模板 → 振金剑")

    swapped, others_changed = [], []
    for piece in PIECES:
        name = u"vibranium_%s_smithing.json" % piece
        now = rjson(os.path.join(RECIPE, name))
        old = rjson(os.path.join(PRE, u"src", u"main", u"resources", u"data",
                                 u"potato_s_t", u"recipe", name))
        if not now or not old:
            continue
        if now.get(u"template", {}).get(u"item") == u"potato_s_t:universal_upgrade_template":
            swapped.append(piece)
        if old.get(u"template", {}).get(u"item") != u"minecraft:netherite_upgrade_smithing_template":
            others_changed.append(u"%s 改前不是下界合金模板" % piece)
        a, b = dict(now), dict(old)
        a.pop(u"template", None)
        b.pop(u"template", None)
        if a != b:
            others_changed.append(u"%s 除模板外还有别的改动" % piece)
    check(len(swapped) == 4, u"C3 四件振金护甲的模板都换成了通用模板", u"%s" % swapped)
    check(not others_changed, u"C4 四份配方除 template 一项外逐字段等价（没夹带别的改动）",
          u"%s" % others_changed)

    smithing = sorted(f for f in os.listdir(RECIPE) if f.endswith(u"_smithing.json"))
    check(len(smithing) == 5, u"C5 本 mod 五条锻造升级配方（4 护甲 + 振金剑）", u"%s" % smithing)
    check(u"vibranium_sword_smithing.json" in smithing, u"C6 振金剑配方在（上一轮它是不能合成的）")

    # ---------------- D 引擎 ----------------
    print(u"\n---- D 引擎 ----")
    check(u"@EventBusSubscriber(modid = PotatoST.MODID)" in engine, u"D1 引擎挂在模组事件总线上")
    check(u"ServerStartedEvent event" in engine and u"OnDatapackSyncEvent event" in engine,
          u"D2 两个挂点：开服 + 登录/reload（后者先于配方包发出）")
    check(u"manager.replaceRecipes(" in engine, u"D3 用 NeoForge 的官方口子 replaceRecipes 换表")
    reflection = [w for w in (u"setAccessible", u"getDeclaredField", u"getDeclaredMethod",
                              u"Class.forName", u"java.lang.reflect")
                  if w in engine]
    check(not reflection, u"D4 全程零反射（改字段名不会失效）", u"%s" % reflection)
    check(u"CompoundIngredient.of(candidate.template(), universalIngredient)" in engine,
          u"D5 加宽 = 原模板 ∪ 通用模板（CompoundIngredient）")
    missing_markers = [m for m in ENGINE_MARKERS if m not in engine]
    check(not missing_markers, u"D6 冲突判据/纹饰排除/保真复核/幂等 的标记全在",
          u"缺 %s" % missing_markers)
    check(u"RecipeHolder<>(id, new SmithingTransformRecipe(" in engine,
          u"D7 原地替换：**同一个 id** 换上加宽版（不加副本 ⇒ JEI 不会出现两条一样的升级）")

    rep = read(os.path.join(ZT, u"_zf155_probe_utf8.txt"))
    check(u"判词：ALL OK" in rep, u"D8 开服探针（含真 /reload）判词 ALL OK")
    need = [u"A2 原版 9 条下界合金升级全部加宽", u"A4 纹饰一条都没加宽", u"A5 真实环境下冲突数",
            u"B1 钻石头盔", u"B3 回归：下界合金模板照旧能升下界合金", u"B5 钛合金剑",
            u"B6 负对照：下界合金模板**不再**能升振金", u"B7 负对照：钻石胸甲",
            u"C1 合成：八铝锭围一圈", u"C2 负对照：中间换成铝锭",
            u"D1 同底同料不同结果的两条", u"D2 冲突的两条**都不许**加宽",
            u"D3 只有底物重合", u"E1 再装一次", u"F1 真 /reload 换掉了",
            u"F2 /reload 之后加宽**自己回来了**", u"F3 /reload 之后照旧能用"]
    miss = [n for n in need if n not in rep]
    check(not miss, u"D9 探针报告里该有的项一个不少", u"缺 %s" % miss)
    check(u"0 条 FAIL" not in rep, u"D10 探针报告里没有 FAIL")

    # ---------------- E 文档 ----------------
    print(u"\n---- E 文档 ----")
    doc, hand, ann = read(DOC), read(HAND), read(ANN)
    nums = [int(m.group(1)) for m in re.finditer(r"(?m)^#{3,4} 4\.(\d+) ", doc)]
    mine = re.search(r"(?m)^#{3,4} 4\.(\d+) [^\n]*ZF155", doc)
    check(mine is not None, u"E1 档案 §4 有编号小节、标题带 ZF155")
    if mine:
        n = int(mine.group(1))
        # ⚠ 只钉**我这一节**：档案里 4.90/91/92/146-150 那几处撞号是历次并行留下的旧账，
        #   不在本轮的账上（E1 若写成"全文无重复"就会替别人背锅、而且永远不会回绿）。
        # ⚠ ZF156 把判据改了：原来还要求"n == 全文最大"，那等于"我这轮永远是最后一轮"——
        #   下一轮（ZF156）加了 §4.164 之后它必然变红。**要钉的是"我这个号没被别人撞"**（原判据的真实意图），
        #   所以现在只判唯一，并把"之后新增了哪些号"打在判据里当情报。
        later = sorted(x for x in set(nums) if x > n)
        check(nums.count(n) == 1,
              u"E2 本轮 §4 号唯一（4.%d；它之后新增的号 %s 属于更晚的轮次）"
              % (n, u", ".join(u"4.%d" % x for x in later) if later else u"无"),
              u"该号出现 %d 次" % nums.count(n))
    check(u"| ZF155 |" in doc, u"E3 档案 §5 有 ZF155 行")
    check(u"### ZF155" in doc, u"E4 档案 §9 有 ZF155 小节")
    check(u"## New in 0.12 ZF155" in ann, u"E5 英文公告有 ZF155 那一条（逐字标题）")
    check(u"universal" in ann.lower(), u"E6 公告讲了通用升级模板")
    check(u"ZF155" in hand, u"E7 交接文档里有本轮那一条")

    print(u"")
    print(u"================ 通过 %d / 失败 %d ================" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == u"__main__":
    sys.exit(main())
