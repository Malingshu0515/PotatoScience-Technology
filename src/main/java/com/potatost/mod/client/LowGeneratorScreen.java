package com.potatost.mod.client;

import com.potatost.mod.LowGeneratorBlockEntity;
import com.potatost.mod.LowGeneratorMenu;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.EnergyBarPart;

import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/**
 * 低级发电机界面：**只有一根能量条**（面板/槽位由 {@link MachineScreen} 画，零贴图）。
 *
 * <p>用户原话：「右键打开 gui 只有能量槽和输入槽」⇒ 这里**刻意不加**进度条与状态灯。
 * 输入槽由 {@code LowGeneratorMenu} 摆，画面上只有右侧那根能量条 (146,17,10x54)。</p>
 *
 * <p>⚠ 因此**界面上看不到"还剩多少燃烧时间"** —— 这是照用户要求做的。
 * 燃烧时长其实已经通过 {@code ContainerData}（{@code DATA_BURN} / {@code DATA_BURN_MAX}）
 * 同步到客户端了，要补一个火焰/进度指示随时可以加，不用改方块实体。</p>
 */
public class LowGeneratorScreen extends MachineScreen<LowGeneratorMenu> {

    public static final int ENERGY_X = 146;
    public static final int ENERGY_Y = 17;
    public static final int ENERGY_W = 10;
    public static final int ENERGY_H = 54;

    public LowGeneratorScreen(LowGeneratorMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title, 176, 166);

        this.parts.add(new EnergyBarPart(ENERGY_X, ENERGY_Y, ENERGY_W, ENERGY_H,
                menu::getEnergy, LowGeneratorBlockEntity.MAX_ENERGY));
    }
}
