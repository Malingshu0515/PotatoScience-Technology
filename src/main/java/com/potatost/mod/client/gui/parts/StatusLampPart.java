package com.potatost.mod.client.gui.parts;

import java.util.function.IntSupplier;

import com.potatost.mod.AcidicReactionChamberBlockEntity;
import com.potatost.mod.AmmoniaSynthesisChamberBlockEntity;
import com.potatost.mod.CombustionChamberBlockEntity;
import com.potatost.mod.DieselGeneratorBlockEntity;
import com.potatost.mod.FluidExchangerBlockEntity;
import com.potatost.mod.HydraulicPressBlockEntity;
import com.potatost.mod.HydrodesulfurizationChamberBlockEntity;
import com.potatost.mod.LithiumBatteryPlantBlockEntity;
import com.potatost.mod.MicroCrusherBlockEntity;
import com.potatost.mod.OilPumpBlockEntity;
import com.potatost.mod.client.gui.GuiPart;
import com.potatost.mod.client.gui.MachineScreen;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.network.chat.Component;

/**
 * 状态灯：一个小方灯 + 悬停说明（0.10 新增，第一台用它的机器是微型粉碎机）。
 *
 * <p>颜色语义（与各机器方块实体里的 STATUS_* 一一对应）：
 * <ul>
 *   <li><b>绿</b>：配方有效且电够，正在运行；</li>
 *   <li><b>红</b>：配方有效但电不够；</li>
 *   <li><b>黄</b>：开不了工——红石信号关机 / 输入槽空 / 物品不可加工 / 输出槽满。</li>
 * </ul>
 * 状态值由服务端每 tick 算好，经 ContainerData 同步过来，客户端只负责上色。</p>
 *
 * <p><b>ⓘ 0.10 ZF30 修：文案前缀必须由构造方给。</b>
 * 第一版把 {@code "gui.potato_s_t.micro_crusher.status."} 写死在类里，
 * 液压机直接复用这个部件 ⇒ 悬停显示的是「<b>正在粉碎</b>」。
 * 颜色/状态码两边本来就一致（六个 STATUS_* 取值相同），所以只有文案会错 ——
 * 这种"复用部件时漏掉参数化"的错误编译不报、检查脚本也查不到（键都存在，只是属于另一台机器），
 * 只能靠**在游戏里把鼠标放上去**发现。用户截图点出来的就是这个。</p>
 */
public class StatusLampPart implements GuiPart {

    public static final int BORDER = 0xFF373737;
    /** 未知状态（理论上不会出现） */
    public static final int OFF = 0xFF2A2A2A;

    public static final int GREEN = 0xFF3FC23F;
    public static final int RED = 0xFFD23B3B;
    public static final int YELLOW = 0xFFE0C040;

    /** 微型粉碎机的文案前缀（老调用点不传前缀时用它，保持向后兼容） */
    public static final String MICRO_CRUSHER_PREFIX = "gui.potato_s_t.micro_crusher.status.";

    private final int x;
    private final int y;
    private final int size;
    private final IntSupplier status;
    /** 悬停文案前缀，形如 {@code gui.potato_s_t.<机器id>.status.} */
    private final String keyPrefix;

    public StatusLampPart(int x, int y, int size, IntSupplier status) {
        this(x, y, size, status, MICRO_CRUSHER_PREFIX);
    }

    public StatusLampPart(int x, int y, int size, IntSupplier status, String keyPrefix) {
        this.x = x;
        this.y = y;
        this.size = size;
        this.status = status;
        this.keyPrefix = keyPrefix;
    }

    @Override
    public void render(MachineScreen<?> screen, GuiGraphics gg) {
        int ax = screen.left() + this.x;
        int ay = screen.top() + this.y;

        gg.fill(ax - 1, ay - 1, ax + this.size + 1, ay + this.size + 1, BORDER);
        gg.fill(ax, ay, ax + this.size, ay + this.size, colorOf(this.status.getAsInt()));
    }

