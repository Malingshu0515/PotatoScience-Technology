# -*- coding: utf-8 -*-
u"""_zf169_wire.py —— ZF169 接线：两个物品的注册 / 能量能力 / 黑洞每 tick / 配方 / 模型 / 五语言

用户原话（两件）：
  ① 矿物探测器：配方【磁铁】【铁锭】【磁铁】/【铜线轴】【电容】【铜线轴】/【】【木棍】【】；
     能量条黄色 1200 FE；右键识别最近的（xz 3×3 区块、y45 格内）矿物并标注；没找到就提示
     「附近没有任何矿物」；一次 600 FE。
  ② 手持式引力装置：配方【锂电池】【磁铁块】【锂电池】/【星璨钢】【信标】【星璨钢】/
     【稳定金属块】【浅层钻石原矿】【稳定金属块】；储能 8 MFE；副手放方块；长按右键蓄力 25 s
     召唤黑洞（3×3 区块内同种方块全吸过来、上限 1200；也吸生物 + 虚空伤害）；一次耗光 8 MFE 并损坏。

⚠ 配方里「浅层钻石原矿」这个名字**先认盘上的真 id**：本 mod 有没有这件方块，脚本自己查
  （有就用它，没有就退回最近的钻石原矿 id 并在报告与档案里点名，绝不默默替换）。
"""
import glob
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
MOD = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
ITEMS = os.path.join(MOD, "ModItems.java")
MAIN = os.path.join(MOD, "PotatoST.java")
RECIPE = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
MODELS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\item")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
DETECTOR = os.path.join(MOD, "OreDetectorItem.java")

fails, notes = [], []


def check(label, ok, detail=u""):
    print(u"  [%s] %s%s" % (u"OK" if ok else u"!!", label, (u"   " + detail) if detail else u""))
    if not ok:
        fails.append(label)
    return ok


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t)


def find_diamond_ore():
    u"""在盘上找出「浅层钻石原矿」的真 id（用户配方里点名的那件）。"""
    src = read(os.path.join(MOD, "ModBlocks.java"))
    ids = re.findall(u'register\\("([a-z0-9_]*diamond[a-z0-9_]*)"', src)
    ids = sorted(set(ids))
    print(u"      盘上与 diamond 有关的方块 id：%s" % (ids or u"（一个都没有）"))
    for want in (u"shallow_diamond_ore", u"deep_diamond_ore"):
        if want in ids:
            return u"potato_s_t:" + want, ids
    return (u"minecraft:diamond_ore", ids) if not ids else (u"potato_s_t:" + ids[0], ids)


