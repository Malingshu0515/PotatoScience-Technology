package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

/**
 * 测试流体储罐界面：
 *  - 服务端持有罐方块实体；客户端为 null。
 *  - 按钮：0..5 = 六个档位（★ 只改容量）；6 = 清空（只清存量）；7 = 灌满（存量=容量）。
 *  - 大数字（最高 21 亿）按 15 位×3 拆分，跨过"数据槽 = short"的同步上限。
 */
public class TestFluidTankMenu extends AbstractContainerMenu {

    /** 档位按钮文字 */
    public static final String[] PRESET_LABELS = {"100", "1k", "10k", "100k", "3.3M", "2.1B"};

    /** 客户端为 null；服务端为真实方块实体 */
    private final TestFluidTankBlockEntity tank;
    private final ContainerData data;

    /** 客户端构造（MenuType 工厂用） */
    public TestFluidTankMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory, null, new SimpleContainerData(TestFluidTankBlockEntity.DATA_COUNT));
    }

    /** 服务端构造（方块实体的 createMenu 用） */
    public TestFluidTankMenu(int containerId, Inventory playerInventory, TestFluidTankBlockEntity tank) {
        this(containerId, playerInventory, tank, tank.getContainerData());
    }

    private TestFluidTankMenu(int containerId, Inventory playerInventory, TestFluidTankBlockEntity tank,
                              ContainerData data) {
        super(ModMenus.TEST_FLUID_TANK_MENU.get(), containerId);
        this.tank = tank;
        this.data = data;
        this.addDataSlots(data);

        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 9; col++) {
                this.addSlot(new Slot(playerInventory, col + row * 9 + 9, 8 + col * 18, 84 + row * 18));
            }
        }
        for (int col = 0; col < 9; col++) {
            this.addSlot(new Slot(playerInventory, col, 8 + col * 18, 142));
        }
    }

    // ===== 供界面读取（客户端/服务端都安全） =====
    public int getTierIndex() {
        return Mth.clamp(this.data.get(TestFluidTankBlockEntity.DATA_TIER), 0, TestFluidTankBlockEntity.MAX_TIER);
    }

    public int getStockAmount() {
        int low = this.data.get(TestFluidTankBlockEntity.DATA_STOCK_LOW) & 0x7FFF;
        int mid = this.data.get(TestFluidTankBlockEntity.DATA_STOCK_MID) & 0x7FFF;
        int high = this.data.get(TestFluidTankBlockEntity.DATA_STOCK_HIGH) & 0x7FFF;
        return (int) (((long) high << 30) | ((long) mid << 15) | (long) low);
    }

    public int getCapacityAmount() {
        return TestFluidTankBlockEntity.STOCK_PRESETS[getTierIndex()];
    }

    public int getFluidId() {
        return this.data.get(TestFluidTankBlockEntity.DATA_FLUID_ID);
    }

    // ===== 按钮（服务端处理） =====
    @Override
    public boolean clickMenuButton(Player player, int id) {
        if (this.tank == null) {
            return false;
        }
        if (id >= 0 && id < TestFluidTankBlockEntity.STOCK_PRESETS.length) {
            this.tank.applyPreset(id);          // 只改容量
            return true;
        }
        if (id == TestFluidTankBlockEntity.BUTTON_CLEAR) {
            this.tank.clearStock();             // 只清存量
            return true;
        }
        if (id == TestFluidTankBlockEntity.BUTTON_FILL) {
            this.tank.fillToCapacity();         // 存量 = 容量
            return true;
        }
        return false;
    }

    @Override
    public boolean stillValid(Player player) {
        if (this.tank == null) {
            return true;   // 客户端不校验
        }
        BlockPos pos = this.tank.getBlockPos();
        return player.level().getBlockState(pos).is(ModBlocks.TEST_FLUID_TANK.get())
                && player.distanceToSqr(pos.getX() + 0.5D, pos.getY() + 0.5D, pos.getZ() + 0.5D) <= 64.0D;
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        return ItemStack.EMPTY;   // 无机器槽位
    }
}