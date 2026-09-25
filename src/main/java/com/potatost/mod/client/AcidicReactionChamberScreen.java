package com.potatost.mod.client;

import com.potatost.mod.AcidicReactionChamberBlockEntity;
import com.potatost.mod.AcidicReactionChamberMenu;
import com.potatost.mod.ModFluids;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.EnergyBarPart;
import com.potatost.mod.client.gui.parts.FluidTankPart;
import com.potatost.mod.client.gui.parts.ProgressBarPart;
import com.potatost.mod.client.gui.parts.RecipeButtonPart;
import com.potatost.mod.client.gui.parts.StatusLampPart;

import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.level.material.Fluids;

/**
 * 酸性反应室界面（0.11 ZF101）：只负责"摆件"（面板/槽位由 {@link MachineScreen} 画，零贴图）。
 *
 * <p>版面（196×216，与 {@link AcidicReactionChamberMenu} 的槽位坐标同一套坐标系）：</p>
 * <pre>
 *   四个原料罐 (26,17)(48,17)(70,17)(92,17) 18×40     硫槽 (120,25) · 输出槽 (120,49)
 *   三个产物罐 (26,64)(48,64)(70,64) 18×40            进度条 (120,80,44×8) · 状态灯 (152,25) · 能量条 (168,17,12×40)
 *   三个选择按钮 (25,110)(47,110)(69,110) 20×14 —— 用户原话「三个选择按钮 在储罐下方」
 * </pre>
 *
 * <p><b>⚠ 状态灯必须传自己的文案前缀</b>（§6.10 ⑪：不传会显示微型粉碎机的「正在粉碎」）。</p>
 * <p>这台机器**有**能量条（用户给了 500 FE/t 与 12400 FE）⇒ 红灯（没电）是会出现的。</p>
 */
public class AcidicReactionChamberScreen extends MachineScreen<AcidicReactionChamberMenu> {

    public static final int WIDTH = 214;
    public static final int HEIGHT = 216;

    /** 状态灯悬停文案前缀 */
    public static final String STATUS_KEY_PREFIX = "gui.potato_s_t.acidic_reaction_chamber.status.";
    /** 按钮与 tooltip 的文案前缀（按钮 = .name.N，说明 = .info.N） */
    public static final String RECIPE_KEY_PREFIX = "gui.potato_s_t.acidic_reaction_chamber.recipe.";

    public static final int TANK_W = 18;
    public static final int TANK_H = 40;
    /** 四个原料罐那一行的 y */
    public static final int INPUT_Y = 17;
    /** 三个产物罐那一行的 y */
    public static final int OUTPUT_Y = 64;

    public static final int BUTTON_Y = 110;
    public static final int BUTTON_W = 20;
    public static final int BUTTON_H = 14;
    public static final int BUTTON_X0 = 25;
    public static final int BUTTON_STEP = 22;

