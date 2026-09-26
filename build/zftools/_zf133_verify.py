# -*- coding: utf-8 -*-
"""_zf133_verify.py —— ZF133 的常驻校验（星璨钢斧 + 冲击波）

> ⚠ 这份脚本在 ZF133 中途被我自己写坏过一次：`io.open(P, "w", newline="\\n")`
>   先把文件截成 0 字节，**然后**断言才发现新参数非法 —— 文件已经空了。
>   教训（已记进档案）：**写文件前把所有断言跑完**，别在断言循环里顺手开写句柄。

分七组：
  A 物品与档位（1192 耐久、钻石级、花费/冷却、夜晚免耐久、属性记账）
  B 冲击波管理器（6 宽 3 高、冻结高度、200 tick 闲置、射程 64、撞墙即停、末地伤害）
  C 注册与接线（ModItems / PotatoST / PotatoSTClient / 数据包 / 渲染器）
  D 贴图与模型（**真解码**核对：§4.92 那一刀）
  E 四语言键集（LangCheck 那条规矩的本地版 + 文案里的数字要与常量对得上）
  F 活体数字（借原版贴图的模型、音效事件…以盘上现数）
  G 探针取证（check/zf133_axe_probe.log 必须存在且 ALL OK）

跑法：python build/zftools/_zf133_verify.py
"""
import hashlib
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
import _zf66_png

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
RES = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
LANG = os.path.join(RES, "lang")
TOOLS = os.path.join(ROOT, r"build\zftools")

FAILS = []
CHECKS = [0]


def read(path):
    return io.open(path, encoding="utf-8").read()


def ok(name, condition, extra=""):
    CHECKS[0] += 1
    if condition:
        print("  [OK]   " + name)
    else:
        FAILS.append(name + (" | " + extra if extra else ""))
        print("  [FAIL] " + name + ("   " + extra if extra else ""))