def main():
    print(u"① 配方材料认 id")
    ore, ore_ids = find_diamond_ore()
    if ore != u"potato_s_t:shallow_diamond_ore":
        notes.append(u"配方里的「浅层钻石原矿」用了 %s（盘上没有 shallow_diamond_ore）" % ore)
    need = {u"磁铁": u"potato_s_t:magnet", u"铜线轴": u"potato_s_t:copper_wire_spool",
            u"电容": u"potato_s_t:capacitor", u"锂电池": u"potato_s_t:lithium_battery",
            u"磁铁块": u"potato_s_t:magnet_block", u"星璨钢": u"potato_s_t:star_steel_ingot",
            u"稳定金属块": u"potato_s_t:stable_metal_block", u"铁锭": u"minecraft:iron_ingot",
            u"木棍": u"minecraft:stick", u"信标": u"minecraft:beacon",
            u"浅层钻石原矿": ore}
    allsrc = read(os.path.join(MOD, "ModItems.java")) + read(os.path.join(MOD, "ModBlocks.java"))
    for name, iid in need.items():
        if iid.startswith(u"potato_s_t:"):
            short = iid.split(u":")[1]
            ok = (u'"%s"' % short) in allsrc
            check(u"%s = %s 真的注册了" % (name, iid), ok)
        else:
            print(u"      %s = %s（原版）" % (name, iid))

    print(u"\n② ModItems：注册两件 + 创造页两行")
    t = read(ITEMS)
    block = u"""
    // ========== 0.14 ZF169：矿物探测器 + 手持式引力装置 ==========
    /** 矿物探测器：1200 FE 储能、右键 600 FE 报最近的一处矿物（见 OreDetectorItem）。 */
    public static final DeferredItem<Item> ORE_DETECTOR =
            ITEMS.register("ore_detector", () -> new OreDetectorItem(new Item.Properties()
                    .stacksTo(1)));

    /** 手持式引力装置：8 MFE 储能、蓄力 25 秒放黑洞，一次就坏（见 GravityDeviceItem）。 */
    public static final DeferredItem<Item> GRAVITY_DEVICE =
            ITEMS.register("gravity_device", () -> new GravityDeviceItem(new Item.Properties()
                    .stacksTo(1).durability(32)));
"""
    if u'ITEMS.register("ore_detector"' in t:
        print(u"  [幂等] 两件已注册")
    else:
        anchor = u"    // ========== 创造模式标签页"
        if t.count(anchor) != 1:
            check(u"注册锚点唯一", False, u"%d 次" % t.count(anchor))
        else:
            t = t.replace(anchor, block + u"\n" + anchor, 1)
            check(u"两件物品已注册", True)
    # 创造页
    if u"ORE_DETECTOR.get()" not in t:
        tanchor = u'                        output.accept(ModBlocks.BEVERAGE_CANNING_MACHINE_ITEM.get());'
        if t.count(tanchor) == 1:
            i = t.index(tanchor)
            j = t.index(u"\n", i) + 1
            t = t[:j] + (
                u"                        output.accept(ORE_DETECTOR.get());// ← 新增（0.14 ZF169 矿物探测器）\n"
                u"                        output.accept(GRAVITY_DEVICE.get());// ← 新增（0.14 ZF169 手持式引力装置）\n"
            ) + t[j:]
            check(u"创造页两行已补", True)
        else:
            check(u"创造页锚点唯一", False, u"%d 次" % t.count(tanchor))
    write(ITEMS, t)

    print(u"\n③ PotatoST：两条物品能量能力 + 黑洞每 tick")
    m = read(MAIN)
    if u"GravityDeviceItem.energyStorage" in m:
        print(u"  [幂等] 已在")
    else:
        # 能力注册：接在最后一条事件注册之后（找 registerCapabilities 里最后一行 event.register…）
        cap_anchor = u"        event.registerBlockEntity(\n                Capabilities.FluidHandler.BLOCK,\n                ModBlocks.BEVERAGE_CANNING_MACHINE_BE.get(),\n                (machine, side) -> machine.getFluidHandler());"
        cap_block = (u"\n\n        // 0.14 ZF169：两件物品的储能（物品能量能力 —— 本工程第一次用）\n"
                     u"        event.registerItem(Capabilities.EnergyStorage.ITEM,\n"
                     u"                (stack, ctx) -> OreDetectorItem.energyStorage(stack),\n"
                     u"                ModItems.ORE_DETECTOR.get());\n"
                     u"        event.registerItem(Capabilities.EnergyStorage.ITEM,\n"
                     u"                (stack, ctx) -> GravityDeviceItem.energyStorage(stack),\n"
                     u"                ModItems.GRAVITY_DEVICE.get());")
        n = m.count(cap_anchor)
        check(u"能力注册锚点唯一", n == 1, u"%d 次" % n)
        if n == 1:
            m = m.replace(cap_anchor, cap_anchor + cap_block, 1)
        # 每 tick：接在 ZF153 那个 onPlayerTick 注册之后
        tick_anchor = u"addListener(StarfallRitualManager::onPlayerLogin);"
        n2 = m.count(tick_anchor)
        check(u"tick 挂载锚点唯一", n2 == 1, u"%d 次" % n2)
        if n2 == 1:
            m = m.replace(tick_anchor, tick_anchor +
                          u"\n        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener("
                          u"\n                (net.neoforged.neoforge.event.tick.ServerTickEvent.Post e) -> "
                          u"BlackHoleManager.tick());   // 0.14 ZF169 黑洞", 1)
        write(MAIN, m)
        check(u"两条能力 + 黑洞 tick 已接", u"GravityDeviceItem.energyStorage" in read(MAIN)
              and u"BlackHoleManager.tick()" in read(MAIN))

    print(u"\n④ 两张配方")
    shaped = {
        u"ore_detector.json": ([u"MDM", u"SCS", u" S "],
                               {u"M": u"potato_s_t:magnet", u"D": u"minecraft:iron_ingot",
                                u"S": u"potato_s_t:copper_wire_spool", u"C": u"potato_s_t:capacitor"},
                               u"potato_s_t:ore_detector"),
        u"gravity_device.json": ([u"LML", u"TBT", u"SOS"],
                                 {u"L": u"potato_s_t:lithium_battery", u"M": u"potato_s_t:magnet_block",
                                  u"T": u"potato_s_t:star_steel_ingot", u"B": u"minecraft:beacon",
                                  u"S": u"potato_s_t:stable_metal_block", u"O": ore},
                                 u"potato_s_t:gravity_device"),
    }
    for name, (pattern, key, result) in shaped.items():
        p = os.path.join(RECIPE, name)
        data = {u"type": u"minecraft:crafting_shaped", u"category": u"misc", u"pattern": pattern,
                u"key": {k: {u"item": v} for k, v in key.items()},
                u"result": {u"id": result, u"count": 1}}
        text = json.dumps(data, ensure_ascii=False, indent=2) + u"\n"
        if os.path.exists(p):
            check(u"%s 已在且相同（幂等）" % name, read(p) == text)
        else:
            write(p, text)
            check(u"%s 已写出" % name, os.path.exists(p))

    print(u"\n⑤ 两个物品模型（占位：借原版图，进待画表）")
    for name, parent in ((u"ore_detector.json", u"minecraft:item/compass"),
                         (u"gravity_device.json", u"minecraft:item/ender_eye")):
        p = os.path.join(MODELS, name)
        text = json.dumps({u"parent": u"minecraft:item/generated",
                           u"textures": {u"layer0": parent}}, ensure_ascii=False, indent=2) + u"\n"
        if os.path.exists(p):
            print(u"  [幂等] %s 已在" % name)
        else:
            write(p, text)
            check(u"%s 已写出（借 %s）" % (name, parent), True)

    print(u"\n⑥ 五语言 %d 个键" % len(KEYS))
    codes = (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh")
    tables = {c: json.loads(read(os.path.join(LANG, c + u".json"))) for c in codes}
    total = 0
    for code in codes:
        d = tables[code]
        added = 0
        for k, vals in KEYS.items():
            if k in d:
                continue
            d[k] = vals[code]
            added += 1
        if added:
            write(os.path.join(LANG, code + u".json"),
                  json.dumps(d, ensure_ascii=False, indent=2) + u"\n")
        total += added
        print(u"      %-6s +%d 键（现 %d）" % (code, added, len(d)))
    after = {c: json.loads(read(os.path.join(LANG, c + u".json"))) for c in codes}
    check(u"新键五份齐全", all(all(k in after[c] for k in KEYS) for c in codes))
    check(u"四语言键集合一致", len(set(frozenset(after[c]) for c in codes[:4])) == 1,
          u" / ".join(u"%s %d" % (c, len(after[c])) for c in codes))
    check(u"lzh 差集仍是 language.name / language.region",
          set(after[u"lzh"]) - set(after[u"zh_cn"]) == {u"language.name", u"language.region"})

    print(u"\n⑦ 探测器源码里不再引用被砍掉的 dir.* 键")
    dt = read(DETECTOR)
    if u'dir." + dir' in dt:
        dt = dt.replace(u'''        Component line = Component.translatable("message.potato_s_t.ore_detector.found",
                best.state().getBlock().getName(),
                Component.translatable("message.potato_s_t.ore_detector.dir." + dir),
                dist, best.pos().getX(), best.pos().getY(), best.pos().getZ());''',
                        u'''        Component line = Component.translatable("message.potato_s_t.ore_detector.found",
                best.state().getBlock().getName(), arrow(dx, dz),
                dist, best.pos().getX(), best.pos().getY(), best.pos().getZ());''')
        write(DETECTOR, dt)
    check(u"不再引用 dir.* 键", u"ore_detector.dir." not in read(DETECTOR))

    print(u"\n备注：")
    for n in notes:
        print(u"  - " + n)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


KEYS = {
    u"item.potato_s_t.ore_detector": {
        u"zh_cn": u"矿物探测器", u"en_us": u"Ore Detector", u"ja_jp": u"鉱物探知機",
        u"ru_ru": u"Детектор руды", u"lzh": u"礦物探测器"},
    u"item.potato_s_t.gravity_device": {
        u"zh_cn": u"手持式引力装置", u"en_us": u"Handheld Gravity Device",
        u"ja_jp": u"携帯重力装置", u"ru_ru": u"Ручное гравитационное устройство",
        u"lzh": u"手持引力之器"},
    u"tooltip.potato_s_t.ore_detector": {
        u"zh_cn": u"储能 1200 FE，右键花 600 FE：报出 3×3 区块、y≤45 内最近的一处矿物（方位 / 距离 / 坐标）。",
        u"en_us": u"Holds 1200 FE; right-click for 600 FE to report the nearest ore within "
                  u"3x3 chunks below y=45 (direction / distance / coordinates).",
        u"ja_jp": u"蓄電 1200 FE。右クリックで 600 FE 消費し、3×3 チャンク・y45 以下で"
                  u"最も近い鉱物を知らせます（方角・距離・座標）。",
        u"ru_ru": u"Хранит 1200 FE; ПКМ за 600 FE сообщает ближайшую руду в 3x3 чанках ниже y=45 "
                  u"(направление / расстояние / координаты).",
        u"lzh": u"儲能千二百 FE，右擊費六百 FE：報三乘三區、y 四十五以下最近之礦（方位、距、坐標）。"},
    u"tooltip.potato_s_t.gravity_device": {
        u"zh_cn": u"储能 8,000,000 FE。副手放一种方块，长按右键蓄力 25 秒：召唤黑洞把 3×3 区块内"
                  u"同种方块（上限 1200 个）与周围生物一起吸过去，并造成虚空伤害。一次耗光电力并损坏。",
        u"en_us": u"Holds 8,000,000 FE. Hold a block in the offhand and hold right-click for 25 s: "
                  u"summons a black hole that drags in every matching block within 3x3 chunks "
                  u"(max 1200) plus nearby mobs, dealing void damage. One shot drains it and breaks it.",
        u"ja_jp": u"蓄電 8,000,000 FE。オフハンドにブロックを入れ、右クリック長押し 25 秒で"
                  u"ブラックホールを召喚：3×3 チャンク内の同種ブロック（最大 1200）と周囲の"
                  u"Mob を吸い込み、ヴォイドダメージを与えます。一度で放電し壊れます。",
        u"ru_ru": u"Хранит 8 000 000 FE. Держите блок во второй руке и удерживайте ПКМ 25 с: "
                  u"призывает чёрную дыру, втягивающую все такие блоки в 3x3 чанках (до 1200) "
                  u"и мобов, нанося урон пустоты. Один выстрел разряжает и ломает предмет.",
        u"lzh": u"儲能八百萬 FE。副手置一方塊，長按右鍵二十五息：召黑洞，收三乘三區內同類方塊"
                u"（至多千二百）與周遭生靈，施虛空之傷。一發即竭而毀。"},
    u"message.potato_s_t.ore_detector.no_power": {
        u"zh_cn": u"电力不足：现在 %s FE，一次要 %s FE", u"en_us": u"Not enough power: %s FE, needs %s FE",
        u"ja_jp": u"電力不足：現在 %s FE、必要 %s FE", u"ru_ru": u"Не хватает энергии: %s FE, нужно %s FE",
        u"lzh": u"電力不足：今 %s FE，一用須 %s FE"},
    u"message.potato_s_t.ore_detector.none": {
        u"zh_cn": u"附近没有任何矿物", u"en_us": u"No ores nearby", u"ja_jp": u"近くに鉱物はありません",
        u"ru_ru": u"Рядом нет руды", u"lzh": u"近處無礦"},
    u"message.potato_s_t.ore_detector.none.chat": {
        u"zh_cn": u"矿物探测器：3×3 区块、y≤45 之内一处矿物都没有（600 FE 已消耗）。",
        u"en_us": u"Ore Detector: nothing found within 3x3 chunks below y=45 (600 FE spent).",
        u"ja_jp": u"鉱物探知機：3×3 チャンク・y45 以下に鉱物はありません（600 FE 消費）。",
        u"ru_ru": u"Детектор руды: в 3x3 чанках ниже y=45 ничего нет (потрачено 600 FE).",
        u"lzh": u"礦物探测器：三乘三區、y 四十五以下無一礦（已耗六百 FE）。"},
    u"message.potato_s_t.ore_detector.found": {
        u"zh_cn": u"最近：%s　方位 %s　距离 %s 格　坐标 %s %s %s",
        u"en_us": u"Nearest: %s  direction %s  distance %s  at %s %s %s",
        u"ja_jp": u"最近：%s　方角 %s　距離 %s　座標 %s %s %s",
        u"ru_ru": u"Ближайшая: %s  направление %s  расстояние %s  координаты %s %s %s",
        u"lzh": u"最近者：%s　方位 %s　距 %s　坐標 %s %s %s"},
    u"message.potato_s_t.ore_detector.arrow": {
        u"zh_cn": u"它在 %s 那一边（x/z 差）", u"en_us": u"It is to %s (x/z offset)",
        u"ja_jp": u"それは %s の方（x/z 差）", u"ru_ru": u"Оно в стороне %s (смещение x/z)",
        u"lzh": u"其在 %s 之方（x/z 之差）"},
    u"message.potato_s_t.ore_detector.more": {
        u"zh_cn": u"附近还有：%s", u"en_us": u"Also nearby: %s", u"ja_jp": u"近くには他に：%s",
        u"ru_ru": u"Также рядом: %s", u"lzh": u"近處尚有：%s"},
    u"message.potato_s_t.gravity.need_offhand": {
        u"zh_cn": u"副手要先放一种方块 —— 黑洞吸的就是那一种",
        u"en_us": u"Put a block in your offhand first - the black hole pulls that block",
        u"ja_jp": u"まずオフハンドにブロックを入れてください（それが吸い込まれます）",
        u"ru_ru": u"Сначала положите блок во вторую руку — дыра втягивает именно его",
        u"lzh": u"須先置一方塊於副手 —— 黑洞所吸者即此"},
    u"message.potato_s_t.gravity.not_full": {
        u"zh_cn": u"储能不足：%s / %s FE（要充满才能放）",
        u"en_us": u"Not fully charged: %s / %s FE (must be full)",
        u"ja_jp": u"蓄電不足：%s / %s FE（満充電が必要）",
        u"ru_ru": u"Не заряжено: %s / %s FE (нужен полный заряд)",
        u"lzh": u"儲能不足：%s / %s FE（須滿方可放）"},
    u"message.potato_s_t.gravity.cancel_offhand": {
        u"zh_cn": u"副手方块没了 —— 蓄力中断",
        u"en_us": u"The offhand block is gone - charge interrupted",
        u"ja_jp": u"オフハンドのブロックが無くなりました —— 中断",
        u"ru_ru": u"Блок из второй руки исчез — зарядка прервана",
        u"lzh": u"副手方塊已失 —— 蓄力中斷"},
    u"message.potato_s_t.gravity.charging": {
        u"zh_cn": u"引力蓄力：%s%%", u"en_us": u"Charging gravity: %s%%",
        u"ja_jp": u"重力充填：%s%%", u"ru_ru": u"Зарядка гравитации: %s%%",
        u"lzh": u"引力蓄力：%s%%"},
    u"message.potato_s_t.gravity.interrupted": {
        u"zh_cn": u"没蓄满就松手了 —— 作废，重来", u"en_us": u"Released too early - nothing happened",
        u"ja_jp": u"途中で離しました —— 失敗", u"ru_ru": u"Отпущено рано — ничего не вышло",
        u"lzh": u"未滿而釋 —— 作廢"},
    u"message.potato_s_t.gravity.fired": {
        u"zh_cn": u"黑洞成形：它开始吸 %s 了",
        u"en_us": u"A black hole forms: it is pulling %s",
        u"ja_jp": u"ブラックホール発生：%s を吸い始めました",
        u"ru_ru": u"Чёрная дыра сформирована: втягивает %s",
        u"lzh": u"黑洞既成：始吸 %s"},
    u"message.potato_s_t.gravity_done": {
        u"zh_cn": u"黑洞坍缩：吸走 %s 个方块，落地 %s 个",
        u"en_us": u"Black hole collapsed: %s blocks pulled, %s placed",
        u"ja_jp": u"ブラックホール崩壊：%s 個吸引、%s 個設置",
        u"ru_ru": u"Чёрная дыра схлопнулась: втянуто %s, размещено %s",
        u"lzh": u"黑洞坍縮：吸 %s 塊，落地 %s 塊"},
}

if __name__ == u"__main__":
    sys.exit(main())
