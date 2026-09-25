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
 * 酸性反应室菜单（0.11 ZF101）：<b>硫槽 + 输出槽</b> + 玩家背包，界面 196×216。
 *
 * <pre>
 *   四个原料罐 (26,17)(48,17)(70,17)(92,17) 18×40     硫槽 (120,25) · 输出槽 (120,49)
 *   三个产物罐 (26,64)(48,64)(70,64) 18×40            进度条 (120,80,44×8) · 状态灯 (152,25) · 能量条 (168,17,12×40)
 *   三个选择按钮 (25,110)(47,110)(69,110) 20×14
 * </pre>
 *
 * <p><b>三个按钮走原版菜单按钮通道</b>：客户端 {@code handleInventoryButtonClick} ⇒ 服务端
 * {@link #clickMenuButton} ⇒ 方块实体的 {@code setSelected}。不用自建网络包，
 * 而且服务端**再校验一次**配方号（客户端说什么不算数）。</p>
 */
public class AcidicReactionChamberMenu extends MachineMenu {

    /** 硫槽（与 Screen 共用） */
    public static final int SULFUR_SLOT_X = 160;
    public static final int SULFUR_SLOT_Y = 25;

    /** 输出槽（与 Screen 共用） */
    public static final int OUTPUT_SLOT_X = 160;
    public static final int OUTPUT_SLOT_Y = 49;

    /** 玩家背包起始 y（三行 + 快捷栏） */
    public static final int PLAYER_INV_Y = 134;

    private final ContainerData data;
    /** 只有"真机器"那一侧能改配方（客户端构造时是 null ⇒ 按钮点了也只是发个包） */
    private final AcidicReactionChamberBlockEntity machine;

    public AcidicReactionChamberMenu(int containerId, Inventory playerInventory,
                                     AcidicReactionChamberBlockEntity be) {
        this(containerId, playerInventory, be, be.getInventory(), be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端构造（MenuType 工厂调用） */
    public AcidicReactionChamberMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory, null,
                new ItemStackHandler(AcidicReactionChamberBlockEntity.SLOT_COUNT),
                new SimpleContainerData(AcidicReactionChamberBlockEntity.DATA_COUNT),
                ContainerLevelAccess.NULL);
    }

    private AcidicReactionChamberMenu(int containerId, Inventory playerInventory,
                                      AcidicReactionChamberBlockEntity machine,
                                      ItemStackHandler machineInventory, ContainerData data,
                                      ContainerLevelAccess access) {
        super(ModMenus.ACIDIC_REACTION_CHAMBER_MENU.get(), containerId,
                AcidicReactionChamberBlockEntity.SLOT_COUNT, access);
        this.machine = machine;
        this.data = data;
        this.addDataSlots(data);

        // 硫槽：只收硫（与方块实体里的 isItemValid 同一口径 —— §4.51 那条"两处门禁"）
        this.addSlot(new SlotItemHandler(machineInventory, AcidicReactionChamberBlockEntity.SULFUR_SLOT,
                SULFUR_SLOT_X, SULFUR_SLOT_Y) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return stack.is(ModItems.SULFUR.get());
            }
        });

        // 输出槽：只能取不能放
        this.addSlot(new SlotItemHandler(machineInventory, AcidicReactionChamberBlockEntity.OUTPUT_SLOT,
                OUTPUT_SLOT_X, OUTPUT_SLOT_Y) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return false;
            }
        });

        this.addPlayerInventory(playerInventory, PLAYER_INV_Y);
    }

    /**
     * 界面那三个按钮点出来的配方号 —— <b>服务端这一侧做最终校验</b>。
     *
     * <p>⚠ 这是本工程第一次用菜单按钮通道（以前都是右键机器切模式）。规矩照旧：
     * 客户端传来的号**不合法就丢掉**，并且改完要 {@code setChanged()} 让存档跟上。</p>
     */
    @Override
    public boolean clickMenuButton(Player player, int id) {
        if (this.machine == null || !AcidicReactionChamberBlockEntity.isValidRecipe(id)) {
            return false;
        }
        this.machine.setSelected(id);
        return true;
    }

    /** Shift 点击：硫直接塞进硫槽（其余走基类默认逻辑，进玩家背包）。 */
    @Override
    protected int getMachineSlotFor(ItemStack stack) {
        return stack.is(ModItems.SULFUR.get()) ? AcidicReactionChamberBlockEntity.SULFUR_SLOT : -1;
    }

    // ================= 读数（界面部件用） =================

    public int getEnergy() {
        return Mth.clamp(this.data.get(AcidicReactionChamberBlockEntity.DATA_ENERGY), 0,
                AcidicReactionChamberBlockEntity.MAX_ENERGY);
    }

    public int getProgress() {
        return Mth.clamp(this.data.get(AcidicReactionChamberBlockEntity.DATA_PROGRESS), 0,
                Math.max(1, getProgressMax()));
    }

    public int getProgressMax() {
        int max = this.data.get(AcidicReactionChamberBlockEntity.DATA_PROGRESS_MAX);
        return max > 0 ? max : AcidicReactionChamberBlockEntity.SULFURIC_DURATION_TICKS;
    }

    public int getStatus() {
        return this.data.get(AcidicReactionChamberBlockEntity.DATA_STATUS);
    }

    /** 当前选中的配方号（三个按钮靠它决定谁高亮）。 */
    public int getSelected() {
        return this.data.get(AcidicReactionChamberBlockEntity.DATA_RECIPE);
    }

    public int getTank(int index) {
        int data0 = switch (index) {
            case AcidicReactionChamberBlockEntity.TANK_OXYGEN -> AcidicReactionChamberBlockEntity.DATA_OXYGEN;
            case AcidicReactionChamberBlockEntity.TANK_AMMONIA -> AcidicReactionChamberBlockEntity.DATA_AMMONIA;
            case AcidicReactionChamberBlockEntity.TANK_WATER -> AcidicReactionChamberBlockEntity.DATA_WATER;
            case AcidicReactionChamberBlockEntity.TANK_CARBONIC -> AcidicReactionChamberBlockEntity.DATA_CARBONIC;
            case AcidicReactionChamberBlockEntity.TANK_NITRIC -> AcidicReactionChamberBlockEntity.DATA_NITRIC;
            case AcidicReactionChamberBlockEntity.TANK_SULFURIC -> AcidicReactionChamberBlockEntity.DATA_SULFURIC;
            // 0.11 ZF102：三个新罐
            case AcidicReactionChamberBlockEntity.TANK_HYDROGEN -> AcidicReactionChamberBlockEntity.DATA_HYDROGEN;
            case AcidicReactionChamberBlockEntity.TANK_CHLORINE -> AcidicReactionChamberBlockEntity.DATA_CHLORINE;
            case AcidicReactionChamberBlockEntity.TANK_HYDROCHLORIC ->
                    AcidicReactionChamberBlockEntity.DATA_HYDROCHLORIC;
            default -> AcidicReactionChamberBlockEntity.DATA_CO2;
        };
        return Mth.clamp(this.data.get(data0), 0, AcidicReactionChamberBlockEntity.TANK_CAPACITY);
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.ACIDIC_REACTION_CHAMBER.get());
    }
}
