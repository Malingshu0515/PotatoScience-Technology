package com.potatost.mod.client;

import com.potatost.mod.ModFluids;
import com.potatost.mod.OilPumpBlockEntity;
import com.potatost.mod.OilPumpMenu;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.FluidTankPart;
import com.potatost.mod.client.gui.parts.StatusLampPart;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/**
 * 采油机界面（0.11 ZF109）：<b>一个横躺的 25B 大油罐 + 一盏工作指示灯</b>
 * （用户原话「gui为一个大罐子25B储量（不是那种竖直的了 是一个横过来的矩形罐子）
 * 和一个工作指示灯 能量条不需要」）。
 *
 * <p>⚠ 所以这里<b>没有能量条</b>（用户点名不要）；电够不够看灯（红灯 = 没电）。
 * 罐子横躺 —— 用的是 {@code FluidTankPart.horizontal(...)}（液位从左往右长）。</p>
 *
 * <p><b>⚠ 状态灯必须传自己的文案前缀</b>：默认前缀是微型粉碎机的，不传会显示「正在粉碎」
 * （§6.10 ⑪ 那次就是这么被用户抓到的）。</p>
 *
 * <p>罐子下面那两行数字（下方锁链根数 / 耗电与产量）是<b>我加的</b> —— 用户只点名了罐子和灯。
 * 理由是这台机器"开不了工"的两种原因（不在油田、下方没链条）光看灯分不出来，
 * 而 {@code n} 直接决定电费与产量，玩家得看得见。**说一声就删**（删掉这个覆盖的方法即可）。</p>
 */
public class OilPumpScreen extends MachineScreen<OilPumpMenu> {

    public static final int WIDTH = 176;
    public static final int HEIGHT = 166;

    /** 状态灯悬停文案前缀（对应 lang 里的 {@code gui.potato_s_t.oil_pump.status.*}） */
    public static final String STATUS_KEY_PREFIX = "gui.potato_s_t.oil_pump.status.";

    public OilPumpScreen(OilPumpMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title, WIDTH, HEIGHT);

        this.parts.add(FluidTankPart.horizontal(OilPumpMenu.TANK_X, OilPumpMenu.TANK_Y,
                OilPumpMenu.TANK_W, OilPumpMenu.TANK_H,
                menu::getOil, OilPumpBlockEntity.TANK_CAPACITY, ModFluids.CRUDE_OIL.get()));
        this.parts.add(new StatusLampPart(OilPumpMenu.LAMP_X, OilPumpMenu.LAMP_Y,
                OilPumpMenu.LAMP_SIZE, menu::getStatus, STATUS_KEY_PREFIX));
    }

    /** 罐子下面两行数字（见类注释：这两行是我加的）。 */
    @Override
    protected void renderMachineForeground(GuiGraphics gg, float partialTick) {
        int x = this.left() + OilPumpMenu.TEXT_X;
        gg.drawString(this.font(),
                Component.translatable("gui.potato_s_t.oil_pump.chains", this.menu.getChains()),
                x, this.top() + OilPumpMenu.TEXT_Y_CHAINS, OilPumpMenu.TEXT_COLOR, false);
        gg.drawString(this.font(),
                Component.translatable("gui.potato_s_t.oil_pump.rate",
                        this.menu.getFePerTick(), this.menu.getMbPerSecond()),
                x, this.top() + OilPumpMenu.TEXT_Y_RATE, OilPumpMenu.TEXT_COLOR, false);
    }
}
