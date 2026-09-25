package com.potatost.mod;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
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
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

public class TerminalBlock extends BaseEntityBlock {

    public static final DirectionProperty FACING = BlockStateProperties.FACING;

    /** 最大直线连接距离（格） */
    public static final int MAX_CONNECTION_DISTANCE = 16;

    /** 每个玩家用铜线轴选中的第一个端子 */
    private static final Map<UUID, BlockPos> PENDING_CONNECTIONS = new HashMap<>();
    /** 每个玩家用紫色动力线缆选中的第一个端子 */
    private static final Map<UUID, BlockPos> PENDING_POWER_CONNECTIONS = new HashMap<>();

    /** 接线端子：截面 4×4，长度 10，紧贴支撑方块 */
    private static final Map<Direction, VoxelShape> SHAPES = Map.of(
            Direction.NORTH, Block.box(6, 6, 6, 10, 10, 16),
            Direction.SOUTH, Block.box(6, 6, 0, 10, 10, 10),
            Direction.EAST,  Block.box(0, 6, 6, 10, 10, 10),
            Direction.WEST,  Block.box(6, 6, 6, 16, 10, 10),
            Direction.UP,    Block.box(6, 0, 6, 10, 10, 10),
            Direction.DOWN,  Block.box(6, 6, 6, 10, 16, 10));

    public TerminalBlock(Properties properties) {
        super(properties);
        this.registerDefaultState(this.stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(TerminalBlock::new);
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        BlockState state = this.defaultBlockState().setValue(FACING, context.getClickedFace());
        if (state.canSurvive(context.getLevel(), context.getClickedPos())) {
            return state;
        }
        for (Direction direction : context.getNearestLookingDirections()) {
            state = this.defaultBlockState().setValue(FACING, direction.getOpposite());
            if (state.canSurvive(context.getLevel(), context.getClickedPos())) {
                return state;
            }
        }
        return null;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPES.get(state.getValue(FACING));
    }

    @Override
    protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        Direction supportSide = state.getValue(FACING).getOpposite();
        return canSupportCenter(level, pos.relative(supportSide), supportSide);
    }

    @Override
    protected void neighborChanged(BlockState state, Level level, BlockPos pos, Block neighborBlock,
                                   BlockPos neighborPos, boolean movedByPiston) {
        if (!state.canSurvive(level, pos)) {
            level.destroyBlock(pos, true);
        }
    }

