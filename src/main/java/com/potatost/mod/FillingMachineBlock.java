package com.potatost.mod;

import java.util.List;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.DirectionProperty;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.phys.BlockHitResult;
import net.neoforged.neoforge.fluids.FluidStack;

/**
 * Filling machine block (0.03).
 *
 * Vanilla cube model with four horizontal facings. Face layout required by the spec:
 * top and bottom differ from the sides, front and back are identical, both sides are
 * identical. That maps to the vanilla "orientable" model family (north = front).
 */
public class FillingMachineBlock extends BaseEntityBlock {

    /** Horizontal facing; the model front is the north face. */
    public static final DirectionProperty FACING = BlockStateProperties.HORIZONTAL_FACING;

    public FillingMachineBlock(Properties properties) {
        super(properties);
        this.registerDefaultState(this.stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(FillingMachineBlock::new);
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return this.defaultBlockState()
                .setValue(FACING, context.getHorizontalDirection().getOpposite());
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new FillingMachineBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        if (level.isClientSide) {
            return null;
        }
        return createTickerHelper(type, ModBlocks.FILLING_MACHINE_BE.get(), FillingMachineBlockEntity::tick);
    }

    /**
     * 空手右键：<b>Shift = 逐槽诊断</b>（为什么没在灌），否则开界面（原行为不动）。
     *
     * <p>0.11 ZF80 加的诊断。用户实测「灌装机不往油桶灌液体」时，探针把整条链验了个遍
     * （54 项全过，含"原油池 → 泵 → 灌装机 → 空油桶"复刻），说明机器逻辑没坏 ——
     * 真正的问题是<b>它什么都不说</b>：罐空 / 缺电 / 罐里是气体 / 容器已满，
     * 四种完全不同的原因，玩家看到的都是"一点反应都没有"。
     * 与分馏塔控制器那句诊断同一个思路（用户点名的"2 可以显示"）。</p>
     *
     * <p>⚠ 只有<b>空手 + Shift</b>才诊断：Shift 右键手上拿着方块会变成"放方块"，
     * 拿着别的物品也是物品先出手（本工程 §4.8 记过这条交互次序）。</p>
     */
    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hitResult) {
        if (!level.isClientSide
                && player instanceof ServerPlayer serverPlayer
                && level.getBlockEntity(pos) instanceof FillingMachineBlockEntity be) {
            if (serverPlayer.isShiftKeyDown()) {
                diagnose(serverPlayer, be);
            } else {
                serverPlayer.openMenu(be);
            }
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    /**
     * 手上拿着流体容器右键 = <b>把容器里的流体倒进罐</b>（0.11 ZF80，与蒸馏塔操作器同一个操作）。
     *
     * <p>倒进哪个罐由 {@link FillingMachineBlockEntity#pourFrom} 决定（先接着同种流体倒，
     * 否则第一个空罐）；倒不进去也一定<b>说清楚是哪一种倒不进去</b>。</p>
     *
     * <p>手上不是容器 ⇒ 原样放行（回到 {@link #useWithoutItem} 开界面），行为不变。</p>
     */
    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
                                              Player player, InteractionHand hand, BlockHitResult hitResult) {
        if (!(stack.getItem() instanceof FluidContainerItem)) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        if (level.isClientSide) {
            return ItemInteractionResult.sidedSuccess(true);
        }
        if (!(level.getBlockEntity(pos) instanceof FillingMachineBlockEntity be)) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        FillingMachineBlockEntity.PourOutcome outcome = be.pourFrom(stack);
        switch (outcome.result()) {
            case NO_CONTAINER:
                return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
            case EMPTY:
                player.displayClientMessage(
                        Component.translatable("gui.potato_s_t.filling.pour.empty"), true);
                break;
            case NO_ROOM:
                player.displayClientMessage(
                        Component.translatable("gui.potato_s_t.filling.pour.noroom"), true);
                break;
            default:
                level.playSound(null, pos, SoundEvents.BUCKET_EMPTY, SoundSource.BLOCKS, 1.0F, 1.0F);
                player.displayClientMessage(Component.translatable("gui.potato_s_t.filling.pour.poured",
                        outcome.tank() + 1, outcome.fluid().getHoverName(), outcome.amount()), true);
                break;
        }
        return ItemInteractionResult.sidedSuccess(false);
    }

    /**
     * 逐槽诊断：第 i 个槽此刻是什么状态，一行一条念给玩家。
     *
     * <p>文案里的原因码全部来自 {@link FillingMachineBlockEntity#stateOf(int)}，
     * 与灌装逻辑逐条对齐（诊断说的话必须就是代码真正做的事）。</p>
     */
    private static void diagnose(ServerPlayer player, FillingMachineBlockEntity be) {
        for (int i = 0; i < FillingMachineBlockEntity.TANK_COUNT; i++) {
            int slot = i + 1;
            FluidStack fluid = be.fluidOf(i);
            Component line = switch (be.stateOf(i)) {
                case TANK_EMPTY -> Component.translatable(
                        "gui.potato_s_t.filling.diag.tank_empty", slot);
                case SLOT_EMPTY -> Component.translatable(
                        "gui.potato_s_t.filling.diag.slot_empty", slot);
                case FULL -> Component.translatable(
                        "gui.potato_s_t.filling.diag.full", slot);
                case NO_POWER -> Component.translatable(
                        "gui.potato_s_t.filling.diag.no_power", slot,
                        be.getEnergy(), FillingMachineBlockEntity.ENERGY_PER_TANK);
                case REJECTED -> Component.translatable(
                        "gui.potato_s_t.filling.diag.rejected", slot, fluid.getHoverName());
                case FILLING -> Component.translatable(
                        "gui.potato_s_t.filling.diag.filling", slot,
                        fluid.getHoverName(), fluid.getAmount(), be.spaceOf(i));
            };
            player.displayClientMessage(line, false);
        }
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    /**
     * 破坏 / 爆炸 / 被其他方块替换时，把 5 个容器槽里的东西掉出来（0.08 修复「吞物品」）。
     *
     * <p>必须在 {@code super.onRemove} <b>之前</b>取方块实体，否则它已经被移除了。</p>
     */
    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {
        if (!state.is(newState.getBlock()) && level.getBlockEntity(pos) instanceof FillingMachineBlockEntity be) {
            MachineDrops.dropInventory(level, pos, be.getInventory());
        }
        super.onRemove(state, level, pos, newState, movedByPiston);
    }

    @Override
    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        return List.of(new ItemStack(this));
    }
}