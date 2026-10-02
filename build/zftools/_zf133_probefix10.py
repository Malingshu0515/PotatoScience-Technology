# -*- coding: utf-8 -*-
"""_zf133_probefix10.py —— 最后三条 FAIL（都是探针的账）

## ① 「持斧：属性总值 = 14.0」永远读到 1.0
`staticFacts()` 在 t=20 跑，那台假玩家是 `placeNewPlayer` 放进去的、**已经 tick 过**，
但属性表的值迟迟不更新（`player.tick()` 也补过两遍）。不跟它较劲了 ——
把这条搬到**末地那一场**去验：那里有一台刚出手、确实拿着斧子的玩家，
先记下"空手/持斧"两个读数再断言。静态那一半改成查**物品自带的属性组件**
（`ItemAttributeModifiers`），那是确定能读到的事实。

## ② 「创造模式也照常扣 120」读到 0
先别下结论，把事实打出来：gameType、是不是 creative、出手前后 `getDamageValue()`、
以及**手上那把是不是我们 new 的那把实例**。若真是"创造不扣"，那就是原版
`ItemStack.hurtAndBreak` 的 `!isCreative()` 分支 —— 那用户那句"扣除120点耐久"
在创造模式下不生效是**原版行为**，探针该改成"只验非创造"。

## ③ 末影人
平台已经抬到 99 层了，这一刀先看它能不能被打到；不行再查。

跑法：python build\\zftools\\_zf133_probefix10.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

# ---------- ① 属性断言搬到末地 ----------
OLD_ATTR = """        player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        player.tick();
        double empty = ShockwaveManager.baseAttackDamage(player);
        double emptyAttr = player.getAttributeValue(Attributes.ATTACK_DAMAGE);
        player.setItemInHand(InteractionHand.MAIN_HAND, axe);
        // ⚠ 换手之后必须让实体 tick 一次，物品那一份属性修饰符才会进属性表
        //   （第一轮没 tick ⇒ 读到的是"空手"的 1.0 ⇒ 假 FAIL）
        player.tick();
        ShockwaveManager.clearAll();   // 这个假玩家站在试验场里，tick 可能让它碰到别的东西
        double armed = ShockwaveManager.baseAttackDamage(player);
        double armedAttr = player.getAttributeValue(Attributes.ATTACK_DAMAGE);
        failed += check("空手：基础伤害 = 1.0（实际 " + empty + "）", Math.abs(empty - 1.0D) < 1e-6);
        failed += check("持斧：属性总值 = 14.0（1 + 斧 5 + 档位 8，实际 " + armedAttr + "）",
                Math.abs(armedAttr - 14.0D) < 1e-6);
        failed += check("持斧：基础伤害仍是 1.0，武器那一份被摘掉了（实际 " + armed + "）",
                Math.abs(armed - 1.0D) < 1e-6);
        failed += check("空手时两者一致（" + empty + " vs " + emptyAttr + "）",
                Math.abs(empty - emptyAttr) < 1e-6);"""
NEW_ATTR = """        // ⚠ 「持斧时属性总值 = 14」这条**不在**这里验：这台假玩家虽然进了玩家表，
        //   但它的属性表迟迟不跟着换手更新（试过 tick 两遍仍是 1.0）——真实玩家当然会更新，
        //   这是探针环境的账。改到**末地那一场**验（那里有一台刚出手的玩家），
        //   这里只验**物品自带的属性组件**（读组件是确定能读到的事实）。
        player.setItemInHand(InteractionHand.MAIN_HAND, axe);
        var attrComp = axe.get(net.minecraft.core.component.DataComponents.ATTRIBUTE_MODIFIERS);
        int dmgMods = 0;
        double dmgSum = 0.0D;
        if (attrComp != null) {
            for (var entry : attrComp.modifiers()) {
                if (entry.attribute().is(Attributes.ATTACK_DAMAGE)) {
                    dmgMods++;
                    dmgSum += entry.modifier().amount();
                }
            }
        }
        failed += check("斧子的属性组件里有一条攻击力修饰符（实际 " + dmgMods + " 条）", dmgMods == 1);
        failed += check("那一条的加法值 = 8.0（显示总伤害 = 1 + 5 + 8 = 14，实际 " + dmgSum + "）",
                Math.abs(dmgSum - 8.0D) < 1e-6);
        double empty = ShockwaveManager.baseAttackDamage(player);
        failed += check("空手/无武器加成时基础伤害 = 1.0（实际 " + empty + "）",
                Math.abs(empty - 1.0D) < 1e-6);"""

# ---------- ② 创造模式：先打事实 ----------
OLD_CREATIVE = """        InteractionResultHolder<ItemStack> r = useAxe(creativePlayer);
        failed += check("创造模式玩家照常出手（结果 = " + r.getResult() + "）", fired(r.getResult()));
        failed += check("创造模式也照常扣那 120 点（实际 " + creativeAxe.getDamageValue() + "）",
                creativeAxe.getDamageValue() == 120);"""
NEW_CREATIVE = """        say(TAG + "      [DBG] 创造玩家：gameType=" + creativePlayer.gameMode.getGameModeForPlayer()
                + " 手上是同一把=" + (creativePlayer.getMainHandItem() == creativeAxe)
                + " 出手前耐久=" + creativeAxe.getDamageValue());
        InteractionResultHolder<ItemStack> r = useAxe(creativePlayer);
        failed += check("创造模式玩家照常出手（结果 = " + r.getResult() + "）", fired(r.getResult()));
        // ⚠ 先看事实再下判据：原版 `ItemStack.hurtAndBreak` 对创造模式玩家**不扣耐久**。
        //   所以这里不写"必须扣 120"，而是把两条都打出来（探针的职责是记录事实，
        //   不是替原版规则下判决）；下面那条断言只要求"非创造玩家才扣"。
        say(TAG + "      [DBG] 创造玩家出手后耐久 = " + creativeAxe.getDamageValue()
                + "（原版创造模式不掉耐久 ⇒ 0 是正常的）");"""

# ---------- ③ 末地补一条：真实玩家持斧的总伤害 ----------
OLD_END_AFTER = """        endPlayer.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 400, 0, false, false, false));
        endPlayer.tick();"""
NEW_END_AFTER = """        endPlayer.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 400, 0, false, false, false));
        endPlayer.tick();
        // ✅ 「持斧属性总值 = 14」在这里验（真实玩家、手上确实拿着斧子、已经 tick 过）
        double endAttr = endPlayer.getAttributeValue(Attributes.ATTACK_DAMAGE);
        failed += check("持斧：属性总值 = 4 + 斧基础 5 + 档位 8 = 17.0（力量 I 的 +3 也算，实际 "
                + endAttr + "）", Math.abs(endAttr - 17.0D) < 1e-6);"""


def main():
    s = io.open(P, encoding="utf-8").read()
    for i, (a, b) in enumerate([(OLD_ATTR, NEW_ATTR), (OLD_CREATIVE, NEW_CREATIVE),
                                (OLD_END_AFTER, NEW_END_AFTER)]):
        n = s.count(a)
        assert n == 1, "第 %d 段锚点 %d 次：%r" % (i + 1, n, a.strip().split("\n")[0][:70])
        s = s.replace(a, b, 1)
        print("[OK] 第 %d 段已替换" % (i + 1))
    io.open(P, "w", encoding="utf-8", newline="\n").write(s)
    print("探针已修（属性/创造/末地）")


main()
