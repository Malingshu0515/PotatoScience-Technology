package com.potatost.mod.client;

import com.potatost.mod.LithiumBatteryPlantMenu;
import com.potatost.mod.ModFluids;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.FluidTankPart;
import com.potatost.mod.client.gui.parts.ProgressArrowPart;
import com.potatost.mod.client.gui.parts.StatusLampPart;

import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/**
 * 锂电池构造间界面（0.11 ZF112）：<b>一个硫酸罐 + 四个输入槽 + 一个输出槽 + 进度箭头 + 工作指示灯</b>。
 *
 * <p>用户只点了功能（通硫酸、放四样料、30 秒出锂电池原件、不吃电），<b>没说界面长什么样</b>
 * ⇒ 照本工程机器家族的样子摆：罐在左、槽在中、箭头发在右、灯在右上（这两样都是我定的，
 * 要挪就是一个常量）。<b>没有能量条</b> —— 这台机器不吃电。</p>
 *
 * <p>⚠ 状态灯必须传自己的文案前缀（默认前缀是微型粉碎机的，不传会显示「正在粉碎」，§6.10 ⑪）。</p>
 */
public class LithiumBatteryPlantScreen extends MachineScreen<LithiumBatteryPlantMenu> {

    public static final int WIDTH = 176;
    public static final int HEIGHT = 166;

    /** 状态灯悬停文案前缀（对应 lang 里的 {@code gui.potato_s_t.lithium_battery_plant.status.*}） */
    public static final String STATUS_KEY_PREFIX = "gui.potato_s_t.lithium_battery_plant.status.";

    public LithiumBatteryPlantScreen(LithiumBatteryPlantMenu menu, Inventory playerInventory,
                                     Component title) {
        super(menu, playerInventory, title, WIDTH, HEIGHT);

        this.parts.add(new FluidTankPart(LithiumBatteryPlantMenu.TANK_X, LithiumBatteryPlantMenu.TANK_Y,
                LithiumBatteryPlantMenu.TANK_W, LithiumBatteryPlantMenu.TANK_H,
                menu::getAcid, menu::getTankCapacity, ModFluids.SULFURIC_ACID.get()));
        this.parts.add(new ProgressArrowPart(LithiumBatteryPlantMenu.ARROW_X,
                LithiumBatteryPlantMenu.ARROW_Y, LithiumBatteryPlantMenu.ARROW_W,
                LithiumBatteryPlantMenu.ARROW_H, menu::getProgress, menu::getProgressMax,
                ProgressArrowPart.DEFAULT_COLOR, ProgressArrowPart.Direction.RIGHT));
        this.parts.add(new StatusLampPart(LithiumBatteryPlantMenu.LAMP_X, LithiumBatteryPlantMenu.LAMP_Y,
                LithiumBatteryPlantMenu.LAMP_SIZE, menu::getStatus, STATUS_KEY_PREFIX));
    }
}
