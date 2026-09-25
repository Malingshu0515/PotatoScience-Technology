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
 * 加氢脱硫反应仓菜单（0.11 ZF96）：<b>左侧 1 个沥青槽 + 右侧 1 个硫输出槽</b> + 玩家背包，
 * 界面 176×166（标准小面板）。
 *
 * <p><b>版面照用户原话摆</b>（「GUI 一个氢气罐 左侧放沥青」）：</p>
 * <pre>
 *   沥青槽 (26,35) → 氢气罐 (52,17,18×52) → 进度箭头 (80,33,22×16) → 硫槽 (112,35)
 *                                             状态灯 (87,52,8×8)
 * </pre>
 * 氢气罐不是槽位，由界面部件 {@code FluidTankPart} 按 {@link ContainerData} 里的数字实时画。
 */
public class HydrodesulfurizationChamberMenu extends MachineMenu {

    /** 沥青槽位（与 Screen 共用） */
    public static final int INPUT_SLOT_X = 26;
    public static final int INPUT_SLOT_Y = 35;

    /** 硫输出槽（与 Screen 共用） */
    public static final int OUTPUT_SLOT_X = 112;
    public static final int OUTPUT_SLOT_Y = 35;

    /** 玩家背包起始 y（三行 + 快捷栏） */
    public static final int PLAYER_INV_Y = 84;

    private final ContainerData data;

    public HydrodesulfurizationChamberMenu(int containerId, Inventory playerInventory,
                                           HydrodesulfurizationChamberBlockEntity be) {
        this(containerId, playerInventory, be.getInventory(), be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端构造（MenuType 工厂调用） */
    public HydrodesulfurizationChamberMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory,
                new ItemStackHandler(HydrodesulfurizationChamberBlockEntity.SLOT_COUNT),
                new SimpleContainerData(HydrodesulfurizationChamberBlockEntity.DATA_COUNT),
                ContainerLevelAccess.NULL);
    }

    private HydrodesulfurizationChamberMenu(int containerId, Inventory playerInventory,
                                            ItemStackHandler machineInventory, ContainerData data,
                                            ContainerLevelAccess access) {
        super(ModMenus.HYDRODESULFURIZATION_CHAMBER_MENU.get(), containerId,
                HydrodesulfurizationChamberBlockEntity.SLOT_COUNT, access);
        this.data = data;
        this.addDataSlots(data);

        // 沥青槽：只收沥青（与方块实体里的 isItemValid 同一口径 —— §4.51 那条"两处门禁"）
        this.addSlot(new SlotItemHandler(machineInventory, HydrodesulfurizationChamberBlockEntity.INPUT_SLOT,
                INPUT_SLOT_X, INPUT_SLOT_Y) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return stack.is(ModItems.BITUMEN.get());
            }
        });

        // 硫输出槽：只能取不能放
        this.addSlot(new SlotItemHandler(machineInventory, HydrodesulfurizationChamberBlockEntity.OUTPUT_SLOT,
                OUTPUT_SLOT_X, OUTPUT_SLOT_Y) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return false;
            }
        });

        this.addPlayerInventory(playerInventory, PLAYER_INV_Y);
    }

    /** Shift 点击：沥青直接塞进沥青槽（其余走基类默认逻辑，进玩家背包）。 */
    @Override
    protected int getMachineSlotFor(ItemStack stack) {
        return stack.is(ModItems.BITUMEN.get())
                ? HydrodesulfurizationChamberBlockEntity.INPUT_SLOT : -1;
    }

    // ================= 读数（界面部件用） =================

    public int getProgress() {
        return Mth.clamp(this.data.get(HydrodesulfurizationChamberBlockEntity.DATA_PROGRESS), 0,
                HydrodesulfurizationChamberBlockEntity.DURATION_TICKS);
    }

    public int getProgressMax() {
        int max = this.data.get(HydrodesulfurizationChamberBlockEntity.DATA_PROGRESS_MAX);
        return max > 0 ? max : HydrodesulfurizationChamberBlockEntity.DURATION_TICKS;
    }

    public int getStatus() {
        return this.data.get(HydrodesulfurizationChamberBlockEntity.DATA_STATUS);
    }

    public int getTankAmount() {
        return Mth.clamp(this.data.get(HydrodesulfurizationChamberBlockEntity.DATA_TANK), 0,
                HydrodesulfurizationChamberBlockEntity.TANK_CAPACITY);
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.HYDRODESULFURIZATION_CHAMBER.get());
    }
}
