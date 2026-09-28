# -*- coding: utf-8 -*-
u"""_zf153_falsify.py —— ZF153 的反证：**每一把刀都必须被点名的那一条判据咬住**

判据不能只证明"现在是绿的"：一条永远绿的判据等于没有判据（§11.1）。所以这里逐把
往被测对象上砍一刀，要求 `_zf153_verify.py` **点名的那一条**变红 —— 只红不点名不算数
（"别的地方碰巧红了"完全可能是别的原因）。

18 把刀覆盖七条需求：
    数值          附魔权重 / 伤害参数 / 攻速参数 / 耐久 / 猛击加成 / 状态时长 / 冷却
    无法破坏      UNBREAKABLE 组件 / 偷偷加 .durability / 偷偷 hurtAndBreak
    免疫          结果枚举 / 免疫表混进别的东西 / 客户端早退 / 两处监听
    猛击          排除自己 / 排除创造模式 / 顺序（hurt 必须在写速度之前）/ n 的口径
    资源          贴图被人动过 / 模型借原版 / 语言缺键 / 语言数字对不上 / 悄悄加配方
    纪律          硬编码中文串

每把刀：① 精确替换（锚点必须**正好一次**）→ ② 跑 `_zf153_verify.py --fast` →
③ 要求 `[FAIL] <点名 id>` 真的出现 → ④ **逐字节还原**并复核 sha256。

跑法：python build\\zftools\\_zf153_falsify.py
"""
import hashlib
import io
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, r"build\zftools")
VERIFY = os.path.join(TOOLS, "_zf153_verify.py")
MOD = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
LANG = os.path.join(ASSETS, "lang")

SWORD = os.path.join(MOD, "VibraniumSwordItem.java")
TIERS = os.path.join(MOD, "ModTiers.java")
ITEMS = os.path.join(MOD, "ModItems.java")
PMAIN = os.path.join(MOD, "PotatoST.java")
TEX = os.path.join(ASSETS, r"textures\item\vibranium_sword.png")
MODEL = os.path.join(ASSETS, r"models\item\vibranium_sword.json")
NEWRECIPE = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe\zf153_knife.json")

