package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;

/**
 * 大型柴油发电机的接线口方块实体（0.11 ZF125）。
 *
 * <p>存在理由与合金炉的接线口一样：<b>能力只能挂在方块实体上</b>，
 * 而"电只从接线块那一格出"这条规则需要那一格是个能挂能力的东西。
 * 这里自己不存任何数据 —— 每次现找主控，把它的<b>出电</b>接口原样交出去。</p>
 *
 * <p><b>为什么找主控只要看脚下</b>：图纸里【接线块】就在控制器<b>正上方</b>
 * （第 2 层 · 最前排 · 正中间），全工程只此一格 ⇒ {@code pos.below()} 就是控制器，
 * 不用像合金炉那样按结构反推（那台机器有 68 格外壳、接线块可以有好几处）。</p>
 */
public class DieselGeneratorPortBlockEntity extends BlockEntity {

    public DieselGeneratorPortBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.DIESEL_GENERATOR_PORT_BE.get(), pos, state);
    }

    /**
     * 结构没成型就返回 {@code null}（没成型 = 不出电）。
     *
     * <p>返回的接口是<b>只出不进</b>的（{@code canExtract()} 恒真）——
     * 邻居的 INPUT 端子会主动来抽（{@code TerminalBlockEntity} 里那一段
     * 「★ 输入模式：主动从相邻能源方块抽取」），控制器自己也会推。</p>
     */
    public IEnergyStorage getEnergyStorage() {
        DieselGeneratorBlockEntity master = master();
        return master != null && master.isFormed() ? master.getEnergyStorage() : null;
    }

    /**
     * 柴油也可以从接线口灌进来（六面同权）。
     *
     * <p>为什么接线口也收：玩家最顺手的摆法是把泵放在<b>机器顶上</b>
     * （接线口上面正好是空的），而不是绕到控制器正面去堵着界面。
     * 控制器本体同样收 —— 两条路都通，没有方向限制。</p>
     */
    public IFluidHandler getFluidHandler() {
        DieselGeneratorBlockEntity master = master();
        return master == null ? null : master.getFluidHandler();
    }

    /** 主控就在正下方（图纸里接线块那一格永远在控制器头顶）。 */
    private DieselGeneratorBlockEntity master() {
        if (this.level == null) {
            return null;
        }
        return this.level.getBlockEntity(this.worldPosition.below()) instanceof DieselGeneratorBlockEntity m
                ? m : null;
    }
}
