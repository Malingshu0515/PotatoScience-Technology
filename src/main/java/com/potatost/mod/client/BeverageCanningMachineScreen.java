package com.potatost.mod.client;

import com.potatost.mod.BeverageCanningMachineBlockEntity;
import com.potatost.mod.BeverageCanningMachineMenu;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.DynamicFluidTankPart;
import com.potatost.mod.client.gui.parts.EnergyBarPart;
import com.potatost.mod.client.gui.parts.ProgressBarPart;
import com.potatost.mod.client.gui.parts.StatusLampPart;

import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/**
 * 饮料罐装机界面（0.13 ZF167）：只负责"摆件"，坐标与 {@link BeverageCanningMachineMenu} 里
 * 的槽位一一对齐（三只罐在上排、输入槽在各自罐下、右侧能量柱、进度条 + 状态灯在中间）。
 */
public class BeverageCanningMachineScreen extends MachineScreen<BeverageCanningMachineMenu> {

    /** 第一只罐的 x；每只间隔 20 px（与菜单里的槽位同一套数）。 */
    private static final int TANK_FIRST_X = 17;
    private static final int TANK_X_STEP = 20;
    private static final int TANK_Y = 15;
    private static final int TANK_W = 18;
    private static final int TANK_H = 52;

    public static final int PROGRESS_X = 86;
    public static final int PROGRESS_Y = 39;
    public static final int PROGRESS_W = 28;
    public static final int PROGRESS_H = 8;

    public static final int LAMP_X = 96;
    public static final int LAMP_Y = 50;
    public static final int LAMP_SIZE = 8;

    private static final int ENERGY_X = 146;
    private static final int ENERGY_Y = 17;
    private static final int ENERGY_W = 10;
    private static final int ENERGY_H = 54;

    public BeverageCanningMachineScreen(BeverageCanningMachineMenu menu, Inventory playerInventory,
                                        Component title) {
        super(menu, playerInventory, title, 176, 184);

        for (int i = 0; i < BeverageCanningMachineBlockEntity.TANK_COUNT; i++) {
            final int tankIndex = i;
            this.parts.add(new DynamicFluidTankPart(TANK_FIRST_X + i * TANK_X_STEP, TANK_Y, TANK_W, TANK_H,
                    () -> menu.getTankAmount(tankIndex),
                    BeverageCanningMachineBlockEntity.capacityOf(tankIndex),
                    () -> menu.getTankFluid(tankIndex),
                    () -> menu.getTankStack(tankIndex)));
        }

        this.parts.add(new ProgressBarPart(PROGRESS_X, PROGRESS_Y, PROGRESS_W, PROGRESS_H,
                menu::getProgress, menu::getProgressMax, ProgressBarPart.DEFAULT_COLOR));
        // ⚠ 状态灯必须传**本机自己的文案前缀**：不传就用微型粉碎机那套键，
        //   悬停会显示「正在粉碎」（0.10 ZF30 踩过一模一样的坑）。
        this.parts.add(new StatusLampPart(LAMP_X, LAMP_Y, LAMP_SIZE, menu::getStatus,
                "gui.potato_s_t.beverage_canning_machine.status."));
        this.parts.add(new EnergyBarPart(ENERGY_X, ENERGY_Y, ENERGY_W, ENERGY_H, menu::getEnergy,
                BeverageCanningMachineBlockEntity.MAX_ENERGY));
    }
}
