package com.potatost.mod;

import java.util.List;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
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
 * 创造模式线缆（方块）：
 *  - 无限 FE 电源（测试用）。
 *  - shift+右键 = 循环切换传输速率；空手右键 = 查看当前速率（动作栏）。
 *  - 供能逻辑在 CreativeCableBlockEntity。
 */
public class CreativeCableBlock extends BaseEntityBlock {

    public CreativeCableBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(CreativeCableBlock::new);
    }

    /** BaseEntityBlock 默认 INVISIBLE；走 JSON 模型必须显式 MODEL */
    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new CreativeCableBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        if (level.isClientSide) {
            return null;   // 只服务端需要发功
        }
        return (tickLevel, pos, blockState, blockEntity) -> {
            if (blockEntity instanceof CreativeCableBlockEntity cable) {
                CreativeCableBlockEntity.tick(tickLevel, pos, blockState, cable);
            }
        };
    }

    /** 手持物品右键：shift 时切档；不按 shift 时交还默认行为（放置等照旧） */
    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                              InteractionHand hand, BlockHitResult hitResult) {
        if (player.isShiftKeyDown()) {
            if (!level.isClientSide && level.getBlockEntity(pos) instanceof CreativeCableBlockEntity cable) {
                cable.cycleRate();
                showRate(player, cable);
            }
            return ItemInteractionResult.sidedSuccess(level.isClientSide);
        }
        return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
    }

    /** 空手右键：shift 时切档；否则显示当前速率 */
    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hitResult) {
        if (!level.isClientSide && level.getBlockEntity(pos) instanceof CreativeCableBlockEntity cable) {
            if (player.isShiftKeyDown()) {
                cable.cycleRate();
            }
            showRate(player, cable);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    private static void showRate(Player player, CreativeCableBlockEntity cable) {
        String text = cable.getRateLabel() + "（" + formatNumber(cable.getCurrentRate()) + "）";
        player.displayClientMessage(Component.translatable("gui.potato_s_t.creative_cable.rate", text), true);
    }

    /** 21400000000 → "21,400,000,000" */
    private static String formatNumber(long value) {
        String digits = Long.toString(value);
        StringBuilder builder = new StringBuilder();
        int count = 0;
        for (int i = digits.length() - 1; i >= 0; i--) {
            builder.append(digits.charAt(i));
            count++;
            if (count % 3 == 0 && i > 0) {
                builder.append(',');
            }
        }
        return builder.reverse().toString();
    }

    @Override
    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        return List.of(new ItemStack(this));
    }
}