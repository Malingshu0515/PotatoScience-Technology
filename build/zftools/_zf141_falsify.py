# -*- coding: utf-8 -*-
r'''_zf141_falsify.py —— ZF141 的**反证刀**：把 `_zf141_verify.py` 挨个咬一遍。

一把刀 = 一次"把盘上改坏一点点"，判据**必须**当场变红并说出**该说的那句话**；
然后逐字节还原、复核还原成功。刀咬不住 = 判据是空的（比没有更糟）。

⚠ 三条设计约束（抄的是前几轮的教训）：
  ① **刀只改源码 / 资源文本**，`_zf141_verify.py` 也**只读源码与资源**（不 javap、不编译）
     ⇒ 不需要"改一次编一次"，秒级跑完，也就不会撞多会话的 `build\classes` 锁（§4.11）；
  ② 每把刀**先备份再改**，改完断言"命中次数 == 1"（防锚点漂移，§4.6）；
  ③ 每把刀都认**期望的失败项名字**（不是"只要变红就算"）—— 否则"任何一个检查红了"都能骗过它。

跑法：python build\zftools\_zf141_falsify.py
      python build\zftools\_zf141_falsify.py --only K256
'''
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
JAVA = r"src\main\java\com\potatost\mod"
RES = r"src\main\resources\assets\potato_s_t"
DATA = r"src\main\resources\data\potato_s_t"
BAK = os.path.join(ZT, "_zf141_falsify_bak")

VERIFY = os.path.join(ZT, u"_zf141_verify.py")

