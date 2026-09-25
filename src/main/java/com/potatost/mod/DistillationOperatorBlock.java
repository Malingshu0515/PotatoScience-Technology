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
 * 分馏塔操作器（0.11 ZF78）：用户原话「放置在一个[分馏塔控制器]旁边，右键打开 gui
 * （类似于电力高炉的大 UI）」。
 *
 * <p>方块本身没朝向（与微型粉碎机同款：对称、16×16 占位贴图），
 * 界面是零贴图大面板（{@link com.potatost.mod.client.DistillationOperatorScreen}）。</p>
 *
 * <p><b>2026-09-24 追加</b>（用户点名）：「手上拿着装油的容器右键 ⇒ 直接倒进石油罐」——
 * 原来的进料口只有管道/泵一条路，实测时很容易卡在"没油"。倒的量与舀取的粒度对称（1000 mB/次）。</p>
 */
public class DistillationOperatorBlock extends BaseEntityBlock {

    /**
     * 手上拿着流体容器右键时，一次倒进多少 mB。
     *
     * <p>与油桶「一次舀一格 = 1000 mB」对称；但罐里余量不足 1000 时<b>能倒多少倒多少</b>
     * （允许倒半格）—— 舀的时候是"装不下就不舀"，倒的时候照那样会很别扭：
     * 罐里只剩 300 mB 空间时你反而一滴都倒不进去。</p>
     */
    public static final int POUR_PER_CLICK = 1000;

    public DistillationOperatorBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(DistillationOperatorBlock::new);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new DistillationOperatorBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
                                                                  BlockEntityType<T> type) {
        return createTickerHelper(type, ModBlocks.DISTILLATION_OPERATOR_BE.get(),
                DistillationOperatorBlockEntity::tick);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hitResult) {
        if (!level.isClientSide
                && player instanceof ServerPlayer serverPlayer
                && level.getBlockEntity(pos) instanceof DistillationOperatorBlockEntity be) {
            serverPlayer.openMenu(be);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    /** 倒流体的结果（**文案由 {@link #useItemOn} 负责**，纯逻辑这一段可以直接被探针调用）。 */
    public enum PourResult {
        /** 手上不是流体容器（或那格不是操作器）⇒ 放行走原逻辑 */
        NO_CONTAINER,
        /** 容器是空的 */
        EMPTY,
        /** 倒不进去：罐满了，或者流体不是原油 */
        REJECTED,
        /** 倒进去了（罐里余量不足 1000 时可能只倒了一部分） */
        POURED
    }

    /**
     * 把手上容器里的流体倒进石油罐 —— <b>纯逻辑</b>（不碰聊天栏、不放音效）。
     *
     * <p>为什么要单独抽出来：探针要能在**没有玩家**的服务端上验它（本工程 §4.43 记过
     * "假玩家 NPE"那一课，能不碰玩家对象就不碰）。</p>
     *
     * <p>三步：① 容器里有什么 ⇒ ② {@code SIMULATE} 问罐子能收多少（罐只认原油，
     * 装气体/别的液体/罐满了都是 0）⇒ ③ 能收多少就只从容器里取多少再灌进去，
     * 全程用真实数量，**不会出现"取多了塞不回去"**。</p>
     */
    public static PourResult pourFrom(ItemStack stack, Level level, BlockPos pos) {
        if (!(stack.getItem() instanceof FluidContainerItem container)) {
            return PourResult.NO_CONTAINER;
        }
        if (!(level.getBlockEntity(pos) instanceof DistillationOperatorBlockEntity operator)) {
            return PourResult.NO_CONTAINER;
        }
        FluidStack held = container.contents(stack);
        if (held.isEmpty()) {
            return PourResult.EMPTY;
        }
        FluidTank oil = operator.getTank(DistillationOperatorBlockEntity.TANK_OIL);
        int want = Math.min(POUR_PER_CLICK, held.getAmount());
        int accepted = oil.fill(held.copyWithAmount(want), IFluidHandler.FluidAction.SIMULATE);
        if (accepted <= 0) {
            return PourResult.REJECTED;
        }
        FluidStack drained = container.drain(stack, accepted);
        if (drained.isEmpty()) {
            return PourResult.REJECTED;
        }
        oil.fill(drained, IFluidHandler.FluidAction.EXECUTE);
        operator.setChanged();
        return PourResult.POURED;
    }

    /**
     * 手上拿着流体容器右键 = 往<b>石油罐</b>里倒（2026-09-24 用户点名要的）。
     *
     * <p>只认 {@link FluidContainerItem}（油桶 / 高压气罐都算），别的物品一律放行走原逻辑；
     * 真正的搬运在 {@link #pourFrom}，这里只负责"说给你听"（提示 + 倒水声）。</p>
     */
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
                        Component.translatable("gui.potato_s_t.distillation.pour.empty"), true);
                break;
            case REJECTED:
                player.displayClientMessage(Component.translatable(
                        "gui.potato_s_t.distillation.pour.rejected",
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
     * 破坏时把沥青槽位里的沥青掉出来。
     *
     * <p>⚠ 与其它机器一样<b>罐里的流体会丢</b>（本模组没有"把罐装进掉落物"的机制，
     * 见档案 §5 待决）—— 拆机前先把罐抽空。</p>
     */
    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {
        if (!state.is(newState.getBlock()) && level.getBlockEntity(pos) instanceof DistillationOperatorBlockEntity be) {
            MachineDrops.dropInventory(level, pos, be.getInventory());
        }
        super.onRemove(state, level, pos, newState, movedByPiston);
    }

    @Override
    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        return List.of(new ItemStack(this));
    }
}
