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
 * 氨气组成室（0.11 ZF97）。
 *
 * <p>用户原话：「氨气组成室 GUi左侧为原料储罐和一个放催化剂（铁粉）的槽位…
 * 右侧则为输出 每t消耗1mB氮气 1mB氢气 200Fe/t 产出1mB氨气 催化剂不消耗
 * 原料储罐下方各有一个放高压气罐的槽位 … 泵只能泵入 氮气 氢气 泵出氨气」。</p>
 *
 * <p>方块本身没朝向（对称占位贴图），右键开界面；破坏时把四个槽里的东西掉出来
 * （⚠ 罐里的气体会丢 —— 老规矩，见 {@link #onRemove}）。</p>
 */
public class AmmoniaSynthesisChamberBlock extends BaseEntityBlock {

    public AmmoniaSynthesisChamberBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(AmmoniaSynthesisChamberBlock::new);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new AmmoniaSynthesisChamberBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
                                                                  BlockEntityType<T> type) {
        return createTickerHelper(type, ModBlocks.AMMONIA_SYNTHESIS_CHAMBER_BE.get(),
                AmmoniaSynthesisChamberBlockEntity::tick);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hitResult) {
        if (!level.isClientSide
                && player instanceof ServerPlayer serverPlayer
                && level.getBlockEntity(pos) instanceof AmmoniaSynthesisChamberBlockEntity be) {
            serverPlayer.openMenu(be);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    /**
     * 破坏时把四个槽（催化剂 + 三个气罐）里的东西掉出来。
     *
     * <p>⚠ 与其它机器一样<b>罐里的流体会丢</b>（老规矩：本模组没有"把罐装进掉落物"的机制），
     * 拆机前先用气罐把氨气接走、或者把原料抽空。</p>
     */
    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {
        if (!state.is(newState.getBlock())
                && level.getBlockEntity(pos) instanceof AmmoniaSynthesisChamberBlockEntity be) {
            MachineDrops.dropInventory(level, pos, be.getInventory());
        }
        super.onRemove(state, level, pos, newState, movedByPiston);
    }

    @Override
    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        return List.of(new ItemStack(this));
    }
}
