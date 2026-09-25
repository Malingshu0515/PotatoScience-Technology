package com.potatost.mod;

import com.potatost.mod.menu.MachineMenu;

import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.neoforged.neoforge.items.ItemStackHandler;
import net.neoforged.neoforge.items.SlotItemHandler;

/**
 * 容器换流器菜单（0.11 ZF82）：左槽（装流体的容器）→ 进度条 → 右槽（空桶）+ 玩家背包；界面 176×166。
 *
 * <p>槽位坐标与 {@code FluidExchangerScreen} 里的进度条 / 状态灯共享同一坐标系：
 * 左槽中心 (44,35) → 进度条 (70,39,40×8) → 右槽中心 (116,35)。</p>
 *
 * <p>⚠ 右槽的门禁与方块实体的 {@code isItemValid} **必须同口径**（§4.51：三道门只改两道的血）。
 * 这里就是那三道门里的"玩家用手放"那道。</p>
 */
public class FluidExchangerMenu extends MachineMenu {

    public static final int LEFT_SLOT_X = 44;
    public static final int LEFT_SLOT_Y = 35;

    public static final int RIGHT_SLOT_X = 116;
    public static final int RIGHT_SLOT_Y = 35;

    private final ContainerData data;

    public FluidExchangerMenu(int containerId, Inventory playerInventory, FluidExchangerBlockEntity be) {
        this(containerId, playerInventory, be.getInventory(), be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端构造（MenuType 工厂调用） */
    public FluidExchangerMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory, new ItemStackHandler(FluidExchangerBlockEntity.SLOT_COUNT),
                new SimpleContainerData(FluidExchangerBlockEntity.DATA_COUNT), ContainerLevelAccess.NULL);
    }

    private FluidExchangerMenu(int containerId, Inventory playerInventory, ItemStackHandler machineInventory,
                               ContainerData data, ContainerLevelAccess access) {
        super(ModMenus.FLUID_EXCHANGER_MENU.get(), containerId, FluidExchangerBlockEntity.SLOT_COUNT, access);
        this.data = data;
        this.addDataSlots(data);

        // 左槽：装流体的容器（油桶 / 高压气罐）——放错东西由状态灯提示，而不是被槽位挡住
        this.addSlot(new SlotItemHandler(machineInventory, FluidExchangerBlockEntity.LEFT_SLOT,
                LEFT_SLOT_X, LEFT_SLOT_Y));

        // 右槽：空桶。产物（那种流体的桶）也留在这个槽里，所以它既能放也能取。
        this.addSlot(new SlotItemHandler(machineInventory, FluidExchangerBlockEntity.RIGHT_SLOT,
                RIGHT_SLOT_X, RIGHT_SLOT_Y) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return stack.is(Items.BUCKET);
            }
        });

        this.addPlayerInventory(playerInventory, 84);
    }

    /** Shift 点击：容器进左槽、空桶进右槽；其余走基类默认逻辑。 */
    @Override
    protected int getMachineSlotFor(ItemStack stack) {
        if (stack.getItem() instanceof FluidContainerItem) {
            return FluidExchangerBlockEntity.LEFT_SLOT;
        }
        if (stack.is(Items.BUCKET)) {
            return FluidExchangerBlockEntity.RIGHT_SLOT;
        }
        return -1;
    }

    public int getProgress() {
        return this.data.get(FluidExchangerBlockEntity.DATA_PROGRESS);
    }

    public int getProgressMax() {
        return this.data.get(FluidExchangerBlockEntity.DATA_PROGRESS_MAX);
    }

    public int getStatus() {
        return this.data.get(FluidExchangerBlockEntity.DATA_STATUS);
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.FLUID_EXCHANGER.get());
    }
}
