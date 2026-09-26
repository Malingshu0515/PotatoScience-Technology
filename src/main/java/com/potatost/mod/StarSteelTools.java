package com.potatost.mod;

import java.util.List;

import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;

/**
 * 星璨钢四把工具（斧 / 剑 / 镐 / 锄）**共用的那一份规矩**（0.11 ZF141）。
 *
 * <p><b>为什么要有这么一个类</b>：Java 没有多继承，而这三把新工具必须分别继承
 * {@code SwordItem} / {@code PickaxeItem} / {@code HoeItem}（继承链见下面那节），
 * 没法抽一个共同基类出来。**能抽出来的是"逻辑"，抽不出来的是"挂点"** ——
 * 所以这里放逻辑（判据、返回值口径、说明文案），三个物品类里各留两个**一行**的覆写。
 * 复制的是挂点，不是算法。</p>
 *
 * <h2>一、「夜晚不磨损」到底管哪两件事（源码现抠，不是印象）</h2>
 * <p>工具的耐久消耗在 1.21.1 只有两个入口，两个都在 {@code Item} 上：</p>
 * <pre>
 *   Item.java:230   mineBlock(...)      ← 采掘；读 DataComponents.TOOL 的 damagePerBlock
 *   Item.java:224   postHurtEnemy(...)  ← 攻击；SwordItem 扣 1、DiggerItem 扣 2
 *   Player.java:1383  if (!level.isClientSide &amp;&amp; ...) itemstack.postHurtEnemy(...)
 * </pre>
 * <p>⚠ <b>本类第一版只打算覆写 {@code mineBlock}</b>（照斧子 ZF133 那么写）。查完源码才知道
 * 那样对**剑**几乎是空话：剑只在破坏方块时掉耐久，而它真正的磨损是**每击 1 点**
 * （{@code SwordItem.postHurtEnemy}）。所以本轮三把工具**两个入口都覆写**：
 * 「夜晚采掘与攻击都不磨损」才是玩家读得懂、也真的成立的一句话。</p>
 *
 * <h2>二、为什么不像斧子那样把 {@code mineBlock} 抄一遍</h2>
 * <p>斧子 ZF133 的写法是把原版那三行照抄、外面套一层"是不是夜晚"。对**斧子**是对的
 * （{@code AxeItem} 的 TOOL 组件里 {@code damagePerBlock == 1}，与原版逐字等价），
 * 但**对剑是错的**：剑的 TOOL 组件 {@code damagePerBlock == 2}
 * （{@code SwordItem.createToolProperties()} 最后那个参数就是 2），照抄会把剑的采掘磨损
 * 从 2 悄悄改成 1。所以本轮白天一律走 {@code super.mineBlock(...)}（**原样**，包括
 * "没有 TOOL 组件就返回 false、一点都不扣"这条），夜晚才走 {@link #nightMineBlockResult}。</p>
 *
 * <h2>三、剑 / 镐 / 锄的继承链（决定了覆写挂在谁身上）</h2>
 * <pre>
 *   Item ─┬─ TieredItem ─┬─ DiggerItem ─┬─ PickaxeItem
 *         │              │              ├─ HoeItem
 *         │              │              └─ AxeItem
 *         │              └─ SwordItem            ← ⚠ 剑**不**经 DiggerItem
 *         └─（mineBlock / postHurtEnemy 都定义在 Item 这一层）
 * </pre>
 * <p>四个入口（{@code mineBlock} / {@code postHurtEnemy}）都在 {@code Item} 上，
 * 所以三个子类各自 {@code @Override} 都能生效；{@code super.xxx(...)} 也都落到 {@code Item}
 * 那一份（DiggerItem / SwordItem 只覆写了 {@code postHurtEnemy}）。</p>
 */
public final class StarSteelTools {

    /** Shift 说明的行数（三把新工具**共用同一句**，所以只有一个键）。 */
    private static final int TOOLTIP_LINES = 1;

    private StarSteelTools() {
    }

    /**
     * 「夜晚不磨损」的判据 = <b>服务端 + 主世界 + 天黑</b>。
     *
     * <p>时段判据**不在这里重写一遍**，直接转调 {@link StarSteelAxeItem#isNight(Level)}
     * ——斧子 ZF133 已经把"主世界 + {@code dayTime % 24000} 落在 [13000, 23000)"
     * 写在那里并过了探针。两份判据 = 以后改一处漏一处。</p>
     *
     * <p>{@code isClientSide} 这一半：采掘那边原版自己就挡了客户端，这里多挡一次是为了
     * 让"夜晚"这条分支在客户端**永远不成立** ⇒ 客户端的表现与白天完全一致，
     * 不掉任何耐久（否则客户端本地先掉一点、等服务端同步回来，快捷栏上会闪一下）。</p>
     */
    public static boolean isNightWearFree(Level level) {
        return !level.isClientSide() && StarSteelAxeItem.isNight(level);
    }

    /**
     * 夜晚那一支的返回值：与 {@code Item.mineBlock} **同口径**
     * （有 {@code TOOL} 组件才是 {@code true}，没有就 {@code false}）。
     *
     * <p>这一步看着多余，其实是把原版那条"没有 TOOL 组件 ⇒ 返回 false、不扣耐久"
     * 的分支原样保留下来 —— 返回值决定"用物品"统计与后续 {@code onBreakBlock} 行为，
     * 不能一律返回 {@code true}。</p>
     */
    public static boolean nightMineBlockResult(ItemStack stack) {
        return stack.get(DataComponents.TOOL) != null;
    }

    /**
     * 三把星璨钢新工具共用的 Shift 说明（按 Shift 或 F3+H 才显示）。
     *
     * <p>文案是**玩法向**的一句话，不是开发笔记（用户 ZF137 的原话：说明不要写成
     * 给我自己看的东西）。数值 1192 / 钻石这些是玩家真会拿去比较的东西，保留。</p>
     */
    public static void appendHoverText(List<Component> tooltip, TooltipFlag flag) {
        if (flag.hasShiftDown() || flag.isAdvanced()) {
            for (int i = 1; i <= TOOLTIP_LINES; i++) {
                tooltip.add(Component.translatable("tooltip.potato_s_t.star_steel_tool." + i)
                        .withStyle(ChatFormatting.GRAY));
            }
        } else {
            tooltip.add(Component.translatable("tooltip.potato_s_t.hold_shift")
                    .withStyle(ChatFormatting.DARK_GRAY));
        }
    }
}
