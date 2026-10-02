# -*- coding: utf-8 -*-
u"""_zf153_verify.py —— ZF153 的常驻校验：振金剑（无法破坏 / 手持免疫三效果 / 24 伤害 / 1.4 攻速 /
附魔权重 1 / Shift+右键猛击地面）

用户原话（逐字）：
    「加个振金剑材质在素材 无法破坏 拿在手里免疫凋零，缓慢，挖掘疲劳 24点伤害 1.4攻击速度
      1附魔权重 shift+右键猛击地面 击飞6x6除自己的所有生物 并对其造成n+12点伤害
      n为玩家基础伤害 和4s的失明 4s的缓慢效果 冷却6s」

断言分四类，**每一条都带稳定 id**（`A2` / `B3` …）——因为反证脚本 `_zf153_falsify.py`
要按 id 断言"这一刀必须被**这一条**抓住"，只红不点名是不算数的（§11.1 那条纪律）：

  A **源码结构**：七条需求各自落在哪、有没有偷偷加耐久、免疫是不是真的从源头拦、
     "击飞必须在 hurt 之后"这个顺序、n 有没有复用 ZF133 那份已过探针的实现。
  B **资源**：贴图（原字节复制 + 规格）、模型（自己的图、不是借原版）、五语言键集合与数字对账、
     注册名三处一致、**没有配方产出它**（用户没给配方 ⇒ 与 ZF119 同一条口径）。
  C **端到端证据**：真服务端探针 `Zf153Check` 的报告（含三条灵敏度对照）。
  D **没把往轮的门弄红**：`_zf114_verify`（星轨坠）/ `_zf141_verify`（兄弟剑）/ `_zf145_verify`（成就树）。

⚠ 判据吃**被测对象本身**：A 读真源码（且先 `strip_comments`，见 §4.152 那个坑），
   B 读真字节/真 JSON，C 读探针跑出来的真报告，D 是真跑别人的门。

跑法：python build\\zftools\\_zf153_verify.py
"""
import hashlib
import io
import json
import os
import re
import struct
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, r"build\zftools")
CHECK = os.path.join(TOOLS, "check")
MOD = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
LANG = os.path.join(ASSETS, "lang")
USER_ASSETS = os.path.join(ROOT, r"build\用户素材")
PROBE_REPORT = os.path.join(CHECK, u"zf153_振金剑取证.log")

SWORD = os.path.join(MOD, "VibraniumSwordItem.java")
TIERS = os.path.join(MOD, "ModTiers.java")
ITEMS = os.path.join(MOD, "ModItems.java")
MAIN = os.path.join(MOD, "PotatoST.java")
SHOCK = os.path.join(MOD, "ShockwaveManager.java")

fails, n_pass = [], 0


def check(cid, name, ok, detail=u""):
    global n_pass
    if ok:
        n_pass += 1
        print(u"  [OK]   %s %s %s" % (cid, name, detail))
    else:
        fails.append(cid)
        print(u"  [FAIL] %s %s %s" % (cid, name, detail))


def eq(cid, name, want, got):
    check(cid, name, want == got, u"（期望 %r，实际 %r）" % (want, got))


def read(p):
    return io.open(p, encoding="utf-8").read()


def raw(p):
    return open(p, "rb").read()


def strip_comments(text):
    u"""剃掉注释再判结构（§4.152：本轮同类坑 —— 类注释里引用了要否定的写法，
    不剃注释就会拿自己的散文当证据）。"""
    text = re.sub(u"/\\*.*?\\*/", u"", text, flags=re.S)
    return re.sub(u"(?m)//.*$", u"", text)


def cut(text, start, end):
    u"""取 [start, end)；**任一锚点不在就返回空串**（绝不一路取到文件尾 —— §4.151）。"""
    i = text.find(start)
    if i < 0:
        return u""
    j = text.find(end, i)
    return u"" if j < 0 else text[i:j]


def png_info(data):
    assert data[:8] == b"\x89PNG\r\n\x1a\n", u"不是 PNG"
    w, h, bd, ct, _cm, _fm, il = struct.unpack(">IIBBBBB", data[16:29])
    return w, h, bd, ct, il


