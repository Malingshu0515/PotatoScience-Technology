package com.potatost.mod;

import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.items.ItemStackHandler;
import net.neoforged.neoforge.items.SlotItemHandler;

import com.potatost.mod.menu.MachineMenu;

/** 晒盐机菜单：1 个输出槽（不能放东西）+ 玩家背包；界面 176x166 */
public class SaltDryerMenu extends MachineMenu {

    public static final int OUTPUT_SLOT_X = 80;
    public static final int OUTPUT_SLOT_Y = 35;

    private final ContainerData data;

    public SaltDryerMenu(int containerId, Inventory playerInventory, SaltDryerBlockEntity be) {
        this(containerId, playerInventory, be.getInventory(), be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端构造（MenuType 工厂调用） */
    public SaltDryerMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory, new ItemStackHandler(SaltDryerBlockEntity.SLOT_COUNT),
                new SimpleContainerData(SaltDryerBlockEntity.DATA_COUNT), ContainerLevelAccess.NULL);
    }

    private SaltDryerMenu(int containerId, Inventory playerInventory, ItemStackHandler machineInventory,
                          ContainerData data, ContainerLevelAccess access) {
        super(ModMenus.SALT_DRYER_MENU.get(), containerId, SaltDryerBlockEntity.SLOT_COUNT, access);
        this.data = data;
        this.addDataSlots(data);

        // 输出槽：只能取不能放
        this.addSlot(new SlotItemHandler(machineInventory, SaltDryerBlockEntity.OUTPUT_SLOT,
                OUTPUT_SLOT_X, OUTPUT_SLOT_Y) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return false;
            }
        });

        this.addPlayerInventory(playerInventory, 84);
    }

    public int getEnergy() {
        return this.data.get(SaltDryerBlockEntity.DATA_ENERGY);
    }

    public int getProgress() {
        return this.data.get(SaltDryerBlockEntity.DATA_PROGRESS);
    }

    public int getState() {
        return this.data.get(SaltDryerBlockEntity.DATA_STATE);
    }

    public int getReason() {
        return this.data.get(SaltDryerBlockEntity.DATA_REASON);
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.SALT_DRYER.get());
    }
}