package com.potatost.mod.client;

import com.potatost.mod.ElectricBlastFurnaceBlockEntity;
import com.potatost.mod.ElectricBlastFurnaceMenu;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.EnergyBarPart;
import com.potatost.mod.client.gui.parts.ProgressBarPart;

import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/**
 * 电力高炉界面（0.10 ZF39）：**放大面板一次显示完**（用户 ZF39 拍板，仿沉浸工程那种大 GUI）。
 *
 * <p>196×234：上面 2 行 × 6 个输入槽、中间 4 行 × 8 个输出槽、下面玩家背包。
 * 每个输入槽底下压一条 16×2 的进度条（12 条），右侧一根竖直能量条。</p>
 *
 * <p>面板本身仍是零贴图（{@link MachineScreen#drawPanel} 的纯色 + 立体边框）。</p>
 */
public class ElectricBlastFurnaceScreen extends MachineScreen<ElectricBlastFurnaceMenu> {

    public static final int WIDTH = 196;
    public static final int HEIGHT = 234;

    public static final int ENERGY_X = 176;
    public static final int ENERGY_Y = 64;
    public static final int ENERGY_W = 10;
    public static final int ENERGY_H = 72;

    /** 每个输入槽下面那根进度条（宽 16 与槽位等宽，高 2） */
    public static final int BAR_H = 2;
    public static final int BAR_GAP = 1;

    public ElectricBlastFurnaceScreen(ElectricBlastFurnaceMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title, WIDTH, HEIGHT);

        this.parts.add(new EnergyBarPart(ENERGY_X, ENERGY_Y, ENERGY_W, ENERGY_H,
                menu::getEnergy, ElectricBlastFurnaceBlockEntity.MAX_ENERGY));

        for (int k = 0; k < ElectricBlastFurnaceBlockEntity.INPUT_COUNT; k++) {
            int x = ElectricBlastFurnaceMenu.INPUT_X + (k % ElectricBlastFurnaceMenu.INPUT_COLS) * 18;
            int y = ElectricBlastFurnaceMenu.INPUT_Y + (k / ElectricBlastFurnaceMenu.INPUT_COLS) * 18 + 17 + BAR_GAP;
            final int index = k;
            this.parts.add(new ProgressBarPart(x, y, 16, BAR_H,
                    () -> menu.getProgress(index),
                    () -> ElectricBlastFurnaceBlockEntity.DURATION_TICKS,
                    ProgressBarPart.DEFAULT_COLOR));
        }
    }
}
