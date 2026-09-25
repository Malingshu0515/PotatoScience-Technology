package com.potatost.mod.client.gui;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.Slot;

import com.potatost.mod.menu.MachineMenu;

/**
 * 机器界面基类（所有机器统一走这里，renderBg 已锁死）：
 *   面板   = drawPanel()（默认零贴图纯色 + 立体边框，可整体换皮）
 *   槽位   = 原版 container/slot 精灵，自动跟随 menu.slots，不用画
 *   动态件 = parts 清单（罐/条/进度），子类构造器里 add
 */
public abstract class MachineScreen<M extends MachineMenu> extends AbstractContainerScreen<M> {

    /** 原版槽位贴图精灵（1.21.1 自带，无需自己画） */
    private static final ResourceLocation SLOT_SPRITE =
            ResourceLocation.fromNamespaceAndPath("minecraft", "container/slot");

    /** 零贴图面板配色（美术 pass 时覆盖 drawPanel 即可整体换皮） */
    protected static final int PANEL_BG = 0xFFC6C6C6;
    protected static final int PANEL_LIGHT = 0xFFFFFFFF;
    protected static final int PANEL_DARK = 0xFF555555;

    /** 部件清单：子类在构造器里 add(...) */
    protected final List<GuiPart> parts = new ArrayList<>();

    /** 上一帧的鼠标位置（0.11 ZF101：按钮部件要在 render 里知道鼠标在哪才能画"悬停态"） */
    private int lastMouseX;
    private int lastMouseY;

    protected MachineScreen(M menu, Inventory playerInventory, Component title, int imageWidth, int imageHeight) {
        super(menu, playerInventory, title);
        this.imageWidth = imageWidth;
        this.imageHeight = imageHeight;
        // 标题固定比背包第一行高 11px（166→73、184→91）
        this.inventoryLabelY = this.imageHeight - 93;
    }

    // ================= 绘制 =================

    @Override
    protected final void renderBg(GuiGraphics gg, float partialTick, int mouseX, int mouseY) {
        drawPanel(gg);
        for (Slot slot : this.menu.slots) {
            gg.blitSprite(SLOT_SPRITE, this.leftPos + slot.x - 1, this.topPos + slot.y - 1, 0, 18, 18);
        }
        for (GuiPart part : this.parts) {
            part.render(this, gg);
        }
        renderMachineForeground(gg, partialTick);
    }

    /** 默认面板：纯色 + 立体边框（左上亮 / 右下暗）。想换皮肤时覆盖这里 */
    protected void drawPanel(GuiGraphics gg) {
        int x0 = this.leftPos;
        int y0 = this.topPos;
        gg.fill(x0, y0, x0 + this.imageWidth, y0 + this.imageHeight, PANEL_BG);
        gg.fill(x0, y0, x0 + this.imageWidth, y0 + 1, PANEL_LIGHT);
        gg.fill(x0, y0, x0 + 1, y0 + this.imageHeight, PANEL_LIGHT);
        gg.fill(x0, y0 + this.imageHeight - 1, x0 + this.imageWidth, y0 + this.imageHeight, PANEL_DARK);
        gg.fill(x0 + this.imageWidth - 1, y0, x0 + this.imageWidth, y0 + this.imageHeight, PANEL_DARK);
    }

    /** 逃生舱：极少数机器需要额外自绘时覆盖（默认什么都不画） */
    protected void renderMachineForeground(GuiGraphics gg, float partialTick) {
    }

    // ================= 渲染与提示 =================

    @Override
    public void render(GuiGraphics gg, int mouseX, int mouseY, float partialTick) {
        this.lastMouseX = mouseX;
        this.lastMouseY = mouseY;
        super.render(gg, mouseX, mouseY, partialTick);
        this.renderTooltip(gg, mouseX, mouseY);
    }

    @Override
    protected void renderTooltip(GuiGraphics gg, int mouseX, int mouseY) {
        super.renderTooltip(gg, mouseX, mouseY);
        for (GuiPart part : this.parts) {
            part.tooltip(this, gg, mouseX, mouseY);
        }
    }

    /**
     * 点击先给部件过一遍（0.11 ZF101 新增）。
     *
     * <p>部件吃掉点击就到此为止 —— 否则会继续走原版那套"点背包槽位/丢东西"的逻辑。
     * 没部件要的时候行为与以前**完全一致**（老界面一个字节的行为都没变）。</p>
     */
    @Override
    public boolean mouseClicked(double mouseX, double mouseY, int button) {
        for (GuiPart part : this.parts) {
            if (part.mouseClicked(this, mouseX, mouseY, button)) {
                return true;
            }
        }
        return super.mouseClicked(mouseX, mouseY, button);
    }

    // ================= 供部件使用 =================

    public int left() {
        return this.leftPos;
    }

    public int top() {
        return this.topPos;
    }

    public Font font() {
        return this.font;
    }

    public boolean hovering(double mouseX, double mouseY, int x, int y, int w, int h) {
        return this.isHovering(x, y, w, h, mouseX, mouseY);
    }

    /** 上一帧的鼠标位置（按钮部件画悬停态用）。 */
    public int lastMouseX() {
        return this.lastMouseX;
    }

    public int lastMouseY() {
        return this.lastMouseY;
    }
}