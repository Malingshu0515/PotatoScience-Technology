package com.potatost.mod;

import java.util.List;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
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
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.templates.FluidTank;

/**
 * 燃烧反应室（0.11 ZF100）。用户原话见 {@link CombustionChamberBlockEntity} 的类注释。
 *
 * <p>方块本身没有朝向（对称 + 占位贴图），界面是零贴图面板
 * （{@link com.potatost.mod.client.CombustionChamberScreen}）。</p>
 *
 * <p><b>氧气怎么进去</b>：两条路 ——</p>
 * <ul>
 *   <li><b>管道/泵</b>：方块登记了 {@code Capabilities.FluidHandler.BLOCK}（六面），只收氧气；</li>
 *   <li><b>手倒</b>：手里拿着装氧气的高压气罐右键机器 ⇒ 一次倒进最多
 *       {@link CombustionChamberBlockEntity#POUR_PER_CLICK} mB
 *       （照加氢脱硫反应仓/灌装机的先例；空手右键仍是开界面）。</li>
 * </ul>
 * <p>二氧化碳与水是<b>只出不进</b>的：把泵接上去抽走即可（泵优先抽二氧化碳）。</p>
 */
public class CombustionChamberBlock extends BaseEntityBlock {

    public CombustionChamberBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(CombustionChamberBlock::new);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new CombustionChamberBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
                                                                  BlockEntityType<T> type) {
        return createTickerHelper(type, ModBlocks.COMBUSTION_CHAMBER_BE.get(),
                CombustionChamberBlockEntity::tick);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hitResult) {
        if (!level.isClientSide
                && player instanceof ServerPlayer serverPlayer
                && level.getBlockEntity(pos) instanceof CombustionChamberBlockEntity be) {
            serverPlayer.openMenu(be);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    /** 倒流体的结果（**文案由 {@link #useItemOn} 负责**，纯逻辑这一段可以被探针直接调用）。 */
    public enum PourResult {
        /** 手上不是流体容器（或那格不是本机器）⇒ 放行走原逻辑 */
        NO_CONTAINER,
        /** 容器是空的 */
        EMPTY,
        /** 倒不进去：氧气罐满了，或者流体不是氧气 */
        REJECTED,
        /** 倒进去了（罐里余量不足 1000 时可能只倒了一部分） */
        POURED
    }

    /**
     * 把手上容器里的流体倒进<b>氧气罐</b> —— 纯逻辑（不碰聊天栏、不放音效）。
     *
     * <p>三步：① 容器里有什么 ⇒ ② {@code SIMULATE} 问罐子能收多少（罐只认氧气，
     * 装别的气体/液体、或者罐满了都是 0）⇒ ③ 能收多少就只从容器里取多少再灌进去，
     * 全程用真实数量，**不会出现"取多了塞不回去"**。</p>
     */
    public static PourResult pourFrom(ItemStack stack, Level level, BlockPos pos) {
        if (!(stack.getItem() instanceof FluidContainerItem container)) {
            return PourResult.NO_CONTAINER;
        }
        if (!(level.getBlockEntity(pos) instanceof CombustionChamberBlockEntity chamber)) {
            return PourResult.NO_CONTAINER;
        }
        FluidStack held = container.contents(stack);
        if (held.isEmpty()) {
            return PourResult.EMPTY;
        }
        FluidTank tank = chamber.getTank(CombustionChamberBlockEntity.TANK_OXYGEN);
        int want = Math.min(CombustionChamberBlockEntity.POUR_PER_CLICK, held.getAmount());
        int accepted = tank.fill(held.copyWithAmount(want), IFluidHandler.FluidAction.SIMULATE);
        if (accepted <= 0) {
            return PourResult.REJECTED;
        }
        FluidStack drained = container.drain(stack, accepted);
        if (drained.isEmpty()) {
            return PourResult.REJECTED;
        }
        tank.fill(drained, IFluidHandler.FluidAction.EXECUTE);
        chamber.setChanged();
        return PourResult.POURED;
    }

    /** 手上拿着流体容器右键 = 往氧气罐里倒（空手右键仍是开界面）。 */
    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
                                              Player player, InteractionHand hand, BlockHitResult hitResult) {
        if (!(stack.getItem() instanceof FluidContainerItem container)) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        if (level.isClientSide) {
            return ItemInteractionResult.sidedSuccess(true);
        }
        PourResult result = pourFrom(stack, level, pos);
        switch (result) {
            case NO_CONTAINER:
                return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
            case EMPTY:
                player.displayClientMessage(
                        Component.translatable("gui.potato_s_t.combustion_chamber.pour.empty"), true);
                break;
            case REJECTED:
                player.displayClientMessage(Component.translatable(
                        "gui.potato_s_t.combustion_chamber.pour.rejected",
                        container.contents(stack).getHoverName()), true);
                break;
            default:
                level.playSound(null, pos, SoundEvents.BUCKET_EMPTY, SoundSource.BLOCKS, 1.0F, 1.0F);
                break;
        }
        return ItemInteractionResult.sidedSuccess(false);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    /**
     * 破坏时把燃料槽/副产物槽里的物品掉出来。
     *
     * <p>⚠ 与其它机器一样<b>罐里的流体会丢</b>（本模组没有"把罐装进掉落物"的机制）——
     * 拆机前先把二氧化碳/水抽走、氧气就别灌太多。</p>
     */
    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {
        if (!state.is(newState.getBlock())
                && level.getBlockEntity(pos) instanceof CombustionChamberBlockEntity be) {
            MachineDrops.dropInventory(level, pos, be.getInventory());
        }
        super.onRemove(state, level, pos, newState, movedByPiston);
    }

    @Override
    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        return List.of(new ItemStack(this));
    }
}
