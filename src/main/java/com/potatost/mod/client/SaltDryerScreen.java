package com.potatost.mod.client;

import com.potatost.mod.SaltDryerBlockEntity;
import com.potatost.mod.SaltDryerMenu;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.EnergyBarPart;
import com.potatost.mod.client.gui.parts.ProgressBarPart;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/**
 * 晒盐机界面：只负责"摆件"。
 * 能量条 (26,25,10,40)、进度条 (48,39,24,8)、状态文字、未工作原因。
 */
public class SaltDryerScreen extends MachineScreen<SaltDryerMenu> {

    public SaltDryerScreen(SaltDryerMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title, 176, 166);

        this.parts.add(new EnergyBarPart(26, 25, 10, 40, menu::getEnergy,
                SaltDryerBlockEntity.MAX_ENERGY));
        this.parts.add(new ProgressBarPart(48, 39, 24, 8, menu::getProgress,
                SaltDryerBlockEntity.PROGRESS_MAX));
    }

    @Override
    protected void renderMachineForeground(GuiGraphics gg, float partialTick) {
        Component status = switch (this.menu.getState()) {
            case SaltDryerBlockEntity.STATE_POWERED ->
                    Component.translatable("gui.potato_s_t.salt_dryer.state.powered");
            case SaltDryerBlockEntity.STATE_PASSIVE ->
                    Component.translatable("gui.potato_s_t.salt_dryer.state.passive");
            default -> Component.translatable("gui.potato_s_t.salt_dryer.state.idle");
        };
        gg.drawCenteredString(this.font, status, this.leftPos + this.imageWidth / 2, this.topPos + 18, 0x404040);

        if (this.menu.getState() == SaltDryerBlockEntity.STATE_IDLE) {
            Component reasonText = switch (this.menu.getReason()) {
                case SaltDryerBlockEntity.REASON_BIOME ->
                        Component.translatable("gui.potato_s_t.salt_dryer.reason.biome");
                case SaltDryerBlockEntity.REASON_HEIGHT ->
                        Component.translatable("gui.potato_s_t.salt_dryer.reason.height");
                case SaltDryerBlockEntity.REASON_WATER ->
                        Component.translatable("gui.potato_s_t.salt_dryer.reason.water");
                case SaltDryerBlockEntity.REASON_OUTPUT ->
                        Component.translatable("gui.potato_s_t.salt_dryer.reason.output");
                default -> Component.empty();
            };
            if (!reasonText.getString().isEmpty()) {
                gg.drawCenteredString(this.font, reasonText,
                        this.leftPos + this.imageWidth / 2, this.topPos + 56, 0x9E2B2B);
            }
        }
    }
}