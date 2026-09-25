package com.potatost.mod.client.gui.parts;

import java.util.function.IntSupplier;

import com.potatost.mod.client.gui.GuiPart;
import com.potatost.mod.client.gui.MachineScreen;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.network.chat.Component;
import net.minecraft.world.level.material.Fluid;
import net.neoforged.neoforge.client.extensions.common.IClientFluidTypeExtensions;

/**
 * 流体罐：框 + 底 + 实时液位（底对齐，高度 = 罐高 × 液量/容量）+ 悬停提示。
 * 液位直接取流体贴图精灵（水是原版动态贴图；氧/氢用我们自己的 still 贴图）。
 */
public class FluidTankPart implements GuiPart {

    public static final int BORDER = 0xFF373737;
    public static final int TROUGH = 0xFF1E1E1E;

    private final int x;
    private final int y;
    private final int w;
    private final int h;
    private final IntSupplier amount;
    private final IntSupplier capacity;
    private Fluid fluid;
    private final Component displayName;
    /** 0.11 ZF109：横躺的罐子（液位从左往右长）—— 采油机的 25B 大油罐要的就是这个 */
    private final boolean horizontal;

    /** 名字默认取流体类型描述（约定：自注册流体在 lang 里加 fluid_type.<ns>.<name>） */
    public FluidTankPart(int x, int y, int w, int h, IntSupplier amount, int capacity, Fluid fluid) {
        this(x, y, w, h, amount, capacity, fluid, fluid.getFluidType().getDescription());
    }

    public FluidTankPart(int x, int y, int w, int h, IntSupplier amount, int capacity,
                         Fluid fluid, Component displayName) {
        this(x, y, w, h, amount, () -> capacity, fluid, displayName);
    }

    /**
     * 容量会随结构变化的机器用这个重载（0.11 ZF78 分馏塔操作器：
     * 石油 12 桶/塔、每种产品 2.5 桶/塔）。
     */
    public FluidTankPart(int x, int y, int w, int h, IntSupplier amount, IntSupplier capacity, Fluid fluid) {
        this(x, y, w, h, amount, capacity, fluid, fluid.getFluidType().getDescription());
    }

    public FluidTankPart(int x, int y, int w, int h, IntSupplier amount, IntSupplier capacity,
                         Fluid fluid, Component displayName) {
        this(x, y, w, h, amount, capacity, fluid, displayName, false);
    }

    /**
     * 0.11 ZF109 新增：<b>横躺的罐子</b>（液位从左往右长，不是从下往上）。
     *
     * <p>采油机的大油罐要的就是"横过来的矩形"（用户原话「不是那种竖直的了 是一个横过来的矩形罐子」）。
     * 做成静态工厂、而不是再复制一个类：罐子这个概念只该有一份实现，
     * 这里只多一个方向开关（竖直那条路的算法与原来逐字相同）。</p>
     */
    public static FluidTankPart horizontal(int x, int y, int w, int h, IntSupplier amount,
                                           IntSupplier capacity, Fluid fluid) {
        return new FluidTankPart(x, y, w, h, amount, capacity, fluid,
                fluid.getFluidType().getDescription(), true);
    }

    /** 横躺版 + 固定容量（与竖版那个 {@code int capacity} 重载对称）。 */
    public static FluidTankPart horizontal(int x, int y, int w, int h, IntSupplier amount,
                                           int capacity, Fluid fluid) {
        return horizontal(x, y, w, h, amount, () -> capacity, fluid);
    }

    private FluidTankPart(int x, int y, int w, int h, IntSupplier amount, IntSupplier capacity,
                          Fluid fluid, Component displayName, boolean horizontal) {
        this.x = x;
        this.y = y;
        this.w = w;
        this.h = h;
        this.amount = amount;
        this.capacity = capacity;
        this.fluid = fluid;
        this.displayName = displayName;
        this.horizontal = horizontal;
    }

    /** The filling machine swaps the displayed fluid per frame; the electrolyzer never calls this. */
    public void setDisplayedFluid(Fluid fluid) {
        this.fluid = fluid;
    }

    @Override
    public void render(MachineScreen<?> screen, GuiGraphics gg) {
        int ax = screen.left() + this.x;
        int ay = screen.top() + this.y;

        gg.fill(ax - 1, ay - 1, ax + this.w + 1, ay + this.h + 1, BORDER);
        gg.fill(ax, ay, ax + this.w, ay + this.h, TROUGH);

        int amt = this.amount.getAsInt();
        int capacityNow = this.capacity.getAsInt();
        if (amt <= 0 || capacityNow <= 0) {
            return;
        }
        // 液位长在哪个轴上：竖罐按高度、横罐按宽度（0.11 ZF109）
        long span = this.horizontal ? this.w : this.h;
        int fill = (int) (span * Math.min(amt, capacityNow) / capacityNow);
        if (fill <= 0) {
            return;
        }

        IClientFluidTypeExtensions ext = IClientFluidTypeExtensions.of(this.fluid);
        TextureAtlasSprite sprite = Minecraft.getInstance()
                .getTextureAtlas(TextureAtlas.LOCATION_BLOCKS)
                .apply(ext.getStillTexture());
        int tint = ext.getTintColor();
        float a = ((tint >> 24) & 0xFF) / 255.0F;
        float r = ((tint >> 16) & 0xFF) / 255.0F;
        float g = ((tint >> 8) & 0xFF) / 255.0F;
        float b = (tint & 0xFF) / 255.0F;
        if (this.horizontal) {
            gg.blit(ax, ay, 0, fill, this.h, sprite, r, g, b, a);                    // 从左往右长
        } else {
            gg.blit(ax, ay + this.h - fill, 0, this.w, fill, sprite, r, g, b, a);    // 从下往上长（原样）
        }
    }

    @Override
    public void tooltip(MachineScreen<?> screen, GuiGraphics gg, int mouseX, int mouseY) {
        if (!screen.hovering(mouseX, mouseY, this.x, this.y, this.w, this.h)) {
            return;
        }
        gg.renderTooltip(screen.font(), Component.translatable("gui.potato_s_t.tank",
                this.displayName, this.amount.getAsInt(), this.capacity.getAsInt()), mouseX, mouseY);
    }
}