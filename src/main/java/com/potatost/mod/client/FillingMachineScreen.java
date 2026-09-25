package com.potatost.mod.client;

import com.potatost.mod.FillingMachineBlockEntity;
import com.potatost.mod.FillingMachineMenu;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.EnergyBarPart;
import com.potatost.mod.client.gui.parts.DynamicFluidTankPart;

import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/**
 * Filling machine screen (0.03): five fluid tanks in a row, one container slot
 * under each tank, and the internal energy bar on the right.
 *
 * All coordinates are panel-relative; the parts add screen.left()/top() themselves.
 */
public class FillingMachineScreen extends MachineScreen<FillingMachineMenu> {

    /** x of the first tank; tanks repeat every 20 px. */
    private static final int TANK_FIRST_X = 17;
    private static final int TANK_X_STEP = 20;
    private static final int TANK_Y = 15;
    private static final int TANK_W = 18;
    private static final int TANK_H = 52;

    private static final int ENERGY_X = 134;
    private static final int ENERGY_W = 10;

    public FillingMachineScreen(FillingMachineMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title, 176, 184);

        for (int i = 0; i < FillingMachineBlockEntity.TANK_COUNT; i++) {
            final int tankIndex = i;
            this.parts.add(new DynamicFluidTankPart(TANK_FIRST_X + i * TANK_X_STEP, TANK_Y, TANK_W, TANK_H,
                    () -> menu.getTankAmount(tankIndex),
                    FillingMachineBlockEntity.TANK_CAPACITY,
                    () -> menu.getTankFluid(tankIndex),
                    () -> menu.getTankStack(tankIndex)));
        }

        this.parts.add(new EnergyBarPart(ENERGY_X, TANK_Y, ENERGY_W, TANK_H, menu::getEnergy,
                FillingMachineBlockEntity.MAX_ENERGY));
    }

}
