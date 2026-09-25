package com.potatost.mod;

import com.potatost.mod.menu.MachineMenu;

import net.minecraft.tags.ItemTags;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.items.ItemStackHandler;
import net.neoforged.neoforge.items.SlotItemHandler;

/**
 * 低级发电机菜单：<b>只有 1 个输入槽</b>（燃料）+ 玩家背包；界面 176x166。
 *
 * <p>用户原话：「右键打开 gui 只有能量槽和输入槽」⇒ 这台机器**不画进度条、不画状态灯**，
 * 只有一根能量条（由 {@code LowGeneratorScreen} 摆）与这一个槽。</p>
 *
 * <p>槽位坐标与 Screen 里的能量条共享同一坐标系：输入槽中心 (80,35)，能量条竖在右侧 (146,17,10x54)。</p>
 */
public class LowGeneratorMenu extends MachineMenu {

    public static final int INPUT_SLOT_X = 80;
    public static final int INPUT_SLOT_Y = 35;

    private final ContainerData data;

    public LowGeneratorMenu(int containerId, Inventory playerInventory, LowGeneratorBlockEntity be) {
        this(containerId, playerInventory, be.getInventory(), be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端构造（MenuType 工厂调用） */
    public LowGeneratorMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory, new ItemStackHandler(LowGeneratorBlockEntity.SLOT_COUNT),
                new SimpleContainerData(LowGeneratorBlockEntity.DATA_COUNT), ContainerLevelAccess.NULL);
    }

    private LowGeneratorMenu(int containerId, Inventory playerInventory, ItemStackHandler machineInventory,
                             ContainerData data, ContainerLevelAccess access) {
        super(ModMenus.LOW_GENERATOR_MENU.get(), containerId, LowGeneratorBlockEntity.SLOT_COUNT, access);
        this.data = data;
        this.addDataSlots(data);

        // 输入槽：只收燃料（方块实体那一侧也有一道同样的门，见 LowGeneratorBlockEntity#items）
        this.addSlot(new SlotItemHandler(machineInventory, LowGeneratorBlockEntity.INPUT_SLOT,
                INPUT_SLOT_X, INPUT_SLOT_Y) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return stack.is(ItemTags.COALS);
            }
        });

        this.addPlayerInventory(playerInventory, 84);
    }

    /** Shift 点击：燃料直接塞进输入槽；其余走基类默认逻辑。 */
    @Override
    protected int getMachineSlotFor(ItemStack stack) {
        return stack.is(ItemTags.COALS) ? LowGeneratorBlockEntity.INPUT_SLOT : -1;
    }

    public int getEnergy() {
        return this.data.get(LowGeneratorBlockEntity.DATA_ENERGY);
    }

    public int getBurnTime() {
        return this.data.get(LowGeneratorBlockEntity.DATA_BURN);
    }

    public int getBurnTotal() {
        return this.data.get(LowGeneratorBlockEntity.DATA_BURN_MAX);
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.LOW_GENERATOR.get());
    }
}
