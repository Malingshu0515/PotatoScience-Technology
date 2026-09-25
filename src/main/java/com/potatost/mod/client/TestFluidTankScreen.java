package com.potatost.mod.client;

import com.potatost.mod.TestFluidTankBlockEntity;
import com.potatost.mod.TestFluidTankMenu;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;

/**
 * 测试流体储罐界面（纯色面板 + 按钮 + 文字，不依赖 GUI 贴图）。
 * 按钮：6 个档位（只改容量）+ 清空（只清存量）+ 灌满（存量=容量）。
 */
public class TestFluidTankScreen extends AbstractContainerScreen<TestFluidTankMenu> {

    public TestFluidTankScreen(TestFluidTankMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title);
        this.imageWidth = 176;
        this.imageHeight = 166;
    }

    @Override
    protected void init() {
        super.init();
        // 上排：6 个档位（★ 只改容量）
        for (int i = 0; i < TestFluidTankMenu.PRESET_LABELS.length; i++) {
            final int preset = i;
            this.addRenderableWidget(Button.builder(Component.literal(TestFluidTankMenu.PRESET_LABELS[i]),
                            button -> this.sendButton(preset))
                    .bounds(this.leftPos + 8 + i * 27, this.topPos + 38, 26, 20)
                    .build());
        }
        // 下排：清空 / 灌满（左右对称居中）
        this.addRenderableWidget(Button.builder(Component.translatable("gui.potato_s_t.test_fluid_tank.clear"),
                        button -> this.sendButton(TestFluidTankBlockEntity.BUTTON_CLEAR))
                .bounds(this.leftPos + 18, this.topPos + 60, 64, 20)
                .build());
        this.addRenderableWidget(Button.builder(Component.translatable("gui.potato_s_t.test_fluid_tank.fill"),
                        button -> this.sendButton(TestFluidTankBlockEntity.BUTTON_FILL))
                .bounds(this.leftPos + 94, this.topPos + 60, 64, 20)
                .build());
    }

    private void sendButton(int id) {
        if (this.minecraft != null && this.minecraft.gameMode != null) {
            this.minecraft.gameMode.handleInventoryButtonClick(this.menu.containerId, id);
        }
    }

    @Override
    public void render(GuiGraphics guiGraphics, int mouseX, int mouseY, float partialTick) {
        super.render(guiGraphics, mouseX, mouseY, partialTick);
        this.renderTooltip(guiGraphics, mouseX, mouseY);
    }

    @Override
    protected void renderBg(GuiGraphics guiGraphics, float partialTick, int mouseX, int mouseY) {
        int x = this.leftPos;
        int y = this.topPos;
        guiGraphics.fill(x, y, x + this.imageWidth, y + this.imageHeight, 0xFFC6C6C6);
        guiGraphics.fill(x, y, x + this.imageWidth, y + 1, 0xFF373737);
        guiGraphics.fill(x, y + this.imageHeight - 1, x + this.imageWidth, y + this.imageHeight, 0xFF373737);
        guiGraphics.fill(x, y, x + 1, y + this.imageHeight, 0xFF373737);
        guiGraphics.fill(x + this.imageWidth - 1, y, x + this.imageWidth, y + this.imageHeight, 0xFF373737);
    }

    @Override
    protected void renderLabels(GuiGraphics guiGraphics, int mouseX, int mouseY) {
        guiGraphics.drawString(this.font, this.title.getString(), 8, 6, 0x404040);

        String fluidName = getFluidName(this.menu.getFluidId()).getString();
        guiGraphics.drawString(this.font,
                Component.translatable("gui.potato_s_t.test_fluid_tank.fluid").getString() + ": " + fluidName,
                8, 17, 0x404040);

        guiGraphics.drawString(this.font,
                Component.translatable("gui.potato_s_t.test_fluid_tank.stock").getString() + ": "
                        + formatNumber(this.menu.getStockAmount()) + " / "
                        + formatNumber(this.menu.getCapacityAmount()) + " mB",
                8, 27, 0x404040);
    }

    private static Component getFluidName(int fluidId) {
        Fluid fluid = fluidId < 0 ? null : BuiltInRegistries.FLUID.byId(fluidId);
        if (fluid == null || fluid == Fluids.EMPTY) {
            return Component.translatable("gui.potato_s_t.test_fluid_tank.none");
        }
        return fluid.getFluidType().getDescription();
    }

    /** 1234567 → "1,234,567" */
    private static String formatNumber(int value) {
        String digits = Integer.toString(value);
        StringBuilder builder = new StringBuilder();
        int count = 0;
        for (int i = digits.length() - 1; i >= 0; i--) {
            builder.append(digits.charAt(i));
            count++;
            if (count % 3 == 0 && i > 0) {
                builder.append(',');
            }
        }
        return builder.reverse().toString();
    }
}