    public AcidicReactionChamberScreen(AcidicReactionChamberMenu menu, Inventory playerInventory,
                                       Component title) {
        super(menu, playerInventory, title, WIDTH, HEIGHT);

        // ⚠ 0.11 ZF113：基类按 `imageHeight - 93` 把「物品栏」标签摆到 y=123，
        //    而四个选择按钮在 y=110..124 ⇒ **标签压在按钮上**（用户截图点出来的重叠）。
        //    这里把标签单独往下挪 6 px（129），按钮与背包槽位一个都没动。
        this.inventoryLabelY = HEIGHT - 87;

        // 四个原料罐：只进不出（顺序：二氧化碳 / 氧气 / 氨气 / 水）
        this.parts.add(new FluidTankPart(26, INPUT_Y, TANK_W, TANK_H,
                () -> menu.getTank(AcidicReactionChamberBlockEntity.TANK_CO2),
                AcidicReactionChamberBlockEntity.TANK_CAPACITY, ModFluids.CARBON_DIOXIDE.get()));
        this.parts.add(new FluidTankPart(48, INPUT_Y, TANK_W, TANK_H,
                () -> menu.getTank(AcidicReactionChamberBlockEntity.TANK_OXYGEN),
                AcidicReactionChamberBlockEntity.TANK_CAPACITY, ModFluids.OXYGEN.get()));
        this.parts.add(new FluidTankPart(70, INPUT_Y, TANK_W, TANK_H,
                () -> menu.getTank(AcidicReactionChamberBlockEntity.TANK_AMMONIA),
                AcidicReactionChamberBlockEntity.TANK_CAPACITY, ModFluids.AMMONIA.get()));
        this.parts.add(new FluidTankPart(92, INPUT_Y, TANK_W, TANK_H,
                () -> menu.getTank(AcidicReactionChamberBlockEntity.TANK_WATER),
                AcidicReactionChamberBlockEntity.TANK_CAPACITY, Fluids.WATER));
        // 0.11 ZF102：两个新原料罐（氢气 / 氯气）
        this.parts.add(new FluidTankPart(114, INPUT_Y, TANK_W, TANK_H,
                () -> menu.getTank(AcidicReactionChamberBlockEntity.TANK_HYDROGEN),
                AcidicReactionChamberBlockEntity.TANK_CAPACITY, ModFluids.HYDROGEN.get()));
        this.parts.add(new FluidTankPart(136, INPUT_Y, TANK_W, TANK_H,
                () -> menu.getTank(AcidicReactionChamberBlockEntity.TANK_CHLORINE),
                AcidicReactionChamberBlockEntity.TANK_CAPACITY, ModFluids.CHLORINE.get()));

        // 三个产物罐：只出不进（顺序：碳酸 / 硝酸 / 硫酸）
        this.parts.add(new FluidTankPart(26, OUTPUT_Y, TANK_W, TANK_H,
                () -> menu.getTank(AcidicReactionChamberBlockEntity.TANK_CARBONIC),
                AcidicReactionChamberBlockEntity.TANK_CAPACITY, ModFluids.CARBONIC_ACID.get()));
        this.parts.add(new FluidTankPart(48, OUTPUT_Y, TANK_W, TANK_H,
                () -> menu.getTank(AcidicReactionChamberBlockEntity.TANK_NITRIC),
                AcidicReactionChamberBlockEntity.TANK_CAPACITY, ModFluids.NITRIC_ACID.get()));
        this.parts.add(new FluidTankPart(70, OUTPUT_Y, TANK_W, TANK_H,
                () -> menu.getTank(AcidicReactionChamberBlockEntity.TANK_SULFURIC),
                AcidicReactionChamberBlockEntity.TANK_CAPACITY, ModFluids.SULFURIC_ACID.get()));
        // 0.11 ZF102：第 4 个产物罐（盐酸）
        this.parts.add(new FluidTankPart(92, OUTPUT_Y, TANK_W, TANK_H,
                () -> menu.getTank(AcidicReactionChamberBlockEntity.TANK_HYDROCHLORIC),
                AcidicReactionChamberBlockEntity.TANK_CAPACITY, ModFluids.HYDROCHLORIC_ACID.get()));

        // 能量条：用户给的 12400 FE 缓冲
        this.parts.add(new EnergyBarPart(190, INPUT_Y, 12, TANK_H,
                menu::getEnergy, AcidicReactionChamberBlockEntity.MAX_ENERGY));

        // 进度条：批次式那一条（1/2/4 号是每 tick 一次，条子基本常满）
        this.parts.add(new ProgressBarPart(120, 80, 44, 8, menu::getProgress, menu::getProgressMax,
                ProgressBarPart.DEFAULT_COLOR));

        // ⚠ 0.11 ZF113：状态灯原来在 (174,25) 8×8 —— 它的框画在 173..183，而**硫槽 (160,25)**
        //    的框到 177 ⇒ 压住 4 px（用户截图里槽右上角那个黄方块就是这盏灯）。
        //    挪到能量条正下方 (190,62)：右下角那一列本来就只有能量条，谁也不碰谁。
        this.parts.add(new StatusLampPart(190, 62, 8, menu::getStatus, STATUS_KEY_PREFIX));

        // 三个选择按钮：在产物储罐下方（用户原话），点哪个跑哪个
        for (int recipe = 0; recipe < AcidicReactionChamberBlockEntity.RECIPE_COUNT; recipe++) {
            this.parts.add(new RecipeButtonPart(
                    BUTTON_X0 + recipe * BUTTON_STEP, BUTTON_Y, BUTTON_W, BUTTON_H, recipe,
                    menu::getSelected,
                    Component.translatable(RECIPE_KEY_PREFIX + "name." + recipe),
                    Component.translatable(RECIPE_KEY_PREFIX + "info." + recipe)));
        }
    }
}