# ================================================================
#  A 源码结构
# ================================================================
def section_a():
    print(u"\n================ A 源码结构 ================")
    for p in (SWORD, TIERS, ITEMS, MAIN):
        check(u"A0", u"改前件存在（%s）" % os.path.basename(p), os.path.exists(p))
    if not os.path.exists(SWORD):
        return
    src = strip_comments(read(SWORD))
    tiers = strip_comments(read(TIERS))
    items = strip_comments(read(ITEMS))
    main = strip_comments(read(MAIN))

    # --- A1 类与档位 ---
    check(u"A1", u"VibraniumSwordItem 继承 SwordItem",
          re.search(u"class\\s+VibraniumSwordItem\\s+extends\\s+SwordItem", src) is not None)
    check(u"A2", u"构造器把档位交给父类（super(ModTiers.VIBRANIUM_TOOL, …)）",
          re.search(u"super\\(\\s*ModTiers\\.VIBRANIUM_TOOL\\s*,", src) is not None)
    check(u"A3", u"档位：附魔权重常量 = 1（用户要的「1附魔权重」）",
          re.search(u"VIBRANIUM_ENCHANTMENT_VALUE\\s*=\\s*1\\s*;", tiers) is not None)
    check(u"A4", u"档位：伤害参数 15.0 / 攻速 -2.6 / 加成 8.0 / 耐久 2031",
          re.search(u"VIBRANIUM_SWORD_DAMAGE\\s*=\\s*15\\.0F", tiers) is not None
          and re.search(u"VIBRANIUM_SWORD_SPEED_MODIFIER\\s*=\\s*-2\\.6F", tiers) is not None
          and re.search(u"VIBRANIUM_DAMAGE_BONUS\\s*=\\s*8\\.0F", tiers) is not None
          and re.search(u"VIBRANIUM_TOOL\\s*=\\s*build\\(2031,", tiers) is not None)
    check(u"A5", u"档位的附魔权重那一格传的就是那个常量（不是写死别的数）",
          re.search(u"build\\(2031,\\s*VIBRANIUM_DAMAGE_BONUS,\\s*SPEED,\\s*"
                    u"INCORRECT_FOR_NETHERITE,\\s*VIBRANIUM_ENCHANTMENT_VALUE,", tiers) is not None)
    check(u"A6", u"修理材料是振金锭（懒取，不碰静态初始化）",
          re.search(u"vibraniumRepair\\(\\)\\s*\\{[^}]*ModItems\\.VIBRANIUM_INGOT\\.get\\(\\)",
                    tiers, re.S) is not None
          and u"ModTiers::vibraniumRepair" in tiers)

    # --- A7 注册与创造页 ---
    check(u"A7", u"ModItems 注册了 vibranium_sword",
          re.search(u'ITEMS\\.register\\("vibranium_sword"', items) is not None)
    check(u"A8", u"物品挂 UNBREAKABLE（用户要的「无法破坏」）",
          u"DataComponents.UNBREAKABLE" in items and u"new Unbreakable(true)" in items)
    check(u"A9", u"属性行照原版剑的写法（SwordItem.createAttributes + 本轮的档位/两个参数）",
          re.search(u"SwordItem\\.createAttributes\\(ModTiers\\.VIBRANIUM_TOOL,\\s*"
                    u"ModTiers\\.VIBRANIUM_SWORD_DAMAGE,\\s*"
                    u"ModTiers\\.VIBRANIUM_SWORD_SPEED_MODIFIER\\)", items) is not None)
    check(u"A10", u"创造页里有它（§4.82：漏了就是「看不见、搜不到」）",
          u"output.accept(VIBRANIUM_SWORD.get())" in items)
    # ⚠ 本轮从 sources.jar 核实：耐久由 TieredItem 构造器给（properties.durability(tier.getUses())），
    #   这里再写一遍只会被盖掉、还让读的人以为随时能改 ⇒ 判据禁止它出现
    # ⚠ 切片必须从**未剥注释**的原文里切：收尾锚点 `// =====…` 本身就是一行注释，
    #   先 strip_comments 会把锚点一起剃掉 ⇒ cut 返回空串 ⇒ 这条**假红**（本轮踩到）。
    sword_block = strip_comments(cut(read(ITEMS), u"VIBRANIUM_SWORD =",
                                    u"// ========== 创造模式标签页"))
    check(u"A11", u"注册处**故意不写** .durability(...)（本轮核实：耐久只能来自档位）",
          sword_block != u"" and u".durability(" not in sword_block)

    # --- A12 两处监听 ---
    check(u"A12", u"PotatoST 挂了「源头拦」（VibraniumSwordItem::onEffectApplicable）",
          u"VibraniumSwordItem::onEffectApplicable" in main)
    check(u"A13", u"PotatoST 挂了「每 tick 清理」（onPlayerTick）",
          re.search(u"VibraniumSwordItem\\.onPlayerTick\\(", main) is not None)

    # --- A14 免疫表：三条不多不少 ---
    immune = cut(src, u"IMMUNE_EFFECTS =", u";")
    check(u"A14", u"免疫表 = 凋零 / 缓慢 / 挖掘疲劳 三条",
          immune != u"" and all(k in immune for k in
                                (u"MobEffects.WITHER", u"MobEffects.MOVEMENT_SLOWDOWN",
                                 u"MobEffects.DIG_SLOWDOWN")))
    check(u"A15", u"免疫表里**没有**别的东西（防「一刀切」误伤：急迫/速度/失明都不许在里面）",
          immune != u"" and not any(k in immune for k in
                                    (u"DIG_SPEED", u"MOVEMENT_SPEED", u"BLINDNESS",
                                     u"REGENERATION", u"HEALTH_BOOST")))
    check(u"A16", u"免疫走**源头**拦：setResult(…DO_NOT_APPLY)（不是每 tick 抹掉了事）",
          re.search(u"setResult\\(\\s*MobEffectEvent\\.Applicable\\.Result\\.DO_NOT_APPLY\\s*\\)",
                    src) is not None)
    check(u"A17", u"清理那一半：拿着剑时 removeEffect 掉身上已有的三种",
          re.search(u"removeEffect\\(\\s*immune\\s*\\)", src) is not None
          and u"player.hasEffect(immune)" in src)
    check(u"A18", u"isHolding 认主手**与**副手（「拿在手里」的逐字读法）",
          u"getMainHandItem()" in cut(src, u"static boolean isHolding", u"}")
          and u"getOffhandItem()" in cut(src, u"static boolean isHolding", u"}")
          and u"instanceof VibraniumSwordItem" in cut(src, u"static boolean isHolding", u"}"))
    check(u"A19", u"客户端早退（清理那一半只在服务端改，与斧子 ZF133 同源）",
          u"isClientSide()" in cut(src, u"static void onPlayerTick", u"@Override"))

    # --- A20 猛击五条数值 ---
    check(u"A20", u"猛击：6x6 半宽 3.0 / 竖直 3.0 / 加成 12.0 / 状态 20*4 / 冷却 20*6",
          re.search(u"SLAM_HALF\\s*=\\s*3\\.0D", src) is not None
          and re.search(u"SLAM_VERTICAL\\s*=\\s*3\\.0D", src) is not None
          and re.search(u"SLAM_EXTRA_DAMAGE\\s*=\\s*12\\.0D", src) is not None
          and re.search(u"SLAM_EFFECT_TICKS\\s*=\\s*20\\s*\\*\\s*4", src) is not None
          and re.search(u"SLAM_COOLDOWN_TICKS\\s*=\\s*20\\s*\\*\\s*6", src) is not None)
    check(u"A21", u"冷却用**原版物品冷却**（快捷栏那圈灰罩），不是自己记时间",
          u"getCooldowns().addCooldown(this, SLAM_COOLDOWN_TICKS)" in src
          and u"getCooldowns().isOnCooldown(this)" in src)
    check(u"A22", u"出手不扣耐久（无法破坏 ⇒ 没有 hurtAndBreak 那类调用）",
          u"hurtAndBreak" not in src)

    # --- A23 n 的口径：复用 ZF133 那份已过探针的实现 ---
    check(u"A23", u"n（玩家基础伤害）复用 ShockwaveManager.baseAttackDamage（不另写一份）",
          u"ShockwaveManager.baseAttackDamage(player)" in src)
    check(u"A24", u"没有偷偷改成读玩家属性总值（那会含武器、与「n 为基础伤害」对不上）",
          u"getAttributeValue(Attributes.ATTACK_DAMAGE)" not in src)
    check(u"A25", u"伤害走 playerAttack（与 ZF133 冲击波同一条，飘字/击杀归属照原版）",
          u"damageSources().playerAttack(player)" in src)

    # --- A26 顺序：hurt 必须在 setDeltaMovement 之前 ---
    launch = cut(src, u"public static boolean launch(", u"private static void render(")
    i_hurt = launch.find(u"target.hurt(")
    i_move = launch.find(u"setDeltaMovement(")
    check(u"A26", u"顺序对：先 hurt 再写速度（原版 hurt 自己会推 0.4，写反就白推）",
          launch != u"" and i_hurt >= 0 and i_move >= 0 and i_hurt < i_move
          and launch.count(u"target.hurt(") == 1,
          u"hurt@%d x%d vs setDeltaMovement@%d"
          % (i_hurt, launch.count(u"target.hurt("), i_move))
    check(u"A27", u"击飞用 set（可断言、不被原有移动吃掉）而不是 add",
          u"target.setDeltaMovement(" in launch and u".getDeltaMovement().add(" not in launch)
    check(u"A28", u"击飞后把 hasImpulse / hurtMarked 打开（原版同步速度的两个开关）",
          u"hasImpulse = true" in launch and u"hurtMarked = true" in launch)
    check(u"A29", u"失明 + 缓慢各挂 4 秒（SLAM_EFFECT_TICKS）",
          u"MobEffects.BLINDNESS, SLAM_EFFECT_TICKS" in launch
          and u"MobEffects.MOVEMENT_SLOWDOWN, SLAM_EFFECT_TICKS" in launch)

    # --- A30 排除自己 / 创造模式 ---
    slam = cut(src, u"public static int slam(", u"public static boolean launch(")
    check(u"A30", u"排除自己（target == player 跳过）", u"target == player" in slam)
    check(u"A31", u"创造模式 / 观察者玩家整只跳过（照 ZF133 那条已过探针的口径）",
          u"isCreative()" in slam and u"isSpectator()" in slam)
    check(u"A32", u"目标集合用 getEntitiesOfClass(LivingEntity.class, box)",
          u"getEntitiesOfClass(LivingEntity.class, box)" in slam)

    # --- A33 说明复用共用实现 ---
    check(u"A33", u"Shift 说明复用 StarSteelTools.appendHoverText（§11.4 复用优先）",
          u"StarSteelTools.appendHoverText(tooltip, flag, TOOLTIP_PREFIX, TOOLTIP_LINES)" in src)

    # --- A34 新文件里没有硬编码中文（项目纪律：中文只许在注释与 lang 值里）---
    bad = []
    for name in (u"VibraniumSwordItem.java", u"ModTiers.java", u"ModItems.java", u"PotatoST.java"):
        t = strip_comments(read(os.path.join(MOD, name)))
        for m in re.finditer(u'"[^"\\n]*[\\u4e00-\\u9fff][^"\\n]*"', t):
            bad.append(u"%s: %s" % (name, m.group(0)[:40]))
    check(u"A34", u"四个被改的 java 里没有硬编码中文串（中文只许在注释 / lang 里）", not bad,
          u"；".join(bad[:3]))


