package com.potatost.mod;

import java.util.List;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
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

/**
 * 大型柴油发电机的<b>接线口</b>（0.11 ZF125）：成型时替换掉控制器正上方那一格【接线块】。
 *
 * <p><b>贴图与接线块完全一样</b>（模型直接指向 {@code potato_s_t:block/wiring_block}），
 * 所以玩家看不出被换过；区别只在它带方块实体 ⇒ 能挂能量能力。
 * 这是本工程多方块机器的老规矩（电力高炉「原来接线块的地方传电」、
 * 合金炉 {@code alloy_smelter_port} 同一套）。</p>
 *
 * <p><b>与合金炉那个接线口的两处不同</b>：</p>
 * <ol>
 *   <li>合金炉那个是 {@code RenderShape.INVISIBLE}（整台机器由控制器的 OBJ 长方体负责画）；
 *       这台机器<b>没有 OBJ</b>（它的外形就是玩家摆的那 30 格方块）⇒ 接线口必须<b>照常渲染</b>，
 *       否则机器顶上会出现一个洞。</li>
 *   <li>它是<b>出电</b>口（{@code canExtract}），不是进电口 —— 邻居端子会主动来抽。</li>
 * </ol>
 *
 * <p>挖掉它掉回一个<b>接线块</b>（玩家当初摆的就是那个）；控制器被挖掉时，
 * {@link DieselGeneratorBlock#onRemove} 会把它换回接线块。</p>
 */
public class DieselGeneratorPortBlock extends BaseEntityBlock {

    public DieselGeneratorPortBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(DieselGeneratorPortBlock::new);
    }

    @Override
    public RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new DieselGeneratorPortBlockEntity(pos, state);
    }

    /** 接线口自己没有逻辑（它只是"电的出口"），tick 由控制器那边做。 */
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
                                                                 BlockEntityType<T> type) {
        return null;
    }

    /** 右键接线口 = 开控制器的界面（玩家不用绕到正面去找控制器）。 */
    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hit) {
        if (level.isClientSide) {
            return InteractionResult.SUCCESS;
        }
        BlockPos controller = pos.below();
        if (!(level.getBlockEntity(controller) instanceof DieselGeneratorBlockEntity be)) {
            return InteractionResult.PASS;
        }
        DieselGeneratorBlock.reportHoles(level, controller, player);
        if (player instanceof ServerPlayer serverPlayer) {
            serverPlayer.openMenu(be);
        }
        return InteractionResult.CONSUME;
    }

    /** 挖接线口掉一个接线块（不是接线口本身 —— 那个东西挖不出来）。 */
    @Override
    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        return List.of(new ItemStack(ModBlocks.WIRING_BLOCK_ITEM.get()));
    }
}
