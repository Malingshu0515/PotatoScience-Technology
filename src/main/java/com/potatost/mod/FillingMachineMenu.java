package com.potatost.mod;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.items.ItemStackHandler;
import net.neoforged.neoforge.items.SlotItemHandler;

import com.potatost.mod.menu.MachineMenu;

/**
 * Filling machine menu (0.03): five container slots in a row plus the player
 * inventory. Panel is 176x184.
 *
 * Slot geometry (relative coordinates, the same system the screen parts use):
 *   tank i is drawn at x = 26 + i * 20, y = 15, size 18x52
 *   slot i sits at x = 17 + i * 20, y = 70, size 18x18  (centred under its tank)
 *   the energy bar is drawn at x = 134, y = 15, size 10x52
 *   the player inventory starts at y = 102 (MachineMenu default)
 *
 * The fluid TYPE of a tank is not carried by ContainerData (only amounts are),
 * so the screen rebuilds it from the synced amount; see FillingMachineScreen.
 * Capacities never change, so they are compile-time constants.
 */
public class FillingMachineMenu extends MachineMenu {

    /** left x of container slot i */
    private static final int[] CONTAINER_SLOT_X = {17, 37, 57, 77, 97};

    /** top y shared by all five container slots */
    public static final int CONTAINER_SLOT_Y = 70;

    private final ContainerData data;

    public FillingMachineMenu(int containerId, Inventory playerInventory, FillingMachineBlockEntity be) {
        this(containerId, playerInventory, be.getInventory(), be.getContainerData(),
                ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    /** Client-side constructor, called by the MenuType factory. */
    public FillingMachineMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory, new ItemStackHandler(FillingMachineBlockEntity.SLOT_COUNT),
                new SimpleContainerData(FillingMachineBlockEntity.DATA_COUNT), ContainerLevelAccess.NULL);
    }

    private FillingMachineMenu(int containerId, Inventory playerInventory, ItemStackHandler machineInventory,
                               ContainerData data, ContainerLevelAccess access) {
        super(ModMenus.FILLING_MACHINE_MENU.get(), containerId, FillingMachineBlockEntity.SLOT_COUNT, access);
        this.data = data;
        this.addDataSlots(data);

        for (int i = 0; i < FillingMachineBlockEntity.TANK_COUNT; i++) {
            this.addSlot(new SlotItemHandler(machineInventory, i, CONTAINER_SLOT_X[i], CONTAINER_SLOT_Y) {
                @Override
                public boolean mayPlace(ItemStack stack) {
                    // ⚠ 2026-09-24 用户实测：「灌装机没办法放油桶」—— 根因就在这一行：
                    //   ZF73 把方块实体（isItemValid）与 Shift 快移（getMachineSlotFor）都改成认
                    //   FluidContainerItem 了，**手放的这道门漏改**，仍是写死的高压气罐。
                    //   三道门必须同口径 ⇒ 一律认接口（气罐 + 油桶 + 以后的任何容器）。
                    return stack.getItem() instanceof FluidContainerItem;
                }

                @Override
                public int getMaxStackSize() {
                    return 1;
                }
            });
        }

        this.addPlayerInventory(playerInventory);
    }

    public int getEnergy() {
        return this.data.get(FillingMachineBlockEntity.DATA_ENERGY);
    }

    /** Fluid currently held by tank `tankIndex` (mB). */
    public int getTankAmount(int tankIndex) {
        return this.data.get(FillingMachineBlockEntity.DATA_TANK_0 + tankIndex);
    }

    /**
     * Fluid to draw for tank `tankIndex`; oxygen when empty.
     *
     * Known limitation: ContainerData carries amounts but not fluid ids, so the
     * client cannot tell WHICH gas is in the tank. All three process gases are
     * accepted, so a tank that ends up holding chlorine while another holds
     * hydrogen will paint both with this same sprite (the amount is always
     * correct, only the colour can be wrong). Fixing it needs one extra data
     * slot per tank carrying the fluid registry id; deferred, see the ZF2 notes.
     */
    public Fluid getTankFluid(int tankIndex) {
        if (getTankAmount(tankIndex) <= 0) {
            return Fluids.EMPTY;
        }
        // 0.11 ZF73：数据槽里现在传的是**流体注册表 id**（0 = minecraft:empty），
        // 这样原油以及以后任何流体都能正确显示，不再局限于那 3 种气体。
        return BuiltInRegistries.FLUID.byId(
                this.data.get(FillingMachineBlockEntity.DATA_TANK_FLUID_0 + tankIndex));
    }

    /** Contents of tank `tankIndex`, built from the two synced data slots. */
    public FluidStack getTankStack(int tankIndex) {
        int amount = getTankAmount(tankIndex);
        if (amount <= 0) {
            return FluidStack.EMPTY;
        }
        return new FluidStack(getTankFluid(tankIndex), amount);
    }

    @Override
    protected int getMachineSlotFor(ItemStack stack) {
        // 0.11 ZF73：Shift 快移从"只认高压气罐"改成"认所有流体容器"（气罐 + 油桶）。
        if (stack.getItem() instanceof FluidContainerItem) {
            // First empty machine slot, else slot 0.
            for (int i = 0; i < FillingMachineBlockEntity.SLOT_COUNT; i++) {
                if (!this.slots.get(i).hasItem()) {
                    return i;
                }
            }
            return 0;
        }
        return -1;
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(this.access, player, ModBlocks.FILLING_MACHINE.get());
    }
}