    /** 空手：潜行右键切换 输入/输出 模式 */
    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hitResult) {
        if (!player.isShiftKeyDown()) {
            return InteractionResult.PASS;
        }
        if (!level.isClientSide) {
            toggleMode(level, pos, player);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
                                              Player player, InteractionHand hand, BlockHitResult hitResult) {
        // 紫色动力线缆：建立动力连接（与铜线轴逻辑一致，独立连接集合）
        if (stack.is(ModItems.POWER_CABLE_SPOOL.get())) {
            if (!level.isClientSide && level instanceof ServerLevel serverLevel) {
                if (handlePowerConnectionTool(level, pos, player)) {
                    stack.hurtAndBreak(1, serverLevel, player, item -> giveEmptySpoolBack(player));
                }
            }
            return ItemInteractionResult.sidedSuccess(level.isClientSide);
        }
        // 铜线轴右键 = 连接 / 取消连接（每次成功连接消耗 1 点耐久）
        if (stack.is(ModItems.COPPER_WIRE_SPOOL.get())) {
            if (!level.isClientSide && level instanceof ServerLevel serverLevel) {
                if (handleConnectionTool(level, pos, player)) {
                    stack.hurtAndBreak(1, serverLevel, player, item -> giveEmptySpoolBack(player));
                }
            }
            return ItemInteractionResult.sidedSuccess(level.isClientSide);
        }
        // 潜行右键 = 切换模式
        if (player.isShiftKeyDown()) {
            if (!level.isClientSide) {
                toggleMode(level, pos, player);
            }
            return ItemInteractionResult.sidedSuccess(level.isClientSide);
        }
        return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
    }

    /** @return true 表示这次右键成功建立了一条新连接（用于扣耐久） */
    private boolean handleConnectionTool(Level level, BlockPos pos, Player player) {
        UUID playerId = player.getUUID();
        BlockPos previous = PENDING_CONNECTIONS.remove(playerId);

        if (previous == null) {
            PENDING_CONNECTIONS.put(playerId, pos);
            player.displayClientMessage(Component.translatable("message.potato_s_t.terminal_selected"), true);
            return false;
        }

        if (previous.equals(pos)) {
            player.displayClientMessage(Component.translatable("message.potato_s_t.terminal_cancelled"), true);
            return false;
        }

        double distance = pos.getCenter().distanceTo(previous.getCenter());
        if (distance > MAX_CONNECTION_DISTANCE) {
            player.displayClientMessage(
                    Component.translatable("message.potato_s_t.terminal_too_far", MAX_CONNECTION_DISTANCE), true);
            return false;
        }

        if (level.getBlockEntity(pos) instanceof TerminalBlockEntity self
                && level.getBlockEntity(previous) instanceof TerminalBlockEntity other) {
            if (self.addConnection(previous)) {
                other.addConnection(pos);
                player.displayClientMessage(Component.translatable("message.potato_s_t.terminal_connected"), true);
                return true;
            }
            player.displayClientMessage(Component.translatable("message.potato_s_t.terminal_already_connected"), true);
            return false;
        }
        player.displayClientMessage(Component.translatable("message.potato_s_t.terminal_missing"), true);
        return false;
    }

    /** 紫色动力线缆连接处理器，@return true 表示这次成功建立新动力连接 */
    private boolean handlePowerConnectionTool(Level level, BlockPos pos, Player player) {
        UUID playerId = player.getUUID();
        BlockPos previous = PENDING_POWER_CONNECTIONS.remove(playerId);
        if (previous == null) {
            PENDING_POWER_CONNECTIONS.put(playerId, pos);
            player.displayClientMessage(Component.translatable("message.potato_s_t.terminal_selected"), true);
            return false;
        }
        if (previous.equals(pos)) {
            player.displayClientMessage(Component.translatable("message.potato_s_t.terminal_cancelled"), true);
            return false;
        }
        double distance = pos.getCenter().distanceTo(previous.getCenter());
        if (distance > MAX_CONNECTION_DISTANCE) {
            player.displayClientMessage(
                    Component.translatable("message.potato_s_t.terminal_too_far", MAX_CONNECTION_DISTANCE), true);
            return false;
        }
        if (level.getBlockEntity(pos) instanceof TerminalBlockEntity self
                && level.getBlockEntity(previous) instanceof TerminalBlockEntity other) {
            if (self.addPowerConnection(previous)) {
                other.addPowerConnection(pos);
                player.displayClientMessage(Component.translatable("message.potato_s_t.terminal_connected"), true);
                return true;
            }
            player.displayClientMessage(Component.translatable("message.potato_s_t.terminal_already_connected"), true);
            return false;
        }
        player.displayClientMessage(Component.translatable("message.potato_s_t.terminal_missing"), true);
        return false;
    }

    private void toggleMode(Level level, BlockPos pos, Player player) {
        if (level.getBlockEntity(pos) instanceof TerminalBlockEntity terminal) {
            terminal.cycleMode();
            player.displayClientMessage(
                    Component.translatable("message.potato_s_t.terminal_mode",
                            Component.translatable("mode.potato_s_t." + terminal.getModeName())),
                    true);
        }
    }

    /** 铜线轴耐久耗尽损坏时，返还一个空线轴（背包满则掉在地上） */
    private void giveEmptySpoolBack(Player player) {
        ItemStack remainder = new ItemStack(ModItems.EMPTY_SPOOL.get());
        if (!player.addItem(remainder)) {
            player.drop(remainder, false);
        }
    }

    /** 直接掉落自身，不用额外写掉落表 */
    @Override
    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        return List.of(new ItemStack(this));
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new TerminalBlockEntity(pos, state);
    }

    /** 服务端每 tick 驱动能量传输 */
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        if (level.isClientSide) {
            return null;
        }
        return createTickerHelper(type, ModBlocks.TERMINAL_BE.get(), TerminalBlockEntity::tick);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }
}