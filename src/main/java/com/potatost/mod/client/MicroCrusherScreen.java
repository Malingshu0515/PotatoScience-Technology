package com.potatost.mod.client;

import com.potatost.mod.MicroCrusherBlockEntity;
import com.potatost.mod.MicroCrusherMenu;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.EnergyBarPart;
import com.potatost.mod.client.gui.parts.ProgressBarPart;
import com.potatost.mod.client.gui.parts.StatusLampPart;

import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/**
 * 微型粉碎机界面：只负责"摆件"。
 *
 * <p>布局（176x166）：输入槽 (35,35) → 进度条 (62,39,28x8) → 输出槽 ×3 (116, 17/35/53)，
 * 状态灯挂在进度条正下方 (72,50,8x8)，能量条竖在右侧 (146,17,10x54)。</p>
 */
public class MicroCrusherScreen extends MachineScreen<MicroCrusherMenu> {

    public static final int PROGRESS_X = 62;
    public static final int PROGRESS_Y = 39;
    public static final int PROGRESS_W = 28;
    public static final int PROGRESS_H = 8;

    /** 状态灯：正好在进度条中心（x=76）下方 */
    public static final int LAMP_X = 72;
    public static final int LAMP_Y = 50;
    public static final int LAMP_SIZE = 8;

    public static final int ENERGY_X = 146;
    public static final int ENERGY_Y = 17;
    public static final int ENERGY_W = 10;
    public static final int ENERGY_H = 54;

    public MicroCrusherScreen(MicroCrusherMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title, 176, 166);

        this.parts.add(new EnergyBarPart(ENERGY_X, ENERGY_Y, ENERGY_W, ENERGY_H, menu::getEnergy,
                MicroCrusherBlockEntity.MAX_ENERGY));
        // 进度条的最大值随配方变（30s / 120s / 180s…），所以传 supplier 而不是常量
        this.parts.add(new ProgressBarPart(PROGRESS_X, PROGRESS_Y, PROGRESS_W, PROGRESS_H,
                menu::getProgress, menu::getProgressMax, ProgressBarPart.DEFAULT_COLOR));
        this.parts.add(new StatusLampPart(LAMP_X, LAMP_Y, LAMP_SIZE, menu::getStatus));
    }
}