    @Override
    public void tooltip(MachineScreen<?> screen, GuiGraphics gg, int mouseX, int mouseY) {
        if (!screen.hovering(mouseX, mouseY, this.x, this.y, this.size, this.size)) {
            return;
        }
        int now = this.status.getAsInt();
        gg.renderTooltip(screen.font(), Component.translatable(this.keyPrefix + suffixOf(now)), mouseX, mouseY);
    }

    private static int colorOf(int status) {
        return switch (status) {
            case MicroCrusherBlockEntity.STATUS_RUNNING -> GREEN;
            case MicroCrusherBlockEntity.STATUS_NO_POWER -> RED;
            case MicroCrusherBlockEntity.STATUS_DISABLED,
                 MicroCrusherBlockEntity.STATUS_EMPTY,
                 MicroCrusherBlockEntity.STATUS_INVALID,
                 MicroCrusherBlockEntity.STATUS_OUTPUT_FULL -> YELLOW;
            // 0.11 ZF79：液压机第 7 个状态"材料数量不够"（沥青要 12 个）—— 与"空/无效"一样是黄灯
            case HydraulicPressBlockEntity.STATUS_MATERIAL -> YELLOW;
            // 0.11 ZF82：容器换流器新增的两个码 —— 7「这种流体没有官方桶」、8「左槽是气体（请接泵）」
            case FluidExchangerBlockEntity.STATUS_NO_BUCKET,
                 FluidExchangerBlockEntity.STATUS_GAS -> YELLOW;
            // 0.11 ZF96：加氢脱硫反应仓的 9「氢气不够一批」—— 与两种"缺料"一样是黄灯
            //   （这台机器不吃电 ⇒ 红灯在这台机器上永远不会出现）
            case HydrodesulfurizationChamberBlockEntity.STATUS_NO_HYDROGEN -> YELLOW;
            // 0.11 ZF97：氨气组成室的两个新号 —— 10「氮气不够」、11「催化剂槽里没有铁粉」
            case AmmoniaSynthesisChamberBlockEntity.STATUS_NO_NITROGEN,
                 AmmoniaSynthesisChamberBlockEntity.STATUS_NO_CATALYST -> YELLOW;
            // 0.11 ZF100：燃烧反应室的两个新号 —— 12「氧气不够一次反应」、13「副产物槽放不下」
            case CombustionChamberBlockEntity.STATUS_NO_OXYGEN,
                 CombustionChamberBlockEntity.STATUS_BYPRODUCT -> YELLOW;
            // 0.11 ZF101：酸性反应室的 14「流体原料不足」（四种原料共用一个号，见方块实体注释）
            case AcidicReactionChamberBlockEntity.STATUS_INPUTS -> YELLOW;
            // 0.11 ZF109：采油机的 15「不在海洋油田群系」、16「下方没有含水锁链」
            //   —— 两种都是"开不了工"，黄灯
            case OilPumpBlockEntity.STATUS_NOT_OILFIELD,
                 OilPumpBlockEntity.STATUS_NO_CHAIN -> YELLOW;
            // 0.11 ZF112：锂电池构造间的 17「硫酸不够」、18「四样原料不齐」—— 都是开不了工
            case LithiumBatteryPlantBlockEntity.STATUS_NO_ACID,
                 LithiumBatteryPlantBlockEntity.STATUS_INPUTS -> YELLOW;
            // 0.11 ZF125：大型柴油发电机的 19「结构不完整」—— 开不了工，黄灯
            case DieselGeneratorBlockEntity.STATUS_NO_STRUCTURE -> YELLOW;
            default -> OFF;
        };
    }

