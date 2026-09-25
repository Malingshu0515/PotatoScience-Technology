package com.potatost.mod.client;

import com.potatost.mod.CombustionChamberBlockEntity;
import com.potatost.mod.CombustionChamberMenu;
import com.potatost.mod.ModFluids;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.FluidTankPart;
import com.potatost.mod.client.gui.parts.ProgressArrowPart;
import com.potatost.mod.client.gui.parts.StatusLampPart;

import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.level.material.Fluids;

/**
 * 燃烧反应室界面（0.11 ZF100）：只负责"摆件"（面板/槽位由 {@link MachineScreen} 画，零贴图）。
 *
 * <p>版面（176×166，与 {@link CombustionChamberMenu} 的槽位坐标同一套坐标系）：</p>
 * <pre>
 *   氧气罐 (26,17) → 二氧化碳罐 (48,17) → 水罐 (70,17) → 箭头 (96,33,22×16) → 燃料槽 (126,26)
 *                                                        状态灯 (103,52,8×8)      副产物槽 (126,48)
 * </pre>
 * 三个罐的画法照用户给的方向：氧气罐在左（**只进不出**）、二氧化碳罐居中（输出）、水罐在右。
 *
 * <p><b>⚠ 没有能量条</b>：这台机器不吃电（用户没给能耗数，见方块实体类注释），
 * 所以状态灯上的红灯永远不会出现 —— 缺氧气 / 副产物槽放不下 / 罐满都是黄灯。</p>
 *
 * <p><b>⚠ 状态灯必须传自己的文案前缀</b>（§6.10 ⑪：不传会显示微型粉碎机的「正在粉碎」）。</p>
 */
public class CombustionChamberScreen extends MachineScreen<CombustionChamberMenu> {

    public static final int WIDTH = 176;
    public static final int HEIGHT = 166;

    /** 状态灯悬停文案前缀（对应 lang 里的 {@code gui.potato_s_t.combustion_chamber.status.*}） */
    public static final String STATUS_KEY_PREFIX = "gui.potato_s_t.combustion_chamber.status.";

    public static final int TANK_Y = 17;
    public static final int TANK_W = 18;
    public static final int TANK_H = 52;

    public static final int OXYGEN_TANK_X = 26;
    public static final int CO2_TANK_X = 48;
    public static final int WATER_TANK_X = 70;

    public static final int ARROW_X = 96;
    public static final int ARROW_Y = 33;
    public static final int ARROW_W = 22;
    public static final int ARROW_H = 16;

    public static final int LAMP_X = 103;
    public static final int LAMP_Y = 52;
    public static final int LAMP_SIZE = 8;

    public CombustionChamberScreen(CombustionChamberMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title, WIDTH, HEIGHT);

        // 氧气罐：**必须输入端**（机器只往里灌，永远不抽出来）
        this.parts.add(new FluidTankPart(OXYGEN_TANK_X, TANK_Y, TANK_W, TANK_H,
                menu::getOxygenAmount, CombustionChamberBlockEntity.OXYGEN_CAPACITY,
                ModFluids.OXYGEN.get()));

        // 二氧化碳罐：输出（泵/管道从这里抽走）
        this.parts.add(new FluidTankPart(CO2_TANK_X, TANK_Y, TANK_W, TANK_H,
                menu::getCo2Amount, CombustionChamberBlockEntity.CO2_CAPACITY,
                ModFluids.CARBON_DIOXIDE.get()));

        // 其他产物罐：目前配方只产水
        this.parts.add(new FluidTankPart(WATER_TANK_X, TANK_Y, TANK_W, TANK_H,
                menu::getWaterAmount, CombustionChamberBlockEntity.WATER_CAPACITY,
                Fluids.WATER));

        // 箭头：输入在左（燃料槽在右边，用 RIGHT 那支把"往右走"的语义留给以后）
        this.parts.add(new ProgressArrowPart(ARROW_X, ARROW_Y, ARROW_W, ARROW_H,
                menu::getProgress, menu::getProgressMax,
                ProgressArrowPart.DEFAULT_COLOR, ProgressArrowPart.Direction.RIGHT));

        this.parts.add(new StatusLampPart(LAMP_X, LAMP_Y, LAMP_SIZE, menu::getStatus, STATUS_KEY_PREFIX));
    }
}
