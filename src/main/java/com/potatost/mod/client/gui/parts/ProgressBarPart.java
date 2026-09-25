package com.potatost.mod.client.gui.parts;

import java.util.function.IntSupplier;

import com.potatost.mod.client.gui.GuiPart;
import com.potatost.mod.client.gui.MachineScreen;

import net.minecraft.client.gui.GuiGraphics;

/** 进度条（左→右填充）。零贴图版；等美术 pass 时再替换成精灵箭头版 */
public class ProgressBarPart implements GuiPart {

    public static final int BORDER = 0xFF373737;
    public static final int TROUGH = 0xFF1E1E1E;
    public static final int DEFAULT_COLOR = 0xFF4A9ED2;

    private final int x;
    private final int y;
    private final int w;
    private final int h;
    private final IntSupplier progress;
    private final IntSupplier max;
    private final int color;

    public ProgressBarPart(int x, int y, int w, int h, IntSupplier progress, int max) {
        this(x, y, w, h, progress, max, DEFAULT_COLOR);
    }

    public ProgressBarPart(int x, int y, int w, int h, IntSupplier progress, int max, int color) {
        this(x, y, w, h, progress, () -> max, color);
    }

    /**
     * 最大值会随配方变化的机器用这个重载（例如微型粉碎机：30s / 120s / 180s 共用同一根条，
     * 条永远表示"当前这一轮的完成度"）。
     */
    public ProgressBarPart(int x, int y, int w, int h, IntSupplier progress, IntSupplier max, int color) {
        this.x = x;
        this.y = y;
        this.w = w;
        this.h = h;
        this.progress = progress;
        this.max = max;
        this.color = color;
    }

    @Override
    public void render(MachineScreen<?> screen, GuiGraphics gg) {
        int ax = screen.left() + this.x;
        int ay = screen.top() + this.y;

        gg.fill(ax - 1, ay - 1, ax + this.w + 1, ay + this.h + 1, BORDER);
        gg.fill(ax, ay, ax + this.w, ay + this.h, TROUGH);

        int maxNow = this.max.getAsInt();
        int value = this.progress.getAsInt();
        if (value <= 0 || maxNow <= 0) {
            return;
        }
        int fill = (int) ((long) this.w * Math.min(value, maxNow) / maxNow);
        if (fill > 0) {
            gg.fill(ax, ay, ax + fill, ay + this.h, this.color);
        }
    }
}