# (刀号, 一句话, [(相对路径, 旧文本, 新文本), …], 期望出现在 FAIL 行里的子串)
KNIVES = [
    ("K251", u"档位耐久 1192 → 1193",
     [(os.path.join(JAVA, "ModTiers.java"),
       u"STAR_STEEL_TOOL = build(1192,", u"STAR_STEEL_TOOL = build(1193,")],
     u"A1 新档位那一行"),
    ("K252", u"挖掘等级 钻石 → 下界合金",
     [(os.path.join(JAVA, "ModTiers.java"),
       u"STAR_STEEL_TOOL = build(1192, STAR_STEEL_DAMAGE, STAR_STEEL_SPEED,\n            BlockTags.INCORRECT_FOR_DIAMOND_TOOL, 22, ModTiers::starSteelRepair);",
        u"STAR_STEEL_TOOL = build(1192, STAR_STEEL_DAMAGE, STAR_STEEL_SPEED,\n            BlockTags.INCORRECT_FOR_NETHERITE_TOOL, 22, ModTiers::starSteelRepair);")],
     u"A1 新档位那一行"),
    ("K253", u"附魔权重 22 → 21（只改新档位那一行）",
     [(os.path.join(JAVA, "ModTiers.java"),
       u"BlockTags.INCORRECT_FOR_DIAMOND_TOOL, 22, ModTiers::starSteelRepair);",
        u"BlockTags.INCORRECT_FOR_DIAMOND_TOOL, 21, ModTiers::starSteelRepair);")],
     u"A1 新档位那一行"),
    ("K254", u"把斧子那一档也改坏（证明 A3b 与改前件逐字节对照有效）",
     [(os.path.join(JAVA, "ModTiers.java"),
       u"STAR_STEEL_AXE = build(1192,", u"STAR_STEEL_AXE = build(1191,")],
     u"A3 斧子那一档"),
    ("K255", u"修理材料 星璨钢锭 → 轻质钛合金",
     [(os.path.join(JAVA, "ModTiers.java"),
       u"return Ingredient.of(ModArmorItems.STAR_STEEL_INGOT.get());",
        u"return Ingredient.of(ModItems.LIGHT_TITANIUM_ALLOY.get());")],
     u"A7 星璨钢修理材料"),
    ("K256", u"剑的 mineBlock 改成斧子那种硬编码 hurtAndBreak(1)（§4.139 那条）",
     [(os.path.join(JAVA, "StarSteelSwordItem.java"),
       u"        return super.mineBlock(stack, level, state, pos, entity);",
        u"        stack.hurtAndBreak(1, entity, EquipmentSlot.MAINHAND);\n        return true;")],
     u"B9-剑"),
    ("K257", u"夜晚判据不再转调斧子的 isNight，自己复制一份时段",
     [(os.path.join(JAVA, "StarSteelTools.java"),
       u"return !level.isClientSide() && StarSteelAxeItem.isNight(level);",
        u"return !level.isClientSide() && level.getDayTime() % 24000L >= 13000L && level.getDayTime() % 24000L < 23000L;")],
     u"B1 判据"),
    ("K258", u"夜晚的返回值恒 true（丢掉原版 TOOL 组件那条口径）",
     [(os.path.join(JAVA, "StarSteelTools.java"),
       u"return stack.get(DataComponents.TOOL) != null;", u"return true;")],
     u"B2 夜晚返回值"),
    ("K259", u"锄不再覆写 postHurtEnemy（夜晚攻击照样磨损）",
     [(os.path.join(JAVA, "StarSteelHoeItem.java"),
       u"    public void postHurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {",
        u"    public void postHurtEnemyDISABLED(ItemStack stack, LivingEntity target, LivingEntity attacker) {")],
     u"B7-锄"),
    ("K260", u"锄的注册整条删掉",
     [(os.path.join(JAVA, "ModItems.java"),
       u'ITEMS.register("star_steel_hoe",', u'ITEMS.register("star_steel_hoe_x",')],
     u"C1-锄"),
    ("K261", u"创造页少一行剑",
     [(os.path.join(JAVA, "ModItems.java"),
       u"output.accept(STAR_STEEL_SWORD.get());", u"// output.accept(STAR_STEEL_SWORD.get());")],
     u"C2-剑"),
    ("K262", u"剑的图纸换成原版斧头那张（XX / X# / ' #'）",
     [(os.path.join(DATA, "recipe", "star_steel_sword.json"),
       u'    "X",\n    "X",\n    "#"', u'    "XX",\n    "X#",\n    " #"')],
     u"D7-sword"),
    ("K263", u"剑的材料换成原版钻石",
     [(os.path.join(DATA, "recipe", "star_steel_sword.json"),
       u'"item": "potato_s_t:star_steel_ingot"', u'"item": "minecraft:diamond"')],
     u"D8-sword"),
    ("K264", u"剑的贴图换成锄那张（真解码会发现与素材不是同一张）",
     [(os.path.join(RES, "textures", "item", "star_steel_sword.png"), None, None)],
     u"D2-star_steel_sword.png"),
    ("K265", u"剑的模型 layer0 借回原版铁剑",
     [(os.path.join(RES, "models", "item", "star_steel_sword.json"),
       u'"potato_s_t:item/star_steel_sword"', u'"minecraft:item/iron_sword"')],
     u"D4-star_steel_sword.png"),
    ("K266", u"四语言把共用的技能说明键改名（键数不变 ⇒ 咬的是 E3 不是 E1）",
     [(os.path.join(RES, "lang", n + ".json"),
       u'  "tooltip.potato_s_t.star_steel_tool.1":', u'  "tooltip.potato_s_t.star_steel_tool_X.1":')
      for n in ("zh_cn", "en_us", "ja_jp", "ru_ru")],
     u"E3 四个新键四语言都在"),
    ("K267", u"俄语的锄名抄成中文（漏翻）",
     [(os.path.join(RES, "lang", "ru_ru.json"),
       u'"item.potato_s_t.star_steel_hoe": "Мотыга из звёздной стали"',
        u'"item.potato_s_t.star_steel_hoe": "星璨钢锄"')],
     u"E5 三件工具名"),
    ("K268", u"说明文案里的 1192 改成 1193",
     [(os.path.join(RES, "lang", "zh_cn.json"),
       u"夜晚采掘与攻击不消耗耐久。1192 耐久", u"夜晚采掘与攻击不消耗耐久。1193 耐久")],
     u"E6 zh_cn"),
    ("K269", u"档案里把 487 键改回 483",
     # ⚠ 锚点必须唯一：`四语言 **483 → 487** 键` 在档案里出现两次（§5 行 + §9 小节）
     #   ⇒ 第一版命中 2 次当场停手。这里改用 §5 行里那句独有的。
     [(r"docs\开发档案.md", u"⑧ 四语言 **483 → 487** 键 ⇒ **32 份**门跟平",
       u"⑧ 四语言 **482 → 483** 键 ⇒ **32 份**门跟平")],
     u"G4b §5 那行自己写着"),
    ("K270", u"交接文档的活体数字打回 483",
     [(r"docs\多会话协作交接.md", u"| 语言键数 | **487 键 × 4**", u"| 语言键数 | **483 键 × 4**")],
     u"G5 交接"),
    ("K271", u"英文公告的键数打回 483",
     [(r"docs\UpdateAnnouncement_EN.md", u"(487 keys each)", u"(483 keys each)")],
     u"G7 英文公告"),
    ("K272", u"凭据里把剑那张的 sha1 改掉",
     # ⚠ 锚点要唯一：`"星璨钢剑.png"` 出现两次（键名 + 原名）⇒ 直接改 sha1 那一行
     [(os.path.join(u"build", u"用户素材", u"_来源凭据.json"),
       u'"sha1": "75b43114c972', u'"sha1": "000000000000')],
     u"F9 凭据里的 sha1"),
    ("K273", u"探针报告里塞一个 [FAIL]",
     [(os.path.join("build", "zftools", u"_zf141_probe_utf8.txt"),
       u"判词：全绿（通过 70）", u"判词：全绿（通过 70）\n[A141] [FAIL] 假的")],
     u"F2 判词"),
    ("K274", u"归档件的 TAG 改成 [A999]（§4.145 那条自检）",
     [(os.path.join("build", "zftools", "check", u"Zf141Check.java"),
       u'"[A141] "', u'"[A999] "')],
     u"F7 归档件与报告"),
    ("K275", u"改前件里把斧子贴图换掉（证明 G10 真在校验备份）",
     [(os.path.join(r"C:\PotatoST救援", "zf141_pre", r"src\main\resources\assets\potato_s_t\textures\item\star_steel_axe.png"),
       None, None)],
     u"G10 改前件"),
]


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_verify():
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, VERIFY], capture_output=True, env=env)
    out = r.stdout.decode("utf-8", "replace")
    if r.returncode != 0 and not out:
        out = r.stderr.decode("utf-8", "replace")
    # ⚠ 只认"**行首**就是 [FAIL]"的那些行。
    #   第一版写成 `if "[FAIL]" in l` ⇒ 把 `[OK]   F2 判词…且没有 [FAIL]` 也数进来了：
    #   于是基线永远"有 1 项失败"，而且 K273（塞假 FAIL 进报告）**不做任何改动就已经咬住** ——
    #   这是一次**假咬**，比漏网更坏（它会让一把空刀看起来有效）。
    fails = [l.strip() for l in out.split(u"\n") if l.strip().startswith(u"[FAIL]")]
    return out, fails


