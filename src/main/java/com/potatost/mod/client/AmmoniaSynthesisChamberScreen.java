package com.potatost.mod.client;

import com.potatost.mod.AmmoniaSynthesisChamberBlockEntity;
import com.potatost.mod.AmmoniaSynthesisChamberMenu;
import com.potatost.mod.ModFluids;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.EnergyBarPart;
import com.potatost.mod.client.gui.parts.FluidTankPart;
import com.potatost.mod.client.gui.parts.StatusLampPart;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/**
 * 氨气组成室界面（0.11 ZF97）：**左侧原料罐 + 催化剂槽、右侧输出罐**（用户原话），
 * 每个罐下方一个高压气罐槽，右边缘一根能量条 + 一盏状态灯。
 *
 * <pre>
 *   氮气罐(26,17) 氢气罐(48,17)  [催化剂槽(78,35)]   氨气罐(152,17)  能量条(176,17)
 *   气罐槽(26,74) 气罐槽(48,74)                     气罐槽(152,74)  状态灯(176,74)
 * </pre>
 *
 * <p><b>催化剂槽上方那行字</b>是用户点名要的：用户原话「在槽位上文字标一下: [催化剂(铁粉)]」
 * ⇒ 画在槽位正上方（y = 20），有铁粉时绿字、没有时暗红 —— 颜色是**附加**信息，
 * 文字本身与用户写的一字不差。</p>
 *
 * <p><b>⚠ 状态灯必须传自己的文案前缀</b>（§6.10 ⑪ 那一课）。</p>
 */
public class AmmoniaSynthesisChamberScreen extends MachineScreen<AmmoniaSynthesisChamberMenu> {

    public static final int WIDTH = 196;
    public static final int HEIGHT = 202;

    /** 状态灯悬停文案前缀（对应 lang 里的 {@code gui.potato_s_t.ammonia_synthesis.status.*}） */
    public static final String STATUS_KEY_PREFIX = "gui.potato_s_t.ammonia_synthesis.status.";

    /** 催化剂标签的位置（槽位正上方） */
    public static final int LABEL_X = AmmoniaSynthesisChamberMenu.CATALYST_SLOT_X;
    public static final int LABEL_Y = 20;

    private static final int LABEL_OK = 0x2E7D32;      // 绿：槽里有铁粉
    private static final int LABEL_MISSING = 0x9E2B25; // 暗红：还没放

    public AmmoniaSynthesisChamberScreen(AmmoniaSynthesisChamberMenu menu, Inventory playerInventory,
                                         Component title) {
        super(menu, playerInventory, title, WIDTH, HEIGHT);

        addTank(AmmoniaSynthesisChamberBlockEntity.TANK_NITROGEN,
                AmmoniaSynthesisChamberMenu.NITROGEN_X, ModFluids.NITROGEN.get());
        addTank(AmmoniaSynthesisChamberBlockEntity.TANK_HYDROGEN,
                AmmoniaSynthesisChamberMenu.HYDROGEN_X, ModFluids.HYDROGEN.get());
        addTank(AmmoniaSynthesisChamberBlockEntity.TANK_AMMONIA,
                AmmoniaSynthesisChamberMenu.AMMONIA_X, ModFluids.AMMONIA.get());

        this.parts.add(new EnergyBarPart(AmmoniaSynthesisChamberMenu.ENERGY_X,
                AmmoniaSynthesisChamberMenu.ENERGY_Y, AmmoniaSynthesisChamberMenu.ENERGY_W,
                AmmoniaSynthesisChamberMenu.ENERGY_H, menu::getEnergy,
                AmmoniaSynthesisChamberBlockEntity.MAX_ENERGY));
        this.parts.add(new StatusLampPart(AmmoniaSynthesisChamberMenu.LAMP_X,
                AmmoniaSynthesisChamberMenu.LAMP_Y, AmmoniaSynthesisChamberMenu.LAMP_SIZE,
                menu::getStatus, STATUS_KEY_PREFIX));
    }

    private void addTank(int tankIndex, int x, net.minecraft.world.level.material.Fluid fluid) {
        this.parts.add(new FluidTankPart(x, AmmoniaSynthesisChamberMenu.TANK_Y,
                AmmoniaSynthesisChamberMenu.TANK_W, AmmoniaSynthesisChamberMenu.TANK_H,
                () -> this.menu.getTankAmount(tankIndex),
                AmmoniaSynthesisChamberBlockEntity.TANK_CAPACITY, fluid));
    }

    /** 催化剂槽上方那行字（用户点名要的标签）。 */
    @Override
    protected void renderMachineForeground(GuiGraphics gg, float partialTick) {
        gg.drawString(this.font, Component.translatable("gui.potato_s_t.ammonia_synthesis.catalyst"),
                this.leftPos + LABEL_X, this.topPos + LABEL_Y,
                this.menu.hasCatalyst() ? LABEL_OK : LABEL_MISSING, false);
    }
}