    /**
     * 状态码 → 文案后缀。
     *
     * <p>用的是 {@link MicroCrusherBlockEntity} 的常量，因为**各机器的六个状态码取值一致**
     * （0=关机 1=空 2=无效 3=没电 4=输出满 5=运行中），这里只按数值映射。
     * 加新机器时如果沿用同一套状态码，只要给出自己的 {@code keyPrefix} 即可。</p>
     *
     * <p>0.11 ZF79：液压机多了一个 <b>6 = 材料数量不够</b>（只有它会按数量吃料），
     * 别的机器永远用不到这个码。</p>
     *
     * <p>0.11 ZF82：容器换流器又加了 <b>7 = 这种流体没有官方桶</b> 与 <b>8 = 左槽是气体（请接泵）</b>。
     * ⚠ 这两个码是**共享命名空间里的新号**：以后哪台机器要用 7/8，得先看看这两条语义能不能共用
     * （真正干净的做法是让每台机器的状态码自带颜色/后缀，那是一次涉及全部机器的重构，先记账）。</p>
     *
     * <p>0.11 ZF96：这一条规矩当场又用了一次 —— 加氢脱硫反应仓要表达「<b>氢气不够一批</b>」，
     * 而 3 号是「没电」（这台机器根本不吃电，拿它当"缺氢气"会让代码语义和灯光提示对不上）
     * ⇒ 另起 <b>9 = 氢气不够</b>。以后要用 9 也得先看这条语义能不能共用。</p>
     *
     * <p>0.11 ZF97：<b>9 号第一次被复用</b> —— 氨气组成室同样要表达「氢气不够」，
     * 语义与 ZF96 那台完全一致 ⇒ 直接用 9，不另起新号（这就是"先看能不能共用"那条规矩的执行）。
     * 另外新起两个号：<b>10 = 氮气不够</b>、<b>11 = 催化剂槽里没有铁粉</b>。</p>
     *
     * <p>0.11 ZF125：大型柴油发电机新起 <b>19 = 结构不完整</b> —— 6~18 全被占了，
     * 语义都对不上「这台机器的壳没搭完」⇒ 只能新起号（这条规矩的另一半：
     * 不能共用时得说清楚为什么）。</p>
     */
    private static String suffixOf(int status) {
        return switch (status) {
            case MicroCrusherBlockEntity.STATUS_RUNNING -> "running";
            case MicroCrusherBlockEntity.STATUS_NO_POWER -> "no_power";
            case MicroCrusherBlockEntity.STATUS_DISABLED -> "disabled";
            case MicroCrusherBlockEntity.STATUS_INVALID -> "invalid";
            case MicroCrusherBlockEntity.STATUS_OUTPUT_FULL -> "output_full";
            case HydraulicPressBlockEntity.STATUS_MATERIAL -> "material";
            case FluidExchangerBlockEntity.STATUS_NO_BUCKET -> "no_bucket";
            case FluidExchangerBlockEntity.STATUS_GAS -> "gas";
            case HydrodesulfurizationChamberBlockEntity.STATUS_NO_HYDROGEN -> "no_hydrogen";
            case AmmoniaSynthesisChamberBlockEntity.STATUS_NO_NITROGEN -> "no_nitrogen";
            case AmmoniaSynthesisChamberBlockEntity.STATUS_NO_CATALYST -> "no_catalyst";
            case CombustionChamberBlockEntity.STATUS_NO_OXYGEN -> "no_oxygen";
            case CombustionChamberBlockEntity.STATUS_BYPRODUCT -> "byproduct";
            // 0.11 ZF101：酸性反应室的 14
            case AcidicReactionChamberBlockEntity.STATUS_INPUTS -> "inputs";
            // 0.11 ZF109：采油机的 15「不在海洋油田」、16「下方没有含水锁链」
            case OilPumpBlockEntity.STATUS_NOT_OILFIELD -> "not_oilfield";
            case OilPumpBlockEntity.STATUS_NO_CHAIN -> "no_chain";
            // 0.11 ZF112：锂电池构造间的 17「硫酸不够」、18「原料不齐」
            case LithiumBatteryPlantBlockEntity.STATUS_NO_ACID -> "no_acid";
            case LithiumBatteryPlantBlockEntity.STATUS_INPUTS -> "inputs";
            // 0.11 ZF125：大型柴油发电机的 19
            case DieselGeneratorBlockEntity.STATUS_NO_STRUCTURE -> "no_structure";
            default -> "empty";
        };
    }
}