# (名字, 文件, 原文, 换成, 必须变红的判据 id)
KNIVES = [
    (u"K01 附魔权重 1 → 22", TIERS,
     u"VIBRANIUM_ENCHANTMENT_VALUE = 1;", u"VIBRANIUM_ENCHANTMENT_VALUE = 22;", u"A3"),
    (u"K02 伤害参数 15 → 14", TIERS,
     u"VIBRANIUM_SWORD_DAMAGE = 15.0F;", u"VIBRANIUM_SWORD_DAMAGE = 14.0F;", u"A4"),
    (u"K03 攻速 -2.6 → -2.4", TIERS,
     u"VIBRANIUM_SWORD_SPEED_MODIFIER = -2.6F;", u"VIBRANIUM_SWORD_SPEED_MODIFIER = -2.4F;", u"A4"),
    (u"K04 档位耐久 2031 → 1192", TIERS,
     u"VIBRANIUM_TOOL = build(2031,", u"VIBRANIUM_TOOL = build(1192,", u"A4"),
    (u"K05 摘掉 UNBREAKABLE（就不「无法破坏」了）", ITEMS,
     u".component(DataComponents.UNBREAKABLE, new Unbreakable(true))\n", u"", u"A8"),
    (u"K06 偷偷给物品加 .durability(1000)", ITEMS,
     u"new VibraniumSwordItem(new Item.Properties()",
     u"new VibraniumSwordItem(new Item.Properties().durability(1000)", u"A11"),
    (u"K07 创造页那行删掉（§4.82 的老毛病）", ITEMS,
     u"output.accept(VIBRANIUM_SWORD.get());// ← 新增（0.12 ZF153 振金剑）\n", u"", u"A10"),
    (u"K08 免疫结果枚举 DO_NOT_APPLY → APPLY（等于没拦）", SWORD,
     u"MobEffectEvent.Applicable.Result.DO_NOT_APPLY", u"MobEffectEvent.Applicable.Result.APPLY", u"A16"),
    (u"K09 免疫表混进急迫（一刀切误伤）", SWORD,
     u"List.of(MobEffects.WITHER,", u"List.of(MobEffects.DIG_SPEED, MobEffects.WITHER,", u"A15"),
    (u"K10 n 改成读属性总值（含武器，口径错）", SWORD,
     u"ShockwaveManager.baseAttackDamage(player)",
     u"player.getAttributeValue(net.minecraft.world.entity.ai.attributes.Attributes.ATTACK_DAMAGE)",
     u"A23"),
    (u"K11 猛击加成 12 → 10", SWORD,
     u"SLAM_EXTRA_DAMAGE = 12.0D;", u"SLAM_EXTRA_DAMAGE = 10.0D;", u"A20"),
    (u"K12 状态时长 4 秒 → 8 秒", SWORD,
     u"SLAM_EFFECT_TICKS = 20 * 4;", u"SLAM_EFFECT_TICKS = 20 * 8;", u"A20"),
    (u"K13 冷却 6 秒 → 15 秒", SWORD,
     u"SLAM_COOLDOWN_TICKS = 20 * 6;", u"SLAM_COOLDOWN_TICKS = 20 * 15;", u"A20"),
    (u"K14 删掉 hurt 那一行（不打伤害了）", SWORD,
     u"        boolean hurt = target.hurt(source, damage);\n", u"", u"A26"),
    (u"K15 不排除自己（把自己也打了）", SWORD,
     u"if (target == player || !target.isAlive()) {", u"if (target == null || !target.isAlive()) {", u"A30"),
    (u"K16 创造模式玩家也照打", SWORD,
     u"if (target instanceof Player other && (other.isCreative() || other.isSpectator())) {",
     u"if (target instanceof Player other && other.isSpectator()) {", u"A31"),
    (u"K17 出手偷偷扣 1 点耐久", SWORD,
     u"        int hits = 0;\n",
     u"        int hits = 0;\n        player.getMainHandItem().hurtAndBreak(1, player, "
     u"net.minecraft.world.entity.EquipmentSlot.MAINHAND);\n", u"A22"),
    (u"K18 硬编码一句中文进 java", SWORD,
     u"private static final String TOOLTIP_PREFIX =",
     u"private static final String ZF153_K18 = \"振金剑\";\n"
     u"    private static final String TOOLTIP_PREFIX =", u"A34"),
    (u"K19 撕掉「源头拦」那处监听", PMAIN,
     u"        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener(\n"
     u"                VibraniumSwordItem::onEffectApplicable);\n", u"", u"A12"),
    (u"K20 撕掉「每 tick 清理」那处监听", PMAIN,
     u"                (net.neoforged.neoforge.event.tick.PlayerTickEvent.Post event) ->\n"
     u"                        VibraniumSwordItem.onPlayerTick(event.getEntity()));\n", u"", u"A13"),
    (u"K21 客户端不早退（两端各改一遍会打架）", SWORD,
     u"        if (player.level().isClientSide()) {\n            return;\n        }\n", u"", u"A19"),
]

# 这几把刀要动的是**资源**（贴图 / 模型 / 语言 / 配方），单独写
RES_KNIVES = [
    (u"K22 贴图被人动了一个字节", u"tex_byte", u"B3"),
    (u"K23 模型改成借原版下界合金剑", u"model_borrow", u"B6"),
    (u"K24 语言缺一个键（ja_jp 少 tooltip.3）", u"lang_missing", u"B9"),
    (u"K25 语言数字对不上（6x6 → 5x5）", u"lang_wrong_number", u"B11"),
    (u"K26 悄悄加了产出它的配方", u"recipe_added", u"B14"),
]

fails = []


def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def sha256b(b):
    return hashlib.sha256(b).hexdigest()


