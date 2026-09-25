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
 * 氨气组成室菜单（0.11 ZF97）：<b>1 个催化剂槽 + 3 个高压气罐槽</b> + 玩家背包，界面 196×202。
 *
 * <p><b>版面照用户原话摆</b>（「GUi左侧为原料储罐和一个放催化剂（铁粉）的槽位 … 右侧则为输出
 * 原料储罐下方各有一个放高压气罐的槽位 … 输出储罐的高压气罐槽为反向」）：</p>
 * <pre>
 *   氮气罐(26,17) 氢气罐(48,17)   [催化剂槽(78,35)]        氨气罐(152,17)   能量条(176,17)
 *   气罐槽(26,74) 气罐槽(48,74)                          气罐槽(152,74)   状态灯(176,74)
 * </pre>
 * 三个储罐与能量条都不是槽位，由界面部件按 {@link ContainerData} 里的数字实时画。
 */
public class AmmoniaSynthesisChamberMenu extends MachineMenu {

    /** 催化剂槽（铁粉；槽位上方在 Screen 里写「催化剂(铁粉)」） */
    public static final int CATALYST_SLOT_X = 78;
    public static final int CATALYST_SLOT_Y = 35;

    /** 三个气罐槽（分别在三个储罐正下方） */
    public static final int NITROGEN_TANK_SLOT_X = 26;
    public static final int HYDROGEN_TANK_SLOT_X = 48;
    public static final int AMMONIA_TANK_SLOT_X = 152;
    public static final int CONTAINER_SLOT_Y = 74;

    /** 三个储罐（与 Screen 共用） */
    public static final int NITROGEN_X = 26;
    public static final int HYDROGEN_X = 48;
    public static final int AMMONIA_X = 152;
    public static final int TANK_Y = 17;
    public static final int TANK_W = 18;
    public static final int TANK_H = 52;

    /** 竖直能量条 + 状态灯（都贴在右边缘） */
    public static final int ENERGY_X = 176;
    public static final int ENERGY_Y = 17;
    public static final int ENERGY_W = 10;
    public static final int ENERGY_H = 52;

    public static final int LAMP_X = 176;
    public static final int LAMP_Y = 74;
    public static final int LAMP_SIZE = 8;

    public static final int PLAYER_INV_Y = 118;

    private final ContainerData data;

    public AmmoniaSynthesisChamberMenu(int containerId, Inventory playerInventory,
                                       AmmoniaSynthesisChamberBlockEntity be) {
        this(containerId, playerInventory, be.getInventory(), be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端构造（MenuType 工厂调用） */
    public AmmoniaSynthesisChamberMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory,
                new ItemStackHandler(AmmoniaSynthesisChamberBlockEntity.SLOT_COUNT),
                new SimpleContainerData(AmmoniaSynthesisChamberBlockEntity.DATA_COUNT),
                ContainerLevelAccess.NULL);
    }

    private AmmoniaSynthesisChamberMenu(int containerId, Inventory playerInventory,
                                        ItemStackHandler machineInventory, ContainerData data,
                                        ContainerLevelAccess access) {
        super(ModMenus.AMMONIA_SYNTHESIS_CHAMBER_MENU.get(), containerId,
                AmmoniaSynthesisChamberBlockEntity.SLOT_COUNT, access);
        this.data = data;
        this.addDataSlots(data);

        // 催化剂槽：只收铁粉（与方块实体里的 isItemValid 同一口径 —— §4.51）
        this.addSlot(new SlotItemHandler(machineInventory, AmmoniaSynthesisChamberBlockEntity.CATALYST_SLOT,
                CATALYST_SLOT_X, CATALYST_SLOT_Y) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return stack.is(ModItems.IRON_POWDER.get());
            }
        });

        // 三个气罐槽：只收流体容器（气罐/油桶）
        for (int idx : new int[] {AmmoniaSynthesisChamberBlockEntity.NITROGEN_TANK_SLOT,
                AmmoniaSynthesisChamberBlockEntity.HYDROGEN_TANK_SLOT,
                AmmoniaSynthesisChamberBlockEntity.AMMONIA_TANK_SLOT}) {
            int x = switch (idx) {
                case AmmoniaSynthesisChamberBlockEntity.NITROGEN_TANK_SLOT -> NITROGEN_TANK_SLOT_X;
                case AmmoniaSynthesisChamberBlockEntity.HYDROGEN_TANK_SLOT -> HYDROGEN_TANK_SLOT_X;
                default -> AMMONIA_TANK_SLOT_X;
            };
            this.addSlot(new SlotItemHandler(machineInventory, idx, x, CONTAINER_SLOT_Y) {
                @Override
                public boolean mayPlace(ItemStack stack) {
                    return stack.getItem() instanceof FluidContainerItem;
                }
            });
        }

        this.addPlayerInventory(playerInventory, PLAYER_INV_Y);
    }

    /** Shift 点击：铁粉直接塞进催化剂槽，气罐塞进第一个空的气罐槽；其余走基类默认逻辑。 */
    @Override
    protected int getMachineSlotFor(ItemStack stack) {
        if (stack.is(ModItems.IRON_POWDER.get())) {
            return AmmoniaSynthesisChamberBlockEntity.CATALYST_SLOT;
        }
        if (stack.getItem() instanceof FluidContainerItem) {
            return AmmoniaSynthesisChamberBlockEntity.NITROGEN_TANK_SLOT;
        }
        return -1;
    }

    // ================= 读数（界面部件用） =================

    public int getEnergy() {
        return Mth.clamp(this.data.get(AmmoniaSynthesisChamberBlockEntity.DATA_ENERGY), 0,
                AmmoniaSynthesisChamberBlockEntity.MAX_ENERGY);
    }

    public int getStatus() {
        return this.data.get(AmmoniaSynthesisChamberBlockEntity.DATA_STATUS);
    }

    public int getTankAmount(int tank) {
        int index = switch (tank) {
            case AmmoniaSynthesisChamberBlockEntity.TANK_NITROGEN ->
                    AmmoniaSynthesisChamberBlockEntity.DATA_NITROGEN;
            case AmmoniaSynthesisChamberBlockEntity.TANK_HYDROGEN ->
                    AmmoniaSynthesisChamberBlockEntity.DATA_HYDROGEN;
            default -> AmmoniaSynthesisChamberBlockEntity.DATA_AMMONIA;
        };
        return Mth.clamp(this.data.get(index), 0, AmmoniaSynthesisChamberBlockEntity.TANK_CAPACITY);
    }

    /** 催化剂槽里是不是铁粉（界面据此决定标签颜色）。 */
    public boolean hasCatalyst() {
        return this.data.get(AmmoniaSynthesisChamberBlockEntity.DATA_CATALYST) != 0;
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.AMMONIA_SYNTHESIS_CHAMBER.get());
    }
}
