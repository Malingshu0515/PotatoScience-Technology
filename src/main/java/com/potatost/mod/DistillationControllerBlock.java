package com.potatost.mod;

import java.util.List;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.phys.BlockHitResult;

/**
 * 分馏塔控制器（0.11 ZF78）。
 *
 * <p>用户原话：「<b>检测周围 32*32*10 格范围内的所有符合的[分馏塔]结构
 * （控制器只负责发送检测的分馏塔数量给操作器）</b>」——
 * 所以这个方块<b>没有 GUI、不存物品、不存流体</b>，唯一的工作就是
 * 定期数一遍周围的塔，把<b>数量</b>推给相邻的 {@link DistillationOperatorBlock}。</p>
 *
 * <p>塔本身没有方块实体、也不会被"装配"成部件格：它就是一堆普通装饰方块摆出的形状，
 * 由 {@link DistillationTowerStructure} 逐格比对（与电力高炉那套"换部件格"完全不同，
 * 因为用户对控制器的要求只有"数数量"这一条）。</p>
 *
 * <p><b>2026-09-24 追加</b>（用户：「2可以显示」）：右击控制器 = <b>把排查结果打进聊天栏</b> ——
 * 数到几座、或者"最像的那一处第几层第几排第几列应该是 X 实际是 Y"。
 * 它**仍然没有 GUI**（不开界面、不存状态），只是把算出来的事实念给你听。</p>
 */
public class DistillationControllerBlock extends BaseEntityBlock {

    public DistillationControllerBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(DistillationControllerBlock::new);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new DistillationControllerBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
                                                                  BlockEntityType<T> type) {
        return createTickerHelper(type, ModBlocks.DISTILLATION_CONTROLLER_BE.get(),
                DistillationControllerBlockEntity::tick);
    }

    /**
     * 邻居变了 ⇒ 立刻重扫一次（放/拆操作器、在控制器边上改方块时界面数字立刻跟上）。
     *
     * <p>⚠ 只能覆盖<b>紧邻</b>的变动：十几格外的塔建好了不会传到这里，
     * 那种情况由 20 tick 的定期扫描兜底（最多慢 1 秒）。</p>
     */
    @Override
    protected void neighborChanged(BlockState state, Level level, BlockPos pos, Block neighborBlock,
                                   BlockPos neighborPos, boolean movedByPiston) {
        super.neighborChanged(state, level, pos, neighborBlock, neighborPos, movedByPiston);
        if (!level.isClientSide && level.getBlockEntity(pos) instanceof DistillationControllerBlockEntity controller) {
            controller.requestRescan();
        }
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    /**
     * 右击控制器 = 把排查结果念给玩家（2026-09-24 用户点名要的；<b>仍然没有 GUI</b>）。
     *
     * <p>三种说法：数到塔 ⇒ 报数量；一座都没数到 ⇒ 报「最像的那一处」的第一处不符
     * （层/排/列 + 坐标 + 应该是什么 + 实际是什么 + 错了多少格）；连锚点都没有（理论上不可能）⇒ 报一句空。</p>
     */
    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hitResult) {
        if (!level.isClientSide && player instanceof ServerPlayer serverPlayer) {
            int count = DistillationTowerStructure.countTowers(level, pos);
            if (count > 0) {
                serverPlayer.displayClientMessage(Component.translatable(
                        "gui.potato_s_t.distillation.diagnosis.found", count), false);
                return InteractionResult.sidedSuccess(false);
            }
            DistillationTowerStructure.Diagnosis best = DistillationTowerStructure.diagnose(level, pos);
            if (best == null || best.expected() == null || best.found() == null) {
                serverPlayer.displayClientMessage(Component.translatable(
                        "gui.potato_s_t.distillation.diagnosis.empty"), false);
                return InteractionResult.sidedSuccess(false);
            }
            BlockPos cell = best.base().offset(best.x(), best.y(), best.z());
            serverPlayer.displayClientMessage(Component.translatable(
                    "gui.potato_s_t.distillation.diagnosis.none",
                    best.wrong(),
                    best.y() + 1, best.z() + 1, best.x() + 1,
                    cell.toShortString(),
                    DistillationTowerStructure.blockFor(best.expected()).getName(),
                    best.found().getBlock().getName()), false);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    /** 控制器自己不存东西，挖掉就掉它自己。 */
    @Override
    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        return List.of(new ItemStack(this));
    }
}
