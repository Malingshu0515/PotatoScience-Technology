package com.potatost.mod;

import com.potatost.mod.menu.MachineMenu;

import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.SimpleContainerData;

/**
 * 采油机菜单（0.11 ZF109）：<b>一个机器槽都没有</b>
 * （用户原话「gui为一个大罐子25B储量…和一个工作指示灯 能量条不需要」）
 * + 玩家背包，界面 176×166。
 *
 * <p>25B 大罐不是槽位，由界面部件 {@code FluidTankPart.horizontal(...)} 按 {@link ContainerData}
 * 里的数字实时画；两行数字（锁链根数 / 耗电与产量）由界面自己在罐子下方写。</p>
 *
 * <p>坐标常量放在菜单里、界面共用（与空气分离器 / 酸性反应室同一个做法）。</p>
 */
public class OilPumpMenu extends MachineMenu {

    /** 横躺的大油罐（与 Screen 共用） */
    public static final int TANK_X = 8;
    public static final int TANK_Y = 16;
    public static final int TANK_W = 140;
    public static final int TANK_H = 28;

    /** 工作指示灯（罐子右边） */
    public static final int LAMP_X = 154;
    public static final int LAMP_Y = 16;
    public static final int LAMP_SIZE = 10;

    /** 两行数字 */
    public static final int TEXT_X = 8;
    public static final int TEXT_Y_CHAINS = 48;
    public static final int TEXT_Y_RATE = 58;
    /** 面板是浅灰（{@code PANEL_BG} = 0xFFC6C6C6），深灰字才看得清 */
    public static final int TEXT_COLOR = 0xFF303030;

    public static final int PLAYER_INV_Y = 84;

    private final ContainerData data;

    public OilPumpMenu(int containerId, Inventory playerInventory, OilPumpBlockEntity be) {
        this(containerId, playerInventory, be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端构造（MenuType 工厂调用） */
    public OilPumpMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory,
                new SimpleContainerData(OilPumpBlockEntity.DATA_COUNT), ContainerLevelAccess.NULL);
    }

    private OilPumpMenu(int containerId, Inventory playerInventory, ContainerData data,
                        ContainerLevelAccess access) {
        // ⚠ machineSlots = 0：这台机器一个槽都没有（基类的 Shift 逻辑照样成立）
        super(ModMenus.OIL_PUMP_MENU.get(), containerId, OilPumpBlockEntity.SLOT_COUNT, access);
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

    public int getStatus() {
        return this.data.get(OilPumpBlockEntity.DATA_STATUS);
    }

    public int getEnergy() {
        return Mth.clamp(this.data.get(OilPumpBlockEntity.DATA_ENERGY), 0,
                OilPumpBlockEntity.MAX_ENERGY);
    }

    public int getOil() {
        return Mth.clamp(this.data.get(OilPumpBlockEntity.DATA_OIL), 0,
                OilPumpBlockEntity.TANK_CAPACITY);
    }

    /** n：下方含水锁链根数 */
    public int getChains() {
        return Math.max(0, Math.min(this.data.get(OilPumpBlockEntity.DATA_CHAINS),
                OilPumpBlockEntity.MAX_CHAIN_SCAN));
    }

    public int getFePerTick() {
        return OilPumpBlockEntity.fePerTick(this.getChains());
    }

    public int getMbPerSecond() {
        return OilPumpBlockEntity.mbPerSecond(this.getChains());
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.OIL_PUMP.get());
    }
}
