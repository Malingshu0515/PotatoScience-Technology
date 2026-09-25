package com.potatost.mod;

import com.potatost.mod.menu.MachineMenu;

import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.items.ItemStackHandler;
import net.neoforged.neoforge.items.SlotItemHandler;

/**
 * 燃烧反应室菜单（0.11 ZF100）：<b>1 个燃料槽 + 1 个燃烧副产物槽</b> + 玩家背包，界面 176×166。
 *
 * <p>版面（与 {@link com.potatost.mod.client.CombustionChamberScreen} 同一套坐标系）：</p>
 * <pre>
 *   氧气罐 (26,17) → 二氧化碳罐 (48,17) → 水罐 (70,17) → 箭头 (96,33,22×16) → 燃料槽 (126,26)
 *                                                        状态灯 (103,52,8×8)      副产物槽 (126,48)
 * </pre>
 * 三个罐都不是槽位，由界面部件 {@code FluidTankPart} 按 {@link ContainerData} 里的数字实时画。
 */
public class CombustionChamberMenu extends MachineMenu {

    /** 燃料槽（与 Screen 共用） */
    public static final int FUEL_SLOT_X = 126;
    public static final int FUEL_SLOT_Y = 26;

    /** 燃烧副产物槽（与 Screen 共用） */
    public static final int BYPRODUCT_SLOT_X = 126;
    public static final int BYPRODUCT_SLOT_Y = 48;

    /** 玩家背包起始 y（三行 + 快捷栏） */
    public static final int PLAYER_INV_Y = 84;

    private final ContainerData data;

    public CombustionChamberMenu(int containerId, Inventory playerInventory,
                                 CombustionChamberBlockEntity be) {
        this(containerId, playerInventory, be.getInventory(), be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端构造（MenuType 工厂调用） */
    public CombustionChamberMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory,
                new ItemStackHandler(CombustionChamberBlockEntity.SLOT_COUNT),
                new SimpleContainerData(CombustionChamberBlockEntity.DATA_COUNT),
                ContainerLevelAccess.NULL);
    }

    private CombustionChamberMenu(int containerId, Inventory playerInventory,
                                  ItemStackHandler machineInventory, ContainerData data,
                                  ContainerLevelAccess access) {
        super(ModMenus.COMBUSTION_CHAMBER_MENU.get(), containerId,
                CombustionChamberBlockEntity.SLOT_COUNT, access);
        this.data = data;
        this.addDataSlots(data);

        // 燃料槽：只收"原版熔炉认的燃料"（+ 柴油/汽油桶）
        // ⚠ 与方块实体里的 isItemValid 是**同一道门禁**，两处必须一起改（§4.51）
        this.addSlot(new SlotItemHandler(machineInventory, CombustionChamberBlockEntity.FUEL_SLOT,
                FUEL_SLOT_X, FUEL_SLOT_Y) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return CombustionChamberBlockEntity.isFuel(stack);
            }
        });

        // 副产物槽：只能取不能放
        this.addSlot(new SlotItemHandler(machineInventory, CombustionChamberBlockEntity.BYPRODUCT_SLOT,
                BYPRODUCT_SLOT_X, BYPRODUCT_SLOT_Y) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return false;
            }
        });

        this.addPlayerInventory(playerInventory, PLAYER_INV_Y);
    }

    /** Shift 点击：燃料直接塞进燃料槽（其余走基类默认逻辑，进玩家背包）。 */
    @Override
    protected int getMachineSlotFor(ItemStack stack) {
        return CombustionChamberBlockEntity.isFuel(stack)
                ? CombustionChamberBlockEntity.FUEL_SLOT : -1;
    }

    // ================= 读数（界面部件用） =================

    public int getProgress() {
        return Mth.clamp(this.data.get(CombustionChamberBlockEntity.DATA_PROGRESS), 0,
                Math.max(1, getProgressMax()));
    }

    public int getProgressMax() {
        int max = this.data.get(CombustionChamberBlockEntity.DATA_PROGRESS_MAX);
        return max > 0 ? max : CombustionChamberBlockEntity.DURATION_DEFAULT;
    }

    public int getStatus() {
        return this.data.get(CombustionChamberBlockEntity.DATA_STATUS);
    }

    public int getOxygenAmount() {
        return Mth.clamp(this.data.get(CombustionChamberBlockEntity.DATA_OXYGEN), 0,
                CombustionChamberBlockEntity.OXYGEN_CAPACITY);
    }

    public int getCo2Amount() {
        return Mth.clamp(this.data.get(CombustionChamberBlockEntity.DATA_CO2), 0,
                CombustionChamberBlockEntity.CO2_CAPACITY);
    }

    public int getWaterAmount() {
        return Mth.clamp(this.data.get(CombustionChamberBlockEntity.DATA_WATER), 0,
                CombustionChamberBlockEntity.WATER_CAPACITY);
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.COMBUSTION_CHAMBER.get());
    }
}
