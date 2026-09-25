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
 * 电力高炉菜单（0.10 ZF39）：<b>12 输入 + 32 输出</b>，界面 196×234。
 *
 * <p>用户原话「12个输入槽 32个输出槽（有可能需要做成匠魂那样下拉式的 要不然显示不全）」，
 * ZF39 拍板改成**放大面板一次显示完**（沉浸工程那种大 GUI），所以这里没有翻页逻辑。</p>
 *
 * <p>坐标（与 {@code ElectricBlastFurnaceScreen} 共用）：
 * 输入 6 列 × 2 行 @ (44,18)；输出 8 列 × 4 行 @ (26,64)；玩家背包 y=150。</p>
 */
public class ElectricBlastFurnaceMenu extends MachineMenu {

    public static final int INPUT_COLS = 6;
    public static final int INPUT_X = 44;
    public static final int INPUT_Y = 18;

    public static final int OUTPUT_COLS = 8;
    public static final int OUTPUT_X = 26;
    public static final int OUTPUT_Y = 64;

    public static final int PLAYER_INV_Y = 150;

    private final ContainerData data;
    private final ItemStackHandler machineInventory;

    public ElectricBlastFurnaceMenu(int containerId, Inventory playerInventory, ElectricBlastFurnaceBlockEntity be) {
        this(containerId, playerInventory, be.getInventory(), be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端构造（MenuType 工厂调用） */
    public ElectricBlastFurnaceMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory,
                new ItemStackHandler(ElectricBlastFurnaceBlockEntity.SLOT_COUNT),
                new SimpleContainerData(ElectricBlastFurnaceBlockEntity.DATA_COUNT),
                ContainerLevelAccess.NULL);
    }

    private ElectricBlastFurnaceMenu(int containerId, Inventory playerInventory, ItemStackHandler machineInventory,
                                     ContainerData data, ContainerLevelAccess access) {
        super(ModMenus.ELECTRIC_BLAST_FURNACE_MENU.get(), containerId,
                ElectricBlastFurnaceBlockEntity.SLOT_COUNT, access);
        this.data = data;
        this.machineInventory = machineInventory;
        this.addDataSlots(data);

        // 12 个输入槽：什么都收（放错只是不加工）
        for (int k = 0; k < ElectricBlastFurnaceBlockEntity.INPUT_COUNT; k++) {
            this.addSlot(new SlotItemHandler(machineInventory, ElectricBlastFurnaceBlockEntity.INPUT_FIRST + k,
                    INPUT_X + (k % INPUT_COLS) * 18, INPUT_Y + (k / INPUT_COLS) * 18));
        }

        // 32 个输出槽：只能取不能放
        for (int k = 0; k < ElectricBlastFurnaceBlockEntity.OUTPUT_COUNT; k++) {
            this.addSlot(new SlotItemHandler(machineInventory, ElectricBlastFurnaceBlockEntity.OUTPUT_FIRST + k,
                    OUTPUT_X + (k % OUTPUT_COLS) * 18, OUTPUT_Y + (k / OUTPUT_COLS) * 18) {
                @Override
                public boolean mayPlace(ItemStack stack) {
                    return false;
                }
            });
        }

        this.addPlayerInventory(playerInventory, PLAYER_INV_Y);
    }

    /** Shift 点击：塞进第一个装得下的输入槽（基类只会往 [target, target+1) 里挪，所以要自己挑）。 */
    @Override
    protected int getMachineSlotFor(ItemStack stack) {
        for (int k = 0; k < ElectricBlastFurnaceBlockEntity.INPUT_COUNT; k++) {
            ItemStack slot = this.machineInventory.getStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST + k);
            if (slot.isEmpty()) {
                return ElectricBlastFurnaceBlockEntity.INPUT_FIRST + k;
            }
            if (ItemStack.isSameItemSameComponents(slot, stack) && slot.getCount() < slot.getMaxStackSize()) {
                return ElectricBlastFurnaceBlockEntity.INPUT_FIRST + k;
            }
        }
        return -1;
    }

    public int getEnergy() {
        return this.data.get(ElectricBlastFurnaceBlockEntity.DATA_ENERGY);
    }

    public int getProgress(int inputIndex) {
        return this.data.get(ElectricBlastFurnaceBlockEntity.DATA_PROGRESS_FIRST + inputIndex);
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.ELECTRIC_BLAST_FURNACE.get());
    }
}
