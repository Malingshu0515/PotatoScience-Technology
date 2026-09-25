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
 * 合金冶炼炉菜单（0.10 ZF49）：<b>5 输入 + 3 输出 + 2 消耗槽</b>，界面 176×186。
 *
 * <p>用户原话：「五个输入槽（只能接受锭标签） 三个输出槽 2个消耗槽（目前放不了东西）」。
 * 输入槽的"只收锭"由 {@code AlloySmelterBlockEntity} 的 {@code isItemValid} 管，
 * 这里只负责摆位置；消耗槽<b>也照画出来</b>（让玩家看见那儿以后会有东西），但同样放不进去。</p>
 */
public class AlloySmelterMenu extends MachineMenu {

    public static final int WIDTH = 176;
    public static final int HEIGHT = 186;

    /** 5 个输入槽：一排 */
    public static final int INPUT_X = 26;
    public static final int INPUT_Y = 20;
    /** 3 个输出槽：一排，下面隔一行（中间留给以后的进度条） */
    public static final int OUTPUT_X = 44;
    public static final int OUTPUT_Y = 62;
    /** 2 个消耗槽：右下角，与输出错开 */
    public static final int CONSUME_X = 116;
    public static final int CONSUME_Y = 62;

    public static final int PLAYER_INV_Y = 104;

    private final ContainerData data;
    private final ItemStackHandler machineInventory;

    public AlloySmelterMenu(int containerId, Inventory playerInventory, AlloySmelterBlockEntity be) {
        this(containerId, playerInventory, be.getInventory(), be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端构造（MenuType 工厂调用） */
    public AlloySmelterMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory,
                new ItemStackHandler(AlloySmelterBlockEntity.SLOT_COUNT),
                new SimpleContainerData(AlloySmelterBlockEntity.DATA_COUNT),
                ContainerLevelAccess.NULL);
    }

    private AlloySmelterMenu(int containerId, Inventory playerInventory, ItemStackHandler machineInventory,
                             ContainerData data, ContainerLevelAccess access) {
        super(ModMenus.ALLOY_SMELTER_MENU.get(), containerId, AlloySmelterBlockEntity.SLOT_COUNT, access);
        this.data = data;
        this.machineInventory = machineInventory;
        this.addDataSlots(data);

        for (int k = 0; k < AlloySmelterBlockEntity.INPUT_COUNT; k++) {
            this.addSlot(new SlotItemHandler(machineInventory, AlloySmelterBlockEntity.INPUT_FIRST + k,
                    INPUT_X + k * 18, INPUT_Y));
        }
        for (int k = 0; k < AlloySmelterBlockEntity.OUTPUT_COUNT; k++) {
            this.addSlot(new SlotItemHandler(machineInventory, AlloySmelterBlockEntity.OUTPUT_FIRST + k,
                    OUTPUT_X + k * 18, OUTPUT_Y) {
                @Override
                public boolean mayPlace(ItemStack stack) {
                    return false;       // 输出槽只能取
                }
            });
        }
        for (int k = 0; k < AlloySmelterBlockEntity.CONSUME_COUNT; k++) {
            this.addSlot(new SlotItemHandler(machineInventory, AlloySmelterBlockEntity.CONSUME_FIRST + k,
                    CONSUME_X + k * 18, CONSUME_Y) {
                @Override
                public boolean mayPlace(ItemStack stack) {
                    return false;       // 用户：「目前放不了东西」——以后放石墨电极
                }
            });
        }

        this.addPlayerInventory(playerInventory, PLAYER_INV_Y);
    }

    /** Shift 点击：塞进第一个装得下的输入槽。 */
    @Override
    protected int getMachineSlotFor(ItemStack stack) {
        if (!stack.is(net.minecraft.tags.ItemTags.create(
                net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("c", "ingots")))) {
            return -1;
        }
        for (int k = 0; k < AlloySmelterBlockEntity.INPUT_COUNT; k++) {
            ItemStack slot = this.machineInventory.getStackInSlot(AlloySmelterBlockEntity.INPUT_FIRST + k);
            if (slot.isEmpty()) {
                return AlloySmelterBlockEntity.INPUT_FIRST + k;
            }
            if (ItemStack.isSameItemSameComponents(slot, stack) && slot.getCount() < slot.getMaxStackSize()) {
                return AlloySmelterBlockEntity.INPUT_FIRST + k;
            }
        }
        return -1;
    }

    public int getEnergy() {
        return this.data.get(AlloySmelterBlockEntity.DATA_ENERGY);
    }

    /**
     * 当前这一轮的进度（0..{@link AlloySmelterBlockEntity#DURATION_TICKS}）—— 界面那支进度箭头用它。
     *
     * <p>走 {@code ContainerData}：只在界面开着的时候同步就够（界面不开也没人看箭头）。</p>
     */
    public int getProgress() {
        return this.data.get(AlloySmelterBlockEntity.DATA_PROGRESS);
    }

    /** 进度箭头的满值 = 一轮的时长（本机目前只有一条配方，所以是常量而不是随配方变的值）。 */
    public int getProgressMax() {
        return AlloySmelterBlockEntity.DURATION_TICKS;
    }

    public boolean isFormed() {
        return this.data.get(AlloySmelterBlockEntity.DATA_FORMED) != 0;
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.ALLOY_SMELTER.get());
    }
}
