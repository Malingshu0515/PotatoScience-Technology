package com.potatost.mod.client;

import com.potatost.mod.FluidPumpMenu;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.Slot;

/**
 * 流体泵界面（自包含版）：
 *   左侧文字：速率 / 耗电 / 流量 / 范围 / 能量；
 *   右侧两列按钮：-100 -10 -1 / +1 +10 +100；
 *   底部右下角能量条；物品栏槽位纯色绘制。
 */
public class FluidPumpScreen extends AbstractContainerScreen<FluidPumpMenu> {

    private static final int COLOR_FRAME = 0xFF1E1E1E;
    private static final int COLOR_PANEL = 0xFF4A4A4A;
    private static final int COLOR_INV = 0xFF3A3A3A;
    private static final int COLOR_SLOT_EDGE = 0xFF202020;
    private static final int COLOR_SLOT_BG = 0xFF8B8B8B;
    private static final int COLOR_TEXT = 0xFFE0E0E0;
    private static final int COLOR_RATE_ON = 0xFFFFD54F;
    private static final int COLOR_RATE_OFF = 0xFF9E9E9E;
    private static final int COLOR_BAR_BG = 0xFF181818;
    private static final int COLOR_BAR = 0xFFE0C020;

    public FluidPumpScreen(FluidPumpMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title);
    }

    @Override
    protected void init() {
        super.init();
        int x = this.leftPos;
        int y = this.topPos;
        this.addRenderableWidget(Button.builder(Component.literal("-100"),
                b -> this.sendButton(FluidPumpMenu.BUTTON_MINUS_100)).bounds(x + 108, y + 14, 28, 20).build());
        this.addRenderableWidget(Button.builder(Component.literal("-10"),
                b -> this.sendButton(FluidPumpMenu.BUTTON_MINUS_10)).bounds(x + 108, y + 34, 28, 20).build());
        this.addRenderableWidget(Button.builder(Component.literal("-1"),
                b -> this.sendButton(FluidPumpMenu.BUTTON_MINUS_1)).bounds(x + 108, y + 54, 28, 20).build());
        this.addRenderableWidget(Button.builder(Component.literal("+1"),
                b -> this.sendButton(FluidPumpMenu.BUTTON_PLUS_1)).bounds(x + 138, y + 14, 28, 20).build());
        this.addRenderableWidget(Button.builder(Component.literal("+10"),
                b -> this.sendButton(FluidPumpMenu.BUTTON_PLUS_10)).bounds(x + 138, y + 34, 28, 20).build());
        this.addRenderableWidget(Button.builder(Component.literal("+100"),
                b -> this.sendButton(FluidPumpMenu.BUTTON_PLUS_100)).bounds(x + 138, y + 54, 28, 20).build());
    }

    private void sendButton(int id) {
        if (this.minecraft != null && this.minecraft.gameMode != null) {
            this.minecraft.gameMode.handleInventoryButtonClick(this.menu.containerId, id);
        }
    }

    @Override
    protected void renderBg(GuiGraphics graphics, float partialTick, int mouseX, int mouseY) {
        int x = this.leftPos;
        int y = this.topPos;
        graphics.fill(x, y, x + this.imageWidth, y + this.imageHeight, COLOR_FRAME);
        graphics.fill(x + 2, y + 2, x + this.imageWidth - 2, y + this.imageHeight - 2, COLOR_PANEL);
        graphics.fill(x + 2, y + 82, x + this.imageWidth - 2, y + this.imageHeight - 2, COLOR_INV);

        // 槽位（纯色）
        for (int i = 0; i < this.menu.slots.size(); i++) {
            Slot slot = this.menu.slots.get(i);
            int sx = x + slot.x;
            int sy = y + slot.y;
            graphics.fill(sx - 1, sy - 1, sx + 17, sy + 17, COLOR_SLOT_EDGE);
            graphics.fill(sx, sy, sx + 16, sy + 16, COLOR_SLOT_BG);
        }

        // 能量条（机器区右下角，避开"物品栏"标签文字）
        int barX = x + 70;
        int barY = y + 76;
        int barW = 98;
        int barH = 4;
        graphics.fill(barX, barY, barX + barW, barY + barH, COLOR_BAR_BG);
        int max = Math.max(1, this.menu.getMaxEnergy());
        int filled = Math.round(barW * (this.menu.getEnergy() / (float) max));
        if (filled > 0) {
            graphics.fill(barX, barY, barX + Math.min(filled, barW), barY + barH, COLOR_BAR);
        }
    }

    @Override
    protected void renderLabels(GuiGraphics graphics, int mouseX, int mouseY) {
        super.renderLabels(graphics, mouseX, mouseY);   // 标题 + "物品栏"

        int rate = this.menu.getRate();
        graphics.drawString(this.font, Component.translatable("gui.potato_s_t.fluid_pump.rate", rate),
                8, 16, rate <= 0 ? COLOR_RATE_OFF : COLOR_RATE_ON);
        graphics.drawString(this.font,
                Component.translatable("gui.potato_s_t.fluid_pump.fe", FluidPumpMenu.fePerTick(rate)),
                8, 27, COLOR_TEXT);
        graphics.drawString(this.font,
                Component.translatable("gui.potato_s_t.fluid_pump.flow", FluidPumpMenu.mbPerTick(rate)),
                8, 38, COLOR_TEXT);
        graphics.drawString(this.font,
                Component.translatable("gui.potato_s_t.fluid_pump.range", FluidPumpMenu.maxRange(rate)),
                8, 49, COLOR_TEXT);
        graphics.drawString(this.font,
                Component.translatable("gui.potato_s_t.fluid_pump.energy", this.menu.getEnergy(), this.menu.getMaxEnergy()),
                8, 60, COLOR_TEXT);
    }
}