package com.potatost.mod;

import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.fluids.FluidUtil;
import net.neoforged.neoforge.items.ItemStackHandler;
import net.neoforged.neoforge.items.SlotItemHandler;

import com.potatost.mod.menu.MachineMenu;

/**
 * 电解器菜单：槽位布局与原来一致（流体槽 27,74 / 电解质槽 64,74 / 背包 y=102 / 快捷栏 y=160）。
 * 通用部分（玩家背包、shift 点击）已上移到 MachineMenu。
 * 双配方版：新增氧气读数（数据槽 4）。
 */
public class ElectrolyzerMenu extends MachineMenu {

    public static final int FLUID_SLOT_X = 27;
    public static final int FLUID_SLOT_Y = 74;
    public static final int ELECTROLYTE_SLOT_X = 64;
    public static final int ELECTROLYTE_SLOT_Y = 74;

    private final ContainerData data;

    /** 服务端构造（从方块实体拿真实数据） */
    public ElectrolyzerMenu(int containerId, Inventory playerInventory, ElectrolyzerBlockEntity be) {
        this(containerId, playerInventory, be.getInventory(), be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** 客户端构造（由 MenuType 工厂调用；数据由同步包写入 SimpleContainerData） */
    public ElectrolyzerMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory, new ItemStackHandler(ElectrolyzerBlockEntity.SLOT_COUNT),
                new SimpleContainerData(ElectrolyzerBlockEntity.DATA_COUNT), ContainerLevelAccess.NULL);
    }

    private ElectrolyzerMenu(int containerId, Inventory playerInventory, ItemStackHandler machineInventory,
                             ContainerData data, ContainerLevelAccess access) {
        super(ModMenus.ELECTROLYZER_MENU.get(), containerId, ElectrolyzerBlockEntity.SLOT_COUNT, access);
        this.data = data;
        this.addDataSlots(data);

        // 槽 0：流体容器（水桶等）；只允许 1 个，保证"水桶 -> 空桶"原地替换
        this.addSlot(new SlotItemHandler(machineInventory, ElectrolyzerBlockEntity.FLUID_SLOT,
                FLUID_SLOT_X, FLUID_SLOT_Y) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return FluidUtil.getFluidHandler(stack).isPresent();
            }

            @Override
            public int getMaxStackSize() {
                return 1;
            }
        });

        // 槽 1：电解质（海盐；有盐 = 盐水制氯，无盐 = 原版纯水制氧）
        this.addSlot(new SlotItemHandler(machineInventory, ElectrolyzerBlockEntity.ELECTROLYTE_SLOT,
                ELECTROLYTE_SLOT_X, ELECTROLYTE_SLOT_Y));

        this.addPlayerInventory(playerInventory);
    }

    // ===== GUI 读数出口（部件只认这几个方法） =====

    public int getEnergy() {
        return this.data.get(ElectrolyzerBlockEntity.DATA_ENERGY);
    }

    public int getInputAmount() {
        return this.data.get(ElectrolyzerBlockEntity.DATA_INPUT);
    }

    public int getOxygenAmount() {
        return this.data.get(ElectrolyzerBlockEntity.DATA_OXYGEN);
    }

    public int getChlorineAmount() {
        return this.data.get(ElectrolyzerBlockEntity.DATA_CHLORINE);
    }

    public int getHydrogenAmount() {
        return this.data.get(ElectrolyzerBlockEntity.DATA_HYDROGEN);
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.ELECTROLYZER.get());
    }

    /** shift 点击：什么物品该进哪个机器槽 */
    @Override
    protected int getMachineSlotFor(ItemStack stack) {
        if (FluidUtil.getFluidHandler(stack).isPresent()) {
            return ElectrolyzerBlockEntity.FLUID_SLOT;
        }
        if (stack.is(ElectrolyzerBlockEntity.ELECTROLYTE_TAG)) {
            return ElectrolyzerBlockEntity.ELECTROLYTE_SLOT;
        }
        return -1;
    }
}