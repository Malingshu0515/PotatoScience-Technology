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
 * 分馏塔操作器菜单（0.11 ZF78）：<b>1 个沥青槽位</b> + 玩家背包，界面 196×202。
 *
 * <p>槽位坐标与 {@link com.potatost.mod.client.DistillationOperatorScreen} 共用：
 * 沥青槽 (158, 92) —— 用户原话「gui 右下角靠里面一点」；玩家背包 y=118。</p>
 *
 * <p>五个罐（石油 / 柴油 / 石脑油 / 汽油 / 液化石油气）与能量条都<b>不是槽位</b>，
 * 由界面部件按 {@link ContainerData} 里的数字实时画；容量随塔数缩放，所以
 * 这里提供的是"算出来的容量"而不是常量。</p>
 */
public class DistillationOperatorMenu extends MachineMenu {

    /**
     * 沥青槽位（与 Screen 共用）。
     * ⚠ 2026-09-24 用户实测「挡住物品栏字样了」⇒ SLOT_Y 92 → **84**（整排上提 8 px）。
     */
    public static final int SLOT_X = 158;
    public static final int SLOT_Y = 84;

    public static final int PLAYER_INV_Y = 118;

    private final ContainerData data;
    private final ItemStackHandler machineInventory;

    public DistillationOperatorMenu(int containerId, Inventory playerInventory, DistillationOperatorBlockEntity be) {
        this(containerId, playerInventory, be.getInventory(), be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端构造（MenuType 工厂调用） */
    public DistillationOperatorMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory,
                new ItemStackHandler(DistillationOperatorBlockEntity.SLOT_COUNT),
                new SimpleContainerData(DistillationOperatorBlockEntity.DATA_COUNT),
                ContainerLevelAccess.NULL);
    }

    private DistillationOperatorMenu(int containerId, Inventory playerInventory, ItemStackHandler machineInventory,
                                     ContainerData data, ContainerLevelAccess access) {
        super(ModMenus.DISTILLATION_OPERATOR_MENU.get(), containerId,
                DistillationOperatorBlockEntity.SLOT_COUNT, access);
        this.data = data;
        this.machineInventory = machineInventory;
        this.addDataSlots(data);

        // 沥青槽位：只收沥青（与方块实体里的 isItemValid 同一口径）
        this.addSlot(new SlotItemHandler(machineInventory, DistillationOperatorBlockEntity.BITUMEN_SLOT,
                SLOT_X, SLOT_Y));

        this.addPlayerInventory(playerInventory, PLAYER_INV_Y);
    }

    /** Shift 点击：沥青直接塞进沥青槽（其余走基类默认逻辑，进玩家背包）。 */
    @Override
    protected int getMachineSlotFor(ItemStack stack) {
        return stack.is(ModItems.BITUMEN.get()) ? DistillationOperatorBlockEntity.BITUMEN_SLOT : -1;
    }

    // ================= 读数（界面部件用）=================

    public int getEnergy() {
        return this.data.get(DistillationOperatorBlockEntity.DATA_ENERGY);
    }

    /** 能量上限 = 8096 × 塔数（随塔数变，所以界面上是动态的）。 */
    public int getEnergyCapacity() {
        return DistillationOperatorBlockEntity.FE_PER_TOWER * getTowers();
    }

    public int getTowers() {
        return Mth.clamp(this.data.get(DistillationOperatorBlockEntity.DATA_TOWERS), 0,
                DistillationOperatorBlockEntity.MAX_TOWERS);
    }

    public int getStatus() {
        return Mth.clamp(this.data.get(DistillationOperatorBlockEntity.DATA_STATUS), 0,
                DistillationOperatorBlockEntity.STATUS_PRODUCT_FULL);
    }

    public int getProgress() {
        return Mth.clamp(this.data.get(DistillationOperatorBlockEntity.DATA_PROGRESS), 0,
                DistillationOperatorBlockEntity.BITUMEN_INTERVAL);
    }

    /** 石油量：两个 15 位分片拼回来（48000 超出短整型，见方块实体的 DATA_OIL_* 注释）。 */
    public int getTankAmount(int tank) {
        if (tank == DistillationOperatorBlockEntity.TANK_OIL) {
            int low = this.data.get(DistillationOperatorBlockEntity.DATA_OIL_LOW)
                    & DistillationOperatorBlockEntity.DATA_CHUNK_MASK;
            int high = this.data.get(DistillationOperatorBlockEntity.DATA_OIL_HIGH)
                    & DistillationOperatorBlockEntity.DATA_CHUNK_MASK;
            return low | (high << DistillationOperatorBlockEntity.DATA_CHUNK_BITS);
        }
        return this.data.get(tankDataIndex(tank));
    }

    /** 罐容量：石油 12 桶/塔、四种产品 2.5 桶/塔。 */
    public int getTankCapacity(int tank) {
        int towers = getTowers();
        int perTower = tank == DistillationOperatorBlockEntity.TANK_OIL
                ? DistillationOperatorBlockEntity.OIL_PER_TOWER
                : DistillationOperatorBlockEntity.PRODUCT_PER_TOWER;
        return perTower * towers;
    }

    private static int tankDataIndex(int tank) {
        return switch (tank) {
            case DistillationOperatorBlockEntity.TANK_DIESEL -> DistillationOperatorBlockEntity.DATA_DIESEL;
            case DistillationOperatorBlockEntity.TANK_NAPHTHA -> DistillationOperatorBlockEntity.DATA_NAPHTHA;
            case DistillationOperatorBlockEntity.TANK_GASOLINE -> DistillationOperatorBlockEntity.DATA_GASOLINE;
            case DistillationOperatorBlockEntity.TANK_LPG -> DistillationOperatorBlockEntity.DATA_LPG;
            default -> DistillationOperatorBlockEntity.DATA_OIL_LOW;
        };
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.DISTILLATION_OPERATOR.get());
    }
}