def run_verify():
    r = subprocess.run([sys.executable, VERIFY, u"--fast"], cwd=ROOT, capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def restore(path, original):
    open(path, "wb").write(original)
    return sha256(path) == sha256b(original)


def knife_text(name, path, old, new, expect):
    u"""文本刀：精确替换（锚点必须正好一次）→ 跑校验 → 点名的那条必须红 → 还原。"""
    if not os.path.exists(path):
        fails.append(u"%s：%s 不在" % (name, path))
        return
    original = open(path, "rb").read()
    text = original.decode("utf-8")
    n = text.count(old)
    if n != 1:
        print(u"  [SKIP] %s —— 锚点出现 %d 次（要 1）" % (name, n))
        fails.append(u"%s：锚点 %d 次" % (name, n))
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(text.replace(old, new, 1))
    rc, out = run_verify()
    hit = (u"[FAIL] %s " % expect) in out or (u"[FAIL] %s" % expect) in out
    ok_restore = restore(path, original)
    status = u"咬住" if hit else u"**没咬住**"
    print(u"  [%s] %-46s ⇒ %s（exit=%d）%s"
          % (u"OK" if (hit and ok_restore) else u"!!", name, status, rc,
             u"" if ok_restore else u"  ⚠ 还原失败！"))
    if not hit:
        fails.append(u"%s：点名判据 %s 没红" % (name, expect))
    if not ok_restore:
        fails.append(u"%s：还原不逐字节相同" % name)


def knife_res(name, kind, expect):
    u"""资源刀：改写贴图 / 模型 / 语言 / 配方，同名判据必须红，然后逐字节还原。"""
    if kind == u"tex_byte":
        original = open(TEX, "rb").read()
        b = bytearray(original)
        b[len(b) // 2] ^= 0xFF
        open(TEX, "wb").write(bytes(b))
        rc, out = run_verify()
        hit = (u"[FAIL] %s " % expect) in out
        ok_restore = restore(TEX, original)
    elif kind == u"model_borrow":
        original = open(MODEL, "rb").read()
        io.open(MODEL, "w", encoding="utf-8", newline=u"\n").write(
            original.decode("utf-8").replace(u"potato_s_t:item/vibranium_sword",
                                              u"minecraft:item/netherite_sword"))
        rc, out = run_verify()
        hit = (u"[FAIL] %s " % expect) in out
        ok_restore = restore(MODEL, original)
    elif kind == u"lang_missing":
        p = os.path.join(LANG, "ja_jp.json")
        original = open(p, "rb").read()
        import json
        d = json.loads(original.decode("utf-8"))
        d.pop(u"tooltip.potato_s_t.vibranium_sword.3", None)
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(
            json.dumps(d, ensure_ascii=False, indent=2) + u"\n")
        rc, out = run_verify()
        hit = (u"[FAIL] %s " % expect) in out
        ok_restore = restore(p, original)
    elif kind == u"lang_wrong_number":
        p = os.path.join(LANG, "zh_cn.json")
        original = open(p, "rb").read()
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(
            original.decode("utf-8").replace(u"6x6 内的所有生物", u"5x5 内的所有生物"))
        rc, out = run_verify()
        hit = (u"[FAIL] %s " % expect) in out
        ok_restore = restore(p, original)
    elif kind == u"recipe_added":
        existed = os.path.exists(NEWRECIPE)
        io.open(NEWRECIPE, "w", encoding="utf-8", newline=u"\n").write(
            u'{\n  "type": "minecraft:crafting_shaped",\n  "pattern": ["X", "X"],\n'
            u'  "key": {"X": {"item": "potato_s_t:vibranium_ingot"}},\n'
            u'  "result": {"id": "potato_s_t:vibranium_sword", "count": 1}\n}\n')
        rc, out = run_verify()
        hit = (u"[FAIL] %s " % expect) in out
        if existed:
            ok_restore = True          # 本来就有同名文件（不该发生），至少别删别人的
        else:
            os.remove(NEWRECIPE)
            ok_restore = not os.path.exists(NEWRECIPE)
    else:
        fails.append(u"%s：未知刀型 %s" % (name, kind))
        return
    print(u"  [%s] %-46s ⇒ %s（exit=%d）%s"
          % (u"OK" if (hit and ok_restore) else u"!!", name, u"咬住" if hit else u"**没咬住**", rc,
             u"" if ok_restore else u"  ⚠ 还原失败！"))
    if not hit:
        fails.append(u"%s：点名判据 %s 没红" % (name, expect))
    if not ok_restore:
        fails.append(u"%s：还原不逐字节相同" % name)


def main():
    print(u"== 反证开始（%d 把文本刀 + %d 把资源刀）==" % (len(KNIVES), len(RES_KNIVES)))
    print(u"\n[起点] 先确认校验现在是绿的（不然下面分不清是谁的红）")
    rc, out = run_verify()
    nfail = len(re.findall(u"\\[FAIL\\]", out))
    print(u"  exit=%d，[FAIL] %d 条（起点必须为 0 —— 除了 C 组探针报告，见下）" % (rc, nfail))
    baseline_c = (u"[FAIL] C1 " in out) or (u"[FAIL] C1\n" in out)
    if nfail > (1 if baseline_c else 0):
        print(u"  [!!] 起点就不干净，先修好再来")
        return 1
    for name, path, old, new, expect in KNIVES:
        knife_text(name, path, old, new, expect)
    # K14 需要两步：**真搬移**（先删原处，再插到写速度之后）。
    # ⚠ 第一版只做了"插入" ⇒ 原处那一行还在、`find` 拿到的还是第一处 ⇒ A26 判对不判红。
    #   刀不狠，判据就永远看不出自己漏了什么（这一条是**反证自己**发现判据缺口的例子：
    #   顺手把 A26 收紧成"target.hurt( 只许出现一次"）。
    print(u"\n[K14b 的第二半] 把 hurt **搬**到 setDeltaMovement 之后（删原处 + 插新处）")
    original = open(SWORD, "rb").read()
    text = original.decode("utf-8")
    line = u"        boolean hurt = target.hurt(source, damage);\n"
    anchor = u"        target.hurtMarked = true;\n"
    if text.count(line) == 1 and text.count(anchor) == 1:
        moved = text.replace(line, u"", 1)
        moved = moved.replace(anchor, anchor + line, 1)
        io.open(SWORD, "w", encoding="utf-8", newline=u"\n").write(moved)
        rc, out = run_verify()
        hit = u"[FAIL] A26 " in out
        ok_restore = restore(SWORD, original)
        print(u"  [%s] %-46s ⇒ %s（exit=%d）"
              % (u"OK" if (hit and ok_restore) else u"!!", u"K14b 顺序：hurt 搬到写速度之后",
                 u"咬住" if hit else u"**没咬住**", rc))
        if not hit:
            fails.append(u"K14b：A26 没红")
        if not ok_restore:
            fails.append(u"K14b：还原失败")
    else:
        fails.append(u"K14b：锚点 line=%d anchor=%d（各要 1 次）"
                     % (text.count(line), text.count(anchor)))
    for name, kind, expect in RES_KNIVES:
        knife_res(name, kind, expect)

    print(u"\n== 收尾：全部还原之后再跑一次校验 ==")
    rc, out = run_verify()
    nfail = len(re.findall(u"\\[FAIL\\]", out))
    tail = [l for l in out.split(u"\n") if u"通过" in l]
    print(u"  %s" % (tail[-1] if tail else u"（没有统计行）"))
    if nfail > 1:
        fails.append(u"收尾：还原后仍有 %d 条红" % nfail)

    print(u"\n被咬住 %d / %d 把，失败项 = %d"
          % (len(KNIVES) + 1 + len(RES_KNIVES) - len(fails), len(KNIVES) + 1 + len(RES_KNIVES),
             len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
