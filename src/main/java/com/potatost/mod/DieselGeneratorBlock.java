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
import net.minecraft.world.item.Item.TooltipContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUtils;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.TooltipFlag;
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
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.templates.FluidTank;

/**
 * 大型柴油发电机的<b>控制器</b>方块（0.11 ZF125）。
 *
 * <p>用户原话「以柴油发电机控制器为正方向 右键打开GUI … 可以用流体泵泵入柴油
 * 或用柴油桶/含有柴油的油桶右键添加柴油」⇒ 这个方块管三件事：</p>
 * <ol>
 *   <li><b>朝向</b>：{@code FACING} = 机器正面（放下时朝着玩家的那一面），
 *       机器朝 {@code FACING.getOpposite()} 铺 5 排、向上 2 层（见
 *       {@link DieselGeneratorStructure#offset}）；</li>
 *   <li><b>空手右键</b>：开界面。结构有缺口时<b>照样开</b>（用户原话只说"右键打开GUI"），
 *       但会先在聊天栏把<b>前 4 处</b>缺口报出来 —— 与分馏塔控制器"让你一眼看出哪不对"同一条做法；</li>
 *   <li><b>拿着柴油容器右键</b>：往罐里倒柴油（§{@link #pourFrom} 是纯逻辑，探针能直接调）。</li>
 * </ol>
 *
 * <p><b>为什么不做"不激活就不开界面"那道门</b>：合金炉有那道门是用户当年点名要的
 * （「类似于匠魂，他只是个控制器，需要先激活他」）；这一轮用户的原话是"右键打开GUI"，
 * 没有这句要求 ⇒ 按字面来，把"壳没搭完"这件事交给界面里的工作指示灯（19 号）和聊天栏。</p>
 */
public class DieselGeneratorBlock extends BaseEntityBlock {

    /** 机器正面朝向（= 控制器的正面）。 */
    public static final DirectionProperty FACING = HorizontalDirectionalBlock.FACING;

    /**
     * 手上拿着流体容器右键时，一次最多倒进多少 mB。
     *
     * <p>与油桶「一次舀一格 = 1000 mB」、分馏塔操作器 {@code POUR_PER_CLICK} 对称；
     * 罐里余量不足 1000 时能倒多少倒多少（允许倒半格）。
     * ⚠ 例外是<b>原版柴油桶</b>：一桶就是 1000，装不下就<b>一滴不倒</b>（不能倒半桶，
     * 否则剩下的 500 mB 会凭空消失）。</p>
     */
    public static final int POUR_PER_CLICK = 1000;

    public DieselGeneratorBlock(Properties properties) {
        super(properties);
        registerDefaultState(this.stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(DieselGeneratorBlock::new);
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
    public RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new DieselGeneratorBlockEntity(pos, state);
    }

    /** 双端 ticker（§4.26：只给服务端会让"以后加循环音效"这类客户端逻辑永远收不到 tick）。 */
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
                                                                 BlockEntityType<T> type) {
        return createTickerHelper(type, ModBlocks.DIESEL_GENERATOR_BE.get(),
                DieselGeneratorBlockEntity::tick);
    }

