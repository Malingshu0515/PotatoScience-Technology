# -*- coding: utf-8 -*-
u"""_zf121_verify.py —— ZF121 常驻校验：振金的合金冶炼炉配方（0.11）

用户原话（第一版）：「振金合金冶炼炉配方；1硬质钛合金+8热力金属+2高碳钢+3银锭+12金锭
                    粗振金+钻石+2下界合金碎片+1红石粉 14500Fe/t 产出1振金」
用户原话（**改口·最终**）：「对不起刚才忘了合金炉的限制 这是新振金合金冶炼炉配方；
                    1硬质钛合金+8热力金属+2高碳钢+3银锭+12金锭 粗振金+2下界合金碎片
                    14500Fe/t 产出1振金」

八段：
  ① 文件账目（改前件 215 份、探针钩子摘了、存档先抄后删）
  ② c: 标签（4 份新标签 + 两处"表 ↔ 盘"漂移补账 + 两个父标签的项数与内容）
  ③ 配方表（第四条：5 输入 / **2** 消耗品 / 1 振金锭 / 600 tick / 14500 FE/t / 8,700,000 FE）
  ④ 方块实体与菜单（**槽位数一个都没动** + 菜单那层 mayPlace=false 撤掉 + shift 点击路由）
  ⑤ 四语言（键集合四份一致、备份里的键一个没少、相对备份只动了脚注那一个值）
  ⑥ 探针 UTF-8 报告（真游戏跑出来的那份）全绿
  ⑦ 文档（档案 §5 / §9、交接文档、英文公告）
  ⑧ 往轮门与反证刀的 retarget 账（_zf71 / _zf111 / _zf114 / _zf119）

⚠ 本轮的活体数字（键数）**故意不钉死**：并行那条线（ZF120 振金套）刚从 464 加到 464，
   钉一个具体数就会互相踩。这里改成"相对改前件"的不变量：四份键集合一致、旧键一个不少、
   值的变动集合恰好 == {脚注}。当前实际键数打印出来存档。
"""
import hashlib
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
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
TAGS = os.path.join(ROOT, r"src\main\resources\data\c\tags\item")
TOOLS = os.path.join(ROOT, r"build\zftools")
CHECK = os.path.join(TOOLS, "check")
DOC = os.path.join(ROOT, r"docs\开发档案.md")
HANDOFF = os.path.join(ROOT, r"docs\多会话协作交接.md")
DOC_EN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")
REPORT = os.path.join(TOOLS, r"_zf121_probe_utf8.txt")
PROBE_ARCHIVE = os.path.join(CHECK, "Zf121Check.java")
BK = r"C:\PotatoST救援\zf121_pre"
LANGS = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]
KEY_TIP = u"tooltip.potato_s_t.alloy_smelter"

BASE_INGOTS = [u"potato_s_t:aluminum_ingot", u"potato_s_t:cobalt_ingot",
               u"potato_s_t:nickel_ingot", u"potato_s_t:silver_ingot",
               u"potato_s_t:uranium_ingot", u"potato_s_t:titanium_ingot",
               u"potato_s_t:vibranium_ingot", u"potato_s_t:high_carbon_steel",
               u"potato_s_t:light_titanium_alloy", u"potato_s_t:star_steel_ingot",
               u"potato_s_t:hard_titanium_alloy", u"potato_s_t:thermal_metal"]

n_pass = 0
fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def check(name, cond, detail=None):
    global n_pass
    if cond:
        n_pass += 1
    else:
        fails.append(name + (u"  ← %s" % detail if detail else u""))


def eq(name, want, got):
    check(name, want == got, u"期望 %r 实际 %r" % (want, got))


def jload(p):
    u"""读 JSON；文件不在或解析失败都返回 None（§4.77 族：不许抛栈把校验器搞崩）。"""
    if not os.path.exists(p):
        return None
    try:
        return json.loads(read(p))
    except Exception:
        return None


