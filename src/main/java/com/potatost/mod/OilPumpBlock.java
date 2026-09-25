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
 * 采油机（0.11 ZF109）。
 *
 * <p>用户原话：「海洋油田可以利用起来了 加一个采油机（配方；【硬质钛合金】【耐热金属块】【硬质钛合金】，
 * 【油桶】【高压气罐】【油桶】，【流体泵】【流体泵】【流体泵】） 在海洋油田群系工作
 * gui为一个大罐子25B储量（不是那种竖直的了 是一个横过来的矩形罐子）和一个工作指示灯
 * 能量条不需要 下方必须有水源方块 检测下方连接的 含水锁链的数量
 * 耗能公式为 80n*1/10n+80n FE/t 原油获取为 10n mb/s （n为下方含水锁链个数）
 * 每开采25~80桶原油 附近10*10的海洋油桶群系会变成符合旁边群系的海洋（冻洋 暖洋 温带海洋...）」。</p>
 *
 * <p>方块本身<b>没有朝向</b>（与微型粉碎机 / 分馏塔操作器 / 空气分离器同款：对称 + 一张 16×16 贴图），
 * 右键开界面。它<b>没有物品槽</b>，所以破坏时不需要掉内容物；罐里剩的油会随方块一起消失
 * （与空气分离器 / 酸性反应室一致 —— 那几台也没做"拆机倒油"）。</p>
 */
public class OilPumpBlock extends BaseEntityBlock {

    public OilPumpBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(OilPumpBlock::new);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new OilPumpBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
                                                                  BlockEntityType<T> type) {
        return createTickerHelper(type, ModBlocks.OIL_PUMP_BE.get(),
                OilPumpBlockEntity::tick);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hitResult) {
        if (!level.isClientSide
                && player instanceof ServerPlayer serverPlayer
                && level.getBlockEntity(pos) instanceof OilPumpBlockEntity be) {
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
}
