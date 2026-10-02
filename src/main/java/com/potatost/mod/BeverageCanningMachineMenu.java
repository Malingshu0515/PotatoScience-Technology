package com.potatost.mod;

import com.potatost.mod.menu.MachineMenu;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.items.ItemStackHandler;
import net.neoforged.neoforge.items.SlotItemHandler;

/**
 * 饮料罐装机的菜单（0.13 ZF167）。
 *
 * <p>面板 176×184（与灌装机同款：三只罐在上排、三个输入槽各在自己那只罐正下方、
 * 右侧一条能量柱）。坐标（面板相对）：</p>
 * <pre>
 *   罐 i      x = 16 + i * 24, y = 12, 20×40
 *   输入槽 i  x = 17 + i * 24, y = 58, 18×18   （槽 0 糖 / 槽 1 可可豆 / 槽 2 空铝罐；对齐在各罐正下方）
 *   输出槽    x = 118, y = 58, 18×18           （与输入槽同一排：一条"产出线"）
 *   进度条    x = 92,  y = 63, 20×8   ；状态灯 x = 100, y = 40, 8×8
 *   能量柱    x = 150, y = 12, 10×40           （与罐组同高）
 *   玩家背包从 y = 102 起（{@link MachineMenu} 的默认值）
 * </pre>
 *
 * <p><b>⚠ 0.13 ZF168 重排过一次</b>（用户：「ui有点别扭 你看着改 好看点就行」）：
 * 旧版是三只 18×52 的**又高又黑**的罐吊在上排、输入槽缩在 y=70、箭头与输出挤在中间、
 * 能量柱孤零零挂最右 —— 现在改成"罐组（40 高）→ 各自罐下的输入槽 → 一条产出线（箭头 + 输出）
 * → 右缘与罐同高的能量柱"，中间空档放状态灯。**坐标只写在这里和 Screen 里两处**，
 * 改一处必须改另一处（两边顶上的注释块就是同步用的）。</p>
 *
 * <p>罐的**液面**走 {@code ContainerData}（每 tick 同步），**流体种类**另占一组数据槽
 * （传的是流体注册表 id，0 = 空）—— 与灌装机 0.11 ZF73 那次修正同一条口径，
 * 那样原油/碳酸这类"以后才加"的流体也能正确显示。</p>
 */
public class BeverageCanningMachineMenu extends MachineMenu {

    /** 第一个输入槽的 x 与间距（与 Screen 里的罐组同一套数：罐宽 20，槽 18 正好居中在罐下）。 */
    public static final int INPUT_SLOT_FIRST_X = 17;
    public static final int INPUT_SLOT_X_STEP = 24;

    /** 三个输入槽共用这一行 y（各自在自己那只罐下面）。 */
    public static final int INPUT_SLOT_Y = 58;

    /** 输出槽（与输入槽同一排，中间隔一条进度箭头）。 */
    public static final int OUTPUT_SLOT_X = 118;
    public static final int OUTPUT_SLOT_Y = 58;

    private final ContainerData data;

    public BeverageCanningMachineMenu(int containerId, Inventory playerInventory,
                                      BeverageCanningMachineBlockEntity be) {
        this(containerId, playerInventory, be.getInventory(), be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端那一侧的构造器（由 MenuType 工厂调用）。 */
    public BeverageCanningMachineMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory,
                new ItemStackHandler(BeverageCanningMachineBlockEntity.SLOT_COUNT),
                new SimpleContainerData(BeverageCanningMachineBlockEntity.DATA_COUNT),
                ContainerLevelAccess.NULL);
    }

    private BeverageCanningMachineMenu(int containerId, Inventory playerInventory,
                                       ItemStackHandler machineInventory, ContainerData data,
                                       ContainerLevelAccess access) {
        super(ModMenus.BEVERAGE_CANNING_MACHINE_MENU.get(), containerId,
                BeverageCanningMachineBlockEntity.SLOT_COUNT, access);
        this.data = data;
        this.addDataSlots(data);

        // 三个输入槽：门禁由方块实体的 isItemValid 说了算（这里与它同一个口径）
        for (int i = 0; i < BeverageCanningMachineBlockEntity.SLOT_OUTPUT; i++) {
            this.addSlot(new SlotItemHandler(machineInventory, i,
                    INPUT_SLOT_FIRST_X + i * INPUT_SLOT_X_STEP, INPUT_SLOT_Y));
        }
        // 输出槽：只能拿不能放
        this.addSlot(new SlotItemHandler(machineInventory, BeverageCanningMachineBlockEntity.SLOT_OUTPUT,
                OUTPUT_SLOT_X, OUTPUT_SLOT_Y) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return false;
            }
        });

        this.addPlayerInventory(playerInventory);
    }

    public int getEnergy() {
        return this.data.get(BeverageCanningMachineBlockEntity.DATA_ENERGY);
    }

    public int getProgress() {
        return this.data.get(BeverageCanningMachineBlockEntity.DATA_PROGRESS);
    }

    public int getProgressMax() {
        return this.data.get(BeverageCanningMachineBlockEntity.DATA_PROGRESS_MAX);
    }

    public int getStatus() {
        return this.data.get(BeverageCanningMachineBlockEntity.DATA_STATUS);
    }

    /** 某只罐现在的液面（mB）。 */
    public int getTankAmount(int tankIndex) {
        return this.data.get(BeverageCanningMachineBlockEntity.DATA_TANK_0 + tankIndex);
    }

    /** 某只罐里是什么流体（液面为 0 时返回空流体）。 */
    public Fluid getTankFluid(int tankIndex) {
        if (getTankAmount(tankIndex) <= 0) {
            return Fluids.EMPTY;
        }
        return BuiltInRegistries.FLUID.byId(
                this.data.get(BeverageCanningMachineBlockEntity.DATA_TANK_FLUID_0 + tankIndex));
    }

    /** 某只罐的内容（给界面上的悬停提示用）。 */
    public FluidStack getTankStack(int tankIndex) {
        int amount = getTankAmount(tankIndex);
        return amount <= 0 ? FluidStack.EMPTY : new FluidStack(getTankFluid(tankIndex), amount);
    }

    /**
     * Shift 快移：按物品送到"它该去的那个输入槽"（糖→0、可可豆→1、空铝罐→2），
     * 满了再退回背包 —— 与本工程其它多槽机器同一条口径。
     */
    @Override
    protected int getMachineSlotFor(ItemStack stack) {
        if (stack.is(net.minecraft.world.item.Items.SUGAR)) {
            return BeverageCanningMachineBlockEntity.SLOT_SUGAR;
        }
        if (stack.is(net.minecraft.world.item.Items.COCOA_BEANS)) {
            return BeverageCanningMachineBlockEntity.SLOT_COCOA;
        }
        if (stack.is(ModItems.EMPTY_ALUMINUM_CAN.get())) {
            return BeverageCanningMachineBlockEntity.SLOT_CAN;
        }
        return -1;
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.BEVERAGE_CANNING_MACHINE.get());
    }
}
