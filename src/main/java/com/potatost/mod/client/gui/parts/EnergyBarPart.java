package com.potatost.mod.client.gui.parts;

import java.util.function.IntSupplier;

import com.potatost.mod.client.gui.GuiPart;
import com.potatost.mod.client.gui.MachineScreen;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.network.chat.Component;

/** 能量条：竖直（默认，底对齐）或水平（左对齐）；悬停显示 能量：x / y FE */
public class EnergyBarPart implements GuiPart {

    public static final int BORDER = 0xFF373737;
    public static final int TROUGH = 0xFF1E1E1E;
    public static final int DEFAULT_COLOR = 0xFFD24A43;

    private final int x;
    private final int y;
    private final int w;
    private final int h;
    private final IntSupplier amount;
    private final IntSupplier max;
    private final int color;
    private final boolean vertical;

    public EnergyBarPart(int x, int y, int w, int h, IntSupplier amount, int max) {
        this(x, y, w, h, amount, max, DEFAULT_COLOR, true);
    }

    public EnergyBarPart(int x, int y, int w, int h, IntSupplier amount, int max, int color, boolean vertical) {
        this(x, y, w, h, amount, () -> max, color, vertical);
    }

    /**
     * 上限会随结构变化的机器用这个重载（0.11 ZF78 分馏塔操作器：上限 = 8096 FE × 分馏塔数）。
     *
     * <p>与固定上限那两版行为完全一样，区别只是每帧重新读一次上限。</p>
     */
    public EnergyBarPart(int x, int y, int w, int h, IntSupplier amount, IntSupplier max) {
        this(x, y, w, h, amount, max, DEFAULT_COLOR, true);
    }

    public EnergyBarPart(int x, int y, int w, int h, IntSupplier amount, IntSupplier max,
                         int color, boolean vertical) {
        this.x = x;
        this.y = y;
        this.w = w;
        this.h = h;
        this.amount = amount;
        this.max = max;
        this.color = color;
        this.vertical = vertical;
    }

    @Override
    public void render(MachineScreen<?> screen, GuiGraphics gg) {
        int ax = screen.left() + this.x;
        int ay = screen.top() + this.y;

        gg.fill(ax - 1, ay - 1, ax + this.w + 1, ay + this.h + 1, BORDER);
        gg.fill(ax, ay, ax + this.w, ay + this.h, TROUGH);

        int amt = this.amount.getAsInt();
        int maxNow = this.max.getAsInt();
        if (amt <= 0 || maxNow <= 0) {
            return;
        }
        int fill = (int) ((long) (this.vertical ? this.h : this.w) * Math.min(amt, maxNow) / maxNow);
        if (fill <= 0) {
            return;
        }
        if (this.vertical) {
            gg.fill(ax, ay + this.h - fill, ax + this.w, ay + this.h, this.color);
        } else {
            gg.fill(ax, ay, ax + fill, ay + this.h, this.color);
        }
    }

    @Override
    public void tooltip(MachineScreen<?> screen, GuiGraphics gg, int mouseX, int mouseY) {
        if (!screen.hovering(mouseX, mouseY, this.x, this.y, this.w, this.h)) {
            return;
        }
        gg.renderTooltip(screen.font(), Component.translatable("gui.potato_s_t.energy",
                this.amount.getAsInt(), this.max.getAsInt()), mouseX, mouseY);
    }
}