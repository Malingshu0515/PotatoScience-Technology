# -*- coding: utf-8 -*-
u"""_zf139_falsify.py —— ZF139 的反证刀（K227~K248）

口径同前（§4.27）：基线绿 → **只改一处语义** ⇒ 门必须 FAIL 且**咬住指定的那一条** ⇒
逐字节还原（比 sha1）⇒ 收尾回到全绿。

本轮门是 `_zf139_verify.py`（本轮的常驻校验）。刀面覆盖四件事的每一条判据：
  甲 护甲值（4/9/7/4 / 韧性 / 击退抗性 / 别动另外两套）
  乙 常驻抗性 I（时长 / 满套判据 / 覆盖规则 / 不占星璨的位）
  丙 免疫摔落（走 LivingFallEvent、不是按伤害标签）
  丁 10% 反伤（概率常量 / 四条排除名单 / 原始伤害 / 还手的对象 / 伤害源实体）
  戊 死亡文案（数据包 message_id / effects / 键序 / 语言的 %1$s）
  己 跟平（往轮门的键数、两份文档的活体数字）

跑法：
    $env:PYTHONIOENCODING='utf-8'
    python E:\\PotatoST\\build\\zftools\\_zf139_falsify.py
"""
import hashlib
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, r"build\zftools")
SRC = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
MATS = os.path.join(SRC, u"ModArmorMaterials.java")
SET = os.path.join(SRC, u"ModVibraniumSet.java")
DT = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\damage_type\vibranium_reflect.json")
ZH = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang\zh_cn.json")
Z100 = os.path.join(ZT, u"_zf100_verify.py")
HAND = os.path.join(ROOT, r"docs\多会话协作交接.md")
VERIFY = os.path.join(ZT, u"_zf139_verify.py")

