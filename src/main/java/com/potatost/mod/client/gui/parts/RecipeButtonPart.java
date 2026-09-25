package com.potatost.mod.client.gui.parts;

import java.util.function.IntSupplier;

import com.potatost.mod.client.gui.GuiPart;
import com.potatost.mod.client.gui.MachineScreen;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.network.chat.Component;

/**
 * 配方选择按钮（0.11 ZF101：酸性反应室那三个按钮）。
 *
 * <p>本工程**第一次**做可点击的界面部件 —— 配套改动有两处：</p>
 * <ul>
 *   <li>{@link GuiPart#mouseClicked} 新接口（默认 false ⇒ 老部件一个都不用改）；</li>
 *   <li>{@link MachineScreen#mouseClicked} 先让部件过一遍，吃掉就不再往下传。</li>
 * </ul>
 *
 * <p><b>点击怎么送到服务端</b>：走<b>原版菜单按钮通道</b>
 * （{@code handleInventoryButtonClick} ⇒ 服务端 {@code AbstractContainerMenu#clickMenuButton}），
 * 不自建网络包。按钮号 = 配方号（0/1/2），服务端那一侧还会再校验一次（客户端说什么不算数）。</p>
 *
 * <p>画法：20×14 的小按钮，选中的那个是"按下去"的样子（深底 + 亮边），
 * 文字居中；悬停给一条 tooltip（这个配方吃什么、产什么）。</p>
 */
public class RecipeButtonPart implements GuiPart {

    private static final int FACE = 0xFF8B8B8B;
    private static final int FACE_ON = 0xFF5A6E4A;      // 选中的按钮偏绿一点
    private static final int FACE_HOVER = 0xFFA8A8A8;
    private static final int BORDER = 0xFF373737;
    private static final int TEXT = 0xFF202020;
    private static final int TEXT_ON = 0xFFF0F0F0;

    private final int x;
    private final int y;
    private final int w;
    private final int h;
    /** 这个按钮代表的配方号（0 = 碳酸 / 1 = 硝酸 / 2 = 硫酸） */
    private final int recipe;
    /** 当前选中的是谁 */
    private final IntSupplier selected;
    /** 按钮上的字（lang key 由屏幕给，例如 gui.potato_s_t.acidic_reaction_chamber.recipe.0） */
    private final Component label;
    /** 悬停说明（这个配方的输入与产物） */
    private final Component tooltip;

    public RecipeButtonPart(int x, int y, int w, int h, int recipe, IntSupplier selected,
                            Component label, Component tooltip) {
        this.x = x;
        this.y = y;
        this.w = w;
        this.h = h;
        this.recipe = recipe;
        this.selected = selected;
        this.label = label;
        this.tooltip = tooltip;
    }

    @Override
    public void render(MachineScreen<?> screen, GuiGraphics gg) {
        int ax = screen.left() + this.x;
        int ay = screen.top() + this.y;
        boolean on = this.selected.getAsInt() == this.recipe;
        boolean hover = screen.hovering(screen.lastMouseX(), screen.lastMouseY(), this.x, this.y, this.w, this.h);
        int face = on ? FACE_ON : (hover ? FACE_HOVER : FACE);
        gg.fill(ax - 1, ay - 1, ax + this.w + 1, ay + this.h + 1, BORDER);
        gg.fill(ax, ay, ax + this.w, ay + this.h, face);
        // 选中时左上压暗、右下提亮（"按下去"的观感），没选中时反过来
        int light = on ? 0xFF4A4A4A : 0xFFFFFFFF;
        gg.fill(ax, ay, ax + this.w, ay + 1, light);
        gg.fill(ax, ay, ax + 1, ay + this.h, light);
        gg.drawCenteredString(screen.font(), this.label,
                ax + this.w / 2, ay + (this.h - 8) / 2 + 1, on ? TEXT_ON : TEXT);
    }

    @Override
    public void tooltip(MachineScreen<?> screen, GuiGraphics gg, int mouseX, int mouseY) {
        if (!screen.hovering(mouseX, mouseY, this.x, this.y, this.w, this.h)) {
            return;
        }
        gg.renderTooltip(screen.font(), this.tooltip, mouseX, mouseY);
    }

    @Override
    public boolean mouseClicked(MachineScreen<?> screen, double mouseX, double mouseY, int button) {
        if (button != 0 || !screen.hovering(mouseX, mouseY, this.x, this.y, this.w, this.h)) {
            return false;
        }
        Minecraft minecraft = Minecraft.getInstance();
        if (minecraft.gameMode != null && minecraft.player != null) {
            minecraft.gameMode.handleInventoryButtonClick(screen.getMenu().containerId, this.recipe);
        }
        return true;
    }
}
