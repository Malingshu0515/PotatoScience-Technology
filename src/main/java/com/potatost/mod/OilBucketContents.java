package com.potatost.mod;

import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.neoforge.fluids.FluidStack;

/**
 * 油桶内容物（0.11 ZF73）。
 *
 * <p><b>为什么另写一份，不把 {@link TankContents} 改成通用的</b>：两者语义不同 ——</p>
 * <ul>
 *   <li>高压气罐：3500 mB、**允许多种气体混装**（存 map）；</li>
 *   <li>油桶：3000 mB、**只允许存在一种流体**（用户原话「只可以存在一种流体
 *       异种流体不可以再被灌装进油桶」）。</li>
 * </ul>
 * <p>把已发布的气罐语义改成"单流体 + 可变容量"是纯粹的回归风险，所以另写一份。
 * 表现层（白色容量条 / Shift tooltip）两边一致。</p>
 *
 * <p>存档格式（{@code CUSTOM_DATA}）：{@code {"fluid": {"id": "potato_s_t:crude_oil", "amount": 1000}}}</p>
 */
public final class OilBucketContents {

    /** 容量：用户定的 3000 mB。 */
    public static final int CAPACITY = 3000;

    /** 一格源方块 = 1000 mB（原版口径；舀一次正好一格）。 */
    public static final int SOURCE_AMOUNT = 1000;

    private static final String KEY = "fluid";
    private static final String KEY_ID = "id";
    private static final String KEY_AMOUNT = "amount";

    private OilBucketContents() {
    }

    // ===================== 读 =====================

    /** 桶里那种流体；空桶返回 {@link Fluids#EMPTY}。坏数据（id 解析不出来/数量非法）当空桶。 */
    public static Fluid fluid(ItemStack stack) {
        if (stack.isEmpty()) {
            return Fluids.EMPTY;
        }
        CompoundTag root = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        if (!root.contains(KEY)) {
            return Fluids.EMPTY;
        }
        CompoundTag tag = root.getCompound(KEY);
        int amount = tag.getInt(KEY_AMOUNT);
        if (amount <= 0) {
            return Fluids.EMPTY;
        }
        ResourceLocation id = ResourceLocation.tryParse(tag.getString(KEY_ID));
        if (id == null) {
            return Fluids.EMPTY;
        }
        Fluid fluid = BuiltInRegistries.FLUID.get(id);
        if (fluid == null || fluid == Fluids.EMPTY) {
            return Fluids.EMPTY;
        }
        return fluid;
    }

    /** 桶里有多少 mB（0 = 空）。 */
    public static int amount(ItemStack stack) {
        if (stack.isEmpty()) {
            return 0;
        }
        CompoundTag root = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        if (!root.contains(KEY)) {
            return 0;
        }
        int amount = root.getCompound(KEY).getInt(KEY_AMOUNT);
        if (amount <= 0 || fluid(stack) == Fluids.EMPTY) {
            return 0;
        }
        return Math.min(amount, CAPACITY);
    }

    /** 与气罐 tooltip 的「总量」对齐用的别名。 */
    public static int total(ItemStack stack) {
        return amount(stack);
    }

    public static boolean isEmpty(ItemStack stack) {
        return amount(stack) <= 0;
    }

    /** 还能装多少 mB。 */
    public static int space(ItemStack stack) {
        return CAPACITY - amount(stack);
    }

    // ===================== 写 =====================

    private static void write(ItemStack stack, Fluid fluid, int amount) {
        if (stack.isEmpty()) {
            return;
        }
        if (fluid == null || fluid == Fluids.EMPTY || amount <= 0) {
            CustomData.update(DataComponents.CUSTOM_DATA, stack, tag -> tag.remove(KEY));
            return;
        }
        CompoundTag tag = new CompoundTag();
        tag.putString(KEY_ID, fluid.builtInRegistryHolder().key().location().toString());
        tag.putInt(KEY_AMOUNT, Math.min(amount, CAPACITY));
        CustomData.update(DataComponents.CUSTOM_DATA, stack, root -> root.put(KEY, tag));
    }

    /**
     * 往桶里灌。
     *
     * <p>三道拒收：① 不是液体（气体挡在 {@link #accepts}）；② 桶里已有**异种**流体；
     * ③ 装不下（一点都装不下就返回 0）。</p>
     *
     * @return 实际灌进去的 mB
     */
    public static int fill(ItemStack stack, FluidStack resource, int maxAmount) {
        if (stack.isEmpty() || resource == null || resource.isEmpty() || maxAmount <= 0) {
            return 0;
        }
        Fluid incoming = resource.getFluid();
        if (!accepts(incoming)) {
            return 0;
        }
        Fluid have = fluid(stack);
        if (have != Fluids.EMPTY && have != incoming) {
            return 0;
        }
        int moved = Math.min(Math.min(resource.getAmount(), maxAmount), Math.max(space(stack), 0));
        if (moved <= 0) {
            return 0;
        }
        write(stack, incoming, amount(stack) + moved);
        return moved;
    }

    /** 往外倒（本轮还没有"倒出"的交互，先给后续的储罐/分馏塔留着）。 */
    public static FluidStack drain(ItemStack stack, int maxAmount) {
        if (stack.isEmpty() || maxAmount <= 0) {
            return FluidStack.EMPTY;
        }
        Fluid have = fluid(stack);
        int amount = amount(stack);
        if (have == Fluids.EMPTY || amount <= 0) {
            return FluidStack.EMPTY;
        }
        int drained = Math.min(amount, maxAmount);
        write(stack, have, amount - drained);
        return new FluidStack(have, drained);
    }

    /**
     * 收不收这种流体：**必须是液体**（非空、非气体）。
     *
     * <p>「不可以罐装气体」这条用户规则就落在这里 —— 也是 §4.44 那个雷的正解。</p>
     */
    public static boolean accepts(Fluid fluid) {
        return ModFluids.isLiquid(fluid);
    }
}
