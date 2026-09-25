package com.potatost.mod;

import java.util.List;

import net.minecraft.util.RandomSource;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/**
 * 盐分解构器的配方与概率（0.10 ZF32）。
 *
 * <p><b>用户指定的三条结果</b>（"目前配方"）：</p>
 * <ul>
 *   <li><b>消耗 64 个海盐</b>，40 秒后结算；</li>
 *   <li><b>60%</b> 概率<b>返还 64 个海盐</b>；</li>
 *   <li><b>5%</b> 概率产出<b>所有种类的粗矿里随机一个</b>；</li>
 *   <li><b>100%</b> 产出<b>氯化钠</b>。</li>
 * </ul>
 *
 * <p>三条是<b>各自独立掷骰</b>的（用户没说是互斥），所以一轮可能同时拿到"海盐 + 氯化钠 + 粗矿"。
 * 期望收益：每 64 个海盐平均拿回 38.4 个 + 1 个氯化钠 + 0.05 个粗矿。</p>
 *
 * <p><b>为什么把概率/耗时都放常量里而不是散在方块实体里</b>：JEI 要展示同一套数字，
 * 两边各写一份迟早会漂（档案里"数值写死在文案里"那条就是这么来的）。</p>
 */
public final class SaltDecomposerRecipes {

    /** 一轮要投入的海盐数量（用户指定 64） */
    public static final int SALT_INPUT = 64;
    /** 一轮耗时（tick）。用户说 40 秒 ⇒ 800 tick。 */
    public static final int DURATION_TICKS = 40 * 20;
    /**
     * 每 tick 耗电（FE）。
     *
     * <p>用户只说了"储能极其低 只有 20 FE"，<b>没给耗电率</b>。
     * 取 20 是为了让<b>缓冲恰好等于 1 tick 的量</b>——最能体现"必须持续通电"的意图；
     * 一块板共 {@code 20 × 800 = 16000} FE。要改就改这一个数（档案 §9 里挂着待用户确认）。</p>
     */
    public static final int ENERGY_PER_TICK = 20;
    /** 返还海盐的概率（百分比）。用户指定 60%。 */
    public static final int SALT_RETURN_PERCENT = 60;
    /** 产出随机粗矿的概率（百分比）。用户指定 5%。 */
    public static final int RAW_ORE_PERCENT = 5;

    /**
     * 一次结算的两枚骰子结果。
     *
     * <p><b>为什么单独抽成 {@link #roll}（而不是直接写在方块实体里）</b>：
     * 概率这种东西"看起来对"没有意义 —— 写成 {@code nextInt(1000) < 60} 也能编译、也能跑，
     * 但实际是 6%。抽成不认识注册表的纯函数之后，就能拿几十万次抽样去<b>验分布</b>
     * （见 {@code build/zftools/check/SaltChanceCheck.java}），这是本项目第六个可脱离游戏验算的部件。</p>
     */
    public record Rolls(boolean saltReturned, boolean rawOre) {
    }

    private SaltDecomposerRecipes() {
    }

    /** 独立掷两枚骰：海盐返还、随机粗矿。（氯化钠是 100%，不必掷。） */
    public static Rolls roll(RandomSource random) {
        boolean salt = random.nextInt(100) < SALT_RETURN_PERCENT;
        boolean ore = random.nextInt(100) < RAW_ORE_PERCENT;
        return new Rolls(salt, ore);
    }

    /**
     * "所有种类的粗矿" = 矿石模块注册的那 7 个（铝/钴/锂/镍/银/铀/锰）。
     *
     * <p><b>懒加载</b>，理由同 {@link MachineRecipes}：这里要读 {@code PotatoSTOres.*.get()}，
     * 写成 {@code static final} 会在注册完成前触发
     * {@code Trying to access unbound value}（§4.1 那次启动崩溃）。</p>
     */
    public static List<Item> allRawOres() {
        return List.of(
                PotatoSTOres.RAW_ALUMINUM.get(),
                PotatoSTOres.RAW_COBALT.get(),
                PotatoSTOres.RAW_LITHIUM.get(),
                PotatoSTOres.RAW_NICKEL.get(),
                PotatoSTOres.RAW_SILVER.get(),
                PotatoSTOres.RAW_URANIUM.get(),
                PotatoSTOres.RAW_MANGANESE.get());
    }

    /** 随机一个粗矿（只掷一次，由调用方保证结果被复用，避免"判断时掷一次、写入时又掷一次"）。 */
    public static ItemStack rollRawOre(RandomSource random) {
        List<Item> raws = allRawOres();
        return new ItemStack(raws.get(random.nextInt(raws.size())));
    }
}
