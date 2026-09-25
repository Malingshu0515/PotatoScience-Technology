package com.potatost.mod.client;

import com.potatost.mod.AirSeparatorBlockEntity;
import com.potatost.mod.AirSeparatorMenu;
import com.potatost.mod.ModFluids;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.FluidTankPart;
import com.potatost.mod.client.gui.parts.StatusLampPart;

import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/**
 * 空气分离器界面（0.11 ZF97）：<b>只有两个储罐 + 一盏工作指示灯</b>
 * （用户原话「gui只有两个储罐（不接受被灌入 只能泵出）一个工作指示灯」）。
 *
 * <p>⚠ 所以这里<b>故意没有</b>能量条、也没有进度条 —— 用户点名"只有"这几样。
 * 电够不够看灯（红灯 = 没电），储罐满没满也看灯（黄灯 = 储罐满）。要加哪个说一声，
 * 部件都是现成的（一行）。</p>
 *
 * <p><b>⚠ 状态灯必须传自己的文案前缀</b>：{@code StatusLampPart} 的默认前缀是微型粉碎机的，
 * 不传会显示「正在粉碎」（§6.10 ⑪ 那次就是这么被用户抓到的）。</p>
 */
public class AirSeparatorScreen extends MachineScreen<AirSeparatorMenu> {

    public static final int WIDTH = 176;
    public static final int HEIGHT = 166;

    /** 状态灯悬停文案前缀（对应 lang 里的 {@code gui.potato_s_t.air_separator.status.*}） */
    public static final String STATUS_KEY_PREFIX = "gui.potato_s_t.air_separator.status.";

    public AirSeparatorScreen(AirSeparatorMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title, WIDTH, HEIGHT);

        this.parts.add(new FluidTankPart(AirSeparatorMenu.NITROGEN_X, AirSeparatorMenu.NITROGEN_Y,
                AirSeparatorMenu.TANK_W, AirSeparatorMenu.TANK_H,
                menu::getNitrogen, AirSeparatorBlockEntity.TANK_CAPACITY, ModFluids.NITROGEN.get()));
        this.parts.add(new FluidTankPart(AirSeparatorMenu.OXYGEN_X, AirSeparatorMenu.OXYGEN_Y,
                AirSeparatorMenu.TANK_W, AirSeparatorMenu.TANK_H,
                menu::getOxygen, AirSeparatorBlockEntity.TANK_CAPACITY, ModFluids.OXYGEN.get()));
        this.parts.add(new StatusLampPart(AirSeparatorMenu.LAMP_X, AirSeparatorMenu.LAMP_Y,
                AirSeparatorMenu.LAMP_SIZE, menu::getStatus, STATUS_KEY_PREFIX));
    }
}
