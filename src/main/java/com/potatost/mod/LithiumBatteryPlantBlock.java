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
 * 锂电池构造间（0.11 ZF112）。
 *
 * <p>用户原话：「加一个锂电池构造间 通入硫酸 放入粗锰/粗铝and 镍/粗镍 and 碳酸锂 and钴/粗钴
 * 每t消耗10mb硫酸 30s后产出一个锂电池原件 不消耗电」。</p>
 *
 * <p>方块本身没有朝向（与空气分离器 / 采油机同款：对称贴图 + 右键开界面）；
 * <b>5 个物品槽在破坏时会全部掉出来</b>（见 {@link #onRemove}）。</p>
 *
 * <p><b>0.11 ZF114 补</b>：这条 {@code onRemove} 是 ZF112 漏掉的，由 {@code Audit.ps1} 的 B 项抓出来
 * （"有物品栏但【未】掉落 —— 破坏即吞物品"）。原来那句"破坏时槽里的东西跟着消失（与其它单方块机器一致）"
 * 是**错的**：其它单方块机器（微型粉碎机 / 液压机 / 盐分解构器 / 灌装机…）全都掉了，
 * 档案 §4.13 就是为这个坑立的规矩。</p>
 */
public class LithiumBatteryPlantBlock extends BaseEntityBlock {

    public LithiumBatteryPlantBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(LithiumBatteryPlantBlock::new);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new LithiumBatteryPlantBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
                                                                  BlockEntityType<T> type) {
        return createTickerHelper(type, ModBlocks.LITHIUM_BATTERY_PLANT_BE.get(),
                LithiumBatteryPlantBlockEntity::tick);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hitResult) {
        if (!level.isClientSide
                && player instanceof ServerPlayer serverPlayer
                && level.getBlockEntity(pos) instanceof LithiumBatteryPlantBlockEntity be) {
            serverPlayer.openMenu(be);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    @Override
    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        return List.of(new ItemStack(this));
    }

    /**
     * 破坏 / 爆炸 / 被其他方块替换时，把 5 个槽里的东西全掉出来（档案 §4.13）。
     *
     * <p>⚠ 必须在 {@code super.onRemove} <b>之前</b>取方块实体 —— super 会把 BE 从区块里摘掉，
     * 之后 {@code getBlockEntity(pos)} 就是 null 了；{@code MachineDrops} 内部对
     * {@code level.isClientSide} 直接返回，免得客户端生成幽灵掉落物。</p>
     */
    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {
        if (!state.is(newState.getBlock())
                && level.getBlockEntity(pos) instanceof LithiumBatteryPlantBlockEntity be) {
            MachineDrops.dropInventory(level, pos, be.getInventory());
        }
        super.onRemove(state, level, pos, newState, movedByPiston);
    }
}
