package com.potatost.mod;

import java.util.List;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Item.TooltipContext;
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
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.DirectionProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.item.TooltipFlag;

/**
 * 合金冶炼炉的控制器方块（0.10 ZF49）。
 *
 * <p>用户图纸里这一格写的是【标靶】—— 用户答复「新加一个控制器方块」，所以这一格换成它。
 * 右键它成型/开界面；手持扳手 Shift 右键拆解（与电力高炉同一套动作）。
 *
 * <p>方块的 {@code FACING} = <b>机器正面朝向</b>（玩家放下去时朝着玩家的那一面），
 * 结构从这一格往 {@code FACING.getOpposite()} 方向铺开（见 {@link AlloySmelterStructure#offset}）。</p>
 */
public class AlloySmelterBlock extends BaseEntityBlock {

    public static final DirectionProperty FACING = HorizontalDirectionalBlock.FACING;

    /**
     * <b>成型状态（0.10 ZF56）—— 模型跟着它走</b>：
     * {@code false} = 主控本体那个 1×1×1 小方块（和物品栏里一模一样）；
     * {@code true} = <b>整台 4×5×4 合金炉</b>（OBJ 长方体，从控制器这一格画出去）。
     *
     * <p>用户原话：「<b>不是主控变成4x5x4是合金炉！合金炉成型后模型！</b>」</p>
     *
     * <p>为什么要有这个属性：ZF54 把 OBJ 直接挂在 {@code facing} 上，于是
     * <b>一放下控制器就是个 4×5×4 大盒子</b>（还没成型也是）。那是错的——
     * 大盒子是"成型之后的合金炉"，不是主控的本体。所以拆成两个变体：
     * {@code formed=false} 用 {@code block/alloy_smelter}（就是物品栏那个 cube_all），
     * {@code formed=true,facing=*} 才用那四份 OBJ。</p>
     */
    public static final BooleanProperty FORMED = BooleanProperty.create("formed");

