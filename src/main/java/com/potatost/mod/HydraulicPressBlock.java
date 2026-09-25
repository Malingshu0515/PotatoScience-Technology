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
 * 液压机方块（0.10 ZF30）：普通方块模型（对称无朝向），右键开 GUI。
 *
 * <p>与微型粉碎机同一个骨架：{@code codec()}（1.20.5 起 {@code BaseEntityBlock} 的抽象方法）、
 * 双端 tick、右键开菜单、{@code onRemove} 掉出内容物。</p>
 *
 * <p><b>⚠ 双端 tick 是 0.10 ZF36 改的，理由值得记：</b>ZF30 时这台机器没有音效，所以
 * {@code getTicker} 在客户端直接 {@code return null}（"省一次每 tick 的空转"）。
 * ZF36 给它加了循环液压声之后，<b>忘记把这里改回双端</b> ⇒ 客户端根本没有 ticker，
 * {@code HydraulicPressBlockEntity.tick} 的客户端分支永远不执行 ⇒
 * <b>注册、sounds.json、ogg 文件全部正确，游戏里却一点声音都没有，而且不报任何错</b>。
 * 与微型粉碎机 / 电解器 / 发电机同一个写法。</p>
 */
public class HydraulicPressBlock extends BaseEntityBlock {

    public HydraulicPressBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(HydraulicPressBlock::new);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new HydraulicPressBlockEntity(pos, state);
    }

    /** 双端都要 tick：客户端那一侧负责驱动"运行中"的循环液压声（{@code MachineRunningSound}）。 */
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
                                                                  BlockEntityType<T> type) {
        return createTickerHelper(type, ModBlocks.HYDRAULIC_PRESS_BE.get(), HydraulicPressBlockEntity::tick);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hitResult) {
        if (!level.isClientSide
                && player instanceof ServerPlayer serverPlayer
                && level.getBlockEntity(pos) instanceof HydraulicPressBlockEntity be) {
            serverPlayer.openMenu(be);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    /**
     * 破坏 / 爆炸 / 被替换时把输入槽与输出槽的东西全掉出来。
     * <b>必须在 {@code super.onRemove} 之前</b>取方块实体，否则它已经被移除了（§4.13）。
     */
    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {
        if (!state.is(newState.getBlock()) && level.getBlockEntity(pos) instanceof HydraulicPressBlockEntity be) {
            MachineDrops.dropInventory(level, pos, be.getInventory());
        }
        super.onRemove(state, level, pos, newState, movedByPiston);
    }

    @Override
    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        return List.of(new ItemStack(this));
    }
}
