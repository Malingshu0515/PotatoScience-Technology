package com.potatost.mod.client;

import com.potatost.mod.AlloySmelterBlockEntity;
import com.potatost.mod.AlloySmelterMenu;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.EnergyBarPart;
import com.potatost.mod.client.gui.parts.ProgressArrowPart;

import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/**
 * 合金冶炼炉界面（0.10 ZF49；箭头进度条 ZF64）：176×186。
 *
 * <p>5 输入 + 3 输出 + 2 消耗槽（画出来但放不进东西），右侧一根能量条，
 * 输入排与输出排之间一支<b>向下</b>的箭头进度条（ZF64 用户要的："正在熔炼什么的箭头，同时也是进度条"）。</p>
 *
 * <p>箭头为什么朝下而不是像 JEI 那样朝右：<b>这台机器的排版是输入排在上、输出排在下</b>
 * （{@link AlloySmelterMenu} 的 INPUT_Y=20 / OUTPUT_Y=62），物料是真的从上往下走 ——
 * 朝右的箭头会指向消耗槽那一侧，反而指错方向。部件本身两种朝向都支持
 * （{@link ProgressArrowPart.Direction}），要改只动这里一行。</p>
 *
 * <p>面板仍是零贴图（{@link MachineScreen#drawPanel} 的纯色 + 立体边框）。</p>
 */
public class AlloySmelterScreen extends MachineScreen<AlloySmelterMenu> {

    public static final int ENERGY_X = 152;
    public static final int ENERGY_Y = 18;
    public static final int ENERGY_W = 10;
    public static final int ENERGY_H = 60;

    /**
     * 箭头进度条：夹在输入排（槽底 y=36）与输出排（槽顶 y=61）之间那 24px 空档里，
     * 水平中心 x=70 —— 正好是输入排（26..114）与输出排（44..96）共同的中线。
     */
    public static final int ARROW_X = 59;
    public static final int ARROW_Y = 38;
    public static final int ARROW_W = 22;
    public static final int ARROW_H = 22;

    public AlloySmelterScreen(AlloySmelterMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title, AlloySmelterMenu.WIDTH, AlloySmelterMenu.HEIGHT);
        this.parts.add(new EnergyBarPart(ENERGY_X, ENERGY_Y, ENERGY_W, ENERGY_H,
                menu::getEnergy, AlloySmelterBlockEntity.MAX_ENERGY));
        this.parts.add(new ProgressArrowPart(ARROW_X, ARROW_Y, ARROW_W, ARROW_H,
                menu::getProgress, menu::getProgressMax,
                ProgressArrowPart.DEFAULT_COLOR, ProgressArrowPart.Direction.DOWN));
    }
}
