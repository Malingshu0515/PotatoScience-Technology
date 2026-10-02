package com.potatost.mod;

import java.util.List;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
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
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.phys.BlockHitResult;

/**
 * 电力高炉的<b>控制器</b>方块（0.10 ZF39）：装配后它占据原来那台原版高炉的位置。
 *
 * <p>整个 3×3×3 的 OBJ 模型挂在它的 blockstate 上（4 个朝向各一份烘焙好的 OBJ，
 * 见 {@code MakeBlastFurnaceModel.py} 与档案 §12.6），另外 25 格是
 * {@link ElectricBlastFurnacePartBlock}（不可见），中间那格是空气。</p>
 */
public class ElectricBlastFurnaceBlock extends BaseEntityBlock {

    public static final DirectionProperty FACING = HorizontalDirectionalBlock.FACING;

    public ElectricBlastFurnaceBlock(Properties properties) {
        super(properties);
        this.registerDefaultState(this.stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(ElectricBlastFurnaceBlock::new);
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
        return new ElectricBlastFurnaceBlockEntity(pos, state);
    }

    /** 双端都要 tick（客户端那一侧驱动循环音效；写成客户端 return null 会静默失声，§4.26）。 */
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
                                                                  BlockEntityType<T> type) {
        return createTickerHelper(type, ModBlocks.ELECTRIC_BLAST_FURNACE_BE.get(),
                ElectricBlastFurnaceBlockEntity::tick);
    }

    /**
     * 空手右键：<b>还没成型</b>（老存档里从物品摆出来的裸控制器）且按着 Shift 时试着用周围建材成型；
     * 其余情况一律开 GUI。
     *
     * <p>⚠ ZF41 起**空手 Shift 不再拆解**；ZF162 起**扳手整个删掉了**（用户：「删除一下 1.扳手
     * 2.物品形式的电力高炉（这两个有bug没必要修了）」）⇒ 现在拆解只剩「挖掉任意一格」这一条路
     * （见 {@link #onRemove}：整体还原 + 掉 GUI 内容物）。</p>
     */
    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hitResult) {
        if (!level.isClientSide
                && player.isShiftKeyDown()
                && level.getBlockEntity(pos) instanceof ElectricBlastFurnaceBlockEntity be
                && !be.isFormed()) {
            Direction facing = state.getValue(FACING);
            ElectricBlastFurnaceStructure.Problem problem =
                    ElectricBlastFurnaceStructure.validate(level, pos, facing);
            if (problem != null) {
                player.displayClientMessage(invalidMessage(problem), true);
            } else {
                BlastFurnaceAssembly.form((ServerLevel) level, pos, facing);
                if (player instanceof ServerPlayer serverPlayer) {
                    // 0.13 ZF162：老存档里的裸控制器也能成型，所以这条老路同样要点亮那条进度
                    EbfFormedTrigger.EBF_FORMED.get().trigger(serverPlayer);
                }
                player.displayClientMessage(Component.translatable("gui.potato_s_t.ebf.formed"), true);
            }
            return InteractionResult.CONSUME;
        }
        if (!level.isClientSide
                && player instanceof ServerPlayer serverPlayer
                && level.getBlockEntity(pos) instanceof ElectricBlastFurnaceBlockEntity be) {
            serverPlayer.openMenu(be);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    /** 模型是整块的 OBJ，由方块模型系统画（不是 BER）。 */
    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    /**
     * 被破坏 = 拆掉整个结构，并**只**掉出被挖掉那一格的**原方块**与 GUI 内容物。
     *
     * <p>用户 ZF39 的规矩：「被破坏后只会毁坏结构和掉落被挖掉的方块以及 gui 内部物品」。
     * ⚠ 0.13 ZF162 起**这个方块没有物品形态了**（用户：「物品形式的电力高炉……有bug没必要修了」）
     * ⇒ 老代码里那条"还没成型的裸控制器拆掉要把物品还回去"的分支整段删掉：物品已经不在注册表里，
     * 再 pop 一次只会掉出一件不存在的东西。老存档里若还有裸控制器，破坏它就是**不返还**（如实记在 §9）。</p>
     *
     * <p>⚠ <b>那道 {@code !be.isDisassembling()} 闸门是必须的</b>，否则会掉两个：
     * {@link ElectricBlastFurnaceBlockEntity#disassemble()} 会把控制器那一格清成空气，
     * 于是**方块自己的 {@code onRemove} 又被触发一次**，第二次再掉一遍。
     * （用户报的"挖掘后会掉落两个电力高炉"就是这个。）</p>
     */
    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {
        if (!state.is(newState.getBlock())
                && level.getBlockEntity(pos) instanceof ElectricBlastFurnaceBlockEntity be
                && !be.isDisassembling()) {
            if (be.isFormed()) {
                BlockState original = be.originalAt(pos);
                if (original != null && !original.isAir()) {
                    Block.popResource(level, pos, new ItemStack(original.getBlock().asItem()));
                }
            }
            // ⚠ 这一行必须留在这个文件里 —— Audit B 项是**文本级**检查
            MachineDrops.dropInventory(level, pos, be.getInventory());
            be.disassemble();
        }
        super.onRemove(state, level, pos, newState, movedByPiston);
    }

    /** 结构不成立的反馈：位置与期望方块都来自结构化数据，文本走 lang（Audit E 项）。 */
    public static Component invalidMessage(ElectricBlastFurnaceStructure.Problem p) {
        return Component.translatable("gui.potato_s_t.ebf.invalid",
                p.y() + 1, p.j() + 1, p.i() + 1, p.expected().getName());
    }

    @Override
    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        // 掉落统一在 onRemove 里做（那里才知道"这一格原来是什么"），这里留空避免掉两份
        return List.of();
    }
}
