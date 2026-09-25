package com.potatost.mod.client;

import com.potatost.mod.PotatoST;

import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.LayeredDraw;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;

/**
 * 星轨坠的倒计时 HUD（0.11 ZF114）—— 画在**快捷栏正上方**的一行红字。
 *
 * <p>用 NeoForge 的图层系统挂在 {@code VanillaGuiLayers.HOTBAR} **之上**
 * （{@link com.potatost.mod.PotatoSTClient} 里那一行 {@code registerAbove}）。
 * 注意那个类在 **NeoForge** 的包里（{@code net.neoforged.neoforge.client.gui.VanillaGuiLayers}），
 * 原版并没有 —— 这是查出来的，不是猜的。</p>
 *
 * <p><b>炫酷但不花哨</b>：深色底条 + 上沿一道同色亮线 + 1.25 倍字号；
 * 最后 5 秒开始轻微脉动（正弦缩放），颜色从橘红转成亮红。
 * 全程零贴图资源（不新增 PNG，公告里的"待画"数不变）、每帧只有一次
 * {@code fill} + 一次 {@code drawCenteredString}，比原版的经验条还便宜。</p>
 */
public class StarfallHudLayer implements LayeredDraw.Layer {

    public static final ResourceLocation ID =
            ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "starfall_countdown");

    /** 距离屏幕底部的偏移：快捷栏与选中物品名之上，聊天下方。 */
    private static final int BOTTOM_OFFSET = 78;
    private static final float BASE_SCALE = 1.25F;

    @Override
    public void render(GuiGraphics graphics, DeltaTracker deltaTracker) {
        Minecraft minecraft = Minecraft.getInstance();
        if (minecraft.player == null || minecraft.options.hideGui) {
            return;
        }
        boolean counting = StarfallClientState.isCounting();
        boolean falling = StarfallClientState.isFalling();
        if (!counting && !falling) {
            return;
        }

        int seconds = counting ? (StarfallClientState.remainTicks() + 19) / 20 : 0;
        Component text = counting
                ? Component.translatable("gui.potato_s_t.starfall.countdown", seconds)
                : Component.translatable("gui.potato_s_t.starfall.falling");
        boolean urgent = counting && seconds <= 5;
        int color = counting ? (urgent ? 0xFFFF3B30 : 0xFFFF7A5C) : 0xFFFFD166;

        int centerX = graphics.guiWidth() / 2;
        int y = graphics.guiHeight() - BOTTOM_OFFSET;
        int width = minecraft.font.width(text);
        float scale = BASE_SCALE + (urgent ? 0.07F * Mth.sin(minecraft.player.tickCount * 0.9F) : 0.0F);

        graphics.pose().pushPose();
        graphics.pose().translate(centerX, y, 0.0F);
        graphics.pose().scale(scale, scale, 1.0F);
        graphics.fill(-width / 2 - 7, -6, width / 2 + 7, 11, urgent ? 0xBB1A0000 : 0x99000000);
        graphics.fill(-width / 2 - 7, -6, width / 2 + 7, -5, color);
        graphics.drawCenteredString(minecraft.font, text, 0, -2, color);
        graphics.pose().popPose();
    }
}
