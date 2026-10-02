package com.potatost.mod;

import java.util.List;

import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/**
 * 饮料罐装机的配方表（0.13 ZF167）。
 *
 * <p><b>用户原话</b>：「先做一个配方试试水 1.10mb碳酸+500mb水+2糖+1可可豆+1空铝罐
 * 5s产出1罐可乐」。</p>
 *
 * <h2>槽位口径（这台机器只有三个输入槽，用户这么定的）</h2>
 * <pre>
 *   槽 0 = 糖        （这一条要 2 个）
 *   槽 1 = 可可豆    （这一条要 1 个）
 *   槽 2 = 空铝罐    （这一条要 1 个）
 *   槽 3 = 输出      （可乐）
 * </pre>
 * <p>三个输入槽**按物品固定**，不按"任意顺序塞"：与本工程其它多槽机器同一条口径
 * （锂电池构造间那台就是"槽 0 粗锰/粗铝、槽 1 镍、槽 2 碳酸锂、槽 3 钴"），
 * 好处是玩家一眼看得懂、也省掉"三槽任意排列组合"的匹配开销。</p>
 *
 * <h2>三种流体（用户给的数，一个字没改）</h2>
 * <pre>
 *   碳酸 10 mB ／ 水 500 mB ／ 乙醇 0 mB（这一条**不用**乙醇 —— 那只罐是留给以后配方的）
 * </pre>
 * <p>⚠ <b>为什么流体在"完成那一刻"一次性扣、而不是每 tick 扣一点</b>：10 mB ÷ 100 tick
 * = 0.1 mB/tick，**除不尽**（整数运算会一路丢余数，最后要么少扣、要么多扣）。
 * 每 tick 只**检查**够不够、完成时**整批扣**，账目是整数、也永远不会"跑了一半发现流体不够
 * 却已经把料吃掉了"。中途被管道抽走 ⇒ 这台机器停在"缺流体"状态、进度保留（见方块实体）。</p>
 *
 * <p><b>⚠ 这张表里不许出现 {@code static final ItemStack}</b>：物品栈要在注册完成之后才建得出来，
 * 写成静态字段就会撞 §4.1 那条"Trying to access unbound value"（{@code MicroCrusherRecipes}
 * 的类注释里记着同一条）。所以 {@link Can#result()} 是**现取**的，{@code Can} 里存的是
 * {@code Item}，产出那一栈在 {@link #find} 里现造。</p>
 */
public final class CanningMachineRecipes {

    /** 一轮 5 秒（用户给的）。 */
    public static final int DURATION_TICKS = 20 * 5;

    /** 工作时的耗电：600 FE/t（用户给的）⇒ 一轮 100 tick × 600 = **60,000 FE**。 */
    public static final int ENERGY_PER_TICK = 600;

    /** 这一条要几份糖 / 可可豆 / 空铝罐。 */
    public static final int SUGAR_COUNT = 2;
    public static final int COCOA_COUNT = 1;
    public static final int CAN_COUNT = 1;

    /** 这一条要多少 mB 碳酸 / 水 / 乙醇。 */
    public static final int CARBONIC_MB = 10;
    public static final int WATER_MB = 500;
    public static final int ETHANOL_MB = 0;

    /**
     * 一条罐装配方。
     *
     * @param sugar     要几份糖（槽 0）
     * @param cocoa     要几份可可豆（槽 1）
     * @param cans      要几个空铝罐（槽 2）
     * @param carbonicMb 要多少 mB 碳酸（碳酸罐）
     * @param waterMb   要多少 mB 水（水罐）
     * @param ethanolMb 要多少 mB 乙醇（乙醇罐；当前这一条是 0）
     * @param result    产出物品（**现取**，见类注释）
     * @param resultCount 产出数量
     * @param durationTicks 一轮多少 tick
     * @param energyPerTick 每 tick 耗电
     */
    public record Can(int sugar, int cocoa, int cans, int carbonicMb, int waterMb, int ethanolMb,
                      net.minecraft.world.item.Item result, int resultCount,
                      int durationTicks, int energyPerTick) {

        /** 一轮总共要多少 FE。 */
        public int totalEnergy() {
            return this.durationTicks * this.energyPerTick;
        }

        /** 产出那一栈（现造：物品栈必须在注册完成之后才建得出来）。 */
        public ItemStack createOutput() {
            return new ItemStack(this.result, this.resultCount);
        }
    }

    private CanningMachineRecipes() {
    }

    /**
     * 全部配方（懒建）。
     *
     * <p>"先做一个配方试试水" —— 这一轮**只有一条**（可乐）。表做成 List 是因为
     * 用户已经给了那只乙醇罐，明显还有下一条（比如"苏打水"），加一条就是往这里添一行。</p>
     */
    private static List<Can> recipes;

    private static List<Can> table() {
        if (recipes == null) {
            recipes = List.of(new Can(SUGAR_COUNT, COCOA_COUNT, CAN_COUNT,
                    CARBONIC_MB, WATER_MB, ETHANOL_MB,
                    ModItems.COLA.get(), 1, DURATION_TICKS, ENERGY_PER_TICK));
        }
        return recipes;
    }

    /**
     * 按三个输入槽找配方；找不到返回 {@code null}（机器据此显示"配方无效"）。
     *
     * <p>判据只吃**物品种类与数量**，流体够不够由方块实体自己查
     * （流体在罐里、不在槽里，这里看不到）。</p>
     */
    public static Can find(ItemStack sugarSlot, ItemStack cocoaSlot, ItemStack canSlot) {
        for (Can can : table()) {
            if (matches(sugarSlot, Items.SUGAR, can.sugar())
                    && matches(cocoaSlot, Items.COCOA_BEANS, can.cocoa())
                    && matches(canSlot, ModItems.EMPTY_ALUMINUM_CAN.get(), can.cans())) {
                return can;
            }
        }
        return null;
    }

    /** 这一槽是不是"正好是某种物品、且数量够"。 */
    private static boolean matches(ItemStack stack, net.minecraft.world.item.Item item, int need) {
        return !stack.isEmpty() && stack.is(item) && stack.getCount() >= need;
    }

    /** 一共几条配方（探针/校验用）。 */
    public static int count() {
        return table().size();
    }
}