def main():
    axe = read(os.path.join(JAVA, "StarSteelAxeItem.java"))
    shock = read(os.path.join(JAVA, "ShockwaveManager.java"))
    net = read(os.path.join(JAVA, "ShockwaveNetworking.java"))
    state = read(os.path.join(JAVA, r"client\ShockwaveClientState.java"))
    rend = read(os.path.join(JAVA, r"client\ShockwaveRenderer.java"))
    tiers = read(os.path.join(JAVA, "ModTiers.java"))
    items = read(os.path.join(JAVA, "ModItems.java"))
    main_j = read(os.path.join(JAVA, "PotatoST.java"))
    client_j = read(os.path.join(JAVA, "PotatoSTClient.java"))

    print("=" * 78)
    print("A 物品与档位")
    print("=" * 78)
    ok("A1 档位耐久 1192", re.search(r"build\(1192,", tiers) is not None)
    # ⚠ 这条**必须**盯那一行 build 调用本身：只写 `"INCORRECT_FOR_DIAMOND_TOOL" in tiers`
    #   是恒真的（文件里别处也出现过这串）—— 反证 K9（把钻石改成下界合金）当场证明了它是漏网。
    m_tier = re.search(r"build\(1192,\s*STAR_STEEL_DAMAGE,\s*STAR_STEEL_SPEED,\s*"
                       r"(BlockTags\.[A-Z_]+),\s*(\d+)\)", tiers)
    ok("A2 挖掘等级 = 钻石标签 + 附魔权重 22（读那一行 build 调用本身）",
       m_tier is not None and m_tier.group(1) == "BlockTags.INCORRECT_FOR_DIAMOND_TOOL"
       and m_tier.group(2) == "22",
       ("抓到 %s / %s" % (m_tier.group(1), m_tier.group(2))) if m_tier else "没抓到 build 调用")
    ok("A3 附魔权重 22", re.search(r"build\(1192,[\s\S]*?, 22\)", tiers) is not None)
    ok("A4 通用 build 复用（不再复制第二份匿名类）",
       tiers.count("public int getUses()") == 1
       and "private static Tier build(int uses, float damageBonus," in tiers)
    ok("A5 花费 120", "SHOCKWAVE_COST = 120" in axe)
    ok("A6 冷却 300 tick（20 * 15）", "SHOCKWAVE_COOLDOWN_TICKS = 20 * 15" in axe)
    ok("A7 急迫 1 秒 / 等级 I",
       "HOLD_EFFECT_TICKS = 20" in axe and "HOLD_EFFECT_AMPLIFIER = 0" in axe)
    ok("A8 夜晚判据限定主世界 + 原版时段（13000~23000）",
       "level.dimension() != Level.OVERWORLD" in axe
       and "dayTime >= 13000L && dayTime < 23000L" in axe)
    ok("A9 mineBlock 夜晚早退（不扣耐久）",
       re.search(r"if \(!level\.isClientSide && isNight\(level\)\) \{\s*return true;", axe) is not None)
    ok("A10 白天仍按原版扣 1 点",
       "stack.hurtAndBreak(1, entity, EquipmentSlot.MAINHAND)" in axe)
    ok("A11 只有 shift 右键才出手", "if (!player.isShiftKeyDown())" in axe)
    ok("A12 冷却中不出手", "player.getCooldowns().isOnCooldown(this)" in axe)
    ok("A13 耐久不够 120 不出手",
       "stack.getMaxDamage() - stack.getDamageValue() < SHOCKWAVE_COST" in axe)
    ok("A14 出手才扣 120 并进冷却",
       "stack.hurtAndBreak(SHOCKWAVE_COST, serverPlayer, slot)" in axe
       and "player.getCooldowns().addCooldown(this, SHOCKWAVE_COOLDOWN_TICKS)" in axe)
    ok("A15 三条 Shift 说明", "TOOLTIP_LINES = 3" in axe
       and '"tooltip.potato_s_t.star_steel_axe." + i' in axe)
    ok("A16 客户端不判定（只在服务端出手）", "if (level.isClientSide) {" in axe)
    ok("A17 修理材料 = 星璨钢锭（覆写 isValidRepairItem —— 探针抓出的真缺陷）",
       "isValidRepairItem" in axe and "STAR_STEEL_INGOT" in axe)
    ok("A18 伤害记账：参数 8.0 + 档位加成 8.0 = 修饰符 16 ⇒ 显示总伤害 17.0（探针实测）",
       "STAR_STEEL_DAMAGE = 8.0F" in tiers
       and "ModTiers.STAR_STEEL_DAMAGE, ModTiers.STAR_STEEL_SPEED_MODIFIER" in items)

    print("=" * 78)
    print("B 冲击波管理器")
    print("=" * 78)
    ok("B1 宽度 6 / 半宽 3 / 高 3",
       "WIDTH = 6" in shock and "HALF_WIDTH = WIDTH / 2" in shock and "HEIGHT = 3" in shock)
    ok("B2 偶数宽按 -3..+2 铺（相对玩家对称）", "int offset = lateral - HALF_WIDTH;" in shock)
    ok("B3 闲置上限 200 tick（10 秒）", "IDLE_LIMIT_TICKS = 200" in shock)
    ok("B4 兜底上限 1200 tick 且注明是护栏", "MAX_TICKS = 1200" in shock and "护栏" in shock)
    ok("B5 射程上限 64 格（补的规则，防跑飞）",
       "MAX_DISTANCE = 64" in shock and "wave.travelled * STEP_PER_TICK > MAX_DISTANCE" in shock)
    ok("B6 高度基准在发射那一刻冻结（不是每 tick 现读玩家 Y）",
       "private final int originY;" in shock and "int oy = wave.originY;" in shock)
    ok("B7 撞墙即停（blocked ⇒ return false）",
       re.search(r"if \(blocked\) \{\s*return false;", shock) is not None)
    ok("B8 硬度为负的方块不算墙（基岩/传送门穿过去）", "if (hardness < 0.0F) {" in shock)
    ok("B9 只拆 #logs / #leaves（用原版标签，不硬编码方块名）",
       "state.is(BlockTags.LOGS) || state.is(BlockTags.LEAVES)" in shock)
    # B10：拆与挡必须是两支（第一版写成一个 continue 套一个 continue，
    # 结果"同一排里有挡路方块 ⇒ 这一排的原木也跟着不拆" —— 探针抓出来的）。
    # 判据盯**顺序**：isChoppable 那一支里必须先出现 destroyBlock，
    # 而 isCorrectToolForDrops 必须排在它后面（只作用于"原木/树叶以外"）。
    i_chop = shock.find("if (isChoppable(state)) {")
    i_destroy = shock.find("destroyBlock(pos, true, owner)")
    i_tool = shock.find("if (!owner.getMainHandItem().isCorrectToolForDrops(state))")
    ok("B10 拆与挡分成两支：isChoppable 支里先 destroyBlock，工具判据排在其后",
       i_chop > 0 and i_destroy > i_chop and i_tool > i_destroy,
       "idx chop=%d destroy=%d tool=%d" % (i_chop, i_destroy, i_tool))
    ok("B10b isAir 早退还在（删了它波会被空气挡死 —— 我踩过，代价四轮）",
       shock.count("if (state.isAir()) {") == 1)
    ok("B11 破坏走 destroyBlock(drops=true)", "wave.level.destroyBlock(pos, true, owner)" in shock)
    ok("B12 滚动窗口：拆到就清零，没拆到才累加",
       re.search(r"if \(broke\) \{\s*wave\.sinceBreak = 0;", shock) is not None
       and "else if (++wave.sinceBreak >= IDLE_LIMIT_TICKS)" in shock)
    ok("B13 倒序遍历（边遍历边删）", "for (int i = WAVES.size() - 1; i >= 0; i--)" in shock)
    ok("B14 玩家退场即散", "onPlayerLogout" in shock and "owner.isAlive()" in shock)
    ok("B15 末地公式 10 + 0.5n", "return 10.0D + 0.5D * baseAttackDamage;" in shock)
    ok("B16 末地伤害真的接在采样循环里（不只是一个没被调用的公式）",
       "damageAt(wave, owner, pos)" in shock and "dimension() == Level.END" in shock)
    ok("B17 不误伤发射者（伤害循环里跳过发射者 UUID）",
       "target.getUUID().equals(wave.owner)" in shock)
    ok("B18 基础伤害摘掉装备那几份（按 id + 加法值 + operation 三条全等）",
       "gearValue[0] == modifier.amount()" in shock
       and "gearValue[1] == signOf(modifier.operation())" in shock)
    ok("B19 算式重演原版三个 operation",
       "case ADD_VALUE -> added += modifier.amount();" in shock
       and "case ADD_MULTIPLIED_BASE -> multipliedBase += modifier.amount();" in shock
       and "case ADD_MULTIPLIED_TOTAL -> multipliedTotal *= 1.0D + modifier.amount();" in shock)
    ok("B20 粒子每 2 tick 一批（不是每 tick）", "PARTICLE_INTERVAL = 2" in shock)
    ok("B21 射线只发一次包", "ShockwaveNetworking.broadcastWave(player," in shock)
    ok("B22 damageAt 只在「定义 + 末地分支调用」两处出现",
       shock.count("damageAt(") == 2)
    ok("B23 产品代码里没有遗留诊断（TRACE/DEBUG/System.out）",
       "TRACE" not in shock and "DEBUG" not in shock and "System.out" not in shock)

    print("=" * 78)
    print("C 注册与接线")
    print("=" * 78)
    ok("C1 ModItems 注册 star_steel_axe",
       re.search(r'ITEMS\.register\("star_steel_axe", \(\) -> new StarSteelAxeItem', items) is not None)
    ok("C2 属性照原版斧写法（createAttributes + 两个档位常量）",
       "AxeItem.createAttributes(ModTiers.STAR_STEEL_AXE" in items)
    ok("C3 创造页有一行", "output.accept(STAR_STEEL_AXE.get())" in items)
    ok("C4 PotatoST：数据包登记", "modEventBus.addListener(ShockwaveNetworking::register)" in main_j)
    ok("C5 PotatoST：推进 + 退场清理 + 手持急迫三条 game 总线监听",
       "ShockwaveManager::onServerTick" in main_j and "ShockwaveManager::onPlayerLogout" in main_j
       and "StarSteelAxeItem.applyHoldEffect" in main_j)
    ok("C6 PotatoSTClient：光墙渲染器 init", "ShockwaveRenderer.init()" in client_j)
    ok("C7 渲染挂 AFTER_ENTITIES 且不补摄像机朝向（AFTER_ENTITIES 已是世界系）",
       "Stage.AFTER_ENTITIES" in rend and "getModelViewMatrix" not in rend)
    ok("C8 渲染用 POSITION_COLOR + 加法混合",
       "DefaultVertexFormat.POSITION_COLOR" in rend and "DestFactor.ONE" in rend)
    ok("C9 客户端按世界时间自己推算位置（不逐 tick 收包）",
       "w.startTick" in state and "getGameTime()" in state and "MAX_SHOW_TICKS" in state)
    ok("C10 数据包只带起点/主轴/正负/时间戳",
       "record ShockwavePayload" in net and "ByteBufCodecs.VAR_LONG" in net)
    ok("C11 投递失败不让右键失败（ZF114 那条账）",
       "catch (Throwable t)" in net and "deliveryWarned" in net)
    ok("C12 广播半径 64 格", "RANGE = 64.0D" in net)

    # ---- C13：客户端渲染的 BufferBuilder 收尾规矩（ZF133 实机崩溃换来的一条）----
    # 把注释剥掉再数（否则 javadoc 里提到的 buildOrThrow() 会骗到判据本身）
    def code_only(src):
        out = re.sub(r"/\*[\s\S]*?\*/", "", src)
        return re.sub(r"//[^\n]*", "", out)

    for name, src in (("ShockwaveRenderer", rend), ("SkyboxRenderer",
                      read(os.path.join(JAVA, r"client\SkyboxRenderer.java")))):
        c = code_only(src)
        begins = c.count("Tesselator.getInstance()")
        draws = len(re.findall(r"drawWithShader\(\s*\w+\.buildOrThrow\(\)\)", c))
        stray = len(re.findall(r"(?<!drawWithShader\()(?<!\.)\bbuffer\.buildOrThrow\(\)", c))
        # 单独成句的 buildOrThrow（不在 drawWithShader 括号里）
        bare = len(re.findall(r"^\s*\w+\.buildOrThrow\(\);\s*$", c, re.M))
        ok("C13 %s：begin 次数 == drawWithShader 次数（开了就必须收尾）" % name,
           begins == draws and begins >= 1, "begin=%d draw=%d" % (begins, draws))
        ok("C13b %s：没有单独成句的 buildOrThrow（空 builder 会抛）" % name,
           bare == 0, "bare=%d" % bare)

    print("=" * 78)
    print("D 贴图与模型（真解码）")
    print("=" * 78)
    tex = os.path.join(RES, r"textures\item\star_steel_axe.png")
    src = os.path.join(ROOT, r"build\用户素材\星璨钢斧.png")
    ok("D1 贴图在位", os.path.isfile(tex))
    if os.path.isfile(tex) and os.path.isfile(src):
        w, h, ctype, px = _zf66_png.read_png(tex)
        ok("D2 真解码 16x16（得 %dx%d）" % (w, h), (w, h) == (16, 16))
        ok("D3 像素数 = IHDR 面积（得 %d）" % len(px), len(px) == w * h == 256)
        ok("D4 与用户素材逐字节一致",
           hashlib.sha1(open(tex, "rb").read()).hexdigest()
           == hashlib.sha1(open(src, "rb").read()).hexdigest())
        opaque = sum(1 for p in px if p[3] > 0)
        ok("D5 有不透明内容（%d / 256）" % opaque, opaque > 20)
    model = os.path.join(RES, r"models\item\star_steel_axe.json")
    ok("D6 模型在位且 layer0 指自己的贴图（没借原版）",
       os.path.isfile(model) and "potato_s_t:item/star_steel_axe" in read(model)
       and "item/handheld" in read(model))

    print("=" * 78)
    print("E 四语言")
    print("=" * 78)
    docs = {}
    for name in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        docs[name] = json.load(io.open(os.path.join(LANG, name + ".json"), encoding="utf-8"))
    counts = {k: len(v) for k, v in docs.items()}
    ok("E1 四语言键数一致 %r" % counts, len(set(counts.values())) == 1)
    zh_keys = set(docs["zh_cn"])
    ok("E2 四语言键集逐字一致", all(set(d) == zh_keys for d in docs.values()))
    want = {"item.potato_s_t.star_steel_axe",
            "tooltip.potato_s_t.star_steel_axe.1",
            "tooltip.potato_s_t.star_steel_axe.2",
            "tooltip.potato_s_t.star_steel_axe.3"}
    ok("E3 本轮四个键四语言都在", all(want <= set(d) for d in docs.values()))
    ok("E4 中文名是「星璨钢斧」", docs["zh_cn"].get("item.potato_s_t.star_steel_axe") == "星璨钢斧")
    ok("E5 四语言的斧子名互不相同（不是漏翻）",
       len({d.get("item.potato_s_t.star_steel_axe") for d in docs.values()}) == 4)
    for lang, d in docs.items():
        tip1 = d.get("tooltip.potato_s_t.star_steel_axe.1", "")
        tip2 = d.get("tooltip.potato_s_t.star_steel_axe.2", "")
        tip3 = d.get("tooltip.potato_s_t.star_steel_axe.3", "")
        ok("E6 %s 文案：1192 耐久" % lang, "1192" in tip1)
        ok("E7 %s 文案：120 点耐久 + 15 秒冷却 + 6 格宽" % lang,
           "120" in tip2 and "15" in tip2 and "6" in tip2)
        ok("E8 %s 文案：10 秒 + 0.5（伤害公式）" % lang,
           "10" in tip3 and "0.5" in tip3)

    print("=" * 78)
    print("F 活体数字（以盘上现数）")
    print("=" * 78)
    models = []
    for root, _dirs, files in os.walk(os.path.join(RES, "models", "item")):
        for f in files:
            if f.endswith(".json"):
                models.append(os.path.join(root, f))
    borrowed = []
    for p in models:
        m = re.search(r'"layer0"\s*:\s*"([^"]+)"', read(p))
        if m and m.group(1).startswith("minecraft:item/"):
            borrowed.append(os.path.basename(p))
    print("      （第 8 道门 TextureCheck 有它自己那套口径；这里按 layer0 现数）")
    print("      还在借原版物品贴图的模型 %d 个：%s" % (len(borrowed), ", ".join(sorted(borrowed))))
    ok("F1 斧子不在那个名单里", "star_steel_axe.json" not in borrowed)
    sounds = os.path.join(RES, "sounds.json")
    ok("F2 本轮没有新增音效事件（用的是原版声音）",
       os.path.isfile(sounds) and "shockwave" not in read(sounds))

    print("=" * 78)
    print("G 探针取证")
    print("=" * 78)
    probe = os.path.join(TOOLS, r"check\zf133_axe_probe.log")
    if os.path.isfile(probe):
        body = read(probe)
        ok("G1 探针报告存在（%d B）" % os.path.getsize(probe), os.path.getsize(probe) > 1000)
        ok("G2 探针判定 ALL OK", "verdict: ALL OK" in body)
        ok("G3 探针零 FAIL", "[FAIL]" not in body)
        ok("G4 探针覆盖九个场景",
           all(s in body for s in ("① 物品与档位", "② (b)", "③ (d)", "④ (e)",
                                   "⑤ (i)", "⑥ (h)", "⑦ (f)", "⑧ (g)", "⑨ (c)")))
        ok("G5 末地伤害实测 12.0（力量 I ⇒ n=4）", "12.0" in body and "末影人" in body)
        ok("G6 属性记账实测：显示总伤害 17.0", "17.0" in body)
    else:
        print("  [SKIP] 探针报告还没生成")

    print("=" * 78)
    print("总计 %d 项检查，失败 %d 项" % (CHECKS[0], len(FAILS)))
    for f in FAILS:
        print("  [FAIL] " + f)
    print("=" * 78)
    return 1 if FAILS else 0


sys.exit(main())