def main():
    global n_pass
    recipes = read(os.path.join(JAVA, "AlloySmelterRecipes.java"))
    be = read(os.path.join(JAVA, "AlloySmelterBlockEntity.java"))
    menu = read(os.path.join(JAVA, "AlloySmelterMenu.java"))
    mrec = read(os.path.join(JAVA, "MachineRecipes.java"))
    main_java = read(os.path.join(JAVA, "PotatoST.java"))
    screen = read(os.path.join(JAVA, r"client\AlloySmelterScreen.java"))
    gen = read(os.path.join(TOOLS, "GenCommonTags.py"))

    # ============ ① 文件账目 ============
    print(u"== ① 文件账目 ==")
    check(u"改前件 zf121_pre 在", os.path.isdir(BK))
    n_bk = 0
    if os.path.isdir(BK):
        for _d, _s, _fs in os.walk(BK):
            n_bk += len(_fs)
    check(u"改前件 ≥200 份", n_bk >= 200, u"实际 %d" % n_bk)
    for rel in (r"src\main\java\com\potatost\mod\PotatoST.java",
                r"src\main\java\com\potatost\mod\AlloySmelterRecipes.java",
                r"src\main\java\com\potatost\mod\AlloySmelterBlockEntity.java",
                r"src\main\java\com\potatost\mod\AlloySmelterMenu.java",
                r"src\main\java\com\potatost\mod\MachineRecipes.java",
                r"build\zftools\GenCommonTags.py"):
        check(u"点名件在改前件里：%s" % os.path.basename(rel), os.path.exists(os.path.join(BK, rel)))
    check(u"探针钩子已摘（PotatoST 里不许留 Zf121Check）", u"Zf121Check" not in main_java)
    check(u"探针源文件已从 src 删掉", not os.path.exists(os.path.join(JAVA, "Zf121Check.java")))
    check(u"探针存档在 build/zftools/check/（先抄后删）", os.path.exists(PROBE_ARCHIVE))

    # ============ ② c: 标签 ============
    print(u"\n== ② c: 标签 ==")
    check(u"生成器 ALLOYS 表里有硬质钛合金", u'("hard_titanium_alloy", "hard_titanium_alloy")' in gen)
    check(u"生成器 ALLOYS 表里有热力金属", u'("thermal_metal", "thermal_metal")' in gen)
    check(u"生成器 METALS 表里补登记了振金（锭 + 粗矿，无矿石方块）",
          u'("vibranium", "vibranium_ingot", "raw_vibranium", [])' in gen)
    check(u"生成器给 stdout 加了 UTF-8（否则反向体检那行必崩，结论看不到）",
          u"sys.stdout.reconfigure" in gen)
    want_tags = [(os.path.join(TAGS, "ingots", "hard_titanium_alloy.json"),
                  [u"potato_s_t:hard_titanium_alloy"], u"c:ingots/hard_titanium_alloy"),
                 (os.path.join(TAGS, "hard_titanium_alloy_ingots.json"),
                  [u"potato_s_t:hard_titanium_alloy"], u"c:hard_titanium_alloy_ingots"),
                 (os.path.join(TAGS, "ingots", "thermal_metal.json"),
                  [u"potato_s_t:thermal_metal"], u"c:ingots/thermal_metal"),
                 (os.path.join(TAGS, "thermal_metal_ingots.json"),
                  [u"potato_s_t:thermal_metal"], u"c:thermal_metal_ingots"),
                 (os.path.join(TAGS, "ingots", "vibranium.json"),
                  [u"potato_s_t:vibranium_ingot"], u"c:ingots/vibranium"),
                 (os.path.join(TAGS, "vibranium_ingots.json"),
                  [u"potato_s_t:vibranium_ingot"], u"c:vibranium_ingots"),
                 (os.path.join(TAGS, "raw_materials", "vibranium.json"),
                  [u"potato_s_t:raw_vibranium"], u"c:raw_materials/vibranium")]
    for p, want, name in want_tags:
        obj = jload(p)
        if obj is None:
            check(u"%s 收下它（文件不在或不是 JSON）" % name, False, os.path.relpath(p, ROOT))
            continue
        eq(u"%s 收下它" % name, want, obj.get(u"values"))
    ing = jload(os.path.join(TAGS, "ingots.json"))
    if ing is None:
        check(u"父标签 c:ingots 可读", False)
    else:
        eq(u"父标签 c:ingots = 12 项且逐项对", BASE_INGOTS, ing.get(u"values"))
    raw = jload(os.path.join(TAGS, "raw_materials.json"))
    if raw is None:
        check(u"父标签 c:raw_materials 可读", False)
    else:
        check(u"父标签 c:raw_materials 收下粗振金（漂移补账）",
              u"potato_s_t:raw_vibranium" in raw.get(u"values", []))
        eq(u"父标签 c:raw_materials = 10 项", 10, len(raw.get(u"values", [])))

    # ============ ③ 配方表 ============
    print(u"\n== ③ 配方表 ==")
    eq(u"一共 4 条配方", 4, recipes.count(u"list.add(new Smelt("))
    check(u"第④条：1 硬质钛合金", u'new Need(ingot("hard_titanium_alloy"), 1)' in recipes)
    check(u"第④条：8 热力金属", u'new Need(ingot("thermal_metal"), 8)' in recipes)
    check(u"第④条：2 高碳钢", u'new Need(ingot("steel"), 2)' in recipes)
    check(u"第④条：3 银锭", u'new Need(ingot("silver"), 3)' in recipes)
    check(u"第④条：12 金锭（走 NeoForge 的 c:ingots/gold）",
          u'new Need(ingot("gold"), 12)' in recipes)
    check(u"第④条：消耗 1 粗振金", u"new Consume(ModItems.RAW_VIBRANIUM.get(), 1)" in recipes)
    check(u"第④条：消耗 2 下界合金碎片", u"new Consume(Items.NETHERITE_SCRAP, 2)" in recipes)
    check(u"用户改口后**不再**消耗钻石", u"Items.DIAMOND" not in recipes)
    check(u"用户改口后**不再**消耗红石粉", u"Items.REDSTONE" not in recipes)
    check(u"第④条产物 = 1 振金锭",
          u"new ItemStack(ModItems.VIBRANIUM_INGOT.get(), 1)" in recipes)
    check(u"第④条用自己的专属常量 VIBRANIUM_ENERGY_PER_TICK（不借 MAX）",
          u"DURATION_TICKS, VIBRANIUM_ENERGY_PER_TICK));" in recipes)
    check(u"星璨钢那条也拆出了自己的 STAR_STEEL_ENERGY_PER_TICK（探针抓到的真雷）",
          u"DURATION_TICKS, STAR_STEEL_ENERGY_PER_TICK));" in recipes)
    check(u"⚠ **没有任何配方**直接引用 MAX_ENERGY_PER_TICK（谁引用谁就会在下一个人加配方时被静默改数）",
          u"DURATION_TICKS, MAX_ENERGY_PER_TICK))" not in recipes)
    check(u"MAX_ENERGY_PER_TICK = 14_500（纯 int 常量，静态守卫能读）",
          u"public static final int MAX_ENERGY_PER_TICK = 14_500;" in recipes)
    check(u"STAR_STEEL_ENERGY_PER_TICK = 12_000（ZF111 用户给的数，写死）",
          u"public static final int STAR_STEEL_ENERGY_PER_TICK = 12_000;" in recipes)
    check(u"VIBRANIUM_ENERGY_PER_TICK = 14_500（ZF121 用户给的数，写死）",
          u"public static final int VIBRANIUM_ENERGY_PER_TICK = 14_500;" in recipes)
    check(u"时长仍 600 tick（用户没给，沿用本机规格）",
          u"public static final int DURATION_TICKS = 30 * 20;" in recipes)
    check(u"注释写明一件 8,700,000 FE", u"8,700,000" in recipes)
    check(u"注释写明用户第一版是 4 样消耗品、他自己改口收窄成 2 样",
          u"忘了合金炉的限制" in recipes and u"4 样消耗品" in recipes)
    check(u"注释写明硬质钛合金**没有**并进 c:ingots/titanium_alloy（防复制漏洞）",
          u"复制漏洞" in recipes)
    check(u"表仍是懒加载（§4.1）", u"if (table == null)" in recipes)
    # 四条配方各自的每 tick 耗电，必须**逐条**等于用户给的数（活体数字的正用法）
    lits = {u"ENERGY_PER_TICK": 800, u"STAR_STEEL_ENERGY_PER_TICK": 12_000,
            u"VIBRANIUM_ENERGY_PER_TICK": 14_500, u"MAX_ENERGY_PER_TICK": 14_500}
    vals = []
    for m in re.finditer(r"DURATION_TICKS,\s*([A-Za-z_0-9]+)\)\)", recipes):
        vals.append(lits.get(m.group(1), -1))
    eq(u"四条配方各自的每 tick 耗电 = 800 / 800 / 12000 / 14500（用户给的字面量）",
       [800, 800, 12_000, 14_500], vals)
    eq(u"全表最贵的正是 MAX_ENERGY_PER_TICK（14500）", 14_500, max(vals) if vals else -1)
    check(u"14500 ≤ 储能 32768（注释里写着）", u"14500 ≤ 32768" in be)

    # ============ ④ 方块实体与菜单 ============
    print(u"\n== ④ 方块实体与菜单 ==")
    check(u"INPUT_COUNT = 5（一个都没动）", u"public static final int INPUT_COUNT = 5;" in be)
    check(u"OUTPUT_COUNT = 3（一个都没动）", u"public static final int OUTPUT_COUNT = 3;" in be)
    check(u"CONSUME_COUNT = 2（用户改口后**没有**扩槽）",
          u"public static final int CONSUME_COUNT = 2;" in be)
    check(u"SLOT_COUNT 注释仍是 10", u"public static final int SLOT_COUNT = CONSUME_FIRST + CONSUME_COUNT;   // = 10" in be)
    check(u"槽位数没动的说明写进了类注释", u"0.11 ZF121：槽位数一个都没动" in be)
    check(u"静态守卫读 MAX_ENERGY_PER_TICK（纯 int，不碰懒加载的表）",
          u"long worstDemand = AlloySmelterRecipes.MAX_ENERGY_PER_TICK;" in be)
    check(u"消耗槽门禁仍是 isConsumable", u"return isConsumable(stack);" in be)
    check(u"消耗槽注释点明了振金那两样",
          u"振金那条（ZF121）是粗振金 ×1 + 下界合金碎片 ×2" in be)
    check(u"菜单：2 个消耗槽坐标仍是原来那两格（116/62）",
          u"public static final int CONSUME_X = 116;" in menu
          and u"public static final int CONSUME_Y = 62;" in menu)
    loop = (u"        for (int k = 0; k < AlloySmelterBlockEntity.CONSUME_COUNT; k++) {\n"
            u"            this.addSlot(new SlotItemHandler(machineInventory, "
            u"AlloySmelterBlockEntity.CONSUME_FIRST + k,\n"
            u"                    CONSUME_X + k * 18, CONSUME_Y));\n"
            u"        }")
    check(u"菜单：消耗槽那一圈**没有** mayPlace 覆盖（ZF49 那层门撤掉了）", loop in menu)
    eq(u"菜单：全文件只剩 1 处 mayPlace（输出槽那个）", 1, menu.count(u"mayPlace"))
    check(u"菜单：消耗品也能 shift 点击（走 isItemValid 判）",
          u"if (!this.machineInventory.isItemValid(slot, stack)) {" in menu)
    check(u"菜单：类注释写明了撤门这件事", u"0.11 ZF121：消耗槽终于能用手放进去了" in menu)
    check(u"JEI：消耗品照样画进输入区（不加新说明行）",
          u"for (AlloySmelterRecipes.Consume consume : smelt.consumes()) {" in mrec
          and u"jei.tag_inputs" not in mrec)
    check(u"PotatoST ㉗ 注释跟上了（2 消耗槽 + 能手放）",
          u"2 消耗槽（自动化可投锭、可取产物；ZF121 起消耗槽也能手放）" in main_java)
    check(u"界面类注释跟上了", u"0.11 ZF121 起这条路才通" in screen)

    # ============ ⑤ 四语言 ============
    print(u"\n== ⑤ 四语言 ==")
    after, before = {}, {}
    for name in LANGS:
        p = os.path.join(LANG, name + u".json")
        obj = jload(p)
        if obj is None:
            check(u"%s 可读" % name, False)
            continue
        after[name] = obj
        bk = jload(os.path.join(BK, r"src\main\resources\assets\potato_s_t\lang", name + u".json"))
        if bk is not None:
            before[name] = bk
    counts = {k: len(v) for k, v in after.items()}
    print(u"    当前键数：%s" % u"、".join(u"%s=%d" % (k, counts[k]) for k in sorted(counts)))
    eq(u"四语言键集合完全一致", 1, len(set(frozenset(v) for v in after.values())))
    for name in after:
        cur, bk = after[name], before.get(name, {})
        check(u"%s：改前件里的键一个都没少" % name, not [k for k in bk if k not in cur])
        changed = [k for k in bk if k in cur and bk[k] != cur[k]]
        eq(u"%s：相对改前件只动了脚注这一个值" % name, [KEY_TIP], changed)
        tip = cur.get(KEY_TIP, u"").split(u"\n")
        btip = bk.get(KEY_TIP, u"").split(u"\n") if bk else []
        eq(u"%s：介绍行数没变（≤20 是 _zf55 的红线）" % name, len(btip), len(tip))
        if btip:
            eq(u"%s：摆放图那几行逐字未动" % name, btip[:-1], tip[:-1])
        if tip:
            last = tip[-1]
            check(u"%s：脚注写了 14500" % name, u"14500" in last)
            check(u"%s：脚注仍写着 12000（星璨钢那条不能丢）" % name, u"12000" in last)
            check(u"%s：脚注里没有 ASCII 双引号" % name, u'"' not in last)
            check(u"%s：脚注还是「2 个消耗槽」口径（没有跟着第一版扩成 4）" % name,
                  u"4 消耗槽" not in last and u"4 consumption slots" not in last
                  and u"消費 4" not in last and u"4 расходных" not in last)
        check(u"%s：整条介绍仍写着 32768（_zf55 会查）" % name,
              u"32768" in u"\n".join(tip))
        check(u"%s：整条介绍仍写着 58（_zf55 会查）" % name, u"58" in u"\n".join(tip))

    # ============ ⑥ 探针报告 ============
    print(u"\n== ⑥ 探针报告 ==")
    check(u"探针 UTF-8 报告在盘上", os.path.exists(REPORT))
    if os.path.exists(REPORT):
        rep = read(REPORT)
        check(u"报告是全绿（verdict: ALL OK）", "verdict: ALL OK" in rep)
        check(u"报告里没有 [FAIL]", "[FAIL]" not in rep)
        check(u"报告里记了四条配方", u"配方表一共 4 条" in rep)
        check(u"报告里记了「每 tick 正好 14500 FE」", u"每 tick 正好 14500 FE" in rep)
        check(u"报告里记了一层总耗电", "8700000" in rep or "8,700,000" in rep)
        check(u"报告里记了「星璨钢那条仍是每 tick 12000 FE」", u"每 tick 12000 FE" in rep)
        check(u"报告里记了两个标签都非空且认得人", u"c:ingots/hard_titanium_alloy 非空" in rep
              and u"c:ingots/thermal_metal 非空" in rep)

    # ============ ⑦ 文档 ============
    print(u"\n== ⑦ 文档 ==")
    doc = read(DOC)
    hand = read(HANDOFF)
    den = read(DOC_EN)
    check(u"档案 §5 有 ZF121 行", u"| ZF121 |" in doc)
    check(u"档案 §9 有 ZF121 小节", u"### ZF121（0.11）" in doc)
    check(u"档案里写明了时长是补的（14500 × 600）", u"8,700,000" in doc)
    check(u"档案里记了用户改口那件事", u"忘了合金炉的限制" in doc)
    check(u"交接文档提到了 ZF121", u"ZF121" in hand)
    check(u"英文公告写了 14,500 FE/t", u"14,500 FE/t" in den)
    check(u"英文公告写了 8,700,000 FE", u"8,700,000 FE" in den)
    check(u"英文公告的振金条目不再说「没有配方」", u"It has **no recipe yet**" not in den)

    # ============ ⑧ 往轮门 retarget 与反证刀 ============
    print(u"\n== ⑧ retarget 与反证刀 ==")
    z71 = read(os.path.join(TOOLS, "_zf71_verify.py"))
    check(u"_zf71 的槽位元组已 retarget（仍是 32768/5/3/2 —— 槽位数本轮没动）",
          u"(32768, 5, 3, 2)" in z71)
    z111 = read(os.path.join(TOOLS, "_zf111_verify.py"))
    check(u"_zf111 已 retarget MAX_ENERGY_PER_TICK = 14_500",
          u"MAX_ENERGY_PER_TICK = 14_500;" in z111)
    check(u"_zf111 已 retarget 守卫注释 14500 ≤ 32768", u"14500 ≤ 32768" in z111)
    z114 = read(os.path.join(TOOLS, "_zf114_verify.py"))
    check(u"_zf114 的 F5b 还在盯「粗振金没有**工作台**配方」",
          u"F5b" in z114 and u"raw_vibranium.json" in z114)
    z119 = read(os.path.join(TOOLS, "_zf119_verify.py"))
    check(u"_zf119 的 B6 口径改准了（数据包/工作台没有，来源是合金炉）",
          u"数据包/工作台" in z119 or u"合金炉" in z119)
    check(u"反证刀脚本在", os.path.exists(os.path.join(TOOLS, "_zf121_falsify.py")))
    check(u"快照脚本在", os.path.exists(os.path.join(TOOLS, "_zf121_gatesnap.py")))

    print(u"")
    print(u"通过 = %d   失败 = %d" % (n_pass, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
