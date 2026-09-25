package com.potatost.mod.client.gui.parts;

import java.util.function.IntSupplier;

import com.potatost.mod.client.gui.GuiPart;
import com.potatost.mod.client.gui.MachineScreen;

import net.minecraft.client.gui.GuiGraphics;

/**
 * 箭头形进度条（0.10 ZF64 新增）—— <b>既是"正在熔炼"的指示，也是进度条</b>
 * （用户原话：「然后就是正在熔炼什么的箭头（同时也是进度条）」）。
 *
 * <p>和 {@link ProgressBarPart}（一条方条）的区别只在形状：这里画成一支<b>带箭头的实心箭头</b>，
 * 箭头长度 = 横截面宽的一半 ⇒ 两条斜边每走一格各收 1px，正好 45°，
 * 空的那些格画成暗色凹槽，让玩家一眼看出"这儿是个箭头、现在走到哪了"。</p>
 *
 * <p><b>零贴图</b>：全是 {@code gg.fill} 的整数像素，和面板、能量条同一套美术（等美术 pass 再换精灵）。
 * 外壳比凹槽各外扩 1px，画成 {@link ProgressBarPart#BORDER} 那种深灰描边。</p>
 *
 * <p>朝向：{@link Direction#DOWN} 给"输入在上、输出在下"的排版（合金冶炼炉就是），
 * {@link Direction#RIGHT} 给"输入在左、输出在右"的排版（和 JEI 那支箭头一致）。</p>
 */
public class ProgressArrowPart implements GuiPart {

    public static final int BORDER = ProgressBarPart.BORDER;
    public static final int TROUGH = ProgressBarPart.TROUGH;
    public static final int DEFAULT_COLOR = ProgressBarPart.DEFAULT_COLOR;

    /** 箭头指向（= 主轴方向，也是进度推进的方向：从箭尾推向箭尖）。 */
    public enum Direction {
        /** 竖直向下：填满时箭头整个亮起，箭尖朝下（输入排在上、输出排在下）。 */
        DOWN,
        /** 水平向右：与 JEI 配方页那支箭头一致。 */
        RIGHT
    }

    private final int x;
    private final int y;
    private final int w;
    private final int h;
    private final IntSupplier progress;
    private final IntSupplier max;
    private final int color;
    private final Direction direction;

    public ProgressArrowPart(int x, int y, int w, int h, IntSupplier progress, int max) {
        this(x, y, w, h, progress, () -> max, DEFAULT_COLOR, Direction.DOWN);
    }

    public ProgressArrowPart(int x, int y, int w, int h, IntSupplier progress, IntSupplier max,
                             int color, Direction direction) {
        this.x = x;
        this.y = y;
        this.w = w;
        this.h = h;
        this.progress = progress;
        this.max = max;
        this.color = color;
        this.direction = direction;
    }

    // ================= 形状 =================

    /** 主轴长（箭头指的方向） */
    private int length() {
        return this.direction == Direction.RIGHT ? this.w : this.h;
    }

    /** 横截面宽（垂直于箭头指的方向） */
    private int cross() {
        return this.direction == Direction.RIGHT ? this.h : this.w;
    }

    /**
     * 主轴第 {@code step} 格（0 = 箭尾）的横截面在横向上占 {@code [lo, hi)}。
     *
     * <p>前段是"杆"（宽度取横截面的一半、居中），后段是"头"（每格收 1px ⇒ 45°，收成 1px 的尖端）。</p>
     */
    private int[] span(int step) {
        int len = length();
        int cross = cross();
        int head = Math.max(1, Math.min(cross / 2, len - 1));   // 头部长度 = 半个横截面宽 ⇒ 斜边 45°
        // 杆宽取横截面的一半，并且**让两侧留白一样宽**：宽 22 的箭头配 11px 的杆会左右差 1px（一眼看出来歪）
        int shaft = Math.max(2, cross / 2);
        if (shaft > 2 && (((cross - shaft) & 1) != 0)) {
            shaft--;
        }
        int center = cross / 2;
        if (step < len - head) {
            int lo = (cross - shaft) / 2;
            return new int[] {lo, lo + shaft};
        }
        int k = step - (len - head);                        // 0 .. head-1
        int half = Math.max(1, center * (head - k) / head);
        return new int[] {center - half, center + half};
    }

    // ================= 绘制 =================

    @Override
    public void render(MachineScreen<?> screen, GuiGraphics gg) {
        int ax = screen.left() + this.x;
        int ay = screen.top() + this.y;

        int len = length();
        int maxNow = this.max.getAsInt();
        int value = this.progress.getAsInt();
        int filled = maxNow > 0
                ? (int) ((long) len * Math.min(Math.max(value, 0), maxNow) / maxNow)
                : 0;

        for (int step = 0; step < len; step++) {
            int[] s = span(step);
            int lo = s[0];
            int hi = s[1];
            boolean on = step < filled;
            if (this.direction == Direction.RIGHT) {
                int px = ax + step;
                gg.fill(px, ay + lo - 1, px + 1, ay + hi + 1, BORDER);
                gg.fill(px, ay + lo, px + 1, ay + hi, on ? this.color : TROUGH);
            } else {
                int py = ay + step;
                gg.fill(ax + lo - 1, py, ax + hi + 1, py + 1, BORDER);
                gg.fill(ax + lo, py, ax + hi, py + 1, on ? this.color : TROUGH);
            }
        }

        // 箭尾封口：主轴两侧的描边靠上面每格自己画，箭尾那一端得补一条
        int[] tail = span(0);
        if (this.direction == Direction.RIGHT) {
            gg.fill(ax - 1, ay + tail[0] - 1, ax, ay + tail[1] + 1, BORDER);
        } else {
            gg.fill(ax + tail[0] - 1, ay - 1, ax + tail[1] + 1, ay, BORDER);
        }
    }
}
