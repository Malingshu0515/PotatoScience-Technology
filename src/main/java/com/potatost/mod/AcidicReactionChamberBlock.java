package com.potatost.mod;

import java.util.List;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.phys.BlockHitResult;

/**
 * 酸性反应室（0.11 ZF101）。用户原话与全部数值见 {@link AcidicReactionChamberBlockEntity} 的类注释。
 *
 * <p>方块没有朝向（对称 + 两张占位贴图），界面是零贴图面板
 * （{@link com.potatost.mod.client.AcidicReactionChamberScreen}）。</p>
 *
 * <p><b>四个原料罐怎么进料</b>：六面都登记了流体能力，管道/泵接上来就行
 * （二氧化碳 / 氧气 / 氨气 / 水各有自己的罐，别的流体一滴不收）。
 * ⚠ <b>本轮没做"手里拿气罐右键倒"</b>（用户没要求；要的话照加氢脱硫反应仓那条加，一次 1000 mB）。</p>
 */
public class AcidicReactionChamberBlock extends BaseEntityBlock {

    public AcidicReactionChamberBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(AcidicReactionChamberBlock::new);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new AcidicReactionChamberBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
                                                                  BlockEntityType<T> type) {
        return createTickerHelper(type, ModBlocks.ACIDIC_REACTION_CHAMBER_BE.get(),
                AcidicReactionChamberBlockEntity::tick);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hitResult) {
        if (!level.isClientSide
                && player instanceof ServerPlayer serverPlayer
                && level.getBlockEntity(pos) instanceof AcidicReactionChamberBlockEntity be) {
            serverPlayer.openMenu(be);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    /**
     * 破坏时把硫槽/输出槽里的物品掉出来。
     *
     * <p>⚠ 与其它机器一样<b>七个罐里的流体会丢</b>（本模组没有"把罐装进掉落物"的机制）——
     * 拆机前先把三种酸抽走。</p>
     */
    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {
        if (!state.is(newState.getBlock())
                && level.getBlockEntity(pos) instanceof AcidicReactionChamberBlockEntity be) {
            MachineDrops.dropInventory(level, pos, be.getInventory());
        }
        super.onRemove(state, level, pos, newState, movedByPiston);
    }

    @Override
    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        return List.of(new ItemStack(this));
    }
}
