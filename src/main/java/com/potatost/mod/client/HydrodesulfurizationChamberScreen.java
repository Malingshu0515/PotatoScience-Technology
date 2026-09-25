package com.potatost.mod.client;

import com.potatost.mod.HydrodesulfurizationChamberBlockEntity;
import com.potatost.mod.HydrodesulfurizationChamberMenu;
import com.potatost.mod.ModFluids;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.FluidTankPart;
import com.potatost.mod.client.gui.parts.ProgressArrowPart;
import com.potatost.mod.client.gui.parts.StatusLampPart;

import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/**
 * 加氢脱硫反应仓界面（0.11 ZF96）：只负责"摆件"（面板/槽位由 {@link MachineScreen} 画，零贴图）。
 *
 * <p>版面（176×166，与 {@link HydrodesulfurizationChamberMenu} 的槽位坐标同一套坐标系）：</p>
 * <pre>
 *   沥青槽 (26,35) → 氢气罐 (52,17,18×52) → 箭头 (80,33,22×16) → 硫槽 (112,35)
 *                                            状态灯 (87,52,8×8)
 * </pre>
 *
 * <p><b>⚠ 没有能量条</b>：这台机器不吃电（用户没给能耗数，见方块实体类注释），
 * 所以状态灯上的红灯永远不会出现 —— 两种缺料（沥青不够 / 氢气不够）都是黄灯。</p>
 *
 * <p><b>⚠ 状态灯必须传自己的文案前缀</b>：{@code StatusLampPart} 的默认前缀是微型粉碎机的，
 * 不传会显示「正在粉碎」（§6.10 ⑪ 那次就是这么被用户抓到的）。</p>
 */
public class HydrodesulfurizationChamberScreen extends MachineScreen<HydrodesulfurizationChamberMenu> {

    public static final int WIDTH = 176;
    public static final int HEIGHT = 166;

    /** 状态灯悬停文案前缀（对应 lang 里的 {@code gui.potato_s_t.hydrodesulfurization_chamber.status.*}） */
    public static final String STATUS_KEY_PREFIX = "gui.potato_s_t.hydrodesulfurization_chamber.status.";

    public static final int TANK_X = 52;
    public static final int TANK_Y = 17;
    public static final int TANK_W = 18;
    public static final int TANK_H = 52;

    public static final int ARROW_X = 80;
    public static final int ARROW_Y = 33;
    public static final int ARROW_W = 22;
    public static final int ARROW_H = 16;

    public static final int LAMP_X = 87;
    public static final int LAMP_Y = 52;
    public static final int LAMP_SIZE = 8;

    public HydrodesulfurizationChamberScreen(HydrodesulfurizationChamberMenu menu,
                                             Inventory playerInventory, Component title) {
        super(menu, playerInventory, title, WIDTH, HEIGHT);

        // 氢气罐：液位取氢气的 still 贴图精灵（ZF85 之后由 PotatoSTClient 注册）
        this.parts.add(new FluidTankPart(TANK_X, TANK_Y, TANK_W, TANK_H,
                menu::getTankAmount, HydrodesulfurizationChamberBlockEntity.TANK_CAPACITY,
                ModFluids.HYDROGEN.get()));

        // 箭头：输入在左、输出在右，与 JEI 那支箭头一致
        this.parts.add(new ProgressArrowPart(ARROW_X, ARROW_Y, ARROW_W, ARROW_H,
                menu::getProgress, menu::getProgressMax,
                ProgressArrowPart.DEFAULT_COLOR, ProgressArrowPart.Direction.RIGHT));

        this.parts.add(new StatusLampPart(LAMP_X, LAMP_Y, LAMP_SIZE, menu::getStatus, STATUS_KEY_PREFIX));
    }
}
