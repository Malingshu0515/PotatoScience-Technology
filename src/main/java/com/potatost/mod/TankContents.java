package com.potatost.mod;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.world.item.component.CustomData;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.neoforge.fluids.FluidStack;

/**
 * High-pressure gas tank contents helper (0.03).
 *
 * Storage: the vanilla CUSTOM_DATA component on the ItemStack:
 *   {"gases": {"potato_s_t:oxygen": 1200, "potato_s_t:hydrogen": 500}}
 * key = fluid registry name, value = amount in mB. Sum is capped at CAPACITY.
 *
 * Why the gas amount is NOT stored in DataComponents.DAMAGE:
 *   1) Item.durability(n) forces stacksTo(1) and combining it with stacksTo()
 *      throws IllegalStateException("Item cannot have both durability and be stackable");
 *   2) a damage value pollutes item comparison / stacking;
 *   3) mixed contents cannot be expressed by a single int anyway.
 *   The white fill bar is drawn by HighPressureTankItem overriding
 *   isBarVisible / getBarWidth / getBarColor instead.
 */
public final class TankContents {

    /** Total tank capacity in mB. */
    public static final int CAPACITY = 3500;

    /** NBT key holding the gas map. */
    private static final String KEY = "gases";

    /** Shared read-only empty map. */
    private static final Map<Fluid, Integer> EMPTY_MAP = Map.of();

    private TankContents() {
    }

    // ===================== read =====================

    /**
     * Reads the gas map. Corrupt data (unknown fluid id, non-positive amount,
     * over-capacity total) degrades silently: worst case the tank looks empty.
     */
    public static Map<Fluid, Integer> read(ItemStack stack) {
        CompoundTag root = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        CompoundTag gases = root.getCompound(KEY);
        if (gases.isEmpty()) {
            return EMPTY_MAP;
        }
        Map<Fluid, Integer> out = new HashMap<>();
        int total = 0;
        for (String name : gases.getAllKeys()) {
            ResourceLocation id = ResourceLocation.tryParse(name);
            if (id == null) {
                continue;
            }
            Fluid fluid = BuiltInRegistries.FLUID.get(id);
            if (fluid == null || fluid == Fluids.EMPTY) {
                continue;
            }
            int amount = gases.getInt(name);
            if (amount <= 0 || total >= CAPACITY) {
                continue;
            }
            amount = Math.min(amount, CAPACITY - total);
            out.merge(fluid, amount, Integer::sum);
            total += amount;
        }
        return out.isEmpty() ? EMPTY_MAP : out;
    }

    // ===================== write =====================

    /** Writes the whole gas map back to CUSTOM_DATA (full overwrite). */
    public static void write(ItemStack stack, Map<Fluid, Integer> contents) {
        CompoundTag gases = new CompoundTag();
        contents.forEach((fluid, amount) -> {
            if (fluid == null || fluid == Fluids.EMPTY || amount == null || amount <= 0) {
                return;
            }
            gases.putInt(fluidKey(fluid), amount);
        });
        CustomData.update(DataComponents.CUSTOM_DATA, stack, tag -> tag.put(KEY, gases));
    }

    // ===================== queries =====================

    /** Total gas in the tank (mB). */
    public static int total(ItemStack stack) {
        int sum = 0;
        for (int amount : read(stack).values()) {
            sum += amount;
        }
        return Math.min(sum, CAPACITY);
    }

    /** Amount of one specific gas (mB). */
    public static int amountOf(ItemStack stack, Fluid fluid) {
        Integer amount = read(stack).get(fluid);
        return amount == null ? 0 : amount;
    }

    public static boolean isEmpty(ItemStack stack) {
        return read(stack).isEmpty();
    }

    /** Remaining space (mB). */
    public static int space(ItemStack stack) {
        return CAPACITY - total(stack);
    }

    /** The gas with the largest amount; Fluids.EMPTY when the tank is empty. */
    public static Fluid mainFluid(ItemStack stack) {
        return read(stack).entrySet().stream()
                .max(Map.Entry.comparingByValue())
                .map(Map.Entry::getKey)
                .orElse(Fluids.EMPTY);
    }

    /**
     * Contents sorted by fluid registry name for stable tooltip output.
     * CompoundTag is backed by a HashMap, so iteration order is not stable.
     */
    public static List<Map.Entry<Fluid, Integer>> sortedContents(ItemStack stack) {
        List<Map.Entry<Fluid, Integer>> list = new ArrayList<>(read(stack).entrySet());
        list.sort((a, b) -> fluidKey(a.getKey()).compareTo(fluidKey(b.getKey())));
        return list;
    }

    /** Fluid registry name, e.g. potato_s_t:oxygen. */
    public static String fluidKey(Fluid fluid) {
        if (fluid == null || fluid == Fluids.EMPTY) {
            return "minecraft:empty";
        }
        return fluid.builtInRegistryHolder().key().location().toString();
    }

    // ===================== gas gate =====================

    /**
     * 只收气体。
     *
     * <p>⚠ <b>0.11 ZF73 改成正向白名单</b>（档案 §4.44）：这里原先是负向写法
     * 「不是水也不是岩浆 ⇒ 气体」，在"世界上只有水和岩浆两种液体"的前提下等价，
     * 但一加原油就变成错的 —— 原油既不是水也不是岩浆，于是
     * {@link #fill} 会把原油灌进高压气罐，直接违反用户规则「不可以罐装气体」。
     * 现在统一委托 {@link ModFluids#isGas}，只认本模组那 3 种气体（含流动变体）。</p>
     */
    public static boolean isGas(Fluid fluid) {
        return ModFluids.isGas(fluid);
    }

    // ===================== fill / drain =====================

    /**
     * Fills the tank.
     *
     * @param maxAmount upper bound for this call
     * @return amount actually filled (0 when nothing fitted)
     */
    public static int fill(ItemStack stack, FluidStack fluid, int maxAmount) {
        if (fluid == null || fluid.isEmpty() || maxAmount <= 0 || stack.isEmpty()) {
            return 0;
        }
        if (!isGas(fluid.getFluid())) {
            return 0;
        }
        Map<Fluid, Integer> contents = new HashMap<>(read(stack));
        int space = CAPACITY - sum(contents);
        int filled = Math.min(Math.min(fluid.getAmount(), maxAmount), Math.max(space, 0));
        if (filled <= 0) {
            return 0;
        }
        contents.merge(fluid.getFluid(), filled, Integer::sum);
        write(stack, contents);
        return filled;
    }

    /**
     * Drains up to maxAmount of one gas out of the tank (used by the filling machine).
     *
     * @return the drained fluid, FluidStack.EMPTY when nothing was available
     */
    public static FluidStack drain(ItemStack stack, Fluid gas, int maxAmount) {
        if (stack.isEmpty() || gas == null || gas == Fluids.EMPTY || maxAmount <= 0) {
            return FluidStack.EMPTY;
        }
        Map<Fluid, Integer> contents = new HashMap<>(read(stack));
        int have = contents.getOrDefault(gas, 0);
        int drained = Math.min(have, maxAmount);
        if (drained <= 0) {
            return FluidStack.EMPTY;
        }
        int left = have - drained;
        if (left > 0) {
            contents.put(gas, left);
        } else {
            contents.remove(gas);
        }
        write(stack, contents);
        return new FluidStack(gas, drained);
    }

    private static int sum(Map<Fluid, Integer> contents) {
        int sum = 0;
        for (int amount : contents.values()) {
            sum += amount;
        }
        return Mth.clamp(sum, 0, CAPACITY);
    }
}