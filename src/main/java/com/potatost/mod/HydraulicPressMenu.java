package com.potatost.mod;

import com.potatost.mod.menu.MachineMenu;

import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.items.ItemStackHandler;
import net.neoforged.neoforge.items.SlotItemHandler;

/**
 * 液压机菜单：左边 1 个输入槽、右边 1 个输出槽 + 玩家背包；界面 176x166。
 *
 * <p>槽位坐标与 {@code HydraulicPressScreen} 里的进度条 / 状态灯 / 能量条共享同一坐标系：
 * 输入槽中心 (44,35) → 进度条 → 输出槽中心 (116,35)，箭头正好横在两者之间。</p>
 */
public class HydraulicPressMenu extends MachineMenu {

    public static final int INPUT_SLOT_X = 44;
    public static final int INPUT_SLOT_Y = 35;

    public static final int OUTPUT_SLOT_X = 116;
    public static final int OUTPUT_SLOT_Y = 35;

    private final ContainerData data;

    public HydraulicPressMenu(int containerId, Inventory playerInventory, HydraulicPressBlockEntity be) {
        this(containerId, playerInventory, be.getInventory(), be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端构造（MenuType 工厂调用） */
    public HydraulicPressMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory, new ItemStackHandler(HydraulicPressBlockEntity.SLOT_COUNT),
                new SimpleContainerData(HydraulicPressBlockEntity.DATA_COUNT), ContainerLevelAccess.NULL);
    }

    private HydraulicPressMenu(int containerId, Inventory playerInventory, ItemStackHandler machineInventory,
                               ContainerData data, ContainerLevelAccess access) {
        super(ModMenus.HYDRAULIC_PRESS_MENU.get(), containerId, HydraulicPressBlockEntity.SLOT_COUNT, access);
        this.data = data;
        this.addDataSlots(data);

        // 输入槽：什么都能放（放错由状态灯提示黄灯，而不是被槽位挡住）
        this.addSlot(new SlotItemHandler(machineInventory, HydraulicPressBlockEntity.INPUT_SLOT,
                INPUT_SLOT_X, INPUT_SLOT_Y));

        // 输出槽：只能取不能放
        this.addSlot(new SlotItemHandler(machineInventory, HydraulicPressBlockEntity.OUTPUT_SLOT,
                OUTPUT_SLOT_X, OUTPUT_SLOT_Y) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return false;
            }
        });

        this.addPlayerInventory(playerInventory, 84);
    }

    /** Shift 点击：能压的锭直接塞进输入槽；其余走基类默认逻辑。 */
    @Override
    protected int getMachineSlotFor(ItemStack stack) {
        return PressRecipes.find(stack) != null ? HydraulicPressBlockEntity.INPUT_SLOT : -1;
    }

    public int getEnergy() {
        return this.data.get(HydraulicPressBlockEntity.DATA_ENERGY);
    }

    public int getProgress() {
        return this.data.get(HydraulicPressBlockEntity.DATA_PROGRESS);
    }

    public int getProgressMax() {
        return this.data.get(HydraulicPressBlockEntity.DATA_PROGRESS_MAX);
    }

    public int getStatus() {
        return this.data.get(HydraulicPressBlockEntity.DATA_STATUS);
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.HYDRAULIC_PRESS.get());
    }
}
