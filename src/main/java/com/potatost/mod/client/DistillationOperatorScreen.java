package com.potatost.mod.client;

import com.potatost.mod.DistillationOperatorBlockEntity;
import com.potatost.mod.DistillationOperatorMenu;
import com.potatost.mod.ModFluids;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.EnergyBarPart;
import com.potatost.mod.client.gui.parts.FluidTankPart;
import com.potatost.mod.client.gui.parts.ProgressBarPart;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.level.material.Fluid;

/**
 * 分馏塔操作器界面（0.11 ZF78）：**放大面板一次显示完**（用户原话「类似于电力高炉的大 UI」）。
 *
 * <p><b>版面照用户原话摆</b>：</p>
 * <pre>
 *  「gui 右下角靠里面一点为[沥青槽位] 左侧为竖直的能量条（一个分馏塔提供 8096Fe）
 *    和总石油储罐（一个分馏塔提供 12 桶容量）再向右则分别为 柴油、石脑油、汽油、液化石油气」
 * </pre>
 * ⇒ 从左到右一排：[能量条][石油罐][柴油][石脑油][汽油][液化石油气] ……… [沥青槽位]，
 * 沥青槽在右下角、离右边框留 20 px（"靠里面一点"）。
 *
 * <p>罐容量不是常量而是"每塔容量 × 塔数"，所以这里传的是 supplier
 * （{@link FluidTankPart} / {@link EnergyBarPart} 为此各加了一个重载）。</p>
 */
public class DistillationOperatorScreen extends MachineScreen<DistillationOperatorMenu> {

    public static final int WIDTH = 196;
    public static final int HEIGHT = 202;

    /**
     * 罐/能量条那一排的 y。
     *
     * <p>⚠ 2026-09-24 用户实测反馈：「储罐ui和沥青槽稍微往上提几个像素 有点挡住物品栏字样了」
     * ⇒ 58 → **50**（整排上提 8 px）。算账：原版把「物品栏」那行字画在
     * {@code imageHeight - 93 = 109}（9 px 高，占 109~118），而这一排原来底边在 110 ⇒ 正好压住；
     * 上提后底边 102、沥青进度条 104~106，离 109 还有 3 px 余量。</p>
     */
    private static final int ROW_Y = 50;
    private static final int TANK_W = 18;
    private static final int TANK_H = 52;

    /** 竖直能量条（在石油罐左边） */
    private static final int ENERGY_X = 26;
    private static final int ENERGY_W = 10;

    /** 五个罐：石油 → 柴油 → 石脑油 → 汽油 → 液化石油气 */
    private static final int TANK_X_FIRST = 44;
    private static final int TANK_STEP = 22;

    /** 沥青槽下面那根 5 tick 进度条 */
    private static final int BAR_H = 2;

    private static final int TEXT_X = 26;
    private static final int TEXT_Y = 20;
    private static final int LABEL_COLOR = 0x404040;
    /** 运行中：绿；其余状态：暗红（屏幕上只有一行字，够用了） */
    private static final int RUNNING_COLOR = 0xFF2E7D32;
    private static final int STOPPED_COLOR = 0xFF9E2B25;

    public DistillationOperatorScreen(DistillationOperatorMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title, WIDTH, HEIGHT);

        this.parts.add(new EnergyBarPart(ENERGY_X, ROW_Y, ENERGY_W, TANK_H,
                menu::getEnergy, menu::getEnergyCapacity));

        addTank(DistillationOperatorBlockEntity.TANK_OIL, ModFluids.CRUDE_OIL.get());
        addTank(DistillationOperatorBlockEntity.TANK_DIESEL, ModFluids.DIESEL.get());
        addTank(DistillationOperatorBlockEntity.TANK_NAPHTHA, ModFluids.NAPHTHA.get());
        addTank(DistillationOperatorBlockEntity.TANK_GASOLINE, ModFluids.GASOLINE.get());
        addTank(DistillationOperatorBlockEntity.TANK_LPG, ModFluids.LPG.get());

        this.parts.add(new ProgressBarPart(DistillationOperatorMenu.SLOT_X,
                DistillationOperatorMenu.SLOT_Y + 18 + BAR_H,
                16, BAR_H, menu::getProgress, DistillationOperatorBlockEntity.BITUMEN_INTERVAL));
    }

    private void addTank(int tankIndex, Fluid fluid) {
        this.parts.add(new FluidTankPart(TANK_X_FIRST + tankIndex * TANK_STEP, ROW_Y, TANK_W, TANK_H,
                () -> this.menu.getTankAmount(tankIndex),
                () -> this.menu.getTankCapacity(tankIndex),
                fluid));
    }

    /** 左上角两行字：分馏塔数量 + 当前状态（罐和条都是自绘部件，文字只能在这里补）。 */
    @Override
    protected void renderMachineForeground(GuiGraphics gg, float partialTick) {
        gg.drawString(this.font, Component.translatable("gui.potato_s_t.distillation.towers",
                        this.menu.getTowers(), DistillationOperatorBlockEntity.MAX_TOWERS),
                this.leftPos + TEXT_X, this.topPos + TEXT_Y, LABEL_COLOR, false);
        gg.drawString(this.font, Component.translatable(statusKey()),
                this.leftPos + TEXT_X, this.topPos + TEXT_Y + 13, statusColor(), false);
    }

    private String statusKey() {
        return switch (this.menu.getStatus()) {
            case DistillationOperatorBlockEntity.STATUS_RUNNING -> "gui.potato_s_t.distillation.status.running";
            case DistillationOperatorBlockEntity.STATUS_NO_CONTROLLER -> "gui.potato_s_t.distillation.status.no_controller";
            case DistillationOperatorBlockEntity.STATUS_NO_TOWER -> "gui.potato_s_t.distillation.status.no_tower";
            case DistillationOperatorBlockEntity.STATUS_NO_REDSTONE -> "gui.potato_s_t.distillation.status.no_redstone";
            case DistillationOperatorBlockEntity.STATUS_BITUMEN_FULL -> "gui.potato_s_t.distillation.status.bitumen_full";
            case DistillationOperatorBlockEntity.STATUS_NO_OIL -> "gui.potato_s_t.distillation.status.no_oil";
            case DistillationOperatorBlockEntity.STATUS_NO_POWER -> "gui.potato_s_t.distillation.status.no_power";
            default -> "gui.potato_s_t.distillation.status.product_full";
        };
    }

    private int statusColor() {
        return this.menu.getStatus() == DistillationOperatorBlockEntity.STATUS_RUNNING
                ? RUNNING_COLOR
                : STOPPED_COLOR;
    }
}
