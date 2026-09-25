package com.potatost.mod.client.gui;

import net.minecraft.client.gui.GuiGraphics;

/**
 * 界面部件：自己负责画 + 自己的悬停提示。
 * 约定：所有坐标都是"界面内相对坐标"（与槽位坐标同一坐标系）。
 */
public interface GuiPart {

    void render(MachineScreen<?> screen, GuiGraphics gg);

    default void tooltip(MachineScreen<?> screen, GuiGraphics gg, int mouseX, int mouseY) {
    }

    /**
     * 点到了这个部件吗？（0.11 ZF101 新增：酸性反应室那三个配方按钮要用）
     *
     * <p>默认返回 {@code false} = 这个部件不接收点击（老部件一个都不用改）。
     * 返回 {@code true} 表示点击**已被吃掉**，{@link MachineScreen} 不会再往下传
     * （否则会顺手触发原版"点背包槽位/丢东西"那一套）。</p>
     *
     * @param mouseX 屏幕坐标（不是界面内相对坐标）
     * @param mouseY 同上
     * @param button 0 = 左键
     */
    default boolean mouseClicked(MachineScreen<?> screen, double mouseX, double mouseY, int button) {
        return false;
    }
}