def main(argv):
    only = None
    if u"--only" in argv:
        only = argv[argv.index(u"--only") + 1]

    base_out, base_fails = run_verify()
    print(u"基线：%s" % (base_out.split(u"\n")[-3].strip() if base_out else u"（读不到）"))
    print(u"基线失败 %d 项（预期是「探针还挂着」那几项）：%s"
          % (len(base_fails), u" ／ ".join(f[:34] for f in base_fails)))

    os.makedirs(BAK, exist_ok=True)
    n_bite, n_miss, notes = 0, 0, []
    for kid, title, edits, expect in KNIVES:
        if only and kid != only:
            continue
        saved = []
        try:
            for path, old, new in edits:
                full = path if os.path.isabs(path) else os.path.join(ROOT, path)
                if not os.path.isfile(full):
                    notes.append(u"  !! %s 目标不在：%s" % (kid, full))
                    raise IOError(full)
                shutil.copy2(full, os.path.join(BAK, u"%s_%s" % (kid, os.path.basename(full))))
                saved.append((full, os.path.join(BAK, u"%s_%s" % (kid, os.path.basename(full)))))
                if old is None:      # 二进制刀：拿另一张图整个覆盖
                    other = os.path.join(ROOT, RES, "textures", "item", u"star_steel_hoe.png") \
                        if u"sword" in path else os.path.join(ROOT, USER_PNG)
                    shutil.copy2(other, full)
                    continue
                text = io.open(full, encoding="utf-8", newline="").read()
                if text.count(old) != 1:
                    notes.append(u"  !! %s 锚点命中 %d 次：%s" % (kid, text.count(old), path))
                    raise IOError(path)
                io.open(full, u"w", encoding="utf-8", newline=u"").write(text.replace(old, new, 1))

            _out, fails = run_verify()
            hit = [f for f in fails if expect in f]
            if hit:
                n_bite += 1
                print(u"  [咬住] %s  %s" % (kid, title))
            else:
                n_miss += 1
                print(u"  [漏网] %s  %s" % (kid, title))
                print(u"         期望的失败项「%s」没出现；实际失败 %d 项：%s"
                      % (expect, len(fails), u" ／ ".join(f[:40] for f in fails[:5])))
        except Exception as e:
            n_miss += 1
            notes.append(u"  !! %s 自己出错：%r" % (kid, e))
            print(u"  [出错] %s  %s" % (kid, e))
        finally:
            for full, bak in saved:
                shutil.copy2(bak, full)
                if sha1(full) != sha1(bak):
                    notes.append(u"  !! %s 还原失败：%s" % (kid, full))

    for n in notes:
        print(n)
    # 收尾：全部还原之后，基线必须回到原样
    _out2, fails2 = run_verify()
    same = sorted(fails2) == sorted(base_fails)
    print(u"")
    print(u"刀 = %d，咬住 = %d，漏网 = %d" % (n_bite + n_miss, n_bite, n_miss))
    print(u"还原后基线%s（%d → %d 项失败）"
          % (u"一致" if same else u"**不一致，要手工查**", len(base_fails), len(fails2)))
    return 1 if (n_miss or not same) else 0


USER_PNG = os.path.join(u"build", u"用户素材", u"星锄子_001.png")

if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
