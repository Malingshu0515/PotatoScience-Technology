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
 * 输入槽的"只收锭"由 {@code AlloySmelterBlockEntity} 的 {@code isItemValid} 管，这里只负责摆位置。</p>
 *
 * <p><b>0.11 ZF121：消耗槽终于能用手放进去了</b>。ZF49 那句"目前放不了东西"当初留了两层门，
 * 方块实体那层 ZF111 已经放开成"某条配方真的会消耗它才收"，<b>可菜单这层的恒 false 还留着</b>
 * ⇒ 手动一个都放不进去（只有漏斗/管道塞得进），而 ZF111 与本轮两条配方都要求消耗槽里有东西
 * —— 那是一条死路。现在交给 {@code machineInventory.isItemValid} 判（没激活时它照样返回 false，
 * 垃圾也照旧进不去，"不能当第二个背包用"这条口径没变）。</p>
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
        // 0.11 ZF121：这 2 槽**不再拦** —— 能不能放由方块实体的 isItemValid 说了算
        //（"某条配方真的会消耗它"才收，没激活时一律 false）。ZF49 那句"目前放不了东西"
        // 从 ZF111 放开方块实体那一刻起就已经名不副实了，这里把它撤掉。
        for (int k = 0; k < AlloySmelterBlockEntity.CONSUME_COUNT; k++) {
            this.addSlot(new SlotItemHandler(machineInventory, AlloySmelterBlockEntity.CONSUME_FIRST + k,
                    CONSUME_X + k * 18, CONSUME_Y));
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
        // 0.11 ZF121：消耗品也走 shift 点击 —— 能不能放交给 isItemValid（配方点名的才收）。
        // 不认这个的话，玩家 shift 点一下粗振金只会被丢回背包，得一个个手动拖。
        for (int k = 0; k < AlloySmelterBlockEntity.CONSUME_COUNT; k++) {
            int slot = AlloySmelterBlockEntity.CONSUME_FIRST + k;
            if (!this.machineInventory.isItemValid(slot, stack)) {
                continue;
            }
            ItemStack cur = this.machineInventory.getStackInSlot(slot);
            if (cur.isEmpty()) {
                return slot;
            }
            if (ItemStack.isSameItemSameComponents(cur, stack) && cur.getCount() < cur.getMaxStackSize()) {
                return slot;
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
