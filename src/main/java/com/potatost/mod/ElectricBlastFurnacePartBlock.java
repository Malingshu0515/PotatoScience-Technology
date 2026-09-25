package com.potatost.mod;

import java.util.List;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.phys.BlockHitResult;

/**
 * 电力高炉的<b>部件格</b>（0.10 ZF39 / ZF41）：装配后除控制器与中间空气格之外的 25 格。
 *
 * <p>它自己不渲染 —— 整块 OBJ 由控制器那一格画，这样"一个模型是一个整体"
 * （用户 ZF39 的原话，参考沉浸工程）。它的作用是让这 25 格在世界上"有主"：</p>
 * <ul>
 *   <li><b>右键任意一格都开 GUI</b>（用户 ZF39：「任意部位右键都可以打开gui」）；</li>
 *   <li><b>破坏任意一格都整体拆解</b>，并且只掉被挖那一格原来的方块；</li>
 *   <li><b>原本是接线块的那两格继续当接电口</b>（ZF41，见
 *       {@link ElectricBlastFurnacePartBlockEntity#getEnergyStorage()}）。</li>
 * </ul>
 *
 * <p>⚠ {@code RenderShape.INVISIBLE} 必须配合控制器模型里的 {@code "automatic_culling": false}，
 * 否则部件格会把整块模型的内部面剔掉。</p>
 */
public class ElectricBlastFurnacePartBlock extends BaseEntityBlock {

    public ElectricBlastFurnacePartBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(ElectricBlastFurnacePartBlock::new);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new ElectricBlastFurnacePartBlockEntity(pos, state);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.INVISIBLE;
    }

    /** 右键**任意部位**都开控制器那本 GUI（沉浸工程那种手感）。 */
    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hitResult) {
        if (!level.isClientSide
                && player instanceof ServerPlayer serverPlayer
                && ElectricBlastFurnacePartBlockEntity.findMaster(level, pos) instanceof
                ElectricBlastFurnaceBlockEntity master) {
            serverPlayer.openMenu(master);
            return InteractionResult.CONSUME;
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    /** 手持扳手 + Shift + 右键 = 整体拆解（ZF41：拆解从"空手 Shift"改成了"扳手"）。 */
    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
                                              Player player, InteractionHand hand, BlockHitResult hitResult) {
        if (!stack.is(ModItems.WRENCH.get()) || !player.isShiftKeyDown()) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        if (!level.isClientSide) {
            ElectricBlastFurnaceBlockEntity master =
                    ElectricBlastFurnacePartBlockEntity.findMaster(level, pos);
            if (master != null) {
                ElectricBlastFurnaceWrench.disassembleByWrench(level, master, pos);
            }
        }
        return ItemInteractionResult.sidedSuccess(level.isClientSide);
    }

    /**
     * 破坏任意一个部件格：结构整体拆解，**只掉这一格原来的方块**与 GUI 内容物。
     *
     * <p>必须在 {@code super.onRemove} 之前找控制器 —— super 之后这一格已经是空气了（§4.13 同理）。</p>
     */
    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {
        if (!state.is(newState.getBlock()) && !level.isClientSide) {
            ElectricBlastFurnaceBlockEntity master = ElectricBlastFurnacePartBlockEntity.findMaster(level, pos);
            if (master != null) {
                BlockState original = master.originalAt(pos);
                if (original != null && !original.isAir()) {
                    Block.popResource(level, pos, new ItemStack(original.getBlock().asItem()));
                }
                master.dropContents();
                master.disassemble(pos);   // 被挖掉这一格留空，别把原方块又还原回去（否则白送一格）
            }
        }
        super.onRemove(state, level, pos, newState, movedByPiston);
    }

    @Override
    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        // 掉落统一在 onRemove 里做（那里才知道"这一格原来是什么"）
        return List.of();
    }
}
