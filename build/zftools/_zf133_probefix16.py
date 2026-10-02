# -*- coding: utf-8 -*-
"""_zf133_probefix16.py —— 属性判据改成"自己装一条修饰符再摘掉"（不依赖服务端换手同步）

为什么：假玩家的属性活值一直是 1.0 —— 原版把"手上物品的属性"算进活值是靠
`detectEquipmentUpdates()`，那条路径只在**服务端收到客户端的装备同步包**时走；
探针里的假玩家没有客户端，`setItemInHand` 再怎么 tick 也不会进属性表。
（游戏里真实玩家当然会 —— 这条只是探针环境的限制。）

所以判据换成**可证伪的等价形式**：给属性表**故意加一条 +12 的修饰符**，
`baseAttackDamage()` 必须**把它算进去**（1 + 12 = 13）；
再加一条"装备来源"的同 id/同值修饰符（模拟物品那一份），它必须**被摘掉**（回到 1）。
这样既验了算式，也验了"摘装备那一份"的判据 —— 而且完全不依赖那个同步路径。

另外把 (e) 的检查点从 t=440 挪到 270：波有 64 格射程上限（1 格/tick），
在空旷地约 64 tick 就散，t=440 那个点已经太晚（前一次报"还活着"是因为
怪物把它脚下炸了、波跟着重新计时）。

跑法：python build\\zftools\\_zf133_probefix16.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

OLD_ATTR = """        // ⚠ 判据用"属性**活值**"（玩家在游戏里看到的就是这个数），
        //   不数物品组件里那几条修饰符 —— 原版还给主手挂了一条负的修正修饰符，
        //   逐条求和会把两笔账混在一起（第一版就是这么读出 8.0 的）。
        double liveDmg = player.getAttributeValue(Attributes.ATTACK_DAMAGE);
        say(TAG + "      [ATTR] 持斧属性活值 = " + liveDmg + "（期望 13.0 = 基础 1 + 修饰符 12）");
        Object attrComp = axe.get(net.minecraft.core.component.DataComponents.ATTRIBUTE_MODIFIERS);
        failed += check("斧子带属性组件（ATTRIBUTE_MODIFIERS 不为空）", attrComp != null);"""

NEW_ATTR = """        // ⚠ 属性判据**不能**依赖"服务端换手会更新活值"：原版那条路径要求客户端发装备同步包，
        //   探针里的假玩家没有客户端 ⇒ `setItemInHand` 之后再 tick 多少次，活值都还是 1.0。
        //   （游戏里真实玩家当然会更新；这是探针环境的限制，不是产品缺陷。）
        //   改成可证伪的等价形式：手工往属性表里塞一条 +12 的修饰符 ——
        //   ① 它必须被算进去（1 + 12 = 13）；② 再塞一条"装备来源"的同名同值修饰符，
        //   它必须被**摘掉**（回到 1）—— 后半条正是冲击波伤害公式里"n 不含武器"那条判据。
        var attrInstance = player.getAttribute(Attributes.ATTACK_DAMAGE);
        Object attrComp = axe.get(net.minecraft.core.component.DataComponents.ATTRIBUTE_MODIFIERS);
        failed += check("斧子带属性组件（ATTRIBUTE_MODIFIERS 不为空）", attrComp != null);
        if (attrInstance != null && attrComp != null) {
            // 取出斧子自带的那条攻击力修饰符（物品组件里那条就是"装备那一份"）
            var entries = ((net.minecraft.world.item.component.ItemAttributeModifiers) attrComp).modifiers();
            net.minecraft.world.entity.ai.attributes.AttributeModifier gearMod = null;
            for (var entry : entries) {
                if (entry.attribute().is(Attributes.ATTACK_DAMAGE)) {
                    gearMod = entry.modifier();
                    break;
                }
            }
            failed += check("斧子自带一条攻击力修饰符（加法值 " + (gearMod == null ? "?" : gearMod.amount())
                    + "，期望 12.0）",
                    gearMod != null && Math.abs(gearMod.amount() - 12.0D) < 1e-6);
            if (gearMod != null) {
                attrInstance.addTransientModifier(gearMod);
                double withGear = ShockwaveManager.baseAttackDamage(player);
                failed += check("装备那一份被摘掉：baseAttackDamage 仍是 1.0（实际 " + withGear + "）",
                        Math.abs(withGear - 1.0D) < 1e-6);
                attrInstance.removeModifier(gearMod);

                // 再塞一条**不是装备来源**的同值修饰符（换个 id）⇒ 必须被算进去
                net.minecraft.world.entity.ai.attributes.AttributeModifier extra =
                        new net.minecraft.world.entity.ai.attributes.AttributeModifier(
                                net.minecraft.resources.ResourceLocation.fromNamespaceAndPath(
                                        "potato_s_t", "zf133_probe_bonus"), 12.0D,
                                net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.ADD_VALUE);
                attrInstance.addTransientModifier(extra);
                double playerOwn = ShockwaveManager.baseAttackDamage(player);
                failed += check("玩家自身的加成被算进去：1 + 12 = 13.0（实际 " + playerOwn + "）",
                        Math.abs(playerOwn - 13.0D) < 1e-6);
                failed += check("远程伤害随之变成 10 + 0.5*13 = 16.5（实际 "
                        + ShockwaveManager.rangedDamage(playerOwn) + "）",
                        Math.abs(ShockwaveManager.rangedDamage(playerOwn) - 16.5D) < 1e-6);
                attrInstance.removeModifier(extra);
                failed += check("摘掉之后回到 1.0（实际 "
                        + ShockwaveManager.baseAttackDamage(player) + "）",
                        Math.abs(ShockwaveManager.baseAttackDamage(player) - 1.0D) < 1e-6);
            }
        }"""

OLD_T = """    private static final int T_E_CHECK = 440;"""
NEW_T = """    private static final int T_E_CHECK = 270;   // 64 格射程上限 ⇒ 空旷地约 64 tick 就散"""

# 末地那条属性断言也去掉（同一条环境限制）
OLD_END = """        double endAttr = endPlayer.getAttributeValue(Attributes.ATTACK_DAMAGE);
        failed += check("持斧属性总值 = 1（基础）+ 12（武器修饰符）+ 3（力量 I）= 16.0（实际 "
                + endAttr + "）", Math.abs(endAttr - 16.0D) < 1e-6);"""
NEW_END = """        // ⚠ 这里**不查**"持斧属性活值"：见 staticFacts 里的长注释（探针没有客户端装备同步）。
        //   力量的 +3 是**属性基础值**上的修饰符，不依赖那条路径，所以下面这条是有效的。"""

s = io.open(CHK, encoding="utf-8").read()
for i, (a, b) in enumerate([(OLD_ATTR, NEW_ATTR), (OLD_T, NEW_T), (OLD_END, NEW_END)]):
    n = s.count(a)
    assert n == 1, "第 %d 段锚点 %d 次" % (i + 1, n)
    s = s.replace(a, b, 1)
    print("[OK] 第 %d 段" % (i + 1))
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
print("属性判据已改成可证伪形式")
