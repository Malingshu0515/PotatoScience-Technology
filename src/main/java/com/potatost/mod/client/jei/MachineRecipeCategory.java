package com.potatost.mod.client.jei;

import com.potatost.mod.MachineRecipes;

import mezz.jei.api.gui.builder.IRecipeLayoutBuilder;
import mezz.jei.api.gui.drawable.IDrawable;
import mezz.jei.api.gui.ingredient.IRecipeSlotsView;
import mezz.jei.api.helpers.IGuiHelper;
import mezz.jei.api.recipe.IFocusGroup;
import mezz.jei.api.recipe.RecipeIngredientRole;
import mezz.jei.api.recipe.RecipeType;
import mezz.jei.api.recipe.category.AbstractRecipeCategory;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.network.chat.Component;

/**
 * 通用「机器配方」分类：左区输入（物品按网格铺、流体各占一行）、右区输出、中间箭头、底部说明行。
 *
 * <p><b>尺寸按数据算，不写死。</b>第一版把宽高写死成 156×96、输入也只用一列往下排，
 * 结果"石英建材"那组有 <b>6 个输入</b>（6×20=120px）直接画出框外，说明行还被压在槽位下面
 * —— 用户截图反馈"配方超出了屏幕很难看"。现在：</p>
 * <ul>
 *   <li>输入物品每行 {@link #IN_COLS} 个、输出每行 {@link #OUT_COLS} 个，横向铺开而不是一路往下堆；</li>
 *   <li>宽高由这台机器<b>实际最坏的一条配方</b>算出来（见 {@code PotatoSTJeiPlugin.registerCategories}），
 *       所以哪怕以后别的 mod 往 {@code c:} 标签里塞了一堆物品、输入变成 20 个，也不会溢出；</li>
 *   <li>说明行排在槽位区<b>下方</b>，不再和槽位重叠。</li>
 * </ul>
 *
 * <p>一台机器一个实例，但只有这一个类 —— 加机器不用写新的分类代码。</p>
 */
public class MachineRecipeCategory extends AbstractRecipeCategory<MachineRecipes.Entry> {

    /** 槽位本身 18px + 间隙 2px */
    private static final int SLOT = 20;
    /** 输入区每行几个 / 输出区每行几个 */
    private static final int IN_COLS = 4;
    private static final int OUT_COLS = 2;
    private static final int PAD = 6;
    /** 输入区与输出区之间留给箭头的宽度 */
    private static final int GAP = 26;
    /** 槽位区与说明行之间的空隙 */
    private static final int INFO_GAP = 4;
    private static final int INFO_LINE_H = 10;

    private final IDrawable background;
    private final IDrawable arrow;
    private final int arrowY;
    private final int infoTop;

    /**
     * @param maxInItems  该机器所有配方里最多的「物品输入」个数
     * @param maxInFluids 最多的「流体输入」个数（各占一整行）
     * @param maxOutItems 最多的「物品输出」个数
     * @param maxOutFluids 最多的「流体输出」个数
     * @param maxInfoLines 最多的说明行数
     */
    public MachineRecipeCategory(RecipeType<MachineRecipes.Entry> type, Component title, IDrawable icon,
                                 IGuiHelper gui,
                                 int maxInItems, int maxInFluids,
                                 int maxOutItems, int maxOutFluids, int maxInfoLines) {
        super(type, title, icon,
                width(),
                height(maxInItems, maxInFluids, maxOutItems, maxOutFluids, maxInfoLines));
        int rows = slotRows(maxInItems, maxInFluids, maxOutItems, maxOutFluids);
        this.background = gui.createBlankDrawable(
                width(), height(maxInItems, maxInFluids, maxOutItems, maxOutFluids, maxInfoLines));
        this.arrow = gui.getRecipeArrow();
        // 箭头的**水平**位置按每条配方算（见 arrowXFor：1 个输入时会左移到输入与输出之间），
        // 竖直方向居中于槽位区。
        this.arrowY = PAD + (rows * SLOT - this.arrow.getHeight()) / 2;
        this.infoTop = PAD + rows * SLOT + INFO_GAP;
    }

    @Override
    public IDrawable getBackground() {
        return this.background;
    }

    // ---------- 尺寸计算（必须是 static：super(...) 要在实例字段之前求值） ----------

    private static int ceilDiv(int a, int b) {
        return (a + b - 1) / b;
    }

    /** 输入占几行：物品按 IN_COLS 折行，之后每个流体各占一行。 */
    private static int inRows(int items, int fluids) {
        return ceilDiv(items, IN_COLS) + fluids;
    }

    private static int outRows(int items, int fluids) {
        return ceilDiv(items, OUT_COLS) + fluids;
    }

    private static int slotRows(int inItems, int inFluids, int outItems, int outFluids) {
        return Math.max(1, Math.max(inRows(inItems, inFluids), outRows(outItems, outFluids)));
    }

    private static int width() {
        return PAD + IN_COLS * SLOT + GAP + OUT_COLS * SLOT + PAD;
    }

