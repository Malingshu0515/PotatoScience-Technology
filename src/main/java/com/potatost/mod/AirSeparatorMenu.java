package com.potatost.mod;

import com.potatost.mod.menu.MachineMenu;

import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.SimpleContainerData;

/**
 * 空气分离器菜单（0.11 ZF97）：<b>一个机器槽都没有</b>（用户原话「gui只有两个储罐…
 * 一个工作指示灯」）+ 玩家背包，界面 176×166。
 *
 * <p>两个储罐不是槽位，由界面部件 {@code FluidTankPart} 按 {@link ContainerData} 里的数字实时画。
 * 因为机器槽数是 0，Shift 点击只会在玩家背包内部搬运（基类 {@code quickMoveStack} 天然成立）。</p>
 */
public class AirSeparatorMenu extends MachineMenu {

    /** 氮气罐（与 Screen 共用） */
    public static final int NITROGEN_X = 46;
    public static final int NITROGEN_Y = 17;
    /** 氧气罐 */
    public static final int OXYGEN_X = 78;
    public static final int OXYGEN_Y = 17;
    /** 两个罐共用的尺寸 */
    public static final int TANK_W = 18;
    public static final int TANK_H = 52;

    /** 工作指示灯 */
    public static final int LAMP_X = 114;
    public static final int LAMP_Y = 38;
    public static final int LAMP_SIZE = 8;

    public static final int PLAYER_INV_Y = 84;

    private final ContainerData data;

    public AirSeparatorMenu(int containerId, Inventory playerInventory, AirSeparatorBlockEntity be) {
        this(containerId, playerInventory, be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端构造（MenuType 工厂调用） */
    public AirSeparatorMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory,
                new SimpleContainerData(AirSeparatorBlockEntity.DATA_COUNT), ContainerLevelAccess.NULL);
    }

    private AirSeparatorMenu(int containerId, Inventory playerInventory, ContainerData data,
                             ContainerLevelAccess access) {
        // ⚠ machineSlots = 0：这台机器一个槽都没有（基类的 Shift 逻辑照样成立）
        super(ModMenus.AIR_SEPARATOR_MENU.get(), containerId, AirSeparatorBlockEntity.SLOT_COUNT, access);
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

    public int getEnergy() {
        return Mth.clamp(this.data.get(AirSeparatorBlockEntity.DATA_ENERGY), 0,
                AirSeparatorBlockEntity.MAX_ENERGY);
    }

    public int getProgress() {
        return Mth.clamp(this.data.get(AirSeparatorBlockEntity.DATA_PROGRESS), 0,
                AirSeparatorBlockEntity.DURATION_TICKS);
    }

    public int getProgressMax() {
        int max = this.data.get(AirSeparatorBlockEntity.DATA_PROGRESS_MAX);
        return max > 0 ? max : AirSeparatorBlockEntity.DURATION_TICKS;
    }

    public int getStatus() {
        return this.data.get(AirSeparatorBlockEntity.DATA_STATUS);
    }

    public int getNitrogen() {
        return Mth.clamp(this.data.get(AirSeparatorBlockEntity.DATA_NITROGEN), 0,
                AirSeparatorBlockEntity.TANK_CAPACITY);
    }

    public int getOxygen() {
        return Mth.clamp(this.data.get(AirSeparatorBlockEntity.DATA_OXYGEN), 0,
                AirSeparatorBlockEntity.TANK_CAPACITY);
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.AIR_SEPARATOR.get());
    }
}
