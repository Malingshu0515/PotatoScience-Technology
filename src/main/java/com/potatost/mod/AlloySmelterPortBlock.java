package com.potatost.mod;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.InteractionResult;
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
import net.minecraft.world.phys.BlockHitResult;

/**
 * 合金冶炼炉的<b>接线口</b>（0.10 ZF49）：成型时替换掉图案里那两格【接线块】。
 *
 * <p><b>贴图与接线块完全一样</b>（模型直接指向 {@code potato_s_t:block/wiring_block}），
 * 所以玩家看不出被换过；区别只在它带方块实体 ⇒ 能挂能量能力。
 * 这样电就只能从这两格进（用户规则：「原来接线块的地方传电」，与电力高炉一致）。</p>
 *
 * <p>挖掉它 = 结构缺一格 ⇒ 控制器下一次复查就失效；同时掉回一个**接线块**（不是接线口本身，
 * 那个东西挖不出来）。</p>
 */
public class AlloySmelterPortBlock extends BaseEntityBlock {

    public static final DirectionProperty FACING = HorizontalDirectionalBlock.FACING;

    public AlloySmelterPortBlock(Properties properties) {
        super(properties);
        registerDefaultState(this.stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(AlloySmelterPortBlock::new);
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
        // ZF54：整台机器由控制器的 OBJ 长方体画 ⇒ 接线口必须**不渲染**，
        // 否则它的贴图会和盒子的面 z-fighting 打架
        return RenderShape.INVISIBLE;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new AlloySmelterPortBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
                                                                 BlockEntityType<T> type) {
        return null;    // 接线口自己没有逻辑，只是"电的入口"
    }

    /** 右键接线口 = 打开控制器界面（玩家不用去正面找控制器）。 */
    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hit) {
        if (level.isClientSide) {
            return InteractionResult.SUCCESS;
        }
        AlloySmelterBlockEntity master = AlloySmelterBlockEntity.findMaster(level, pos);
        if (master == null) {
            return InteractionResult.PASS;
        }
        player.openMenu(master, master.getBlockPos());
        return InteractionResult.CONSUME;
    }

    /**
     * 挖掉接线口：掉一个**接线块**回去（玩家当初摆的就是接线块），并让控制器失效。
     *
     * <p>拆解期间（{@code master.isDisassembling()}）不重复掉落 —— 那是控制器自己在换方块。</p>
     */
    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {
        if (!state.is(newState.getBlock())) {
            AlloySmelterBlockEntity master = AlloySmelterBlockEntity.findMaster(level, pos);
            if (master != null && !master.isDisassembling()) {
                Block.popResource(level, pos, new ItemStack(ModBlocks.WIRING_BLOCK_ITEM.get()));
                master.dropContents();
                // ⚠ ZF55 补的坑：接线口也是"外壳上的一格"。ZF54 起外壳整片会被换成不渲染的部件格，
                //    而这里原来只 setFormed(false) —— 剩下的部件格就**永远留在地图上**
                //    （机器看不见了、方块还在、还挖不出东西）。所以要和部件格走同一条路：
                //    disassemble(pos) 把其余格原样还原，被挖的这格留空（它的接线块上面已经掉了）。
                master.disassemble(pos);
            }
        }
        super.onRemove(state, level, pos, newState, movedByPiston);
    }
}
