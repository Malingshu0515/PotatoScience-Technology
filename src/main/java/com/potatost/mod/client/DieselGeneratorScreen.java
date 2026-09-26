package com.potatost.mod.client;

import com.potatost.mod.DieselGeneratorBlockEntity;
import com.potatost.mod.DieselGeneratorMenu;
import com.potatost.mod.ModFluids;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.EnergyBarPart;
import com.potatost.mod.client.gui.parts.FluidTankPart;
import com.potatost.mod.client.gui.parts.StatusLampPart;

import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/**
 * 大型柴油发电机的界面（0.11 ZF125）：<b>一个柴油罐 + 一盏工作指示灯</b>
 * （用户原话「右键打开GUI 显示流体储罐（8000mB）工作指示灯」）。
 *
 * <p><b>0.11 ZF126 加一根能量条</b>：用户原话「这个加个fe缓存 18k的fe」（附游戏内截图）
 * ⇒ 缓冲从 7200 改成 <b>18000 FE</b>（{@code DieselGeneratorBlockEntity.MAX_ENERGY}），
 * 并在这条界面上把那个数画出来（原来它是个看不见的内部数字）。
 * 用户没点名要这根条，但"点名了一个缓冲值"+界面本来就在眼前 ⇒ 画出来是唯一能让他
 * 自己确认 18k 生效的办法；不要的话删一行即可。</p>
 *
 * <p>⚠ 仍然<b>没有</b>进度条 —— 这台机器没有"一炉多久"的概念，它每 tick 结一次账。</p>
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
        this.parts.add(new EnergyBarPart(DieselGeneratorMenu.ENERGY_X, DieselGeneratorMenu.ENERGY_Y,
                DieselGeneratorMenu.ENERGY_W, DieselGeneratorMenu.ENERGY_H,
                menu::getEnergy, DieselGeneratorBlockEntity.MAX_ENERGY));
        this.parts.add(new StatusLampPart(DieselGeneratorMenu.LAMP_X, DieselGeneratorMenu.LAMP_Y,
                DieselGeneratorMenu.LAMP_SIZE, menu::getStatus, STATUS_KEY_PREFIX));
    }
}