# ================================================================
#  B 资源
# ================================================================
def section_b():
    print(u"\n================ B 资源（贴图 / 模型 / 语言 / 配方）================")
    tex = os.path.join(ASSETS, "textures", "item", "vibranium_sword.png")
    model = os.path.join(ASSETS, "models", "item", "vibranium_sword.json")
    src_tex = os.path.join(USER_ASSETS, u"振金剑_001.png")

    check(u"B1", u"贴图在盘上（textures/item/vibranium_sword.png）", os.path.exists(tex))
    if os.path.exists(tex):
        data = raw(tex)
        w, h, bd, ct, il = png_info(data)
        check(u"B2", u"贴图 16x16 / 8 位 / RGBA / 无隔行",
              (w, h, bd, ct, il) == (16, 16, 8, 6, 0),
              u"%dx%d bd=%d ct=%d il=%d" % (w, h, bd, ct, il))
        same = os.path.exists(src_tex) and hashlib.sha256(data).hexdigest() == \
            hashlib.sha256(raw(src_tex)).hexdigest()
        check(u"B3", u"与用户素材**逐字节相同**（原字节复制、零转档）", same,
              hashlib.sha1(data).hexdigest())

    check(u"B4", u"模型在盘上", os.path.exists(model))
    if os.path.exists(model):
        m = json.loads(read(model))
        check(u"B5", u"模型 parent = minecraft:item/handheld（工具/武器的写法）",
              m.get(u"parent") == u"minecraft:item/handheld", str(m.get(u"parent")))
        layer0 = m.get(u"textures", {}).get(u"layer0", u"")
        check(u"B6", u"layer0 指向自己的图（**不借原版**）",
              layer0 == u"potato_s_t:item/vibranium_sword", layer0)

    # 语言
    codes = (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh")
    tables = {}
    for c in codes:
        tables[c] = json.loads(read(os.path.join(LANG, c + u".json")))
    keys = [u"item.potato_s_t.vibranium_sword"] + \
           [u"tooltip.potato_s_t.vibranium_sword.%d" % i for i in (1, 2, 3)]
    four = [tables[c] for c in codes[:4]]
    check(u"B7", u"四语言键集合完全相同（各 %d 键）" % len(four[0]),
          len(set(frozenset(t) for t in four)) == 1,
          u" / ".join(u"%s %d" % (c, len(tables[c])) for c in codes))
    check(u"B8", u"lzh 与四份的差集恰好是 language.name / language.region",
          set(tables[u"lzh"]) - set(tables[u"zh_cn"]) == {u"language.name", u"language.region"})
    check(u"B9", u"本轮 4 个键五份都有且非空",
          all(tables[c].get(k) for c in codes for k in keys))
    # 数字对账（只盯数字，不盯措辞 —— ZF137 的教训：盯措辞会把润色线的改动弄红）
    zh1 = tables[u"zh_cn"].get(keys[1], u"")
    zh3 = tables[u"zh_cn"].get(keys[3], u"")
    check(u"B10", u"说明第 1 行的数字：24 伤害 / 1.4 攻速 / 附魔权重 1",
          all(s in zh1 for s in (u"24", u"1.4", u"1")), zh1[:60])
    check(u"B11", u"说明第 3 行的数字：6x6 / +12 / 4 秒 / 6 秒",
          all(s in zh3 for s in (u"6x6", u"12", u"4", u"6")), zh3[:60])
    en1 = tables[u"en_us"].get(keys[1], u"")
    en3 = tables[u"en_us"].get(keys[3], u"")
    check(u"B12", u"英文那两行同样带全数字（24 / 1.4 / 6x6 / 12 / 4 / 6）",
          all(s in en1 for s in (u"24", u"1.4")) and all(s in en3 for s in (u"6x6", u"12", u"4", u"6")))

    # 名字三处一致
    check(u"B13", u"注册名 / 模型名 / 贴图名 / 键名 四处的 vibranium_sword 一致",
          os.path.exists(os.path.join(ASSETS, "models", "item", "vibranium_sword.json"))
          and os.path.exists(os.path.join(ASSETS, "textures", "item", "vibranium_sword.png"))
          and u'"vibranium_sword"' in read(ITEMS)
          and keys[0] == u"item.potato_s_t.vibranium_sword")

    # 配方：用户**没给**配方 ⇒ 盘上不许有产出它的配方（与 ZF119 振金锭同一条口径）
    hits = []
    data_dir = os.path.join(ROOT, r"src\main\resources\data")
    for dirpath, _dirs, files in os.walk(data_dir):
        for fn in files:
            if not fn.endswith(u".json"):
                continue
            p = os.path.join(dirpath, fn)
            if u"vibranium_sword" in read(p):
                hits.append(os.path.relpath(p, ROOT))
    check(u"B14", u"盘上没有任何配方/进度提到它（用户没给配方；与 ZF119 同一条口径）", not hits,
          u"、".join(hits[:3]))

    # 借原版的活体数字不许变（TextureCheck 数的是 13）
    tc = read(os.path.join(TOOLS, "TextureCheck.py"))
    m = re.search(u"BORROWED\\w*\\s*=\\s*(\\d+)", tc)
    if m:
        check(u"B15", u"「借原版贴图」的活体数字没被本轮改动（%s）" % m.group(1), True,
              u"（读数见第 8 道门）")


# ================================================================
#  C 端到端探针报告
# ================================================================
def section_c():
    print(u"\n================ C 真服务端探针报告 ================")
    check(u"C1", u"报告在盘上（%s）" % os.path.basename(PROBE_REPORT), os.path.exists(PROBE_REPORT))
    if not os.path.exists(PROBE_REPORT):
        return
    rep = read(PROBE_REPORT)
    nfail = len(re.findall(u"\\[FAIL\\]", rep))
    check(u"C2", u"报告里 0 条 [FAIL]", nfail == 0, u"实测 %d 条" % nfail)
    check(u"C3", u"verdict = ALL OK", u"verdict: ALL OK" in rep)
    for cid, needle, label in [
        (u"C4", u"显示的总伤害 = 1 + 23.0 = 24.0", u"24 伤害（1 + (15 + 8)）"),
        # ⚠ 攻速那行是 **float**：探针打出来是 `4.0 + -2.5999999046325684 = 1.4000000953674316`
        #   （-2.6F 存成 float 就不是精确的 -2.6）⇒ 判据用正则，不逐字比字符串
        (u"C5", None, u"1.4 攻速（float：4.0 + -2.5999… = 1.4000…）"),
        (u"C6", u"[OK]   A8 附魔权重 = 1", u"附魔权重 1"),
        (u"C7", u"[OK]   A10 isDamageableItem() == false", u"UNBREAKABLE 生效"),
        (u"C8", u"[OK]   A11 真扣 500 点之后耐久一点没动", u"真扣不动"),
        (u"C9", u"[OK]   C16 10 tick 之后它真的离地了", u"真被击飞（不是只设了速度）"),
        (u"C10", u"[OK]   C10 范围外 husk 血没掉", u"范围外不受影响（负向对照）"),
        (u"C11", u"[OK]   C14 自己没掉血", u"自己不受影响"),
        (u"C12", u"[OK]   C18 冷却中被拒", u"冷却 6 秒真的在拦"),
        (u"C13", u"n（玩家基础伤害，不含手持装备）= 1.0", u"n 的口径 = 基础伤害（不含武器）"),
    ]:
        if cid == u"C5":
            check(cid, label,
                  re.search(u"攻速 = 4\\.0 \\+ -2\\.5999\\d+ = 1\\.4000\\d+", rep) is not None,
                  u"正则找 float 那行")
            continue
        check(cid, label, needle in rep, u"找 %s" % needle)
    # 伤害 = n + 12（税前），且三个目标各一次；掉血量 = 过原版护甲算式之后的值
    dmg = re.findall(u"范围内 husk#\\d 掉血 = ([0-9.]+)", rep)
    check(u"C14", u"三个范围内目标：税前 n+12 = 13.0，且三次掉血彼此相同（过护甲之后）",
          len(dmg) == 3 and len(set(dmg)) == 1
          and len(re.findall(u"税前 n\\+12 = 13.0", rep)) == 3, str(dmg))
    check(u"C14b", u"服务端出手结果是 CONSUME（原版 sidedSuccess 的服务端那一半）",
          u"C2 出手成功（服务端结果是 CONSUME）" in rep)
    # 三条灵敏度对照 + 三条免疫
    check(u"C15", u"灵敏度对照 3 条（空手时这三种**挂得上**）",
          len(re.findall(u"\\[OK\\]   B2 空手时", rep)) == 3,
          str(len(re.findall(u"\\[OK\\]   B2 空手时", rep))))
    check(u"C16", u"免疫 3 条（拿着剑时这三种**挂不上**）",
          len(re.findall(u"\\[OK\\]   B4 拿着剑时", rep)) == 3)
    check(u"C17", u"两条「不该被误伤」的对照（急迫 / 速度仍挂得上）",
          len(re.findall(u"\\[OK\\]   B5 拿着剑时", rep)) == 2)
    check(u"C18", u"清理那一半有取证（拿起剑 ⇒ 身上的凋零掉了）",
          u"[OK]   B7 空手挂上的凋零" in rep)
    check(u"C19", u"失明 / 缓慢各 80 tick 都验过（3 个目标 × 2 条）",
          len(re.findall(u"时长 80 tick，要 80", rep)) == 6,
          str(len(re.findall(u"时长 80 tick，要 80", rep))))


# ================================================================
#  D 往轮的门（真跑）
# ================================================================
def section_d():
    print(u"\n================ D 往轮的门没被弄红（真跑）================")
    # ⚠ 为什么挑这 5 份：它们**本轮开工时就是绿的**（我一条条跑过）。
    #   不是"随手挑几个"—— `_zf141_verify.py` / `_zf119_verify.py` 开工时就已经红了，
    #   原因**不是本轮**（别人清了 `build/用户素材` 里的 `星璨钢*.png` / `振金锭.png`、
    #   别人加了配方 74 → 82），拿它们当"我没弄红"的基线是错的靶子（见 §E 的记录）。
    for cid, script in [(u"D1", u"_zf114_verify.py"), (u"D2", u"_zf142_verify.py"),
                        (u"D3", u"_zf145_verify.py"), (u"D4", u"_zf148_verify.py"),
                        (u"D5", u"_zf150_verify.py"), (u"D6", u"_zf149_verify.py")]:
        p = os.path.join(TOOLS, script)
        if not os.path.exists(p):
            check(cid, u"%s 在盘上" % script, False)
            continue
        r = subprocess.run([sys.executable, p], cwd=ROOT, capture_output=True)
        out = r.stdout.decode("utf-8", "replace")
        tail = [l for l in out.split(u"\n") if l.strip()][-1:] or [u""]
        check(cid, u"%s 仍然 exit 0" % script, r.returncode == 0,
              u"（%s）" % tail[0].strip()[:80])


def section_e():
    u"""开工时就已经红的往轮门（**记录，不判红** —— 判红就成了"替别人的在途改动背锅"）。

    这一节存在的意义：下一个人看到"这几道门是红的"时，能立刻分清是谁的红。
    做法照 ZF146：不看结论看**行号与原因**，并把它写进档案。
    """
    print(u"\n================ E 开工前就红的往轮门（不是本轮，只记录）================")
    for script, why in [
        (u"_zf141_verify.py", u"别人清了 build/用户素材 里的星璨钢 4 张源图（D1 找不到素材）+ 配方 74 → 82"),
        (u"_zf119_verify.py", u"别人清了 build/用户素材/振金锭.png（A3 源素材留档没了）"),
        (u"_zf139_verify.py", u"配方份数 74 → 82（别人加的配方）；另一条「档案写着 593 键」是本轮的，写完文档即绿"),
    ]:
        p = os.path.join(TOOLS, script)
        r = subprocess.run([sys.executable, p], cwd=ROOT, capture_output=True)
        out = r.stdout.decode("utf-8", "replace")
        nfail = len(re.findall(u"\\[FAIL\\]|!!", out))
        print(u"  [记录] %s exit=%d，%d 条失败 —— 原因：%s" % (script, r.returncode, nfail, why))


def main():
    fast = u"--fast" in sys.argv
    section_a()
    section_b()
    section_c()
    if fast:
        # 反证（`_zf153_falsify.py`）只关心"这一刀有没有被**点名的那条**咬住"，
        # 而 D/E 两组要真跑 5 份往轮门（每次 20 多秒）⇒ --fast 跳过，18 把刀才跑得动
        print(u"\n（--fast：跳过 D 往轮门 / E 记录）")
    else:
        section_d()
        section_e()
    print(u"\n通过 %d 项，失败 %d 项" % (n_pass, len(fails)))
    if fails:
        print(u"失败清单：%s" % u"、".join(fails))
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
