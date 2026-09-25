package com.potatost.mod.client.gui.parts;

import java.util.function.IntSupplier;
import java.util.function.Supplier;

import com.potatost.mod.client.gui.GuiPart;
import com.potatost.mod.client.gui.MachineScreen;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.network.chat.Component;
import net.minecraft.world.level.material.Fluid;
import net.neoforged.neoforge.client.extensions.common.IClientFluidTypeExtensions;
import net.neoforged.neoforge.fluids.FluidStack;

/**
 * Fluid tank part whose fluid TYPE is read on every frame (0.03, filling machine).
 *
 * FluidTankPart stores the fluid in a final field, which is fine for the
 * electrolyzer (one fixed gas per column) but wrong for a machine that can hold
 * a different gas in the same tank over time. This variant takes suppliers so the
 * sprite follows the fluid for as long as the tank is non-empty.
 *
 * Drawing rules are identical to FluidTankPart: frame, trough, bottom-aligned
 * fill using the real fluid sprite, hover tooltip via gui.potato_s_t.tank.
 */
public class DynamicFluidTankPart implements GuiPart {

    public static final int BORDER = 0xFF373737;
    public static final int TROUGH = 0xFF1E1E1E;

    private final int x;
    private final int y;
    private final int w;
    private final int h;
    private final IntSupplier amount;
    private final int capacity;
    private final Supplier<Fluid> fluid;
    private final Supplier<FluidStack> stack;

    public DynamicFluidTankPart(int x, int y, int w, int h, IntSupplier amount, int capacity,
                                Supplier<Fluid> fluid, Supplier<FluidStack> stack) {
        this.x = x;
        this.y = y;
        this.w = w;
        this.h = h;
        this.amount = amount;
        this.capacity = capacity;
        this.fluid = fluid;
        this.stack = stack;
    }

    @Override
    public void render(MachineScreen<?> screen, GuiGraphics gg) {
        int ax = screen.left() + this.x;
        int ay = screen.top() + this.y;

        gg.fill(ax - 1, ay - 1, ax + this.w + 1, ay + this.h + 1, BORDER);
        gg.fill(ax, ay, ax + this.w, ay + this.h, TROUGH);

        int amt = this.amount.getAsInt();
        FluidStack contents = this.stack.get();
        if (amt <= 0 || this.capacity <= 0 || contents.isEmpty()) {
            return;
        }

        int fill = (int) ((long) this.h * Math.min(amt, this.capacity) / this.capacity);
        if (fill <= 0) {
            return;
        }

        Fluid current = this.fluid.get();
        if (current == null) {
            return;
        }

        IClientFluidTypeExtensions ext = IClientFluidTypeExtensions.of(current);
        TextureAtlasSprite sprite = Minecraft.getInstance()
                .getTextureAtlas(TextureAtlas.LOCATION_BLOCKS)
                .apply(ext.getStillTexture());
        int tint = ext.getTintColor();
        float a = ((tint >> 24) & 0xFF) / 255.0F;
        float r = ((tint >> 16) & 0xFF) / 255.0F;
        float g = ((tint >> 8) & 0xFF) / 255.0F;
        float b = (tint & 0xFF) / 255.0F;
        gg.blit(ax, ay + this.h - fill, 0, this.w, fill, sprite, r, g, b, a);
    }

    @Override
    public void tooltip(MachineScreen<?> screen, GuiGraphics gg, int mouseX, int mouseY) {
        if (!screen.hovering(mouseX, mouseY, this.x, this.y, this.w, this.h)) {
            return;
        }
        Component name = this.stack.get().getHoverName();
        gg.renderTooltip(screen.font(), Component.translatable("gui.potato_s_t.tank",
                name, this.amount.getAsInt(), this.capacity), mouseX, mouseY);
    }
}