KNIVES = [
    # ---------------- 甲：护甲值 ----------------
    dict(id="K227", why=u"头盔护甲值 4 → 3（各 +1 少了一处）", path=MATS,
         old=u"                    4, 9, 7, 4,", new=u"                    3, 9, 7, 4,",
         expect=u"源码里那一行护甲值就是 4, 9, 7, 4"),
    dict(id="K228", why=u"四个数整行改回下界合金 3/8/6/3（乙方案没了）", path=MATS,
         old=u"                    4, 9, 7, 4,", new=u"                    3, 8, 6, 3,",
         expect=u"源码里那一行护甲值就是 4, 9, 7, 4"),
    dict(id="K229", why=u"韧性 3.0 → 2.0（顺手改坏了别的一个数）", path=MATS,
         old=u"VIBRANIUM_ENCHANTMENT_VALUE, 3.0F, 0.1F,", new=u"VIBRANIUM_ENCHANTMENT_VALUE, 2.0F, 0.1F,",
         expect=u"源码里附魔权重/韧性/击退抗性那一行没被动过"),
    dict(id="K230", why=u"击退抗性 0.1 → 0.0", path=MATS,
         old=u"VIBRANIUM_ENCHANTMENT_VALUE, 3.0F, 0.1F,", new=u"VIBRANIUM_ENCHANTMENT_VALUE, 3.0F, 0.0F,",
         expect=u"源码里附魔权重/韧性/击退抗性那一行没被动过"),
    dict(id="K231", why=u"顺手把星璨钢的护甲值也改了（波及另一套）", path=MATS,
         old=u"                    5, 9, 7, 5,", new=u"                    6, 9, 7, 5,",
         expect=u"反向·源码：星璨钢那一行仍是 5, 9, 7, 5"),

    # ---------------- 乙：常驻抗性 I ----------------
    dict(id="K232", why=u"抗性时长 320 → 640（每次 32 秒）", path=SET,
         old=u"RESISTANCE_TICKS = 320;", new=u"RESISTANCE_TICKS = 640;",
         expect=u"RESISTANCE_TICKS = 320"),
    dict(id="K233", why=u"不判满套了（只有一件也给）", path=SET,
         old=u"        if (!ModArmorMaterials.hasFullVibraniumSet(player)) {\n            return;\n        }\n"
             u"        MobEffectInstance current = player.getEffect(MobEffects.DAMAGE_RESISTANCE);",
         new=u"        if (false) {\n            return;\n        }\n"
             u"        MobEffectInstance current = player.getEffect(MobEffects.DAMAGE_RESISTANCE);",
         expect=u"判的是「满套」"),
    dict(id="K234", why=u"覆盖规则取反：身上有更高等级也压回 I", path=SET,
         old=u"if (current != null && current.getAmplifier() >= RESISTANCE_I",
         new=u"if (current != null && current.getAmplifier() <= RESISTANCE_I",
         expect=u"已有效果且等级不低于目标"),
    dict(id="K235", why=u"补的抗性变成不可见（visible=false，图标没了）", path=SET,
         old=u"RESISTANCE_TICKS, RESISTANCE_I, true, true));",
         new=u"RESISTANCE_TICKS, RESISTANCE_I, true, false));",
         expect=u"ambient=true（粒子淡）"),
    dict(id="K236", why=u"onFall 里不判满套了（谁摔都给免）", path=SET,
         old=u"    public static void onFall(LivingFallEvent event) {\n"
             u"        if (ModArmorMaterials.hasFullVibraniumSet(event.getEntity())) {\n"
             u"            event.setCanceled(true);\n        }\n    }",
         new=u"    public static void onFall(LivingFallEvent event) {\n"
             u"        if (true) {\n"
             u"            event.setCanceled(true);\n        }\n    }",
         expect=u"onFall 里判的是满套"),

    # ---------------- 丙：免疫摔落 ----------------
    dict(id="K237", why=u"onFall 里不取消事件（只判不做事）", path=SET,
         old=u"    public static void onFall(LivingFallEvent event) {\n"
             u"        if (ModArmorMaterials.hasFullVibraniumSet(event.getEntity())) {\n"
             u"            event.setCanceled(true);\n        }\n    }",
         new=u"    public static void onFall(LivingFallEvent event) {\n"
             u"        if (ModArmorMaterials.hasFullVibraniumSet(event.getEntity())) {\n"
             u"            event.setDistance(0.0F);\n        }\n    }",
         expect=u"onFall 里取消事件"),

    # ---------------- 丁：10% 反伤 ----------------
    dict(id="K238", why=u"概率 0.1 → 0.5（用户要的 10% 没了）", path=SET,
         old=u"REFLECT_CHANCE = 0.1F;", new=u"REFLECT_CHANCE = 0.5F;",
         expect=u"REFLECT_CHANCE = 0.1"),
    dict(id="K239", why=u"删掉「没掉血那一下不掷骰」那道判据", path=SET,
         old=u"        if (event.getNewDamage() <= 0.0F) {\n            return;\n        }",
         new=u"        if (event.getNewDamage() < -1.0F) {\n            return;\n        }",
         expect=u"「没掉血那一下」不掷骰"),
    dict(id="K240", why=u"删掉递归保护（反伤可以被再反回来）", path=SET,
         old=u"        if (source.is(VIBRANIUM_REFLECT)\n", new=u"        if (false\n",
         expect=u"排除名单①：反伤本身"),
    dict(id="K241", why=u"弹射物从排除名单里删掉", path=SET,
         old=u"                || source.is(DamageTypeTags.IS_PROJECTILE)\n", new=u"",
         expect=u"三条排除名单整段在同一个 if 里"),
    dict(id="K242", why=u"爆炸从排除名单里删掉", path=SET,
         old=u"                || source.is(DamageTypeTags.IS_EXPLOSION)) {", new=u"                ) {",
         expect=u"三条排除名单整段在同一个 if 里"),
    dict(id="K243", why=u"反伤数值改成「我掉了多少血」", path=SET,
         old=u"float amount = event.getOriginalDamage();", new=u"float amount = event.getNewDamage();",
         expect=u"反的是**这一击的原始伤害**"),
    dict(id="K244", why=u"还手对象写反（反给自己）", path=SET,
         old=u"attacker.hurt(reflectSource(wearer), amount);", new=u"wearer.hurt(reflectSource(wearer), amount);",
         expect=u"真的把伤害还回去"),
    dict(id="K245", why=u"伤害源的实体换成攻击者（击杀归属与文案名字都会错）", path=SET,
         old=u"        return new DamageSource(type, wearer);", new=u"        return new DamageSource(type, wearer, null);",
         expect=u"伤害源的实体 = 穿戴者"),

    # ---------------- 戊：死亡文案 ----------------
    dict(id="K246", why=u"数据包的 message_id 改名（文案键就对不上了）", path=DT,
         old=u'"message_id": "potato_s_t.vibranium_reflect"', new=u'"message_id": "vibranium_reflect"',
         expect=u"message_id = potato_s_t.vibranium_reflect"),
    dict(id="K247", why=u"effects 从 thorns 改成默认（挨打那一声没了）", path=DT,
         old=u'"effects": "thorns",', new=u'"effects": "hurt",',
         expect=u"effects = thorns"),
    dict(id="K248", why=u"中文死亡文案里把 %1$s 删掉（谁死的都写成同一句）", path=ZH,
         old=u'"death.attack.potato_s_t.vibranium_reflect":  "%1$s踢到了铁板"',
         new=u'"death.attack.potato_s_t.vibranium_reflect":  "踢到了铁板"',
         expect=u"正好一个 %1$s"),

    # ---------------- 己：跟平 ----------------
    dict(id="K249", why=u"往轮门的键数改回 482（活体数字又过期）", path=Z100,
         old=u"EXPECT_KEYS = 483", new=u"EXPECT_KEYS = 482",
         expect=u"往轮门里的键数全部跟到 483"),
    dict(id="K250", why=u"交接文档的活体数字改回 482", path=HAND,
         old=u"**483 键 × 4**", new=u"**482 键 × 4**",
         expect=u"交接文档的活体数字是 483 键"),
]

