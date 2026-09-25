package com.potatost.mod.client;

import com.potatost.mod.SaltDecomposerBlockEntity;
import com.potatost.mod.SaltDecomposerMenu;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.EnergyBarPart;
import com.potatost.mod.client.gui.parts.ProgressBarPart;
import com.potatost.mod.client.gui.parts.StatusLampPart;

import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/**
 * 盐分解构器界面：只负责"摆件"（面板/槽位由 {@link MachineScreen} 画，零贴图）。
 *
 * <p>布局（176x166）：输入槽 (44,35) → 进度条 (70,39,40x8) → 输出槽 ×3 (116, 17/35/53)，
 * 状态灯挂在进度条正下方 (86,50,8x8)，能量条竖在右侧 (146,17,10x54)。</p>
 *
 * <p>⚠ 状态灯**必须传自己的文案前缀**：{@code StatusLampPart} 的默认前缀是微型粉碎机的，
 * 不传会显示「正在粉碎」（§6.10 ⑪ 那次就是这么被用户抓到的）。</p>
 */
public class SaltDecomposerScreen extends MachineScreen<SaltDecomposerMenu> {

    /** 状态灯悬停文案前缀（对应 lang 里的 {@code gui.potato_s_t.salt_decomposer.status.*}） */
    public static final String STATUS_KEY_PREFIX = "gui.potato_s_t.salt_decomposer.status.";

    public static final int PROGRESS_X = 70;
    public static final int PROGRESS_Y = 39;
    public static final int PROGRESS_W = 40;
    public static final int PROGRESS_H = 8;

    public static final int LAMP_X = 86;
    public static final int LAMP_Y = 50;
    public static final int LAMP_SIZE = 8;

    public static final int ENERGY_X = 146;
    public static final int ENERGY_Y = 17;
    public static final int ENERGY_W = 10;
    public static final int ENERGY_H = 54;

    public SaltDecomposerScreen(SaltDecomposerMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title, 176, 166);

        // 容量只有 20 FE ⇒ 那根能量条基本永远是"满/空"两态，这正是"储能极低"的直观体现
        this.parts.add(new EnergyBarPart(ENERGY_X, ENERGY_Y, ENERGY_W, ENERGY_H, menu::getEnergy,
                SaltDecomposerBlockEntity.MAX_ENERGY));
        this.parts.add(new ProgressBarPart(PROGRESS_X, PROGRESS_Y, PROGRESS_W, PROGRESS_H,
                menu::getProgress, menu::getProgressMax, ProgressBarPart.DEFAULT_COLOR));
        this.parts.add(new StatusLampPart(LAMP_X, LAMP_Y, LAMP_SIZE, menu::getStatus, STATUS_KEY_PREFIX));
    }
}