    /** 摆下控制器：让下一次 tick 立刻复查结构。 */
    @Override
    protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState,
                           boolean movedByPiston) {
        super.onPlace(state, level, pos, oldState, movedByPiston);
        markDirty(level, pos);
    }

    /**
     * 旁边方块一变就点名复查（摆完最后一格是<b>立刻</b>成型，不用等那半秒的心跳）。
     *
     * <p>⚠ 这里<b>只置一个标志</b>，绝不在邻居更新的栈里直接 setBlock —— 成型时要换接线口，
     * 换方块又会触发邻居更新，在栈里直接干就是自己套自己（合金炉当年那道
     * {@code isDisassembling} 锁就是为这个加的；这里用"下一 tick 再办"躲开它）。</p>
     */
    @Override
    protected void neighborChanged(BlockState state, Level level, BlockPos pos, Block neighborBlock,
                                   BlockPos neighborPos, boolean movedByPiston) {
        super.neighborChanged(state, level, pos, neighborBlock, neighborPos, movedByPiston);
        markDirty(level, pos);
    }

    private static void markDirty(Level level, BlockPos pos) {
        if (!level.isClientSide && level.getBlockEntity(pos) instanceof DieselGeneratorBlockEntity be) {
            be.markStructureDirty();
        }
    }

    // ================= 右键：开界面 / 报缺口 =================

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hit) {
        if (level.isClientSide) {
            return InteractionResult.SUCCESS;
        }
        if (!(level.getBlockEntity(pos) instanceof DieselGeneratorBlockEntity be)) {
            return InteractionResult.PASS;
        }
        reportHoles(level, pos, player);
        if (player instanceof ServerPlayer serverPlayer) {
            serverPlayer.openMenu(be);
        }
        return InteractionResult.CONSUME;
    }

    /**
     * 把<b>前 4 处</b>结构缺口打在聊天栏（控制器本体与接线口右键共用）。
     *
     * <p>结构完整时一句都不打。缺口的文案格式照合金炉那条：第几层/第几排/第几列 +
     * <b>该放什么</b> + <b>现在是什么</b> + 世界坐标 —— 只报"这里缺一块"没法排查（ZF53 那一课）。</p>
     */
    public static void reportHoles(Level level, BlockPos controller, Player player) {
        if (level.isClientSide
                || !(level.getBlockEntity(controller) instanceof DieselGeneratorBlockEntity be)) {
            return;
        }
        for (DieselGeneratorStructure.Problem hole : be.findHoles(4)) {
            BlockPos bad = DieselGeneratorStructure.offset(controller, be.facing(), hole.y(), hole.j(), hole.i());
            DieselGeneratorStructure.Kind kind = DieselGeneratorStructure.kindAt(hole.y(), hole.j(), hole.i());
            player.displayClientMessage(Component.translatable("gui.potato_s_t.diesel_generator.invalid",
                    hole.y() + 1, hole.j() + 1, hole.i() + 1,
                    DieselGeneratorStructure.blockFor(kind).getName(),
                    hole.found().getName(),
                    bad.getX(), bad.getY(), bad.getZ()), false);
        }
    }

    // ================= 右键：倒柴油 =================

    /** 倒流体的结果（**文案由 {@link #useItemOn} 负责**，纯逻辑这一段可以直接被探针调用）。 */
    public enum PourResult {
        /** 手上不是柴油桶也不是流体容器 ⇒ 放行走原逻辑 */
        NO_CONTAINER,
        /** 容器是空的 */
        EMPTY,
        /** 倒不进去：里面装的不是柴油 */
        REJECTED,
        /** 倒不进去：罐满了（柴油桶还要 1000 mB 一次，装不下就一滴不倒） */
        FULL,
        /** 倒进去了 */
        POURED
    }

    /** 这个物品能不能拿来倒（柴油桶 / 油桶 / 高压气罐）。 */
    public static boolean isPourable(ItemStack stack) {
        return !stack.isEmpty()
                && (stack.is(ModItems.DIESEL_BUCKET.get()) || stack.getItem() instanceof FluidContainerItem);
    }

    /**
     * 把手上的柴油倒进罐里 —— <b>纯逻辑</b>（不碰聊天栏、不放音效、不见了空桶由调用方补）。
     *
     * <p>两条路：① <b>原版柴油桶</b>（{@code BucketItem}，整桶 1000 mB，装不下就不倒）；
     * ② {@link FluidContainerItem}（油桶 / 高压气罐）—— 先问罐子能收多少再取多少，
     * 全程用真实数量，不会出现"取多了塞不回去"。</p>
     */
    public static PourResult pourFrom(ItemStack stack, Level level, BlockPos pos) {
        if (!(level.getBlockEntity(pos) instanceof DieselGeneratorBlockEntity be)) {
            return PourResult.NO_CONTAINER;
        }
        FluidTank tank = be.getTank();

        // ① 柴油桶：一桶 1000 mB，装不下就一滴不倒（倒半桶会让剩下的凭空消失）
        if (stack.is(ModItems.DIESEL_BUCKET.get())) {
            FluidStack one = new FluidStack(ModFluids.DIESEL.get(), POUR_PER_CLICK);
            if (tank.fill(one, IFluidHandler.FluidAction.SIMULATE) < POUR_PER_CLICK) {
                return PourResult.FULL;
            }
            tank.fill(one, IFluidHandler.FluidAction.EXECUTE);
            be.setChanged();
            return PourResult.POURED;
        }

        // ② 油桶 / 高压气罐：只认柴油
        if (stack.getItem() instanceof FluidContainerItem container) {
            FluidStack held = container.contents(stack);
            if (held.isEmpty()) {
                return PourResult.EMPTY;
            }
            if (!DieselGeneratorBlockEntity.isDiesel(held)) {
                return PourResult.REJECTED;
            }
            int want = Math.min(POUR_PER_CLICK, held.getAmount());
            int accepted = tank.fill(held.copyWithAmount(want), IFluidHandler.FluidAction.SIMULATE);
            if (accepted <= 0) {
                return PourResult.FULL;
            }
            FluidStack drained = container.drain(stack, accepted);
            if (drained.isEmpty()) {
                return PourResult.FULL;
            }
            tank.fill(drained, IFluidHandler.FluidAction.EXECUTE);
            be.setChanged();
            return PourResult.POURED;
        }
        return PourResult.NO_CONTAINER;
    }

    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
                                              Player player, InteractionHand hand, BlockHitResult hit) {
        if (!isPourable(stack)) {
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
                        Component.translatable("gui.potato_s_t.diesel_generator.pour.empty"), true);
                break;
            case REJECTED:
                player.displayClientMessage(Component.translatable(
                        "gui.potato_s_t.diesel_generator.pour.rejected",
                        ((FluidContainerItem) stack.getItem()).contents(stack).getHoverName()), true);
                break;
            case FULL:
                player.displayClientMessage(
                        Component.translatable("gui.potato_s_t.diesel_generator.pour.full"), true);
                break;
            default:
                // 柴油桶：整桶倒空 ⇒ 还玩家一个空铁桶（空桶由原版工具类处理堆叠/创造模式）
                if (stack.is(ModItems.DIESEL_BUCKET.get())) {
                    player.setItemInHand(hand,
                            ItemUtils.createFilledResult(stack, player, new ItemStack(Items.BUCKET)));
                }
                level.playSound(null, pos, SoundEvents.BUCKET_EMPTY, SoundSource.BLOCKS, 1.0F, 1.0F);
                break;
        }
        return ItemInteractionResult.sidedSuccess(false);
    }

    // ================= 破坏 =================

    /**
     * 控制器被挖掉：把头上那一格接线口<b>换回接线块</b>。
     *
     * <p>不做这件事的话，接线口会永远留在世界上（它挖出来掉的是接线块，玩家不会亏，
     * 但地图上就多了一个"看着像接线块、其实不是"的方块）。换回接线块 = 玩家当初摆的就是它。</p>
     */
    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {
        if (!state.is(newState.getBlock()) && !level.isClientSide) {
            BlockPos port = DieselGeneratorStructure.portPos(pos);
            if (DieselGeneratorStructure.isPort(level.getBlockState(port))) {
                level.setBlock(port, ModBlocks.WIRING_BLOCK.get().defaultBlockState(), Block.UPDATE_ALL);
            }
        }
        super.onRemove(state, level, pos, newState, movedByPiston);
    }

    /** 挖控制器掉控制器本身（这台机器没有物品槽，罐里的柴油和别的机器一样会丢）。 */
    @Override
    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        return List.of(new ItemStack(this));
    }

    /** Shift 悬停说明（与其它机器一致的做法）。 */
    public static void appendTooltip(ItemStack stack, TooltipContext context,
                                     List<Component> tooltip, TooltipFlag flag) {
        if (flag.hasShiftDown() || flag.isAdvanced()) {
            tooltip.add(Component.translatable("tooltip.potato_s_t.diesel_generator_controller"));
        } else {
            tooltip.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
        }
    }
}
