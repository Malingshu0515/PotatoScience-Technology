package com.potatost.mod;

import java.util.EnumMap;
import java.util.List;
import java.util.Map;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import net.neoforged.neoforge.capabilities.Capabilities;

/**
 * 流体管道：纯导体，无方块实体、无存储、不主动搬运（要泵才动）。
 *   六向连接属性（序列化名 north/east/south/west/up/down）；四种情况会连通：
 *     1) 相邻是管道 → 连；
 *     2) 相邻是泵、且接触面在泵的前/后两面 → 连（其余面一律不连，按规格）；
 *     3) 相邻方块暴露流体能力（电解器、水罐、其它模组的流体容器）→ 连；
 *     4) ★ 相邻方块是"源流体"（水/岩浆源方块）→ 连（管网吸水口；流动的液体不算）。
 *   形状 = 中心 8×8×8 芯 + 各连通方向 8×8 截面的手臂（碰撞箱 8×8 像素），
 *   "检测到相邻目标就转向它"由此天然成立（L 形/十字/T 形）。
 */
public class FluidPipeBlock extends Block {

    /** 六向连接属性（复用原版的 BooleanProperty 对象，序列化名与惯例一致） */
    public static final Map<Direction, BooleanProperty> PROPERTY_BY_DIRECTION = createPropertyMap();

    private static Map<Direction, BooleanProperty> createPropertyMap() {
        Map<Direction, BooleanProperty> map = new EnumMap<>(Direction.class);
        map.put(Direction.NORTH, BlockStateProperties.NORTH);
        map.put(Direction.SOUTH, BlockStateProperties.SOUTH);
        map.put(Direction.WEST, BlockStateProperties.WEST);
        map.put(Direction.EAST, BlockStateProperties.EAST);
        map.put(Direction.UP, BlockStateProperties.UP);
        map.put(Direction.DOWN, BlockStateProperties.DOWN);
        return map;
    }

    private static final VoxelShape CORE = Block.box(4.0D, 4.0D, 4.0D, 12.0D, 12.0D, 12.0D);
    private static final Map<Direction, VoxelShape> ARM = createArms();

    private static Map<Direction, VoxelShape> createArms() {
        Map<Direction, VoxelShape> map = new EnumMap<>(Direction.class);
        map.put(Direction.NORTH, Block.box(4.0D, 4.0D, 0.0D, 12.0D, 12.0D, 4.0D));
        map.put(Direction.SOUTH, Block.box(4.0D, 4.0D, 12.0D, 12.0D, 12.0D, 16.0D));
        map.put(Direction.WEST, Block.box(0.0D, 4.0D, 4.0D, 4.0D, 12.0D, 12.0D));
        map.put(Direction.EAST, Block.box(12.0D, 4.0D, 4.0D, 16.0D, 12.0D, 12.0D));
        map.put(Direction.UP, Block.box(4.0D, 12.0D, 4.0D, 12.0D, 16.0D, 12.0D));
        map.put(Direction.DOWN, Block.box(4.0D, 0.0D, 4.0D, 12.0D, 4.0D, 12.0D));
        return map;
    }

    /** 64 种连接组合的形状缓存（索引 = 六向布尔位） */
    private static final VoxelShape[] SHAPE_CACHE = new VoxelShape[64];

    public FluidPipeBlock(Properties properties) {
        super(properties);
        BlockState state = this.stateDefinition.any();
        for (BooleanProperty property : PROPERTY_BY_DIRECTION.values()) {
            state = state.setValue(property, Boolean.FALSE);
        }
        this.registerDefaultState(state);
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        for (BooleanProperty property : PROPERTY_BY_DIRECTION.values()) {
            builder.add(property);
        }
    }

    /**
     * 连通判定：
     *   相邻管道 → 恒连通；
     *   相邻泵   → 只在前/后两面连通（规格如此，其余面即使有流体能力也不连）；
     *   其余方块 → 该面暴露流体能力就连通（电解器/水罐/其它模组容器）；
     *              ★ 或该方块是源流体（水/岩浆源）也连通——作为管网吸水口。
     * 注："罐里有没有液体"无关——空罐也暴露能力，所以也连。
     */
    private static boolean connectsTo(LevelReader level, BlockPos pos, Direction side) {
        BlockPos neighborPos = pos.relative(side);
        BlockState neighborState = level.getBlockState(neighborPos);
        if (neighborState.getBlock() instanceof FluidPipeBlock) {
            return true;
        }
        if (neighborState.getBlock() instanceof FluidPumpBlock) {
            Direction pumpFront = neighborState.getValue(FluidPumpBlock.FACING);
            Direction faceTowardThisPipe = side.getOpposite();   // 泵朝向本管道的那一面
            return faceTowardThisPipe == pumpFront || faceTowardThisPipe == pumpFront.getOpposite();
        }
        // ① 相邻方块暴露流体能力 → 连接（容器/机器，自动兼容其它模组）
        if (level instanceof Level realLevel) {
            if (realLevel.getCapability(Capabilities.FluidHandler.BLOCK, neighborPos, side.getOpposite()) != null) {
                return true;
            }
        }
        // ② ★ 相邻方块是源流体（水源/岩浆源等）→ 连接（流向由泵决定，这里只表示"可吸"）
        FluidState fluid = neighborState.getFluidState();
        return !fluid.isEmpty() && fluid.isSource();
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        BlockState state = this.defaultBlockState();
        LevelReader level = context.getLevel();
        BlockPos pos = context.getClickedPos();
        for (Map.Entry<Direction, BooleanProperty> entry : PROPERTY_BY_DIRECTION.entrySet()) {
            state = state.setValue(entry.getValue(), connectsTo(level, pos, entry.getKey()));
        }
        return state;
    }

    @Override
    protected BlockState updateShape(BlockState state, Direction direction, BlockState neighborState,
                                     LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        return state.setValue(PROPERTY_BY_DIRECTION.get(direction), connectsTo(level, pos, direction));
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shapeFor(state);
    }

    @Override
    protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shapeFor(state);
    }

    private static VoxelShape shapeFor(BlockState state) {
        int index = 0;
        int bit = 1;
        for (Map.Entry<Direction, BooleanProperty> entry : PROPERTY_BY_DIRECTION.entrySet()) {
            if (state.getValue(entry.getValue())) {
                index |= bit;
            }
            bit <<= 1;
        }
        VoxelShape cached = SHAPE_CACHE[index];
        if (cached != null) {
            return cached;
        }
        VoxelShape shape = CORE;
        for (Map.Entry<Direction, BooleanProperty> entry : PROPERTY_BY_DIRECTION.entrySet()) {
            if (state.getValue(entry.getValue())) {
                shape = Shapes.or(shape, ARM.get(entry.getKey()));
            }
        }
        SHAPE_CACHE[index] = shape;
        return shape;
    }

    @Override
    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        return List.of(new ItemStack(this));
    }
}