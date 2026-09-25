package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

/**
 * 流体泵界面：
 *  - 服务端：直接持有泵；客户端：null（速率/能量经 ContainerData 数据槽同步）。
 *  - 按钮（clickMenuButton）：-100 / -10 / -1 / +1 / +10 / +100，结果 clamp 到 0..800。
 *  - 两个构造：两参给 MenuType 的 MenuSupplier 工厂（客户端），三参给 BlockEntity#createMenu（服务端）。
 */
public class FluidPumpMenu extends AbstractContainerMenu {

    public static final int BUTTON_MINUS_100 = 0;
    public static final int BUTTON_MINUS_10 = 1;
    public static final int BUTTON_MINUS_1 = 2;
    public static final int BUTTON_PLUS_1 = 3;
    public static final int BUTTON_PLUS_10 = 4;
    public static final int BUTTON_PLUS_100 = 5;

    /** 客户端为 null；服务端为真实方块实体 */
    private final FluidPumpBlockEntity pump;
    private final ContainerData data;

    /** 客户端构造（MenuType 工厂用） */
    public FluidPumpMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory, null, new SimpleContainerData(FluidPumpBlockEntity.DATA_COUNT));
    }

    /** 服务端构造（FluidPumpBlockEntity#createMenu 用） */
    public FluidPumpMenu(int containerId, Inventory playerInventory, FluidPumpBlockEntity pump) {
        this(containerId, playerInventory, pump, pump.getContainerData());
    }

    private FluidPumpMenu(int containerId, Inventory playerInventory, FluidPumpBlockEntity pump, ContainerData data) {
        super(ModMenus.FLUID_PUMP_MENU.get(), containerId);
        this.pump = pump;
        this.data = data;
        this.addDataSlots(data);

        // 玩家背包（机器本身没有物品槽）
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 9; col++) {
                this.addSlot(new Slot(playerInventory, col + row * 9 + 9, 8 + col * 18, 84 + row * 18));
            }
        }
        for (int col = 0; col < 9; col++) {
            this.addSlot(new Slot(playerInventory, col, 8 + col * 18, 142));
        }
    }

    // ===== 供 GUI 读取（客户端/服务端都安全） =====
    public int getRate() {
        return this.data.get(FluidPumpBlockEntity.DATA_RATE);
    }

    public int getEnergy() {
        return this.data.get(FluidPumpBlockEntity.DATA_ENERGY);
    }

    public int getMaxEnergy() {
        return FluidPumpBlockEntity.MAX_ENERGY;
    }

    public static int fePerTick(int ratePercent) {
        return FluidPumpBlockEntity.fePerTick(ratePercent);
    }

    public static int mbPerTick(int ratePercent) {
        return FluidPumpBlockEntity.mbPerTick(ratePercent);
    }

    public static int maxRange(int ratePercent) {
        return FluidPumpBlockEntity.maxRange(ratePercent);
    }

    // ===== 按钮（服务端处理） =====
    @Override
    public boolean clickMenuButton(Player player, int id) {
        if (this.pump == null) {
            return false;
        }
        int delta = switch (id) {
            case BUTTON_MINUS_100 -> -100;
            case BUTTON_MINUS_10 -> -10;
            case BUTTON_MINUS_1 -> -1;
            case BUTTON_PLUS_1 -> 1;
            case BUTTON_PLUS_10 -> 10;
            case BUTTON_PLUS_100 -> 100;
            default -> 0;
        };
        if (delta == 0) {
            return false;
        }
        this.pump.setRate(this.pump.getRate() + delta);
        return true;
    }

    @Override
    public boolean stillValid(Player player) {
        if (this.pump == null) {
            return true;   // 客户端不校验；服务端校验失败会自动关闭
        }
        BlockPos pos = this.pump.getBlockPos();
        return player.level().getBlockState(pos).is(ModBlocks.FLUID_PUMP.get())
                && player.distanceToSqr(pos.getX() + 0.5D, pos.getY() + 0.5D, pos.getZ() + 0.5D) <= 64.0D;
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        return ItemStack.EMPTY;   // 无机器槽位
    }
}