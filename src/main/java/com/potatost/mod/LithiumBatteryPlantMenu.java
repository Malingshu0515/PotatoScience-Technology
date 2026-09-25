package com.potatost.mod;

import com.potatost.mod.menu.MachineMenu;

import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.items.ItemStackHandler;
import net.neoforged.neoforge.items.SlotItemHandler;

/**
 * 锂电池构造间菜单（0.11 ZF112）：<b>4 个输入槽 + 1 个输出槽</b> + 硫酸罐（罐由界面部件画）。
 *
 * <p>槽位顺序与方块实体一致：0 粗锰/粗铝、1 镍锭/粗镍、2 碳酸锂、3 钴锭/粗钴、4 输出。
 * 门禁只在方块实体的 {@code isItemValid}（{@code SlotItemHandler} 默认就问它）——
 * 不会出现"界面放得进、机器不认"那种两处不一致（§4.51）。</p>
 */
public class LithiumBatteryPlantMenu extends MachineMenu {

    /** 硫酸罐（竖罐，与界面共用） */
    public static final int TANK_X = 8;
    public static final int TANK_Y = 17;
    public static final int TANK_W = 18;
    public static final int TANK_H = 52;

    /** 四个输入槽（2×2）+ 输出槽 —— 坐标在这里定，界面读它 */
    public static final int SLOT_0_X = 44;
    public static final int SLOT_0_Y = 17;
    public static final int SLOT_STEP = 18;
    public static final int OUTPUT_X = 118;
    public static final int OUTPUT_Y = 26;

    /** 进度箭头 */
    public static final int ARROW_X = 88;
    public static final int ARROW_Y = 27;
    public static final int ARROW_W = 22;
    public static final int ARROW_H = 16;

    /** 工作指示灯 */
    public static final int LAMP_X = 146;
    public static final int LAMP_Y = 20;
    public static final int LAMP_SIZE = 10;

    public static final int PLAYER_INV_Y = 84;

    private final ContainerData data;

    public LithiumBatteryPlantMenu(int containerId, Inventory playerInventory, LithiumBatteryPlantBlockEntity be) {
        this(containerId, playerInventory, be.getContainerData(), be.getInventory(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端构造（MenuType 工厂调用） */
    public LithiumBatteryPlantMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory,
                new SimpleContainerData(LithiumBatteryPlantBlockEntity.DATA_COUNT),
                new ItemStackHandler(LithiumBatteryPlantBlockEntity.SLOT_COUNT),
                ContainerLevelAccess.NULL);
    }

    private LithiumBatteryPlantMenu(int containerId, Inventory playerInventory, ContainerData data,
                                    ItemStackHandler handler, ContainerLevelAccess access) {
        super(ModMenus.LITHIUM_BATTERY_PLANT_MENU.get(), containerId,
                LithiumBatteryPlantBlockEntity.SLOT_COUNT, access);
        this.data = data;
        this.addDataSlots(data);
        // 四个输入槽：2×2
        for (int i = 0; i < 4; i++) {
            int x = SLOT_0_X + (i % 2) * SLOT_STEP;
            int y = SLOT_0_Y + (i / 2) * SLOT_STEP;
            this.addSlot(new SlotItemHandler(handler, i, x, y));
        }
        // 输出槽：只能取
        this.addSlot(new SlotItemHandler(handler, LithiumBatteryPlantBlockEntity.OUTPUT_SLOT,
                OUTPUT_X, OUTPUT_Y) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return false;
            }
        });
        this.addPlayerInventory(playerInventory, PLAYER_INV_Y);
    }

    /** 没有"某样东西优先去哪个机器槽"的规则 ⇒ Shift 点击走基类的背包内部搬运。 */
    @Override
    protected int getMachineSlotFor(ItemStack stack) {
        return -1;
    }

    // ================= 读数（界面部件用） =================

    public int getProgress() {
        return Mth.clamp(this.data.get(LithiumBatteryPlantBlockEntity.DATA_PROGRESS), 0,
                LithiumBatteryPlantBlockEntity.DURATION_TICKS);
    }

    public int getProgressMax() {
        return LithiumBatteryPlantBlockEntity.DURATION_TICKS;
    }

    public int getStatus() {
        return this.data.get(LithiumBatteryPlantBlockEntity.DATA_STATUS);
    }

    public int getAcid() {
        return Mth.clamp(this.data.get(LithiumBatteryPlantBlockEntity.DATA_TANK_FLUID), 0,
                LithiumBatteryPlantBlockEntity.TANK_CAPACITY);
    }

    public int getTankCapacity() {
        return LithiumBatteryPlantBlockEntity.TANK_CAPACITY;
    }

    /** 供界面显示"每 tick 10 mB"。 */
    public int getAcidPerTick() {
        return LithiumBatteryPlantBlockEntity.ACID_PER_TICK;
    }

    /** 未用但保留：将来若要给"一次一炉要多少酸"提示。 */
    public static int acidPerOperation() {
        return LithiumBatteryPlantBlockEntity.ACID_PER_OPERATION;
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.LITHIUM_BATTERY_PLANT.get());
    }

    /** 基类的槽位表（探针用得到）。 */
    public Slot slotAt(int index) {
        return this.slots.get(index);
    }
}