fails = []


def run():
    try:
        r = subprocess.run([sys.executable, VERIFY], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=600,
                           env=dict(os.environ, PYTHONIOENCODING=u"utf-8"))
        return r.returncode, r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 99, u"**超时**"


def summary(out):
    lines = [l for l in out.split(u"\n") if u"通过" in l and u"失败" in l]
    return u" / ".join(l.strip() for l in lines) or u"?"


def bitten(out, expect):
    return any(l.strip().startswith(u"!!") and expect in l for l in out.split(u"\n"))


def main():
    rc, out = run()
    print(u"基线：%s（退出码 %d）" % (summary(out), rc))
    if rc != 0:
        print(u"  [STOP] 基线不绿，先修")
        for l in out.split(u"\n"):
            if l.strip().startswith(u"!!"):
                print(u"    " + l.strip())
        return 1
    n_ok = 0
    for k in KNIVES:
        path = k["path"]
        orig = open(path, "rb").read()
        before = hashlib.sha1(orig).hexdigest()
        try:
            text = orig.decode("utf-8")
            nl = u"\r\n" if u"\r\n" in text else u"\n"
            old = k["old"].replace(u"\n", nl)
            new = k["new"].replace(u"\n", nl)
            if text.count(old) != 1:
                fails.append(u"%s：锚点命中 %d 次" % (k["id"], text.count(old)))
                print(u"  [BAD]  %s 锚点命中 %d 次（%s）" % (k["id"], text.count(old), k["why"]))
                continue
            open(path, "wb").write(text.replace(old, new, 1).encode("utf-8"))
            rc, out = run()
        finally:
            open(path, "wb").write(orig)
        after = hashlib.sha1(open(path, "rb").read()).hexdigest()
        if after != before:
            fails.append(u"%s：还原失败" % k["id"])
            break
        if rc != 0 and bitten(out, k["expect"]):
            n_ok += 1
            print(u"  [OK]   %s %s ⇒ 咬住「%s」" % (k["id"], k["why"], k["expect"]))
        else:
            print(u"  [BAD]  %s %s（退出码 %d）" % (k["id"], k["why"], rc))
            fails.append(u"%s %s ⇒ %s" % (k["id"], k["why"],
                                          u"门还是绿的" if rc == 0 else u"咬错了检查"))
    rc, out = run()
    print(u"收尾：%s（退出码 %d）" % (summary(out), rc))
    if rc != 0:
        fails.append(u"收尾不是全绿")
    print(u"刀 = %d，咬住 = %d，失败项 = %d" % (len(KNIVES), n_ok, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
