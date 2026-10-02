# -*- coding: utf-8 -*-
"""_zf133_probefix.py —— 第一轮探针暴露的问题，逐条修（探针 + 产品代码各一处）

第一轮（`_zf133_run2.log`）抓到 4 类问题，**3 类是探针自己的**、**1 类是产品代码的**：

| # | 现象 | 真因 | 修法 |
|---|---|---|---|
| 1 | 每次右键都返回 PASS、耐久一动不动 | 假玩家的 `isShiftKeyDown()` 是 false ⇒ `use()` 在 shift 那一步就 PASS 了 | `useAxe()` 先把 shift 按下去（**并断言结果 = SUCCESS**，不能再用 `consumesAction()`——`PASS.consumesAction()` 是 true，第一轮就是被它骗过去的） |
| 2 | 换手后属性总值仍是 1.0 | 属性的物品修饰符要**实体 tick 一次**才收进去 | 换手后 `player.tick()` |
| 3 | 「修理材料 = 星璨钢锭」FAIL | **产品代码的真缺陷**：`AxeItem` 的修理材料来自档位，而档位那个是共用的（轻质钛合金）⇒ 覆写 `isValidRepairItem` | 改 `StarSteelAxeItem` |
| 4 | 「黑曜石斧子挖得动」FAIL | **探针的判据错了**：黑曜石要镐子，斧子本来就不行（与挖掘等级无关） | 换成"下界合金镐挖得动 / 钻石镐也挖得动"的对照 |

跑法：python build\\zftools\\_zf133_probefix.py
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
P = os.path.join(ROOT, r"src\main\java\com\potatost\mod\Zf133Check.java")

EDITS = [
    # ---- 1) useAxe：先按 shift + 断言 SUCCESS ----
    ("""    private static InteractionResultHolder<ItemStack> useAxe(ServerPlayer who) {
        ItemStack stack = who.getMainHandItem();
        InteractionResultHolder<ItemStack> r =
                stack.getItem().use(who.level(), who, InteractionHand.MAIN_HAND);
        say(TAG + "      右键结果 = " + r.getResult() + "（耐久 "
                + stack.getDamageValue() + "/" + stack.getMaxDamage() + "）");
        return r;
    }""",
     """    /**
     * 出手。
     *
     * <p>⚠ 两件事是**第一轮探针踩出来的**：
     * ① 假玩家的 {@code isShiftKeyDown()} 恒为 false ⇒ 不先按下去的话 {@code use()} 会在
     * shift 那一步直接 PASS（第一轮八个场景全是这么假通过的）；
     * ② 判据不能用 {@code consumesAction()} —— 原版 {@code InteractionResult.PASS} 的
     * {@code consumesAction()} 也是 true（"物品没接这一下、但手要挥"），
     * 所以只认 {@code SUCCESS}。**判据必须能不能失败地卡住"真的出手了"这件事**。</p>
     */
    private static InteractionResultHolder<ItemStack> useAxe(ServerPlayer who) {
        who.setShiftKeyDown(true);
        ItemStack stack = who.getMainHandItem();
        InteractionResultHolder<ItemStack> r =
                stack.getItem().use(who.level(), who, InteractionHand.MAIN_HAND);
        who.setShiftKeyDown(false);
        say(TAG + "      右键结果 = " + r.getResult() + "（耐久 "
                + stack.getDamageValue() + "/" + stack.getMaxDamage() + "）");
        return r;
    }"""),

    ("""        failed += check("右键出手（结果 = " + r.getResult() + "）", r.getResult().consumesAction());""",
     """        failed += check("右键出手（结果 = " + r.getResult() + "）",
                r.getResult() == net.minecraft.world.InteractionResult.SUCCESS);"""),

    ("""        failed += check("冷却中再右键不出手（结果 = " + r.getResult() + "）",
                !r.getResult().consumesAction());""",
     """        failed += check("冷却中再右键不出手（结果 = " + r.getResult() + "）",
                r.getResult() != net.minecraft.world.InteractionResult.SUCCESS);"""),

    ("""        failed += check("耐久 119 < 120 ⇒ 拒绝出手（结果 = " + r.getResult() + "）",
                !r.getResult().consumesAction());""",
     """        failed += check("耐久 119 < 120 ⇒ 拒绝出手（结果 = " + r.getResult() + "）",
                r.getResult() != net.minecraft.world.InteractionResult.SUCCESS);"""),

    ("""        failed += check("耐久正好 120 ⇒ 出手（结果 = " + r.getResult() + "）",
                r.getResult().consumesAction());""",
     """        failed += check("耐久正好 120 ⇒ 出手（结果 = " + r.getResult() + "）",
                r.getResult() == net.minecraft.world.InteractionResult.SUCCESS);"""),

    ("""        failed += check("创造模式玩家照常出手（结果 = " + r.getResult() + "）",
                r.getResult().consumesAction());""",
     """        failed += check("创造模式玩家照常出手（结果 = " + r.getResult() + "）",
                r.getResult() == net.minecraft.world.InteractionResult.SUCCESS);"""),

    ("""        failed += check("末地出手成功（结果 = " + r.getResult() + "）", r.getResult().consumesAction());""",
     """        failed += check("末地出手成功（结果 = " + r.getResult() + "）",
                r.getResult() == net.minecraft.world.InteractionResult.SUCCESS);"""),

    # ---- 2) 换手后 tick ----
    ("""        player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        double empty = ShockwaveManager.baseAttackDamage(player);
        double emptyAttr = player.getAttributeValue(Attributes.ATTACK_DAMAGE);
        player.setItemInHand(InteractionHand.MAIN_HAND, axe);
        double armed = ShockwaveManager.baseAttackDamage(player);""",
     """        player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        player.tick();
        double empty = ShockwaveManager.baseAttackDamage(player);
        double emptyAttr = player.getAttributeValue(Attributes.ATTACK_DAMAGE);
        player.setItemInHand(InteractionHand.MAIN_HAND, axe);
        // ⚠ 换手之后必须让实体 tick 一次，物品那一份属性修饰符才会进属性表
        //   （第一轮没 tick ⇒ 读到的是"空手"的 1.0 ⇒ 假 FAIL）
        player.tick();
        ShockwaveManager.clearAll();   // 这个假玩家站在试验场里，tick 可能让它碰到别的东西
        double armed = ShockwaveManager.baseAttackDamage(player);"""),

    # ---- 3) 黑曜石判据换成工具种类对照 ----
    ("""        // 钻石级的两条可观测推论：黑曜石挖得动（下界合金也一样），但"钻石挖不动"的集合与下界合金不同
        failed += check("钻石级 ⇒ 黑曜石不算\\"挖不动\\"（isCorrectToolForDrops = true）",
                axe.isCorrectToolForDrops(Blocks.OBSIDIAN.defaultBlockState()));
        failed += check("钻石级 ⇒ 下界合金块也不算\\"挖不动\\"",
                axe.isCorrectToolForDrops(Blocks.NETHERITE_BLOCK.defaultBlockState()));""",
     """        // ⚠ 第一版拿黑曜石当"钻石级挖得动"的判据是**错的**：黑曜石要镐子，
        //   斧子本来就不行（原版行为，与挖掘等级无关）⇒ 探针当场顶红。
        //   正确的区分办法是"同一块方块换个工具试"：黑曜石换个镐子就挖得动 ⇒
        //   差别在**工具种类**而不是等级；等级那一半只留上面那条读档位对象本身的断言。
        ItemStack netheritePick = new ItemStack(Items.NETHERITE_PICKAXE);
        ItemStack diamondPick = new ItemStack(Items.DIAMOND_PICKAXE);
        failed += check("黑曜石：斧子挖不动（原版行为，与等级无关）",
                !axe.isCorrectToolForDrops(Blocks.OBSIDIAN.defaultBlockState()));
        failed += check("黑曜石：下界合金镐挖得动 ⇒ 上面那条的差别在工具种类",
                netheritePick.isCorrectToolForDrops(Blocks.OBSIDIAN.defaultBlockState()));
        failed += check("黑曜石：钻石镐也挖得动（对照，钻石这一档不低）",
                diamondPick.isCorrectToolForDrops(Blocks.OBSIDIAN.defaultBlockState()));"""),
]


def main():
    s = io.open(P, encoding="utf-8").read()
    for i, (a, b) in enumerate(EDITS):
        n = s.count(a)
        if n != 1:
            print("[FAIL] 第 %d 段锚点出现 %d 次：%r" % (i + 1, n, a[:70]))
            sys.exit(1)
        s = s.replace(a, b, 1)
        print("[OK ] 第 %d 段已替换" % (i + 1))
    io.open(P, "w", encoding="utf-8", newline="\n").write(s)
    print("探针已修：%d 段" % len(EDITS))


main()