    private static int height(int inItems, int inFluids, int outItems, int outFluids, int infoLines) {
        return PAD + slotRows(inItems, inFluids, outItems, outFluids) * SLOT
                + INFO_GAP + Math.max(1, infoLines) * INFO_LINE_H + PAD;
    }

    private static int outX() {
        return PAD + IN_COLS * SLOT + GAP;
    }

    // ---------- 布局 ----------

    @Override
    public void setRecipe(IRecipeLayoutBuilder builder, MachineRecipes.Entry recipe, IFocusGroup focuses) {
        // 输入物品：按 IN_COLS 折行的网格
        int inItems = recipe.itemIn().size();
        for (int i = 0; i < inItems; i++) {
            builder.addSlot(RecipeIngredientRole.INPUT,
                            PAD + (i % IN_COLS) * SLOT,
                            PAD + (i / IN_COLS) * SLOT)
                    .addItemStack(recipe.itemIn().get(i))
                    .setStandardSlotBackground();
        }
        // 输入流体：接在物品行之后，每个占一整行
        int inRow = ceilDiv(inItems, IN_COLS);
        for (int i = 0; i < recipe.fluidIn().size(); i++) {
            MachineRecipes.FluidAmount fluid = recipe.fluidIn().get(i);
            builder.addSlot(RecipeIngredientRole.INPUT, PAD, PAD + (inRow + i) * SLOT)
                    .addFluidStack(fluid.fluid(), fluid.mb())
                    .setStandardSlotBackground();
        }

        // 输出物品
        int outItems = recipe.itemOut().size();
        for (int i = 0; i < outItems; i++) {
            builder.addSlot(RecipeIngredientRole.OUTPUT,
                            outX() + (i % OUT_COLS) * SLOT,
                            PAD + (i / OUT_COLS) * SLOT)
                    .addItemStack(recipe.itemOut().get(i))
                    .setOutputSlotBackground();
        }
        // 输出流体
        int outRow = ceilDiv(outItems, OUT_COLS);
        for (int i = 0; i < recipe.fluidOut().size(); i++) {
            MachineRecipes.FluidAmount fluid = recipe.fluidOut().get(i);
            builder.addSlot(RecipeIngredientRole.OUTPUT, outX(), PAD + (outRow + i) * SLOT)
                    .addFluidStack(fluid.fluid(), fluid.mb())
                    .setOutputSlotBackground();
        }
    }

    /**
     * 这条配方的箭头该画在哪（2026-09-24 用户看液压机的 JEI 页面：
     * 「液压机所有配方的箭头稍微左移一点」）。
     *
     * <p><b>原先的问题</b>：箭头永远居中于"4 列输入区与输出区之间那段固定空隙"。
     * 可液压机每条配方**只有 1 个输入**，输入图标只占第 1 列 ⇒ 左边空出 60px、
     * 箭头却紧贴输出槽（看着像贴着输出、离输入很远）。</p>
     *
     * <p><b>改法</b>：按这条配方**实际占用的输入列数**算 —— 箭头在"输入区实际右边界"与
     * "输出区左边界"之间居中。于是：1 个输入时它落在两者正中间（左移约 30px）；
     * 输入铺满 4 列时位置与原先**一模一样**（44 行那种 12 输入的配方不会压到任何槽位）。</p>
     */
    private int arrowXFor(MachineRecipes.Entry recipe) {
        return arrowXBase(recipe) + arrowDx(recipe.machineId());
    }

    /**
     * 每台机器的箭头**微调**（像素；没写的机器就是 0）。
     *
     * <p>0.11 ZF113：合金炉现在画 <b>7 个输入</b>（5 个锭 + ZF111 那 2 个消耗品）⇒
     * 「输入区与输出区之间居中」算出来会紧贴右边的消耗品槽。用户原话「合金冶炼炉的 jei 配方箭头
     * 也向左移 5 个像素」⇒ 只给这台机器 -5，别的机器一格不动。</p>
     */
    private static int arrowDx(String machineId) {
        return "alloy_smelter".equals(machineId) ? -5 : 0;
    }

    /** 居中算法本身（不含每台机器的微调）。 */
    private int arrowXBase(MachineRecipes.Entry recipe) {
        int usedCols = Math.max(1, Math.min(recipe.itemIn().size(), IN_COLS));
        int left = PAD + usedCols * SLOT;
        int right = outX();
        int span = right - left;
        if (span <= this.arrow.getWidth()) {
            // 空隙比箭头还窄（理论上不会）⇒ 贴着输出区左边放，别越界
            return right - this.arrow.getWidth();
        }
        return left + (span - this.arrow.getWidth()) / 2;
    }

    /** 箭头 + 底部说明行（说明行在槽位区**下方**，不会再被槽位压住）。 */
    @Override
    public void draw(MachineRecipes.Entry recipe, IRecipeSlotsView slotsView,
                     GuiGraphics graphics, double mouseX, double mouseY) {
        this.arrow.draw(graphics, arrowXFor(recipe), this.arrowY);

        Font font = Minecraft.getInstance().font;
        int y = this.infoTop;
        for (Component line : recipe.info()) {
            graphics.drawString(font, line, PAD, y, 0xFF404040, false);
            y += INFO_LINE_H;
        }
    }
}
