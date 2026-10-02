package com.potatost.mod;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.neoforge.fluids.FluidStack;

import com.potatost.mod.menu.MachineMenu;

/**
 * 流体转化器菜单（0.13 ZF166）：**没有机器物品槽**（只有玩家背包）+ 两根流体槽 + 一根能量条。
 *
 * <p>罐里的<b>流体种类</b>不走 {@code ContainerData} 的整数编号，而是同步<b>流体注册表 id</b>
 * （0 = {@code minecraft:empty}），这样任何流体都能正确显示（与灌装机 ZF73 那次同一个口径）。</p>
 *
 * <p>状态（为什么没在转）是<b>服务端算好再同步</b>的（{@link FluidConverterBlockEntity#DATA_STATE}），
 * 界面不自己再判一遍 —— 免得出现"界面说的和代码做的不一样"（§4.51）。</p>
 */
public class FluidConverterMenu extends MachineMenu {

    /** 两个罐在界面上的位置（与 {@code FluidConverterScreen} 同一坐标）。 */
    public static final int TANK_W = 18;
    public static final int TANK_H = 52;
    public static final int INPUT_X = 44;
    public static final int OUTPUT_X = 114;
    public static final int TANK_Y = 18;
    public static final int ENERGY_X = 26;
    public static final int ENERGY_Y = 18;
    public static final int ENERGY_W = 10;
    public static final int ENERGY_H = 52;

    /**
     * 玩家背包第一行的 y。
     *
     * <p>界面高度 = 这个值 + 84 = 202（与分馏塔操作器同一个版面口径）：罐子下面要留三行字
     * （输入罐 / 输出罐 / 状态），而基类把「物品栏」标签画在 {@code imageHeight - 93}
     * —— 用默认的 102 会正好压在那三行字上。</p>
     */
    public static final int PLAYER_INV_Y = 118;

    private final ContainerData data;

    public FluidConverterMenu(int containerId, Inventory playerInventory, FluidConverterBlockEntity be) {
        this(containerId, playerInventory, be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端构造器（MenuType 工厂用）。 */
    public FluidConverterMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory,
                new SimpleContainerData(FluidConverterBlockEntity.DATA_COUNT), ContainerLevelAccess.NULL);
    }

    private FluidConverterMenu(int containerId, Inventory playerInventory, ContainerData data,
                               ContainerLevelAccess access) {
        super(ModMenus.FLUID_CONVERTER_MENU.get(), containerId, 0, access);
        this.data = data;
        this.addDataSlots(data);
        this.addPlayerInventory(playerInventory, PLAYER_INV_Y);
    }

    public int getEnergy() {
        return this.data.get(FluidConverterBlockEntity.DATA_ENERGY);
    }

    public int getInputAmount() {
        return this.data.get(FluidConverterBlockEntity.DATA_INPUT);
    }

    public int getOutputAmount() {
        return this.data.get(FluidConverterBlockEntity.DATA_OUTPUT);
    }

    public Fluid getInputFluid() {
        return BuiltInRegistries.FLUID.byId(this.data.get(FluidConverterBlockEntity.DATA_INPUT_FLUID));
    }

    public Fluid getOutputFluid() {
        return BuiltInRegistries.FLUID.byId(this.data.get(FluidConverterBlockEntity.DATA_OUTPUT_FLUID));
    }

    public FluidStack getInputStack() {
        int amount = getInputAmount();
        return amount <= 0 ? FluidStack.EMPTY : new FluidStack(getInputFluid(), amount);
    }

    public FluidStack getOutputStack() {
        int amount = getOutputAmount();
        return amount <= 0 ? FluidStack.EMPTY : new FluidStack(getOutputFluid(), amount);
    }

    /** 空罐时要有个非空流体给部件画底（部件是按 {@code Fluid} 画的，不能给 null）。 */
    public Fluid getInputFluidOrEmpty() {
        Fluid f = getInputFluid();
        return f == null ? Fluids.EMPTY : f;
    }

    public Fluid getOutputFluidOrEmpty() {
        Fluid f = getOutputFluid();
        return f == null ? Fluids.EMPTY : f;
    }

    /**
     * 服务端同步过来的状态码（见 {@link FluidConverterBlockEntity#DATA_STATE}）：
     * 0 = 服务端还没算过（界面显示「待机」），1..7 与 {@link FluidConverterBlockEntity.State} 一一对应。
     *
     * <p>界面把它原样交给 {@link FluidConverterBlockEntity#statusLine}，自己不再判一遍。</p>
     */
    public int getStateCode() {
        return this.data.get(FluidConverterBlockEntity.DATA_STATE);
    }

    @Override
    protected int getMachineSlotFor(net.minecraft.world.item.ItemStack stack) {
        // 本机器没有物品槽：Shift 快移只在玩家背包内部挪（返回 −1 = 走基类那条"背包内互换"的路）
        return -1;
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.FLUID_CONVERTER.get());
    }
}
