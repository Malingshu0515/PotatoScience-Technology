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
 * 微型粉碎机（0.10 新增）：普通方块模型（对称、无朝向，方便以后整体换成带建模的版本），右键开 GUI。
 *
 * <p>现在用的是 16×16 占位贴图（顶面 + 侧面），跟项目里其它机器一样等美术 pass。</p>
 */
public class MicroCrusherBlock extends BaseEntityBlock {

    public MicroCrusherBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(MicroCrusherBlock::new);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new MicroCrusherBlockEntity(pos, state);
    }

    /**
     * 双端都要 tick：客户端那一侧负责驱动"运行中"的循环音效（{@code MachineRunningSound}），
     * 只在服务端跑就没人去启动声音了。与电解器 / 发电机同一个理由。
     */
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return createTickerHelper(type, ModBlocks.MICRO_CRUSHER_BE.get(), MicroCrusherBlockEntity::tick);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hitResult) {
        if (!level.isClientSide
                && player instanceof ServerPlayer serverPlayer
                && level.getBlockEntity(pos) instanceof MicroCrusherBlockEntity be) {
            serverPlayer.openMenu(be);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    /**
     * 破坏 / 爆炸 / 被其他方块替换时，把输入槽与 3 个输出槽里的东西全掉出来。
     *
     * <p>必须在 {@code super.onRemove} <b>之前</b>取方块实体，否则它已经被移除了（§4.13）。</p>
     */
    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {
        if (!state.is(newState.getBlock()) && level.getBlockEntity(pos) instanceof MicroCrusherBlockEntity be) {
            MachineDrops.dropInventory(level, pos, be.getInventory());
        }
        super.onRemove(state, level, pos, newState, movedByPiston);
    }

    @Override
    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        return List.of(new ItemStack(this));
    }
}
