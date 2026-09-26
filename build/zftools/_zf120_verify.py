# -*- coding: utf-8 -*-
u"""_zf120_verify.py —— 本轮（振金套）的常驻校验

用户这一轮的原话（逐条对应到下面的组）：
    「加个振金套 基础数据与下界合金一致 只不过全套都是无限耐久 附魔权重2（非常低）
      自带附魔纹理 贴图先用铁套
      套装效果；1，穿戴者免疫弹射物攻击并反弹任何弹射物（如果可以反弹的话）
      2，降低爆炸伤害50%  免疫任何击退」
    （配方那一条是随后的答复：「照抄原版下界合金的锻造台配方，只不过是钛合金作为升级基底」）

**证据怎么取**（沿用 ZF103 立的口径，不新造）：
  · 数值/组件/事件 —— 读 `build/classes/java/main/**.class` 的常量池 + 字节码立即数
    + `javap -p -c -constants` 的指令流。理由：源码里写错一个字、或某处被注释掉，
    grep 源码看不出来，而常量池只装"真的编进去了"的东西。
  · 那些**不进常量池**的字面量（0.0/1.0 是 dconst_*、小整数是 bipush/sipush、
    静态常量走 `javap -constants` 的字段声明行）分别用 `num()` / `bc_ints` /
    `field_constants()` 三个口子取 —— 这正是 ZF103 首跑 26 条假 FAIL 的教训。
  · 贴图/配方/语言 —— 直接读盘上的文件，配方还跟 **client.jar 里那张原版下界合金配方
    逐字段对照**（"照抄原版"这句话只有这样才验得了）。

⚠ 反证原则（档案 §4.27）：下面的 EXPECT 表全部照**用户原话 + 原版源码**抄，
   不是从本工程的源码抄；从源码抄的话，源码改坏探针跟着变，等于没检查。

跑法：
    $env:PYTHONIOENCODING='utf-8'
    python E:\\PotatoST\\build\\zftools\\_zf120_verify.py       # 退出码 0 = 全过
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
RDIR = os.path.join(PROJ, "src", "main", "resources", "data", "potato_s_t", "recipe")
LANG = os.path.join(ASSETS, "lang")
VANILLA_JAR = r"E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar"

# ⚠ 复用 ZF103 那套取证工具（常量池解析 / 字节码立即数 / javap / call_arg_sequences）。
#   不重写一遍的理由：那套东西的坑（CONSTANT_End 占位、double 占两格、dconst_*）
#   已经踩过并写在它的注释里，抄一份出来等于把坑再挖一遍。
#   `_zf103_dump.py` 是同一个用法（ZF103 起就有先例）。它自己在 `__main__` 里才跑断言。
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
call_arg_sequences = v.call_arg_sequences
static_init_constants = v.static_init_constants


def check_ok(ok, label, detail=u""):
    u"""`v.check` 的薄包装：**把结果返回出来**。

    ⚠ 为什么必须有它：`_zf103_verify.py` 里的 `check()` 只记账、**不返回任何东西**（返回 None），
    所以 `if not check_ok(文件存在): continue` 这种写法会**永远走 continue** ——
    本轮第一次跑就是这样：探针报"77 断言 0 失败"，看着全绿，
    实际后面 30+ 条"文件存在才继续"的断言**一条都没跑**。
    假绿灯比红灯坏得多（档案 §4.53 那条的兄弟）。
    """
    v.check(ok, label, detail)
    return ok

# ============================================================
#  期望值（照用户原话 + 原版源码抄）
# ============================================================
# 「基础数据与下界合金一致」。
#   护甲值/韧性/击退抗性 来自 ArmorMaterials.java:70-76 的 NETHERITE 那一行；
#   耐久 = ArmorItem.Type 的部位基数 × 材料系数 37（11/16/15/13 × 37，见 ArmorItem.java:150-153）。
PARTS = [u"helmet", u"chestplate", u"leggings", u"boots"]
NETHERITE_DURABILITY = {u"helmet": 407, u"chestplate": 592, u"leggings": 555, u"boots": 481}
NETHERITE_DEFENSE = {u"helmet": 3, u"chestplate": 8, u"leggings": 6, u"boots": 3}
# ⚠ ZF139：振金不再"与下界合金一致"，而是**各 +1**（用户拍板的"乙方案"）——
#   这两个表都留着：NETHERITE_* 是"原版那一行"的取证底稿，VIBRANIUM_* 才是本轮期望值。
VIBRANIUM_DEFENSE = {u"helmet": 4, u"chestplate": 9, u"leggings": 7, u"boots": 4}
NETHERITE_TOUGHNESS = 3.0
NETHERITE_KNOCKBACK_RESISTANCE = 0.1
# 「附魔权重2（非常低）」
VIBRANIUM_ENCHANT = 2
# 「自带附魔纹理」= 附魔光效（glint），1.21.1 里由这两个数据组件表达
GLINT_COMPONENTS = [u"UNBREAKABLE", u"ENCHANTMENT_GLINT_OVERRIDE"]

fails = []


def read_json(path):
    return json.loads(io.open(path, encoding="utf-8").read())


def main():
    items = cls(u"ModArmorItems")
    mats = cls(u"ModArmorMaterials")
    setc = cls(u"ModVibraniumSet")
    piece = cls(u"ModVibraniumPiece")
    main_cls = cls(u"PotatoST")
    moditems = cls(u"ModItems")
    # 源码文本：几处"只查名字查不出来"的判据要用它（语句还在、但里面的东西被换掉）
    src_mats = read_source(u"ModArmorMaterials")
    src_set = read_source(u"ModVibraniumSet")

    print(u"")
    print(u"================ ① 注册：4 件 + 创造页 ================")
    for part in PARTS:
        ident = u"vibranium_" + part
        check(ident in items.strings, u"ModArmorItems 里有注册名 %s" % ident)
        check(ident in main_cls.strings or ident in moditems.strings or ident in items.strings,
              u"注册名 %s 出现在常量池（进的是 ModItems.ITEMS）" % ident)
        field = u"VIBRANIUM_" + part.upper()
        check(field in moditems.names,
              u"ModItems 引用字段 %s（创造页 output.accept 的落点）" % field,
              u"名字池里没有 %s" % field)
    check(u"registerVibranium" in items.strings,
          u"注册走的是 registerVibranium(...)（与前两套的参数表不同，故意分开写）")

    print(u"")
    print(u"================ ② 基础数据 = 下界合金各 +1（材料里，ZF139）================")
    check(u"vibranium" in mats.strings, u"材料注册名 vibranium 编进常量池")
    check(u"ARMOR_EQUIP_NETHERITE" in mats.names,
          u"装备音效用下界合金的（与「基础数据一致」同一口径）")
    check(u"registerBorrowingLayer" in mats.strings,
          u"材料走 registerBorrowingLayer(...) 这个重载（贴图借原版那一类）")
    dis_mats = javap(u"ModArmorMaterials")
    init = static_init_constants(dis_mats, u"VIBRANIUM").get(u"VIBRANIUM")
    check(init is not None, u"javap 里找得到 VIBRANIUM 的静态初始化常量串")
    want_def = [VIBRANIUM_DEFENSE[p] for p in PARTS]
    want_init = [VIBRANIUM_ENCHANT, NETHERITE_TOUGHNESS, NETHERITE_KNOCKBACK_RESISTANCE] + want_def
    if init is not None:
        # ⚠ **一条整串相等**顶掉五条"值在不在"。
        #   分开查会漏：`3.0 in [2, 0.0, 0.1, 3, 8, 6, 3]` 在 Python 里是 **True**
        #   —— 因为头盔护甲值就是 3，而 `3.0 == 3`。K2 那一刀（韧性 3.0 → 0.0）
        #   第一轮就是这么**没被咬住**的（反证脚本当时报 [FAIL] K2）。
        #   整串比还顺手把"参数顺序串了"一起管住。
        check(init == want_init,
              u"VIBRANIUM 的初始化常量串正好是 %s（附魔权重 → 韧性 → 击退抗性 → 头/胸/腿/靴）"
              % want_init,
              u"实际 %s" % init)

    print(u"")
    print(u"================ ③ 无限耐久 + 自带附魔光效（数据组件） ================")
    for comp in GLINT_COMPONENTS:
        check(comp in items.names, u"ModArmorItems 引用了数据组件 %s" % comp)
    check(any(s.endswith(u"/Unbreakable") for s in items.strings),
          u"UNBREAKABLE 用的是 Unbreakable 记录（带 showInTooltip 的那个）")
    check(u"vibraniumProperties" in items.strings,
          u"四件共用 vibraniumProperties(...)（一个口子改，不会漏一件）")
    dis_items = javap(u"ModArmorItems")
    seqs = call_arg_sequences(dis_items, u"registerVibranium")
    check(len(seqs) == 4, u"registerVibranium 被调了 4 次（实际 %d）" % len(seqs))
    got = {}
    for s in seqs:
        part = [x for x in s if x in (u"HELMET", u"CHESTPLATE", u"LEGGINGS", u"BOOTS")]
        num = [x for x in s if x.lstrip(u"-").isdigit()]
        if part and num:
            got[part[0]] = int(num[-1])
    for part in PARTS:
        want = NETHERITE_DURABILITY[part]
        check(got.get(part.upper()) == want,
              u"registerVibranium(%s) 的耐久 = %d（下界合金同款；玩家看不到但可附魔的前提）"
              % (part, want),
              u"调用点取到的是 %s" % got)
    for part in PARTS:
        want = NETHERITE_DURABILITY[part]
        check(want in items.bc_ints or want in items.ints,
              u"耐久 %d 真的编进了字节码（sipush/常量池）" % want)

    print(u"")
    print(u"================ ④ 三条套装效果（ModVibraniumSet） ================")
    handlers = [
        (u"onProjectileImpact",
         u"(Lnet/neoforged/neoforge/event/entity/ProjectileImpactEvent;)V",
         u"① 弹射物命中（免疫 + 反弹）"),
        (u"onIncomingDamage",
         u"(Lnet/neoforged/neoforge/event/entity/living/LivingIncomingDamageEvent;)V",
         u"① 兜底免疫 + ② 爆炸减伤"),
        (u"onKnockback",
         u"(Lnet/neoforged/neoforge/event/entity/living/LivingKnockBackEvent;)V",
         u"③ 受击击退"),
        (u"onExplosionKnockback",
         u"(Lnet/neoforged/neoforge/event/level/ExplosionKnockbackEvent;)V",
         u"③ 爆炸击退"),
        # ---- ZF139 加的三条 ----
        (u"onPlayerTick",
         u"(Lnet/neoforged/neoforge/event/tick/PlayerTickEvent$Post;)V",
         u"④ 满套常驻抗性提升 I"),
        (u"onFall",
         u"(Lnet/neoforged/neoforge/event/entity/living/LivingFallEvent;)V",
         u"⑤ 满套免疫摔落伤害"),
        (u"onDamagePost",
         u"(Lnet/neoforged/neoforge/event/entity/living/LivingDamageEvent$Post;)V",
         u"⑥ 10% 反伤"),
    ]
    for name, desc, why in handlers:
        # ⚠ 只查常量池（strings），**不要**用 `read_class_methods`（`p.methods`）——
        #   那个函数是坏的（ZF103 起就在，实测把方法名读成了类名/读成空表），
        #   ZF103 的探针从头到尾也只用 `strings` 取方法名与描述符，我这个探针跟着它走。
        #   方法名与它的描述符都是 Utf8 常量池条目 ⇒ "名字在 + 描述符在"能钉住事件类型。
        check(name in setc.strings and desc in setc.strings,
              u"%s —— %s（方法名 + 描述符都在常量池里）" % (name, why),
              u"名字 %s / 描述符 %s" % (name in setc.strings, desc in setc.strings))
    check(u"hasFullVibraniumSet" in setc.names, u"三条效果都先判「满套振金」")
    # 四个 handler 各判一次 —— 少了任何一处（比如弹射物那条忘了判）都要报出来。
    # 为什么用"数次数"而不是逐个方法解析：这四个方法体都很短，少一处 = 计数少一，
    # 而"删掉某个 handler 里那次判据"正是最容易漏的那种改法（K16 就是砍的这一刀）。
    # ZF139 起是 **7** 处：弹射物 / 兜底+爆炸 / 受击击退 / 爆炸击退 /
    #                        常驻抗性 / 免摔落 / 反伤
    check(src_set.count(u"hasFullVibraniumSet(") == 7,
          u"七个 handler 各判了一次满套（共 7 次调用）",
          u"实际 %d 次" % src_set.count(u"hasFullVibraniumSet("))
    check(u"hasFullVibraniumSet" in mats.names or u"hasFullVibraniumSet" in mats.strings,
          u"ModArmorMaterials 自己声明了 hasFullVibraniumSet（唯一实现）")
    # 「满套」的语义落在 ModArmorMaterials.hasFullSet 里：四个槽**逐个**判、有一个不对就 false。
    # 只看"方法在不在"是抓不住"取反写反"的（那会变成"至少一件就算满套"），
    # 所以这里按**源码结构**钉住那两行的形状（K15 就是砍的这一刀）。
    check(u"if (!isMaterial(entity.getItemBySlot(slot), material)) {" in src_mats
          and u"for (EquipmentSlot slot : ARMOR_SLOTS) {" in src_mats,
          u"hasFullSet = 「四个槽逐个判、有一个不对就 false」（不是「至少一件」）")
    # 「反弹」用的是原版 deflection 机制
    check((u"deflect", u"(Lnet/minecraft/world/entity/projectile/ProjectileDeflection;"
                       u"Lnet/minecraft/world/entity/Entity;Lnet/minecraft/world/entity/Entity;Z)Z")
          in setc.refs,
          u"调的是 Projectile.deflect(ProjectileDeflection, Entity, Entity, boolean)")
    check(u"REVERSE" in setc.names, u"用的是 ProjectileDeflection.REVERSE（沿原路弹回、速度减半）")
    check(u"setCanceled" in setc.names, u"命中被取消（取消 = 不结算伤害、不插在身上）")
    # 两条伤害规则靠伤害源标签
    check(u"IS_PROJECTILE" in setc.names, u"弹射物免疫按 #minecraft:is_projectile 判")
    check(u"IS_EXPLOSION" in setc.names, u"爆炸减伤按 #minecraft:is_explosion 判")
    check(u"setAmount" in setc.names, u"爆炸减伤改的是「待结算伤害」（setAmount）")
    check(u"setKnockbackVelocity" in setc.names,
          u"爆炸击退用 setKnockbackVelocity 置零（那个事件不可取消）")
    check(u"ZERO" in setc.names, u"置零用的是 Vec3.ZERO")
    cst = field_constants(javap(u"ModVibraniumSet"))
    check(cst.get(u"EXPLOSION_DAMAGE_MULTIPLIER") in (u"0.5f", u"0.5F", u"0.5"),
          u"EXPLOSION_DAMAGE_MULTIPLIER = 0.5（javap -constants 的字段值）",
          u"实际 %s" % cst.get(u"EXPLOSION_DAMAGE_MULTIPLIER"))
    for hit, why in [
        (u"@EventBusSubscriber(modid = PotatoST.MODID)", u"挂在游戏事件总线上"),
        (u"projectile.deflect(ProjectileDeflection.REVERSE, wearer, wearer, true)",
         u"反弹那一句（实体=穿戴者、新的 owner 也是穿戴者 ⇒ 击杀算玩家的）"),
        (u"projectile.getDeltaMovement().dot(outward) <= 0.0",
         u"第二帧保护：已经朝外飞的就只取消命中、不再翻转（否则会在身上来回抖）"),
        (u"event.setAmount(event.getAmount() * EXPLOSION_DAMAGE_MULTIPLIER)",
         u"爆炸减半那一句"),
        (u"event.setCanceled(true)", u"取消命中/取消伤害"),
        (u"event.setKnockbackVelocity(Vec3.ZERO)", u"爆炸击退置零那一句"),
    ]:
        check(hit in src_set, why)

    print(u"")
    print(u"================ ⑤ 贴图：先用原版铁套 ================")
    with zipfile.ZipFile(VANILLA_JAR) as zf:
        vanilla_names = set(zf.namelist())
    for part in PARTS:
        mp = os.path.join(ASSETS, u"models", u"item", u"vibranium_%s.json" % part)
        if not check_ok(os.path.isfile(mp), u"背包模型 vibranium_%s.json 存在" % part):
            continue
        obj = read_json(mp)
        want = u"minecraft:item/iron_%s" % part
        check(obj.get(u"parent") == u"minecraft:item/generated",
              u"vibranium_%s 走 item/generated" % part)
        check(obj.get(u"textures", {}).get(u"layer0") == want,
              u"vibranium_%s 的 layer0 = %s（用户原话「贴图先用铁套」）" % (part, want),
              u"实际 %s" % obj.get(u"textures", {}).get(u"layer0"))
        png = u"assets/minecraft/textures/item/iron_%s.png" % part
        check(png in vanilla_names, u"原版真的提供了 %s（借得到）" % png)
    # 身上那一层：材料的 Layer 显式指向 minecraft:iron
    check(u'ResourceLocation.fromNamespaceAndPath("minecraft", "iron")' in src_mats,
          u"材料 Layer 显式写 minecraft:iron（**不用** withDefaultNamespace 那种隐式写法）")
    # ⚠ 这条判据必须看**常量池**而不是源码文本：源码里那句注释也写着 withDefaultNamespace
    #   （本轮第一版就是拿 `in src_mats` 判的 ⇒ 被自己的注释绊了一跤，假 FAIL）。
    #   与 `_zf103_verify.py` 里 K6/K10 那两把刀的判据保持同一个口子。
    check(not any(n == u"withDefaultNamespace" for n, _d in mats.refs),
          u"本类里没有一处 withDefaultNamespace 调用（K6/K10 那两把刀的判据保持不变）")
    for layer in (1, 2):
        png = u"assets/minecraft/textures/models/armor/iron_layer_%d.png" % layer
        check(png in vanilla_names, u"原版盔甲图层 %s 存在" % png)

    print(u"")
    print(u"================ ⑥ 配方：照抄原版下界合金的锻造台配方 ================")
    with zipfile.ZipFile(VANILLA_JAR) as zf:
        for part in PARTS:
            van = json.loads(zf.read(u"data/minecraft/recipe/netherite_%s_smithing.json" % part))
            p = os.path.join(RDIR, u"vibranium_%s_smithing.json" % part)
            if not check_ok(os.path.isfile(p), u"配方 vibranium_%s_smithing.json 存在" % part):
                continue
            mine = read_json(p)
            check(mine.get(u"type") == van.get(u"type") == u"minecraft:smithing_transform",
                  u"%s：type 与原版一致（smithing_transform）" % part)
            check(list(mine.keys()) == list(van.keys()),
                  u"%s：字段集合与**键序**都照抄原版" % part,
                  u"本工程 %s vs 原版 %s" % (list(mine.keys()), list(van.keys())))
            check(mine.get(u"template") == van.get(u"template"),
                  u"%s：模板 = 原版下界合金升级模板（用户只说基底改成钛合金）" % part,
                  u"实际 %s" % mine.get(u"template"))
            check(mine.get(u"base", {}).get(u"item") == u"potato_s_t:titanium_alloy_%s" % part,
                  u"%s：基底 = 同部位的钛合金件（用户点名的那一处）" % part,
                  u"实际 %s" % mine.get(u"base"))
            check(mine.get(u"addition", {}).get(u"item") == u"potato_s_t:vibranium_ingot",
                  u"%s：添加物 = 振金锭" % part)
            check(mine.get(u"result") == {u"count": 1, u"id": u"potato_s_t:vibranium_%s" % part},
                  u"%s：产物 = 振金件 ×1" % part)
    check(len([n for n in os.listdir(RDIR)
               if n.startswith(u"vibranium_") and n.endswith(u".json")]) == 4,
          u"盘上振金配方正好 4 张")

    print(u"")
    print(u"================ ⑦ 语言：四语言各 5 键 ================")
    want_keys = [u"item.potato_s_t.vibranium_%s" % p for p in PARTS] \
                + [u"tooltip.potato_s_t.vibranium_set"]
    for lang in (u"zh_cn.json", u"en_us.json", u"ja_jp.json", u"ru_ru.json"):
        obj = read_json(os.path.join(LANG, lang))
        miss = [k for k in want_keys if not obj.get(k)]
        check(not miss, u"%s：5 个振金键都在且非空（缺 %s）" % (lang, miss or u"无"))
        if lang == u"zh_cn.json":
            check(u"无限耐久" in obj.get(want_keys[0], u"") + obj.get(want_keys[-1], u""),
                  u"zh_cn 说明里写着「无限耐久」（用户原话里的要求）")

    print(u"")
    print(u"==============================")
    print(u"断言数 = %d   失败项 = %d" % (v.count, len(v.fails)))
    for f in v.fails:
        print(u"  !! " + f)
    print(u"结论: %s" % (u"通过" if not v.fails else u"有失败项"))
    return 1 if v.fails else 0


if __name__ == "__main__":
    sys.exit(main())
