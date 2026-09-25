package com.potatost.mod;

import java.util.List;
import java.util.Map;

import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.neoforge.fluids.FluidStack;

/**
 * High-pressure gas tank (0.03).
 *   - not stackable (Properties.stacksTo(1)), 3500 mB total, mixing allowed
 *   - filled only by the filling machine; no hand pouring / no direct interaction
 *     (this class deliberately overrides no use/interaction method)
 *   - the vanilla durability-bar slot shows a WHITE bar following the fill level
 *   - hydrogen >= 2800 mB detonates on contact with fire / lava / lit campfire
 *     (detection lives in GasTankExplosionHandler, phase ZF3)
 */
public class HighPressureTankItem extends Item implements FluidContainerItem {

    /** Hydrogen amount that makes the tank dangerous (mB). */
    public static final int HYDROGEN_EXPLOSION_THRESHOLD = 2800;

    /** Full bar width (vanilla constant Item.MAX_BAR_WIDTH). */
    private static final int BAR_FULL_WIDTH = 13;

    /** Tolerance used by isFull (mB). */
    private static final int FULL_TOLERANCE = 1;

    public HighPressureTankItem(Properties properties) {
        super(properties);
    }

    // ===================== fill bar (replaces the durability bar) =====================

    /** Empty tanks draw no bar at all. */
    @Override
    public boolean isBarVisible(ItemStack stack) {
        return TankContents.total(stack) > 0;
    }

    /** 0..13, proportional to the fill level. */
    @Override
    public int getBarWidth(ItemStack stack) {
        int total = TankContents.total(stack);
        if (total <= 0) {
            return 0;
        }
        return (int) Math.round((double) BAR_FULL_WIDTH * Math.min(total, TankContents.CAPACITY)
                / TankContents.CAPACITY);
    }

    /** Always white; the vanilla renderer forces alpha to 0xFF. */
    @Override
    public int getBarColor(ItemStack stack) {
        return 0xFFFFFF;
    }

    // ===================== tooltip =====================

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context,
                                List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
        if (!tooltipFlag.hasShiftDown() && !tooltipFlag.isAdvanced()) {
            tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
            return;
        }

        int total = TankContents.total(stack);
        tooltipComponents.add(Component.translatable("tooltip.potato_s_t.high_pressure_tank.total",
                total, TankContents.CAPACITY));

        if (total <= 0) {
            tooltipComponents.add(Component.translatable("tooltip.potato_s_t.high_pressure_tank.empty"));
            return;
        }

        for (Map.Entry<Fluid, Integer> entry : TankContents.sortedContents(stack)) {
            tooltipComponents.add(Component.translatable("tooltip.potato_s_t.high_pressure_tank.entry",
                    entry.getKey().getFluidType().getDescription(), entry.getValue()));
        }

        if (hasHydrogenAtLeast(stack, HYDROGEN_EXPLOSION_THRESHOLD)) {
            tooltipComponents.add(Component.translatable("tooltip.potato_s_t.high_pressure_tank.hydrogen_risk",
                    HYDROGEN_EXPLOSION_THRESHOLD));
        }
    }

    // ===================== used by the explosion check =====================

    /** True when the tank holds at least `threshold` mB of hydrogen (mixed contents included). */
    public static boolean hasHydrogenAtLeast(ItemStack stack, int threshold) {
        return TankContents.amountOf(stack, ModFluids.HYDROGEN.get()) >= threshold;
    }

    /** True when the tank cannot take any more gas. */
    public static boolean isFull(ItemStack itemStack) {
        return TankContents.total(itemStack) >= TankContents.CAPACITY - FULL_TOLERANCE;
    }

    // ===================== FluidContainerItem（0.11 ZF73：灌装机只认接口）=====================

    @Override
    public int space(ItemStack stack) {
        return TankContents.space(stack);
    }

    /** 气罐只收气体（判定已改成 {@link ModFluids#isGas} 的正向白名单，见档案 §4.44）。 */
    @Override
    public boolean accepts(Fluid fluid) {
        return TankContents.isGas(fluid);
    }

    @Override
    public int fill(ItemStack stack, FluidStack fluid, int maxAmount) {
        return TankContents.fill(stack, fluid, maxAmount);
    }

    @Override
    public boolean isEmpty(ItemStack stack) {
        return TankContents.isEmpty(stack);
    }

    // ---- 0.11 ZF78：取出来（与油桶同一条接口；气罐目前没被哪个机器倒过，但接口要求实现）----

    @Override
    public FluidStack contents(ItemStack stack) {
        Fluid gas = TankContents.mainFluid(stack);
        if (gas == null || gas == Fluids.EMPTY) {
            return FluidStack.EMPTY;
        }
        return new FluidStack(gas, TankContents.amountOf(stack, gas));
    }

    @Override
    public FluidStack drain(ItemStack stack, int maxAmount) {
        FluidStack held = contents(stack);
        if (held.isEmpty()) {
            return FluidStack.EMPTY;
        }
        return TankContents.drain(stack, held.getFluid(), maxAmount);
    }
}