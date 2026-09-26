package com.potatost.mod.client;

import com.potatost.mod.DieselGeneratorBlockEntity;
import com.potatost.mod.DieselGeneratorMenu;
import com.potatost.mod.ModFluids;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.FluidTankPart;
import com.potatost.mod.client.gui.parts.StatusLampPart;

import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/**
 * 大型柴油发电机的界面（0.11 ZF125）：<b>一个柴油罐 + 一盏工作指示灯</b>
 * （用户原话「右键打开GUI 显示流体储罐（8000mB）工作指示灯」）。
 *
 * <p>⚠ 所以这里<b>故意没有</b>能量条、也没有进度条 —— 用户点名只有这两样。
 * 内部那 7200 FE 的缓冲是"过路式"的（一满就暂停烧油），要看它加一条
 * {@code EnergyBarPart} 即可（一行）。</p>
 *
 * <p><b>⚠ 状态灯必须传自己的文案前缀</b>：{@code StatusLampPart} 的默认前缀是微型粉碎机的，
 * 不传会显示「正在粉碎」（§6.10 ⑪ 那次就是这么被用户抓到的）。</p>
 */
public class DieselGeneratorScreen extends MachineScreen<DieselGeneratorMenu> {

    public static final int WIDTH = 176;
    public static final int HEIGHT = 166;

    /** 状态灯悬停文案前缀（对应 lang 里的 {@code gui.potato_s_t.diesel_generator.status.*}） */
    public static final String STATUS_KEY_PREFIX = "gui.potato_s_t.diesel_generator.status.";

    public DieselGeneratorScreen(DieselGeneratorMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title, WIDTH, HEIGHT);

        this.parts.add(new FluidTankPart(DieselGeneratorMenu.TANK_X, DieselGeneratorMenu.TANK_Y,
                DieselGeneratorMenu.TANK_W, DieselGeneratorMenu.TANK_H,
                menu::getDiesel, DieselGeneratorBlockEntity.TANK_CAPACITY, ModFluids.DIESEL.get()));
        this.parts.add(new StatusLampPart(DieselGeneratorMenu.LAMP_X, DieselGeneratorMenu.LAMP_Y,
                DieselGeneratorMenu.LAMP_SIZE, menu::getStatus, STATUS_KEY_PREFIX));
    }
}
