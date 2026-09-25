package com.potatost.mod;

import org.jetbrains.annotations.Nullable;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * 太阳能板方块（0.10 ZF22）。
 *
 * <p><b>碰撞箱与模型一致（用户要求）：</b>模型只有一个元素 {@code [0,0,0] → [16,1,16]}，
 * 也就是贴着地面、1 像素厚、占满整格的平板 ⇒ {@link #SHAPE} = {@code box(0,0,0,16,1,16)}。
 * 选中框与碰撞箱<b>两个都覆写</b>成同一个 shape，避免"看着能站上去、其实踩空"这类不一致。</p>
 */
public class SolarPanelBlock extends BaseEntityBlock {

    /** 与模型逐字对应：单元素 [0,0,0] → [16,1,16] */
    public static final VoxelShape SHAPE = Block.box(0.0D, 0.0D, 0.0D, 16.0D, 1.0D, 16.0D);

    public SolarPanelBlock(Properties properties) {
        super(properties);
    }

    /** 1.20.5 起 {@code Block} 要求带 codec（照抄微型粉碎机的写法）。 */
    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(SolarPanelBlock::new);
    }

    /** 选中框（鼠标指上去的高亮轮廓） */
    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPE;
    }

    /** 碰撞箱：与模型一致 */
    @Override
    protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos,
                                           CollisionContext context) {
        return SHAPE;
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    @Nullable
    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new SolarPanelBlockEntity(pos, state);
    }

    /** 只有服务端需要 tick（发电/供电/重算并联组），客户端不需要。 */
    @Nullable
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
                                                                  BlockEntityType<T> type) {
        if (level.isClientSide) {
            return null;
        }
        return createTickerHelper(type, ModBlocks.SOLAR_PANEL_BE.get(), SolarPanelBlockEntity::tick);
    }

    /**
     * 水平邻居变了 ⇒ 作废邻居的组快照（ZF24 共享储能）。
     *
     * <p>方块和方块实体<b>一起查</b>是刻意的：挖掉一块板时，邻居读到的状态是<b>空气</b>
     * （挖的那块自己已经不在世界里了），而放置一块板时读到的是<b>方块 + 方块实体都在</b>。
     * 所以要处理"来了"和"走了"两种情况，判据得同时看这两样 —— 只判方块会在挖掉时漏，
     * 只判方块实体会在放置那一瞬间漏（BE 还没挂上）。</p>
     *
     * <p>本块自己的能力监听者也要清：控制器身份可能因为新邻居而转移。</p>
     */
    @Override
    protected void neighborChanged(BlockState state, Level level, BlockPos pos, Block neighborBlock,
                                   BlockPos neighborPos, boolean movedByPiston) {
        super.neighborChanged(state, level, pos, neighborBlock, neighborPos, movedByPiston);
        if (level.isClientSide) {
            return;
        }
        level.invalidateCapabilities(pos);
        for (Direction dir : Direction.Plane.HORIZONTAL) {
            BlockPos n = pos.relative(dir);
            if (level.getBlockState(n).getBlock() instanceof SolarPanelBlock
                    && level.getBlockEntity(n) instanceof SolarPanelBlockEntity panel) {
                panel.invalidateGroup();
                level.invalidateCapabilities(n);
            }
        }
    }

    /**
     * Shift+右键 ⇒ 在聊天栏回报并联情况。
     *
     * <p>普通右键（不按 Shift）直接 {@code PASS}，把交互让给别人 ——
     * 这块板很薄，玩家多半是想在它上面/旁边放东西，抢掉右键会很烦。</p>
     */
    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos,
                                               Player player, BlockHitResult hit) {
        if (!player.isShiftKeyDown()) {
            return InteractionResult.PASS;
        }
        if (level.getBlockEntity(pos) instanceof SolarPanelBlockEntity panel) {
            if (!level.isClientSide) {
                panel.sendStatus(player);
            }
            return InteractionResult.sidedSuccess(level.isClientSide);
        }
        return InteractionResult.PASS;
    }
}