    public AlloySmelterBlock(Properties properties) {
        super(properties);
        registerDefaultState(this.stateDefinition.any()
                .setValue(FACING, Direction.NORTH)
                .setValue(FORMED, false));
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(AlloySmelterBlock::new);
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING, FORMED);
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
        return new AlloySmelterBlockEntity(pos, state);
    }

    /**
     * 双端 ticker。
     *
     * <p>（§4.26 的教训：只给服务端 ticker 会让"以后加循环音效"这类客户端逻辑永远收不到 tick。）</p>
     */
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
                                                                 BlockEntityType<T> type) {
        return createTickerHelper(type, ModBlocks.ALLOY_SMELTER_BE.get(), AlloySmelterBlockEntity::tick);
    }

    /**
     * 摆下控制器时顺手试一次自动成型（ZF55）。
     *
     * <p>三个调用点：控制器被摆下（{@link #onPlace}）、控制器旁边有方块变动
     * （{@link #neighborChanged}）、以及没激活的控制器每半秒一次的心跳
     * （{@link AlloySmelterBlockEntity#tick}）—— 最后那个负责"最后一块摆在老远、
     * 控制器挨不着"的情况。</p>
     */
    @Override
    protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState,
                           boolean movedByPiston) {
        super.onPlace(state, level, pos, oldState, movedByPiston);
        if (!level.isClientSide) {
            tryAutoForm(level, pos);
        }
    }

    /** 旁边方块一变就试一次（玩家把最后一块补在控制器边上时是**立刻**成型的）。 */
    @Override
    protected void neighborChanged(BlockState state, Level level, BlockPos pos, Block neighborBlock,
                                   BlockPos neighborPos, boolean movedByPiston) {
        super.neighborChanged(state, level, pos, neighborBlock, neighborPos, movedByPiston);
        if (!level.isClientSide) {
            tryAutoForm(level, pos);
        }
    }

    /**
     * 未激活时试一次自动成型（ZF55「直接激活」）。
     *
     * <p>外壳围满 + 至少一个接线块 ⇒ 直接成型，<b>不需要玩家右键</b>。
     * 成型是纯服务端动作，客户端那一半靠方块实体同步。</p>
     *
     * <p>⚠ 必须挡住两个重入来源：已经成型（不必再验）、正在拆解/成型
     * （{@code isDisassembling()} —— 换方块会触发邻居更新，否则会自己套自己）。</p>
     */
    public static void tryAutoForm(Level level, BlockPos pos) {
        if (!(level.getBlockEntity(pos) instanceof AlloySmelterBlockEntity be)
                || be.isFormed() || be.isDisassembling()) {
            return;
        }
        if (AlloySmelterStructure.shellComplete(level, pos, be.facing())) {
            be.form();
        }
    }

    /**
     * 右键控制器时该做什么（0.10 ZF51 抽出来的纯函数 —— 探针能脱离 Player 验这条规则）。
     *
     * <p>用户原话：「合金炉主控需要激活多方块结构才可以使用，而不是直接为合金冶炼炉，
     * 类似于匠魂，他只是个控制器，需要先激活他」⇒ 所以：</p>
     * <ul>
     *   <li><b>没激活</b>：右键（带不带 Shift 都算）= 试着激活；激活失败就报"哪一格不对"，
     *       <b>绝不开界面</b>（匠魂那种控制器）；</li>
     *   <li><b>已激活</b>：右键 = 开界面；Shift + 右键 = 在聊天栏报一句状态。</li>
     * </ul>
     *
     * <p><b>ZF55 补充</b>：判定放宽（只要求"是机器方块"；顶面的两列与内部 12 格不查）；
     * <b>ZF59 起顶面图纸画了方块的那 10 格也进判定</b>（用户：「等第四层摆完再成型」）⇒
     * 图纸 4 层全摆完才会自动成型，见 {@link #tryAutoForm}。
     * 这是用户后来的要求：「像沉浸改成那样的 直接激活的不行吗」。</p>
     */
    public enum Action { ACTIVATE, OPEN_GUI, STATUS }

    public static Action decide(boolean formed, boolean shiftDown) {
        if (!formed) {
            return Action.ACTIVATE;
        }
        return shiftDown ? Action.STATUS : Action.OPEN_GUI;
    }

    /** 空手右键 = 激活（未激活时）/ 开界面（已激活时）；Shift 右键 = 激活 / 报状态。 */
    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hit) {
        if (level.isClientSide) {
            return InteractionResult.SUCCESS;
        }
        if (!(level.getBlockEntity(pos) instanceof AlloySmelterBlockEntity be)) {
            return InteractionResult.PASS;
        }
        Action action = decide(be.isFormed(), player.isShiftKeyDown());
        if (action == Action.ACTIVATE) {
            // ZF55：判定只要求"是机器方块"；ZF59 起顶面画了方块的那 10 格也要查。一次列**前 4 处**缺口
            AlloySmelterStructure.Report report =
                    AlloySmelterStructure.inspect(level, be.getBlockPos(), be.facing(), 4);
            for (AlloySmelterStructure.Problem hole : report.holes()) {
                BlockPos bad = AlloySmelterStructure.offset(be.getBlockPos(), be.facing(),
                        hole.y(), hole.j(), hole.i());
                player.displayClientMessage(Component.translatable("gui.potato_s_t.alloy_smelter.invalid",
                        hole.y() + 1, hole.j() + 1, hole.i() + 1,
                        hole.found().getName(),
                        bad.getX(), bad.getY(), bad.getZ()), false);
            }
            if (!report.holes().isEmpty()) {
                return InteractionResult.CONSUME;
            }
            if (report.wiring() == 0) {
                // 外壳围好了但一个接线块都没有 ⇒ 这台机器没地方进电
                player.displayClientMessage(
                        Component.translatable("gui.potato_s_t.alloy_smelter.no_port"), false);
                return InteractionResult.CONSUME;
            }
            be.form();
            player.displayClientMessage(Component.translatable("gui.potato_s_t.alloy_smelter.formed"), true);
            return InteractionResult.CONSUME;
        }
        if (action == Action.STATUS) {
            player.displayClientMessage(Component.translatable("gui.potato_s_t.alloy_smelter.status",
                    be.getEnergyStored(), AlloySmelterBlockEntity.MAX_ENERGY), true);
            return InteractionResult.CONSUME;
        }
        player.openMenu(be, pos);
        return InteractionResult.CONSUME;
    }

    /** 手持扳手 Shift 右键拆解（复用电力高炉那把扳手）。 */
    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
                                              Player player, net.minecraft.world.InteractionHand hand,
                                              BlockHitResult hit) {
        if (!stack.is(ModItems.WRENCH.get()) || !player.isShiftKeyDown()) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        if (!level.isClientSide && level.getBlockEntity(pos) instanceof AlloySmelterBlockEntity be) {
            be.dropContents();
            be.disassemble();
            level.setBlock(pos, net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
            Block.popResource(level, pos, new ItemStack(ModBlocks.ALLOY_SMELTER_ITEM.get()));
        }
        return ItemInteractionResult.sidedSuccess(level.isClientSide);
    }

    /**
     * 被挖掉/被拆掉时：掉出 GUI 内容物。
     *
     * <p>Audit 的 B 项要求"带物品栏的方块实体，其方块必须显式调 {@code MachineDrops}"，
     * 所以这里必须出现 {@code MachineDrops.dropInventory} 这行字（文本级检查）。
     * 机器本体由战利品表掉（{@code loot_table/blocks/alloy_smelter.json}）。</p>
     */
    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {
        if (!state.is(newState.getBlock())
                && level.getBlockEntity(pos) instanceof AlloySmelterBlockEntity be) {
            if (!be.isDisassembling()) {
                MachineDrops.dropInventory(level, pos, be.getInventory());
                be.disassemble();
            }
        }
        super.onRemove(state, level, pos, newState, movedByPiston);
    }

    /** Shift 悬停说明（与其它机器一致的做法）。 */
    public static void appendTooltip(ItemStack stack, TooltipContext context,
                                     List<Component> tooltip, TooltipFlag flag) {
        if (flag.hasShiftDown() || flag.isAdvanced()) {
            tooltip.add(Component.translatable("tooltip.potato_s_t.alloy_smelter"));
        } else {
            tooltip.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
        }
    }
}
