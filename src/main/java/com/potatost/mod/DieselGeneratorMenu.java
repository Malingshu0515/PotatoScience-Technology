package com.potatost.mod;

import com.potatost.mod.menu.MachineMenu;

import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.SimpleContainerData;

/**
 * 大型柴油发电机的菜单（0.11 ZF125）：<b>一个机器槽都没有</b>
 * （用户原话「右键打开GUI 显示流体储罐（8000mB）工作指示灯」）+ 玩家背包，界面 176×166。
 *
 * <p>柴油罐不是槽位，由界面部件 {@code FluidTankPart} 按 {@link ContainerData} 里的数字实时画。
 * 因为机器槽数是 0，Shift 点击只会在玩家背包内部搬运（基类 {@code quickMoveStack} 天然成立）。</p>
 */
public class DieselGeneratorMenu extends MachineMenu {

    /** 柴油罐（与 Screen 共用） */
    public static final int TANK_X = 62;
    public static final int TANK_Y = 17;
    public static final int TANK_W = 18;
    public static final int TANK_H = 52;

    /**
     * 能量条（0.11 ZF126）。
     *
     * <p>用户原话「这个加个fe缓存 18k的fe」—— 缓冲本身是方块实体里的
     * {@code DieselGeneratorBlockEntity.MAX_ENERGY}；这里只是把它**画出来**
     * （放下界面之前看不见的那个数，玩家就只能靠猜）。</p>
     */
    public static final int ENERGY_X = 34;
    public static final int ENERGY_Y = 17;
    public static final int ENERGY_W = 12;
    public static final int ENERGY_H = 52;

    /** 工作指示灯 */
    public static final int LAMP_X = 108;
    public static final int LAMP_Y = 38;
    public static final int LAMP_SIZE = 8;

    public static final int PLAYER_INV_Y = 84;

    private final ContainerData data;

    public DieselGeneratorMenu(int containerId, Inventory playerInventory, DieselGeneratorBlockEntity be) {
        this(containerId, playerInventory, be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端构造（MenuType 工厂调用） */
    public DieselGeneratorMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory,
                new SimpleContainerData(DieselGeneratorBlockEntity.DATA_COUNT), ContainerLevelAccess.NULL);
    }

    private DieselGeneratorMenu(int containerId, Inventory playerInventory, ContainerData data,
                                ContainerLevelAccess access) {
        // ⚠ machineSlots = 0：这台机器一个槽都没有（基类的 Shift 逻辑照样成立）
        super(ModMenus.DIESEL_GENERATOR_MENU.get(), containerId,
                DieselGeneratorBlockEntity.SLOT_COUNT, access);
        this.data = data;
        this.addDataSlots(data);
        this.addPlayerInventory(playerInventory, PLAYER_INV_Y);
    }

    /** 没有机器槽 ⇒ Shift 点击只走基类的"背包内部搬运"。 */
    @Override
    protected int getMachineSlotFor(net.minecraft.world.item.ItemStack stack) {
        return -1;
    }

    // ================= 读数（界面部件用） =================

    public int getDiesel() {
        return Mth.clamp(this.data.get(DieselGeneratorBlockEntity.DATA_DIESEL), 0,
                DieselGeneratorBlockEntity.TANK_CAPACITY);
    }

    public int getStatus() {
        return this.data.get(DieselGeneratorBlockEntity.DATA_STATUS);
    }

    public int getEnergy() {
        return Mth.clamp(this.data.get(DieselGeneratorBlockEntity.DATA_ENERGY), 0,
                DieselGeneratorBlockEntity.MAX_ENERGY);
    }

    /** 结构完整吗（界面上暂时只用来做悬停/调试，灯本身看的是 19 号状态）。 */
    public boolean isFormed() {
        return this.data.get(DieselGeneratorBlockEntity.DATA_STRUCTURE) != 0;
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.DIESEL_GENERATOR.get());
    }
}
