package com.potatost.mod.client;

import com.potatost.mod.FluidExchangerMenu;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.ProgressBarPart;
import com.potatost.mod.client.gui.parts.StatusLampPart;

import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/**
 * 容器换流器界面（0.11 ZF82）：零贴图小面板 176×166。
 *
 * <p>布局（与 {@code FluidExchangerMenu} 同一坐标）：左槽 (44,35) → 进度条 (70,39,40×8) →
 * 右槽 (116,35)，状态灯挂在进度条正下方 (86,50,8×8)。
 * 这台机器**没有电**（用户没给能耗数），所以没有能量条。</p>
 *
 * <p>⚠ 状态灯必须传自己的文案前缀（默认前缀是微型粉碎机的，不传会显示「正在粉碎」——
 * 0.10 ZF30 用户截图点出的就是这个）。</p>
 */
public class FluidExchangerScreen extends MachineScreen<FluidExchangerMenu> {

    /** 状态灯悬停文案前缀（对应 lang 里的 {@code gui.potato_s_t.fluid_exchanger.status.*}） */
    public static final String STATUS_KEY_PREFIX = "gui.potato_s_t.fluid_exchanger.status.";

    public static final int PROGRESS_X = 70;
    public static final int PROGRESS_Y = 39;
    public static final int PROGRESS_W = 40;
    public static final int PROGRESS_H = 8;

    /** 状态灯：正好在进度条中心（x=90）下方 */
    public static final int LAMP_X = 86;
    public static final int LAMP_Y = 50;
    public static final int LAMP_SIZE = 8;

    public FluidExchangerScreen(FluidExchangerMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title, 176, 166);

        this.parts.add(new ProgressBarPart(PROGRESS_X, PROGRESS_Y, PROGRESS_W, PROGRESS_H,
                menu::getProgress, menu::getProgressMax, ProgressBarPart.DEFAULT_COLOR));
        this.parts.add(new StatusLampPart(LAMP_X, LAMP_Y, LAMP_SIZE, menu::getStatus, STATUS_KEY_PREFIX));
    }
}
