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
 * 微型粉碎机菜单：左侧 1 个输入槽 + 右侧 3 个输出槽（纵向排）+ 玩家背包；界面 176x166。
 *
 * <p>槽位坐标与 {@code MicroCrusherScreen} 里的进度条 / 状态灯 / 能量条共享同一坐标系：
 * 输入槽中心 y=43，三个输出槽中心 y=25 / 43 / 61，箭头正好落在 62~90 之间。</p>
 */
public class MicroCrusherMenu extends MachineMenu {

    public static final int INPUT_SLOT_X = 35;
    public static final int INPUT_SLOT_Y = 35;

    public static final int OUTPUT_SLOT_X = 116;
    public static final int OUTPUT_SLOT_Y_FIRST = 17;
    public static final int OUTPUT_SLOT_STEP = 18;

    private final ContainerData data;

    public MicroCrusherMenu(int containerId, Inventory playerInventory, MicroCrusherBlockEntity be) {
        this(containerId, playerInventory, be.getInventory(), be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端构造（MenuType 工厂调用） */
    public MicroCrusherMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory, new ItemStackHandler(MicroCrusherBlockEntity.SLOT_COUNT),
                new SimpleContainerData(MicroCrusherBlockEntity.DATA_COUNT), ContainerLevelAccess.NULL);
    }

    private MicroCrusherMenu(int containerId, Inventory playerInventory, ItemStackHandler machineInventory,
                             ContainerData data, ContainerLevelAccess access) {
        super(ModMenus.MICRO_CRUSHER_MENU.get(), containerId, MicroCrusherBlockEntity.SLOT_COUNT, access);
        this.data = data;
        this.addDataSlots(data);

        // 输入槽：什么都能放（放错由状态灯提示黄灯，而不是被槽位挡住）
        this.addSlot(new SlotItemHandler(machineInventory, MicroCrusherBlockEntity.INPUT_SLOT,
                INPUT_SLOT_X, INPUT_SLOT_Y));

        // 输出槽 ×3：只能取不能放
        for (int i = 0; i < MicroCrusherBlockEntity.OUTPUT_COUNT; i++) {
            this.addSlot(new SlotItemHandler(machineInventory, MicroCrusherBlockEntity.OUTPUT_FIRST + i,
                    OUTPUT_SLOT_X, OUTPUT_SLOT_Y_FIRST + i * OUTPUT_SLOT_STEP) {
                @Override
                public boolean mayPlace(ItemStack stack) {
                    return false;
                }
            });
        }

        this.addPlayerInventory(playerInventory, 84);
    }

    /** Shift 点击：能粉碎的物品直接塞进输入槽；其余走基类默认逻辑。 */
    @Override
    protected int getMachineSlotFor(ItemStack stack) {
        return MicroCrusherRecipes.find(stack) != null ? MicroCrusherBlockEntity.INPUT_SLOT : -1;
    }

    public int getEnergy() {
        return this.data.get(MicroCrusherBlockEntity.DATA_ENERGY);
    }

    public int getProgress() {
        return this.data.get(MicroCrusherBlockEntity.DATA_PROGRESS);
    }

    public int getProgressMax() {
        return this.data.get(MicroCrusherBlockEntity.DATA_PROGRESS_MAX);
    }

    public int getStatus() {
        return this.data.get(MicroCrusherBlockEntity.DATA_STATUS);
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.MICRO_CRUSHER.get());
    }
}
