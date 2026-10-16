package com.potatost.mod;

import java.util.List;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.DirectionProperty;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.phys.BlockHitResult;

/**
 * 流体转化器方块（0.13 ZF166）：见 {@link FluidConverterBlockEntity} 的类注释。
 *
 * <p>交互：空手右键 = 开界面；<b>空手潜行右键 = 逐条诊断</b>（为什么没在转）——与灌装机同一个手势
 * （用户点过名的"它得告诉我缺啥"）。</p>
 */
public class FluidConverterBlock extends BaseEntityBlock {

    public static final DirectionProperty FACING = HorizontalDirectionalBlock.FACING;

    public FluidConverterBlock(Properties properties) {
        super(properties);
        this.registerDefaultState(this.stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(FluidConverterBlock::new);
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return this.defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new FluidConverterBlockEntity(pos, state);
    }

    /** 只在服务端 tick（这台机器没有动画/音效要驱动）。 */
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
                                                                  BlockEntityType<T> type) {
        if (level.isClientSide) {
            return null;
        }
        return createTickerHelper(type, ModBlocks.FLUID_CONVERTER_BE.get(), FluidConverterBlockEntity::tick);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hitResult) {
        if (!level.isClientSide
                && player instanceof ServerPlayer serverPlayer
                && level.getBlockEntity(pos) instanceof FluidConverterBlockEntity be) {
            if (serverPlayer.isShiftKeyDown()) {
                diagnose(serverPlayer, be);
            } else {
                serverPlayer.openMenu(be);
            }
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    /**
     * 手拿容器右键 = 倒流体（0.13 ZF166）：<b>普通右键倒进输出罐（= 设样板），潜行右键倒进输入罐（= 喂料）</b>。
     *
     * <p>倒进哪个罐由 {@code toOutput} 说了算；两条路都只按"<b>真的进了罐的那部分</b>"结算，
     * 倒不进去的仍然留在容器里（与灌装机同一条「绝不凭空吞流体」的规矩）。
     * 样板也可以由<b>管道</b>给（见 {@link FluidConverterBlockEntity#getFluidHandler()}），
     * 手倒只是给玩家省事的那条路。倒完就地报一遍状态（复用机器自己那套状态文案，不另开语言键）。</p>
     */
    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
                                              Player player, InteractionHand hand, BlockHitResult hitResult) {
        if (level.isClientSide || stack.isEmpty()) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        if (!(level.getBlockEntity(pos) instanceof FluidConverterBlockEntity be)) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        boolean toOutput = player.isShiftKeyDown();
        // ① 容器里有流体 ⇒ 倒进罐（普通 = 输出罐设样板，潜行 = 输入罐喂料）
        FluidConverterBlockEntity.Pour pour =
                be.pourFrom(stack, toOutput, FluidConverterBlockEntity.POUR_PER_CLICK);
        // ② 倒不进去（手里是空容器 / 目标罐里是**另一种**流体收不下）⇒ 反过来试：从罐装进容器。
        //    0.13 ZF168 加：这一条正是"输出罐改不了样板"的正解 —— 空桶右键把旧样板装走，
        //    罐空了就能倒新的进去（FluidTank 对异种流体一律拒收，所以必须先腾空）。
        if (pour.moved() <= 0) {
            pour = be.fillContainerFrom(stack, toOutput, FluidConverterBlockEntity.POUR_PER_CLICK);
        }
        if (pour.moved() <= 0) {
            // 手里拿着**有流体**的容器、而目标罐里是**另一种**流体 ⇒ 明说怎么换样板
            if (player instanceof ServerPlayer sp && be.targetBlocked(stack, toOutput)) {
                sp.displayClientMessage(Component.translatable("block.potato_s_t.fluid_converter")
                        .append(Component.literal(" "))
                        .append(Component.translatable(
                                "gui.potato_s_t.fluid_converter.pour.occupied",
                                toOutput ? be.getOutputTank().getFluid().getHoverName()
                                        : be.getInputTank().getFluid().getHoverName())), false);
            }
            // ⚠ 手里是流体容器（空桶 / 满桶 / 我们的气罐油桶 / 别人的罐）就**必须吃下这次交互**：
            //   返回 PASS 会让原版接着跑 `BucketItem.useOn` ⇒ **把桶里的流体倒进世界**（凭空丢流体）。
            //   用户实测原话：「shift+右键会把流体倒出来 而不是倒进版样」—— 0.13 ZF170 补的就是这一行。
            return FluidConverterBlockEntity.isFluidContainer(stack)
                    ? ItemInteractionResult.sidedSuccess(false)
                    : ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        if (pour.container() != stack) {
            player.setItemInHand(hand, pour.container());
        }
        if (player instanceof ServerPlayer serverPlayer) {
            diagnose(serverPlayer, be);
        }
        return ItemInteractionResult.sidedSuccess(false);
    }

    /**
     * 逐条诊断（照灌装机 {@code diagnose} 的写法）：第一句 = 这台机器此刻为什么转 / 不转，
     * 后面两句 = 两个罐里现在各是什么、多少。
     *
     * <p>文案与界面那一行<b>共用</b> {@link FluidConverterBlockEntity#statusLine}（§4.51：界面说的
     * 必须就是代码真正在做的那一条；lang 里那几句自带 {@code [流体转化器]} 前缀，这里不再叠机器名）。</p>
     */
    private static void diagnose(ServerPlayer player, FluidConverterBlockEntity be) {
        Component line = FluidConverterBlockEntity.statusLine(be.stateCode(),
                be.getInputTank().getFluid(), be.getOutputTank().getFluid(), be.getEnergy());
        player.displayClientMessage(line, false);
        player.displayClientMessage(FluidConverterBlockEntity.tankLine(
                FluidConverterBlockEntity.LANG_TANK_INPUT, be.getInputTank().getFluid()), false);
        player.displayClientMessage(FluidConverterBlockEntity.tankLine(
                FluidConverterBlockEntity.LANG_TANK_OUTPUT, be.getOutputTank().getFluid()), false);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    /**
     * 破坏时把"物品栏"掉出来 —— 本机器**一个物品槽都没有**（{@code SLOT_COUNT = 0}），所以这一行
     * 实际上什么都不掉；它在这里是因为本工程有一条**文本级**判据（Audit B）：
     * 带物品栏的方块实体必须在 {@code onRemove} 里显式调 {@code MachineDrops.dropInventory}。
     * 两个罐里的**流体**不掉（流体不是物品，掉出来等于凭空造桶）。
     */
    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {
        if (!state.is(newState.getBlock()) && level.getBlockEntity(pos) instanceof FluidConverterBlockEntity be) {
            MachineDrops.dropInventory(level, pos, be.getInventory());
        }
        super.onRemove(state, level, pos, newState, movedByPiston);
    }

    @Override
    public List<net.minecraft.world.item.ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        return List.of(new net.minecraft.world.item.ItemStack(this));
    }
}
