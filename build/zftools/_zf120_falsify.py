# -*- coding: utf-8 -*-
u"""_zf120_falsify.py —— **本轮自己的反证刀**：证明 `_zf120_verify.py` 真的会失败

档案 §4.17 的口径：**「能失败的检查」才算检查**。
所以这里对每个关键要求各砍一刀（改坏 → 重编 → 跑本轮探针），
要求「探针必须报错」，然后逐字还原并核对哈希 + 探针回到全绿。

⚠ 每刀都**先从备份还原再砍下一刀**（刀与刀之间不能叠加，否则分不清是谁被抓到）。
⚠ 备份目录放在 `build/tmp/`（被 `.gitignore` 的 `build/*` 排除）并带**进程号** ——
   2026-09-25 那次 156 个 `_zf*_falsify_bak_*` 被 `git add -A` 提交进仓库，
   就是因为在 `build/zftools/` 下建备份（那一整个目录有 `!build/zftools/` 例外）。

刀的设计原则：**每把刀都对着一条具体的判据**，而且优先砍"只查名字查不出来的东西"：
  · 数值抄错列（四个护甲值都在、但顺序错了）  ← 只有位置取证抓得住
  · 语句还在、但乘法被拿掉（setAmount 照样被调用）  ← 只有结构取证抓得住
  · 事件还在监听、但满套判据被换成"至少一件"  ← 只有源码结构取证抓得住

跑法：
    $env:PYTHONIOENCODING='utf-8'
    python build/zftools/_zf120_falsify.py            # 全部
    python build/zftools/_zf120_falsify.py K4 K10     # 只跑名字里含 K4/K10 的
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
ZT = os.path.join(PROJ, "build", "zftools")
BAK = os.path.join(PROJ, "build", "tmp", "zf120_falsify_bak_%d" % os.getpid())
CLS = os.path.join(PROJ, "build", "classes", "java", "main", "com", "potatost", "mod")
SRC = os.path.join(PROJ, "src", "main", "java", "com", "potatost", "mod")
RES = os.path.join(PROJ, "src", "main", "resources")
RECIPE = os.path.join(RES, "data", "potato_s_t", "recipe")
MODELS = os.path.join(RES, "assets", "potato_s_t", "models", "item")
LANG = os.path.join(RES, "assets", "potato_s_t", "lang")

fails = []

MATS = os.path.join(SRC, "ModArmorMaterials.java")
ITEMS = os.path.join(SRC, "ModArmorItems.java")
SET = os.path.join(SRC, "ModVibraniumSet.java")
MODITEMS = os.path.join(SRC, "ModItems.java")

# 每把刀：(名字, 文件, 原文, 改成, 需要重编吗)
KNIVES = [
    # ---- ① 数值：与下界合金一致的那四个数 + 附魔权重 2 ----
    (u"K1 附魔权重 2 → 15（掉到下界合金同级，不再「非常低」）",
     MATS, u"public static final int VIBRANIUM_ENCHANTMENT_VALUE = 2;",
     u"public static final int VIBRANIUM_ENCHANTMENT_VALUE = 15;", True),
    (u"K2 盔甲韧性 3.0 → 0.0（不再与下界合金一致）",
     MATS, u"VIBRANIUM_ENCHANTMENT_VALUE, 3.0F, 0.1F,",
     u"VIBRANIUM_ENCHANTMENT_VALUE, 0.0F, 0.1F,", True),
    (u"K3 击退抗性 0.1 → 0.0（不再与下界合金一致）",
     MATS, u"VIBRANIUM_ENCHANTMENT_VALUE, 3.0F, 0.1F,",
     u"VIBRANIUM_ENCHANTMENT_VALUE, 3.0F, 0.0F,", True),
    (u"K4 护甲值抄错列：胸 8 与腿 6 对调（四个数都还在！）",
     MATS, u"                    3, 8, 6, 3,",
     u"                    3, 6, 8, 3,", True),
    (u"K5 振金头盔耐久 407 → 4070（不再与下界合金一致）",
     ITEMS, u'registerVibranium("vibranium_helmet", ArmorItem.Type.HELMET, 407)',
     u'registerVibranium("vibranium_helmet", ArmorItem.Type.HELMET, 4070)', True),
    # ---- ② 无限耐久 + 附魔光效（两个数据组件）----
    (u"K6 摘掉 UNBREAKABLE 组件（无限耐久没了）",
     ITEMS, u"                .component(DataComponents.UNBREAKABLE, new Unbreakable(true))\n",
     u"", True),
    (u"K7 摘掉附魔光效组件（自带附魔纹理没了）",
     ITEMS,
     u"                .component(DataComponents.UNBREAKABLE, new Unbreakable(true))\n"
     u"                .component(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, Boolean.TRUE);",
     u"                .component(DataComponents.UNBREAKABLE, new Unbreakable(true));", True),
    # ---- ③ 三条套装效果 ----
    (u"K8 反弹那一句被抽掉（只剩免疫，不弹回去）",
     SET, u"            projectile.deflect(ProjectileDeflection.REVERSE, wearer, wearer, true);\n",
     u"", True),
    (u"K9 反弹方向从 REVERSE 换成 AIM_DEFLECT（沿视线打飞，不是沿原路弹回）",
     SET, u"ProjectileDeflection.REVERSE, wearer, wearer, true",
     u"ProjectileDeflection.AIM_DEFLECT, wearer, wearer, true", True),
    (u"K10 第二帧保护方向写反（dot <= 0 → dot >= 0，会在身上来回抖）",
     SET, u"projectile.getDeltaMovement().dot(outward) <= 0.0",
     u"projectile.getDeltaMovement().dot(outward) >= 0.0", True),
    (u"K11 爆炸倍率 0.5 → 0.8（不再「降低50%」）",
     SET, u"public static final float EXPLOSION_DAMAGE_MULTIPLIER = 0.5F;",
     u"public static final float EXPLOSION_DAMAGE_MULTIPLIER = 0.8F;", True),
    (u"K12 setAmount 还在、但乘数被拿掉（减伤其实没生效）",
     SET, u"event.setAmount(event.getAmount() * EXPLOSION_DAMAGE_MULTIPLIER);",
     u"event.setAmount(event.getAmount());", True),
    (u"K13 弹射物免疫的标签换成 is_fire（判错了伤害类型）",
     SET, u"if (source.is(DamageTypeTags.IS_PROJECTILE)) {",
     u"if (source.is(DamageTypeTags.IS_FIRE)) {", True),
    (u"K14 爆炸击退那条被抽掉（爆炸照样把人炸飞）",
     SET, u"            event.setKnockbackVelocity(Vec3.ZERO);\n", u"", True),
    (u"K15 满套判据被换成「至少一件」（hasFullSet 的取反写反）",
     MATS, u"            if (!isMaterial(entity.getItemBySlot(slot), material)) {\n"
           u"                return false;\n            }",
     u"            if (isMaterial(entity.getItemBySlot(slot), material)) {\n"
     u"                return true;\n            }", True),
    (u"K16 某一处套装效果忘了判满套（onProjectileImpact 里那次判据被删）",
     SET, u"        if (!(hit.getEntity() instanceof LivingEntity wearer)) {\n"
          u"            return;\n        }\n"
          u"        if (!ModArmorMaterials.hasFullVibraniumSet(wearer)) {\n"
          u"            return;\n        }\n",
     u"        if (!(hit.getEntity() instanceof LivingEntity wearer)) {\n"
     u"            return;\n        }\n", True),
    # ---- ④ 贴图：先用原版铁套 ----
    (u"K17 材料 Layer 不再借原版铁（改成自己的 potato_s_t:vibranium）",
     MATS, u'ResourceLocation.fromNamespaceAndPath("minecraft", "iron")',
     u'ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "vibranium")', True),
    (u"K18 头盔背包图标不再借原版铁（改成自己的贴图）",
     os.path.join(MODELS, "vibranium_helmet.json"),
     u'"minecraft:item/iron_helmet"', u'"potato_s_t:item/iron_helmet"', False),
    # ---- ⑤ 配方：照抄原版下界合金的锻造台配方 ----
    (u"K19 配方基底换成钻石件（不照「钛合金作为升级基底」）",
     os.path.join(RECIPE, "vibranium_helmet_smithing.json"),
     u'"item": "potato_s_t:titanium_alloy_helmet"',
     u'"item": "minecraft:diamond_helmet"', False),
    (u"K20 配方添加物换成下界合金锭（不再是振金锭）",
     os.path.join(RECIPE, "vibranium_chestplate_smithing.json"),
     u'"item": "potato_s_t:vibranium_ingot"',
     u'"item": "minecraft:netherite_ingot"', False),
    (u"K21 模板换成别的（不再是原版下界合金升级模板）",
     os.path.join(RECIPE, "vibranium_boots_smithing.json"),
     u'"item": "minecraft:netherite_upgrade_smithing_template"',
     u'"item": "minecraft:nether_brick"', False),
    # ---- ⑥ 语言 / 创造页 ----
    (u"K22 zh_cn 的振金套装说明键被改名（玩家看到原始 key）",
     os.path.join(LANG, "zh_cn.json"),
     u'"tooltip.potato_s_t.vibranium_set":', u'"tooltip.potato_s_t.vibranium_set_typo":', False),
    (u"K23 创造页漏掉振金靴子（§4.82 那个漏过一次的坑）",
     MODITEMS, u"                        output.accept(ModArmorItems.VIBRANIUM_BOOTS.get());\n",
     u"", True),
]


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def run_verify():
    p = subprocess.run([sys.executable, os.path.join(ZT, "_zf120_verify.py")],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def run_compile():
    log = os.path.join(ZT, "_zf120_falsify_compile.log")
    with open(log, "wb") as fh:
        p = subprocess.run(["cmd", "/c", "cd /d %s && .\\gradlew.bat compileJava --offline "
                            "--no-build-cache" % PROJ], stdout=fh, stderr=subprocess.STDOUT)
    return p.returncode


def main():
    only = sys.argv[1:] or None
    if os.path.isdir(BAK):
        shutil.rmtree(BAK)
    os.makedirs(BAK)

    print(u"================ 备份 ================")
    targets = sorted(set([k[1] for k in KNIVES]))
    manifest = []
    for t in targets:
        if not os.path.isfile(t):
            print(u"  [SKIP] %s（不存在）" % t)
            fails.append(u"备份目标缺失：%s" % t)
            continue
        dst = os.path.join(BAK, os.path.basename(t) + u"." + hashlib.md5(
            t.encode("utf-8")).hexdigest()[:8])
        shutil.copy2(t, dst)
        h_src, h_dst = sha(t), sha(dst)
        manifest.append((t, dst, h_dst))
        print(u"  [%s] %-34s %s" % (u"OK" if h_src == h_dst else u"FAIL",
                                    os.path.basename(t), h_dst[:16]))
        if h_src != h_dst:
            fails.append(u"备份哈希不符：%s" % t)

    def restore():
        for t, dst, h in manifest:
            if not os.path.isfile(dst):
                fails.append(u"备份副本不见了（另一条流程动过？）：%s" % dst)
                print(u"         ↳ [FAIL] 备份副本不见了：%s" % dst)
                continue
            shutil.copy2(dst, t)
            if sha(t) != h:
                fails.append(u"还原后哈希不符：%s" % t)

    print(u"")
    print(u"================ 逐刀 ================")
    for name, path, old, new, recompile in KNIVES:
        if only and not any(o in name for o in only):
            continue
        before = sha(path) if os.path.isfile(path) else None
        if before is None:
            print(u"  [SKIP] %s —— 目标文件不存在" % name)
            fails.append(u"目标缺失：%s" % name)
            continue
        text = io.open(path, encoding="utf-8").read()
        if text.count(old) != 1:
            print(u"  [FAIL] %s —— 锚点命中 %d 次（应为 1）" % (name, text.count(old)))
            fails.append(u"锚点不唯一：%s" % name)
            continue
        io.open(path, "w", encoding="utf-8", newline=u"").write(text.replace(old, new))

        rc_c = run_compile() if recompile else 0
        rc_v, out = run_verify()
        caught = (rc_v != 0)
        # 抓到的必须是"判据不对"这一类，不是编译失败导致的假捕获
        gate_ok = caught and (rc_c == 0 or not recompile)
        print(u"  [%s] %s" % (u"OK" if gate_ok else u"FAIL", name))
        print(u"         ↳ 编译退出码 %s，探针退出码 %s（要求非 0）" % (rc_c, rc_v))
        for l in [x for x in out.split(u"\n") if x.strip().startswith(u"!!")][:2]:
            print(u"         ↳ %s" % l.strip()[:110])
        if not gate_ok:
            fails.append(name)

        restore()
        if recompile:
            run_compile()
        rc_v2, out2 = run_verify()
        back = os.path.isfile(path) and sha(path) == before
        back_ok = (rc_v2 == 0 and back)
        print(u"         ↳ 还原后哈希一致 %s，探针回到全绿 %s"
              % (u"✓" if back else u"✗", u"✓" if rc_v2 == 0 else u"✗"))
        if not back_ok:
            fails.append(u"还原失败：%s" % name)
            for l in [x for x in out2.split(u"\n") if x.strip().startswith(u"!!")][:3]:
                print(u"         ↳ %s" % l.strip()[:110])
        print(u"")

    print(u"================ 收尾 ================")
    for t, _dst, h in manifest:
        same = os.path.isfile(t) and sha(t) == h
        print(u"  [%s] %s 回到备份状态" % (u"OK" if same else u"FAIL", os.path.basename(t)))
        if not same:
            fails.append(u"收尾哈希不符：%s" % t)

    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
