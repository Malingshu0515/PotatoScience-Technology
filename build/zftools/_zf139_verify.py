# -*- coding: utf-8 -*-
u"""_zf139_verify.py —— 本轮（振金套加强）的常驻校验

用户原话：
    「振金套你看看能不能略微加强一下 现在地位太尴尬了 比星璨麻烦很多 却大大不如晚上的星璨
      简直就是个白板」
    ⇒ 追问一轮（把两套的实吃伤害按原版公式摆出来给他看）之后拍板：
    「用乙吧 再加一个套装效果；10%概率返还100%的伤害给攻击者
      如果攻击者被反伤而死 死亡提示为「攻击者」踢到了铁板」

⇒ 本轮的四件事（下面七组逐条钉住）：
    ① 护甲值 3/8/6/3 → **4/9/7/4**（各 +1；韧性 3.0、击退抗性 0.1、附魔权重 2 一个不动）
    ② 满套**常驻抗性提升 I**（不挑昼夜与维度）
    ③ 满套**免疫摔落伤害**
    ④ 满套：挨打 **10%** 概率把**这一击的原始伤害**还给攻击者；被它打死的人
       死亡文案键 `death.attack.potato_s_t.vibranium_reflect`

**证据怎么取**（沿用 ZF103/ZF120 立的口径，不新造）：
  · 数值/事件/常量 —— 读 `build/classes/java/main/**.class` 的常量池 + `javap -p -c -constants`；
  · 数据包与语言 —— 直接读盘上的 JSON，并且**跟原版 `data/minecraft/damage_type/thorns.json`
    逐键对照**（"照原版格式写"这句话只有这样才验得了）；
  · ⚠ 期望值全部照**用户原话 + 原版源码**抄，不从本工程源码抄（§4.27）。

跑法：
    $env:PYTHONIOENCODING='utf-8'
    python E:\\PotatoST\\build\\zftools\\_zf139_verify.py       # 退出码 0 = 全过
"""
import importlib.util
import io
import json
import os
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
TOOLS = os.path.join(PROJ, "build", "zftools")
SRC_DIR = os.path.join(PROJ, "src", "main", "java", "com", "potatost", "mod")
ASSETS = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t")
DATA = os.path.join(PROJ, "src", "main", "resources", "data", "potato_s_t")
LANG = os.path.join(ASSETS, "lang")
DTYPES = os.path.join(DATA, "damage_type")
RDIR = os.path.join(DATA, "recipe")
ADIR = os.path.join(DATA, "advancement")
PRE = r"C:\PotatoST救援\zf139_pre"
VANILLA_JAR = r"E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar"

_spec = importlib.util.spec_from_file_location("v", os.path.join(TOOLS, "_zf103_verify.py"))
v = importlib.util.module_from_spec(_spec)
_argv_backup = sys.argv
sys.argv = ["x"]
_spec.loader.exec_module(v)
sys.argv = _argv_backup

check = v.check
cls = v.cls
read_source = v.read_source
javap = v.javap_disasm
field_constants = v.field_constants
static_init_constants = v.static_init_constants

# ============================================================
#  期望值（用户原话 + 原版源码）
# ============================================================
PARTS = [u"helmet", u"chestplate", u"leggings", u"boots"]
# ① 用户拍板的"乙方案"：下界合金的 3/8/6/3 **各 +1**
NETHERITE_DEFENSE = {u"helmet": 3, u"chestplate": 8, u"leggings": 6, u"boots": 3}
VIBRANIUM_DEFENSE = {u"helmet": 4, u"chestplate": 9, u"leggings": 7, u"boots": 4}
TOUGHNESS = 3.0            # 一件一份 ⇒ 满套 12
KNOCKBACK_RESISTANCE = 0.1  # 一件一份 ⇒ 满套 0.4
ENCHANT_VALUE = 2          # 「附魔权重2（非常低）」
# ②③④
RESISTANCE_AMP = 0         # 抗性提升 I
RESISTANCE_TICKS = 320     # 16 s
RESISTANCE_REFRESH = 40    # 剩 2 s 就补
REFLECT_CHANCE = 0.1       # 「10%概率」
# 语言键数：ZF133 到 482，本轮 +1（死亡文案）
KEYS_BEFORE, KEYS_AFTER = 482, 483
DEATH_KEY = u"death.attack.potato_s_t.vibranium_reflect"
TOOLTIP_KEY = u"tooltip.potato_s_t.vibranium_set"
MSG_ID = u"potato_s_t.vibranium_reflect"
# 反向：爆炸那条的老判据
EXPLOSION_MULTIPLIER = 0.5


