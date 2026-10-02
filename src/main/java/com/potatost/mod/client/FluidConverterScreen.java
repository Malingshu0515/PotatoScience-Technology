package com.potatost.mod.client;

import com.potatost.mod.FluidConverterBlockEntity;
import com.potatost.mod.FluidConverterMenu;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.DynamicFluidTankPart;
import com.potatost.mod.client.gui.parts.EnergyBarPart;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/**
 * 流体转化器界面（0.13 ZF166）：零贴图面板 176×202。
 *
 * <p>版面（坐标与 {@link FluidConverterMenu} 共用同一套）：能量条 (26,18,10×52)、
 * 输入罐 (44,18,18×52)、输出罐 (114,18,18×52)，罐子下面三行字 ——
 * <b>输入罐的名字/数量、输出罐（样板）的名字/数量、机器此刻的状态</b>
 * （状态那一行是"为什么没在转"，与空手潜行右键的诊断<b>同一份文案</b>）。</p>
 *
 * <p>⚠ 三行字都走 lang（Java 里不许出现用户可见的硬编码中文），且都用
 * {@link FluidConverterBlockEntity#statusLine} / {@link FluidConverterBlockEntity#tankLine}
 * 拼 —— 界面与聊天栏诊断不会各写一套。</p>
 *
 * <p>⚠ 状态那几句是给聊天栏写的长文案（最长约 40 个汉字），直接整句画在 176 宽的面板里
 * 会左右各溢出上百像素，所以这里按面板宽度<b>截断</b>（{@code plainSubstrByWidth}）。</p>
 */
public class FluidConverterScreen extends MachineScreen<FluidConverterMenu> {

    public static final int WIDTH = 176;
    public static final int HEIGHT = FluidConverterMenu.PLAYER_INV_Y + 84;

    /** 三行字：左起点 + 三个 y。 */
    private static final int TEXT_X = 8;
    private static final int TEXT_Y_INPUT = 74;
    private static final int TEXT_Y_OUTPUT = 84;
    private static final int TEXT_Y_STATUS = 94;
    /** 普通读数：深灰（与分馏塔操作器同一个色号） */
    private static final int LABEL_COLOR = 0x404040;
    /** 正在转：绿；其余状态：暗红（屏幕小，一行字够用了） */
    private static final int RUNNING_COLOR = 0xFF2E7D32;
    private static final int STOPPED_COLOR = 0xFF9E2B25;

    public FluidConverterScreen(FluidConverterMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title, WIDTH, HEIGHT);
        this.parts.add(new EnergyBarPart(FluidConverterMenu.ENERGY_X, FluidConverterMenu.ENERGY_Y,
                FluidConverterMenu.ENERGY_W, FluidConverterMenu.ENERGY_H,
                menu::getEnergy, FluidConverterBlockEntity.MAX_ENERGY));
        this.parts.add(new DynamicFluidTankPart(FluidConverterMenu.INPUT_X, FluidConverterMenu.TANK_Y,
                FluidConverterMenu.TANK_W, FluidConverterMenu.TANK_H,
                menu::getInputAmount, FluidConverterBlockEntity.TANK_CAPACITY,
                menu::getInputFluidOrEmpty, menu::getInputStack));
        this.parts.add(new DynamicFluidTankPart(FluidConverterMenu.OUTPUT_X, FluidConverterMenu.TANK_Y,
                FluidConverterMenu.TANK_W, FluidConverterMenu.TANK_H,
                menu::getOutputAmount, FluidConverterBlockEntity.TANK_CAPACITY,
                menu::getOutputFluidOrEmpty, menu::getOutputStack));
    }

    /** 两个罐的名字/数量 + 机器此刻的状态（罐和条都是自绘部件，文字只能在这里补）。 */
    @Override
    protected void renderMachineForeground(GuiGraphics gg, float partialTick) {
        int code = this.menu.getStateCode();
        boolean running = FluidConverterBlockEntity.isRunning(code);

        drawLine(gg, FluidConverterBlockEntity.tankLine(FluidConverterBlockEntity.LANG_TANK_INPUT,
                this.menu.getInputStack()), TEXT_Y_INPUT, LABEL_COLOR);
        drawLine(gg, FluidConverterBlockEntity.tankLine(FluidConverterBlockEntity.LANG_TANK_OUTPUT,
                this.menu.getOutputStack()), TEXT_Y_OUTPUT, LABEL_COLOR);
        drawLine(gg, FluidConverterBlockEntity.statusLine(code, this.menu.getInputStack(),
                        this.menu.getOutputStack(), this.menu.getEnergy()),
                TEXT_Y_STATUS, running ? RUNNING_COLOR : STOPPED_COLOR);
    }

    /** 画一行字：超出面板宽度的部分截掉（见类注释里那条"长文案"的说明）。 */
    private void drawLine(GuiGraphics gg, Component text, int y, int color) {
        String shown = this.font.plainSubstrByWidth(text.getString(), this.imageWidth - 2 * TEXT_X);
        gg.drawString(this.font, shown, this.left() + TEXT_X, this.top() + y, color, false);
    }
}