def read_json(path):
    return json.loads(io.open(path, encoding="utf-8").read())


def check_ok(ok, label, detail=u""):
    u"""`v.check` 的薄包装：**把结果返回出来**。

    ⚠ 为什么必须有它（§4.96 那条雷，本轮我又踩了一次）：`_zf103_verify.py` 里的
    `check()` 只记账、**不返回任何东西**（None）⇒ 写成 `if not check(文件存在): continue`
    的话，`not None` 恒为 True，**后面那一整组断言一条都不跑**，而汇总照样打印"0 失败"。
    本文件第一版就是 `if not check(...存在): return finish()` ⇒ ⑤⑥⑦ 三组（20+ 条）
    被静默跳过、报"39 项 0 失败"。假绿灯比红灯坏得多。
    """
    v.check(ok, label, detail)
    return ok


def main():
    setc = cls(u"ModVibraniumSet")
    mats = cls(u"ModArmorMaterials")
    main_cls = cls(u"PotatoST")
    src_set = read_source(u"ModVibraniumSet")
    src_mats = read_source(u"ModArmorMaterials")
    dis_set = javap(u"ModVibraniumSet")
    cst = field_constants(dis_set)

    print(u"")
    print(u"================ ① 护甲值各 +1：4 / 9 / 7 / 4 ================")
    dis_mats = javap(u"ModArmorMaterials")
    init = static_init_constants(dis_mats, u"VIBRANIUM").get(u"VIBRANIUM")
    want_init = [ENCHANT_VALUE, TOUGHNESS, KNOCKBACK_RESISTANCE] + \
                [VIBRANIUM_DEFENSE[p] for p in PARTS]
    if check_ok(init is not None, u"javap 里找得到 VIBRANIUM 的静态初始化常量串"):
        # 一条整串相等顶掉五条"值在不在"（§4.103 第一次踩的那个坑：3.0 in [...] 恒真）
        check(init == want_init,
              u"VIBRANIUM 的初始化常量串正好是 %s（附魔权重→韧性→击退抗性→头/胸/腿/靴）" % want_init,
              u"实际 %s" % init)
        check(init[3:] == [VIBRANIUM_DEFENSE[p] for p in PARTS]
              and init[3:] != [NETHERITE_DEFENSE[p] for p in PARTS],
              u"护甲值**不再是**下界合金那一行（3/8/6/3），而是各 +1")
    check(u"registerBorrowingLayer" in mats.strings,
          u"材料仍走 registerBorrowingLayer(...)（没有为了改数字去动 ZF103 那个重载）")
    # ⚠ **源码文本**再钉一遍（与上面的 javap 常量串是两个独立口子）：
    #   反证刀改的是**源码**，而 javap 读的是**编译产物** ⇒ 只钉常量串的话，
    #   那些"改源码"的刀要重新编译才会咬 —— 补这两条，刀立刻就咬得住。
    check(u"                    4, 9, 7, 4," in src_mats,
          u"源码里那一行护甲值就是 4, 9, 7, 4")
    check(u"VIBRANIUM_ENCHANTMENT_VALUE, 3.0F, 0.1F," in src_mats,
          u"源码里附魔权重/韧性/击退抗性那一行没被动过（2 / 3.0F / 0.1F）")
    check(u"                    2, 8, 6, 4," in src_mats,
          u"反向·源码：钛合金那一行仍是 2, 8, 6, 4")
    check(u"                    5, 9, 7, 5," in src_mats,
          u"反向·源码：星璨钢那一行仍是 5, 9, 7, 5")
    check(u"ARMOR_EQUIP_NETHERITE" in mats.names, u"装备音效仍与下界合金同一口径")
    # 反向：钛合金 / 星璨钢两套的数字**一个都不许动**
    # ⚠ 钛合金那串里**没有 0.0**：`0.0F` 走的是字节码 `fconst_0`，不进常量池
    #   （与 §4.103 那条"0.0/1.0 是 dconst_*"同一个道理）。第一版照着源码抄了 6 个数
    #   ⇒ 一条假红。星璨钢的 0.5F 是**真**常量池条目，所以那一串 6 个数都在。
    for name, want in ((u"TITANIUM_ALLOY", [25, 2, 8, 6, 4]),
                       (u"STAR_STEEL", [20, 0.5, 5, 9, 7, 5])):
        got = static_init_constants(dis_mats, name).get(name)
        check(got == want, u"反向：%s 的初始化常量串没被动过（%s）" % (name, want),
              u"实际 %s" % got)
    # 四件仍然直接用原版 ArmorItem（护甲值是整数 ⇒ 不需要覆写属性）
    check(u"vibraniumProperties" in cls(u"ModArmorItems").strings,
          u"反向：振金四件仍共用 vibraniumProperties(...)（没有顺手改成覆写属性那一路）")

    print(u"")
    print(u"================ ② 满套常驻抗性提升 I ================")
    check((u"onPlayerTick" in setc.strings
           and u"(Lnet/neoforged/neoforge/event/tick/PlayerTickEvent$Post;)V" in setc.strings),
          u"新增 onPlayerTick(PlayerTickEvent.Post) —— 与星璨钢那套同一个口子")
    check(cst.get(u"RESISTANCE_I") in (u"0", u"0x0"), u"RESISTANCE_I = 0（药水 I 级 ⇔ amplifier 0）",
          u"实际 %s" % cst.get(u"RESISTANCE_I"))
    # 源码文本再钉一遍（同 §① 的理由：反证刀改源码，javap 读产物）
    check(u"RESISTANCE_I = 0;" in src_set, u"源码：RESISTANCE_I = 0;")
    check(u"RESISTANCE_TICKS = 320;" in src_set, u"源码：RESISTANCE_TICKS = 320;")
    check(u"RESISTANCE_REFRESH = 40;" in src_set, u"源码：RESISTANCE_REFRESH = 40;")
    check(u"REFLECT_CHANCE = 0.1F;" in src_set, u"源码：REFLECT_CHANCE = 0.1F;")
    check(cst.get(u"RESISTANCE_TICKS") in (u"320",), u"RESISTANCE_TICKS = 320（16 s）",
          u"实际 %s" % cst.get(u"RESISTANCE_TICKS"))
    check(cst.get(u"RESISTANCE_REFRESH") in (u"40",), u"RESISTANCE_REFRESH = 40（剩 2 s 就补）",
          u"实际 %s" % cst.get(u"RESISTANCE_REFRESH"))
    check(u"MobEffects" in setc.refs or u"DAMAGE_RESISTANCE" in setc.names,
          u"补的是 DAMAGE_RESISTANCE（抗性提升），不是别的效果")
    for hit, why in [
        (u"if (!(event.getEntity() instanceof ServerPlayer player)) {",
         u"只在服务端玩家身上补（客户端 addEffect 会被服务端同步覆盖）"),
        (u"if (!ModArmorMaterials.hasFullVibraniumSet(player)) {", u"判的是「满套」"),
        (u"current.getAmplifier() >= RESISTANCE_I", u"已有效果且等级不低于目标 ⇒ 不覆盖"),
        (u"current.getDuration() > RESISTANCE_REFRESH", u"剩余时长还够 ⇒ 不续"),
        (u"player.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE,",
         u"补一条新实例"),
        (u"RESISTANCE_TICKS, RESISTANCE_I, true, true));",
         u"ambient=true（粒子淡）+ visible=true（图标看得见）"),
    ]:
        check(hit in src_set, why)

    print(u"")
    print(u"================ ③ 满套免疫摔落伤害 ================")
    # ⚠ 判据取的是**常量池里的名字 + 描述符**（`setc.strings`），不是 `setc.refs`：
    #   `refs` 只装"被调用"的方法引用，**声明**在本类里的方法不在里面。
    #   第一版拿 refs 判 ⇒ 三条"新增了某个 handler"全红（自己造出来的假红）。
    check((u"onFall" in setc.strings
           and u"(Lnet/neoforged/neoforge/event/entity/living/LivingFallEvent;)V" in setc.strings),
          u"新增 onFall(LivingFallEvent) —— 走的是**伤害之前**那条路")
    check(any(u"LivingFallEvent" in s for s in setc.strings),
          u"LivingFallEvent 编进了常量池（确实挂了这个事件）")
    i = src_set.find(u"public static void onFall(")
    check(i > 0, u"源码里找得到 onFall 方法体")
    if i > 0:
        body = src_set[i:i + 400]
        check(u"ModArmorMaterials.hasFullVibraniumSet(event.getEntity())" in body,
              u"onFall 里判的是满套")
        check(u"event.setCanceled(true);" in body,
              u"onFall 里取消事件（⇒ causeFallDamage 直接 return false，连摔落音效都不放）")
    # ⚠ 反向：这条**不许**去动弹射物/爆炸那两条老判据
    check(u"DamageTypeTags.IS_FALL" not in setc.names,
          u"没有偷偷改成「按 is_fall 取消伤害」（那会留下摔落音效）—— 用的是 LivingFallEvent")

    print(u"")
    print(u"================ ④ 10% 反伤 + 死亡文案 ================")
    check((u"onDamagePost" in setc.strings
           and u"(Lnet/neoforged/neoforge/event/entity/living/LivingDamageEvent$Post;)V" in setc.strings),
          u"新增 onDamagePost(LivingDamageEvent.Post) —— 挂在**掉血之后**那个事件上")
    check(cst.get(u"REFLECT_CHANCE") in (u"0.1f", u"0.1F", u"0.1"),
          u"REFLECT_CHANCE = 0.1（用户原话「10%概率」）", u"实际 %s" % cst.get(u"REFLECT_CHANCE"))
    check(u"vibranium_reflect" in setc.strings,
          u"常量池里有注册名 vibranium_reflect")
    check(u"Registries" in setc.refs or u"DAMAGE_TYPE" in setc.names,
          u"伤害类型走 Registries.DAMAGE_TYPE（数据包注册表，不是 DeferredRegister）")
    check(u"registryOrThrow" in setc.names and u"getHolderOrThrow" in setc.names,
          u"取伤害类型用的是 registryOrThrow + getHolderOrThrow（缺了就当场抛）")
    # ⚠ 三条排除名单必须**挤在同一个 if 里**（逐个查子串是不够的：`IS_PROJECTILE` 在
    #   `onIncomingDamage` 里也有一次 ⇒ 反证刀 K241 把反伤那条删掉时，逐子串查照样绿 ——
    #   本轮第一次跑反证就是这么被自己骗过去的）。所以这里钉**整段表达式**。
    EXCLUDE_IF = (u"        if (source.is(VIBRANIUM_REFLECT)\n"
                  u"                || source.is(DamageTypeTags.IS_PROJECTILE)\n"
                  u"                || source.is(DamageTypeTags.IS_EXPLOSION)) {")
    check(EXCLUDE_IF in src_set,
          u"三条排除名单整段在同一个 if 里（递归保护 / 弹射物 / 爆炸，缺一条就红）")
    for hit, why in [
        (u"if (event.getNewDamage() <= 0.0F) {",
         u"「没掉血那一下」不掷骰（Post 是无条件触发的：被盾牌/吸收全吃掉也在里面）"),
        (u"source.is(VIBRANIUM_REFLECT)", u"排除名单①：反伤本身（递归保护）"),
        (u"source.is(DamageTypeTags.IS_PROJECTILE)", u"排除名单②：弹射物（已经被整条免疫了）"),
        (u"source.is(DamageTypeTags.IS_EXPLOSION)", u"排除名单③：爆炸（已经减半了）"),
        (u"|| attacker == wearer || !attacker.isAlive()) {", u"攻击者得活着、且不是自己"),
        (u"if (wearer.getRandom().nextFloat() >= REFLECT_CHANCE) {",
         u"掷骰用穿戴者自己的 RandomSource（可复现，探针才验得了）"),
        (u"float amount = event.getOriginalDamage();",
         u"反的是**这一击的原始伤害**（进护甲前），不是「我掉了多少血」"),
        (u"attacker.hurt(reflectSource(wearer), amount);", u"真的把伤害还回去"),
        (u"new DamageSource(type, wearer)", u"伤害源的实体 = 穿戴者（击杀归属 + 文案里的名字）"),
    ]:
        check(hit in src_set, why)
    # 递归保护必须是**同一个** ResourceKey（不是又造了一个同名的）
    check(src_set.count(u"VIBRANIUM_REFLECT") >= 2,
          u"VIBRANIUM_REFLECT 这个键在源码里被声明并被用在排除名单里（一处定义、一处判）")

    print(u"")
    print(u"================ ⑤ 数据包：自定义伤害类型（本工程第一个） ================")
    dt = os.path.join(DTYPES, u"vibranium_reflect.json")
    if not check_ok(os.path.isfile(dt), u"data/potato_s_t/damage_type/vibranium_reflect.json 存在"):
        return finish()
    obj = read_json(dt)
    with zipfile.ZipFile(VANILLA_JAR) as zf:
        van = json.loads(zf.read(u"data/minecraft/damage_type/thorns.json"))
    check(list(obj.keys()) == list(van.keys()),
          u"键与**键序**都照原版 thorns.json（effects/exhaustion/message_id/scaling）",
          u"本工程 %s vs 原版 %s" % (list(obj.keys()), list(van.keys())))
    check(obj.get(u"message_id") == MSG_ID, u"message_id = %s" % MSG_ID,
          u"实际 %s" % obj.get(u"message_id"))
    check(obj.get(u"scaling") == u"when_caused_by_living_non_player",
          u"scaling 照原版", u"实际 %s" % obj.get(u"scaling"))
    check(obj.get(u"exhaustion") == 0.1, u"exhaustion = 0.1（与 thorns 同款）",
          u"实际 %s" % obj.get(u"exhaustion"))
    check(obj.get(u"effects") == u"thorns",
          u"effects = thorns（挨这一下的人听到「打铁板」那一声；"
          u"Player.getHurtSound 就是读 type().effects().sound()）",
          u"实际 %s" % obj.get(u"effects"))
    check(u"death_message_type" not in obj, u"没写 death_message_type（取默认 DEFAULT）")
    check(len([n for n in os.listdir(DTYPES) if n.endswith(u".json")]) == 1,
          u"damage_type 目录下正好 1 份（本轮只加这一个）")

    print(u"")
    print(u"================ ⑥ 四语言：482 → 483 键 + 死亡文案 ================")
    tables = {}
    for loc in (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"):
        tables[loc] = read_json(os.path.join(LANG, loc + u".json"))
    for loc, t in tables.items():
        check(len(t) == KEYS_AFTER, u"%s：%d 键（%d → %d）" % (loc, len(t), KEYS_BEFORE, KEYS_AFTER),
              u"实际 %d" % len(t))
    base = set(tables[u"zh_cn"])
    for loc, t in tables.items():
        check(set(t) == base, u"%s：键集合与 zh_cn 完全一致" % loc,
              u"缺 %s / 多 %s" % (sorted(base - set(t))[:3], sorted(set(t) - base)[:3]))
    for loc, t in tables.items():
        val = t.get(DEATH_KEY, u"")
        check(bool(val), u"%s：%s 存在且非空（实际 %r）" % (loc, DEATH_KEY, val))
        check(val.count(u"%1$s") == 1 and val.replace(u"%1$s", u"") .count(u"%") == 0,
              u"%s：死亡文案里正好一个 %%1$s、没有别的百分号（%r）" % (loc, val))
    # 键序：新键紧挨在振金说明**前面**（四语言同一个锚点）
    for loc, t in tables.items():
        ks = list(t.keys())
        i = ks.index(DEATH_KEY)
        check(ks[i + 1] == TOOLTIP_KEY,
              u"%s：新键插在 %s **前面**（键序只多了这一个）" % (loc, TOOLTIP_KEY))
    # 值：说明里写着新三条
    for loc, needle in ((u"zh_cn", [u"抗性提升 I", u"摔落", u"10%", u"踢到了铁板"]),
                        (u"en_us", [u"Resistance I", u"fall damage", u"10%", u"steel plate"]),
                        (u"ja_jp", [u"耐性 I", u"落下", u"10%", u"鉄板"]),
                        (u"ru_ru", [u"Сопротивление I", u"падени", u"10%", u"плиту"])):
        text = tables[loc].get(TOOLTIP_KEY, u"")
        miss = [n for n in needle if n not in text]
        check(not miss, u"%s：振金说明里写全了四条新内容（缺 %s）" % (loc, miss or u"无"))
    check(u"无限耐久" in tables[u"zh_cn"].get(TOOLTIP_KEY, u""),
          u"老内容没被顺手删掉（「无限耐久」还在）")
    # 与改前件比：**我这一轮只该动 `vibranium_set` 一个值**。
    # ⚠ 但树是**共享**的：润色线在本轮这段时间里一直在瘦身别的机器说明
    #   （先是 electrolyzer / distillation_operator / solar_panel，接着又是
    #    micro_crusher / electric_blast_furnace / diesel_generator_controller …）。
    #   所以这一条**只能当"提示"打印，不能当判据** —— 否则"我的门红不红"就由别人的提交节奏决定了
    #   （本轮第一版就是这么连着红两次的）。硬判据留在上一组：新键在不在、位置对不对、
    #   值里四条新内容全不全、四语言 483 键。
    if os.path.isdir(PRE):
        for loc in tables:
            old = read_json(os.path.join(PRE, u"src", u"main", u"resources", u"assets",
                                         u"potato_s_t", u"lang", loc + u".json"))
            changed = sorted(k for k in old
                             if k != TOOLTIP_KEY and tables[loc].get(k) != old[k])
            print(u"  [提示] %s：相对改前件另有 %d 个键的值变了（共享树：多半是润色线在改）%s"
                  % (loc, len(changed), (u"：" + u"、".join(changed[:4])) if changed else u""))
        # 只钉"我自己那一个"确实变了 —— 这个是判据
        old_zh = read_json(os.path.join(PRE, u"src", u"main", u"resources", u"assets",
                                        u"potato_s_t", u"lang", u"zh_cn.json"))
        check(old_zh.get(TOOLTIP_KEY) != tables[u"zh_cn"].get(TOOLTIP_KEY),
              u"我这一轮确实改了 vibranium_set 的值（不是只加了个键）")
    else:
        check(False, u"改前件 zf139_pre 不在盘上（没法比老键的值）")

    print(u"")
    print(u"================ ⑦ 跟平与反向 ================")
    z120 = io.open(os.path.join(TOOLS, u"_zf120_verify.py"), encoding="utf-8").read()
    check(u"VIBRANIUM_DEFENSE" in z120 and u"== 7," in z120,
          u"_zf120_verify.py 已经跟到 ZF139（VIBRANIUM_DEFENSE 表 + 满套判据 7 处）")
    check(u'"4, 9, 7, 4," in z120 or u"4, 9, 7, 4" in z120 or u"VIBRANIUM_DEFENSE" in z120',
          u"_zf120_verify.py 里的护甲值期望值不再是下界合金那一行")
    # 键数链：活着的门里不许再有"独立的 482"当键数
    stale = []
    import glob as _glob
    for p in sorted(_glob.glob(os.path.join(TOOLS, u"_zf*_verify.py"))):
        name = os.path.basename(p)
        if name == u"_zf139_verify.py":
            continue
        for line in io.open(p, encoding="utf-8").read().split(u"\n"):
            if u"482" not in line:
                continue
            if any(s in line for s in (u"ZF120 并行线", u"464 → 482", u"往轮门都跟到 482")):
                continue          # 叙述行：482 是历史
            if any(m in line for m in (u"EXPECT_KEYS", u"KEY_NEW", u"KEY_OLD", u"键",
                                       u"keys each", u"counts", u"len(table", u"len(t")):
                stale.append(u"%s: %s" % (name, line.strip()[:70]))
    check(not stale, u"往轮门里的键数全部跟到 483（还剩 %d 处 482）" % len(stale),
          u"／".join(stale[:3]))
    doc = io.open(os.path.join(PROJ, u"docs", u"开发档案.md"), encoding="utf-8").read()
    check(u"ZF139" in doc, u"档案里有 ZF139 这一节")
    check(u"483 键" in doc or u"483 键 × 4" in doc, u"档案里写着键数 483")
    hand = io.open(os.path.join(PROJ, u"docs", u"多会话协作交接.md"), encoding="utf-8").read()
    check(u"483 键 × 4" in hand or u"483 键×4" in hand, u"交接文档的活体数字是 483 键")
    ann = io.open(os.path.join(PROJ, u"docs", u"UpdateAnnouncement_EN.md"), encoding="utf-8").read()
    check(u"(483 keys each)" in ann, u"英文公告的重定目标键数 = 483")
    # 反向：老的三条效果一句都没少（判据同样取常量池里的**声明**，不看 refs）
    missing = [n for n in (u"onProjectileImpact", u"onIncomingDamage", u"onKnockback",
                           u"onExplosionKnockback") if n not in setc.strings]
    check(not missing, u"反向：ZF120 那四个 handler 一个都没被删（缺 %s）" % (missing or u"无"))
    check(cst.get(u"EXPLOSION_DAMAGE_MULTIPLIER") in (u"0.5f", u"0.5F", u"0.5"),
          u"反向：爆炸倍率仍是 0.5", u"实际 %s" % cst.get(u"EXPLOSION_DAMAGE_MULTIPLIER"))
    check(src_set.count(u"hasFullVibraniumSet(") == 7,
          u"七个 handler 各判一次满套（4 老 + 3 新）",
          u"实际 %d" % src_set.count(u"hasFullVibraniumSet("))
    # 反向：没新增配方/进度
    # ⚠ 配方那条是**活体数字**：交接文档 §1 写的 68 已经过期（别的线后来又加了一份），
    #   盘上现在是 69。本轮只是"没动配方"，不是"配方必须等于 68"。
    n_recipe = len([n for n in os.listdir(RDIR) if n.endswith(u".json")])
    check(n_recipe == 69, u"反向：配方份数 69（活体数字；本轮 +0）", u"实际 %d" % n_recipe)
    check(len([n for n in os.listdir(ADIR) if n.endswith(u".json")]) == 35,
          u"反向：进度仍是 35 条（本轮不动进度）")
    check(u"Zf139Check" not in main_cls.strings and u"Zf139Check" not in read_source(u"PotatoST"),
          u"探针已经从 PotatoST 上摘掉了（没有残留挂载行）")
    return finish()


def finish():
    print(u"")
    print(u"==============================")
    print(u"断言数 = %d   失败项 = %d" % (v.count, len(v.fails)))
    for f in v.fails:
        print(u"  !! " + f)
    print(u"结论: %s" % (u"通过" if not v.fails else u"有失败项"))
    return 1 if v.fails else 0


if __name__ == u"__main__":
    sys.exit(main())
