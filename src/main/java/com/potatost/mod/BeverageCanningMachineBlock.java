package com.potatost.mod;

import java.util.List;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
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
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.IFluidHandlerItem;

/**
 * 饮料罐装机（0.13 ZF167）：普通方块模型（对称、无朝向），右键开 GUI，
 * **手里拿着装流体的容器右键 = 手倒**（与灌装机 / 蒸馏塔操作器同一个口径）。
 */
public class BeverageCanningMachineBlock extends BaseEntityBlock {

    public BeverageCanningMachineBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(BeverageCanningMachineBlock::new);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new BeverageCanningMachineBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
                                                                  BlockEntityType<T> type) {
        return createTickerHelper(type, ModBlocks.BEVERAGE_CANNING_MACHINE_BE.get(),
                BeverageCanningMachineBlockEntity::tick);
    }

    /**
     * 右键：手里拿着**装流体的容器**（桶、高压气罐、油桶…）就先手倒，否则开界面。
     *
     * <p>走 NeoForge 的**物品流体能力**（{@code Capabilities.FluidHandler.ITEM}），
     * 而不是照灌装机那样只认本 mod 的 {@code FluidContainerItem}：
     * 水的来源绝大多数是**原版水桶**，原版桶自己就带这个能力 ⇒ 一台"要灌水"的机器
     * 必须认它，否则玩家拿水桶右键只会打开界面、水倒不进去（这正是灌装机 0.11 ZF73
     * 那次"油桶倒不进去"的同一类坑）。</p>
     *
     * <p>倒多少：一次最多 {@link BeverageCanningMachineBlockEntity#POUR_PER_CLICK} mB
     * （与灌装机/蒸馏塔操作器同一个数）。收不收由**罐自己的校验器**说了算
     * （碳酸罐只收碳酸、水罐只收水、乙醇罐只收 {@code c:ethanol} 标签里的东西），
     * 所以拿一桶水右键不会污染碳酸罐。</p>
     */
    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
                                              Player player, InteractionHand hand, BlockHitResult hitResult) {
        IFluidHandlerItem held = stack.getCapability(Capabilities.FluidHandler.ITEM);
        if (held == null) {
            // 不是流体容器（空手 / 别的物品）⇒ 原样放行：原版会接着走 useWithoutItem 开界面。
            // ⚠ 这一行照抄灌装机 ZF80 那份（它已过真服务端探针）：返回 PASS 之后界面照开，
            //   而"手上拿着方块"也不会被摆到机器上。
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        FluidStack contents = held.getFluidInTank(0);
        if (contents.isEmpty()) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        if (level.isClientSide) {
            return ItemInteractionResult.sidedSuccess(true);
        }
        if (!(level.getBlockEntity(pos) instanceof BeverageCanningMachineBlockEntity be)) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        int want = Math.min(contents.getAmount(),
                BeverageCanningMachineBlockEntity.POUR_PER_CLICK);
        int accepted = be.getFluidHandler().fill(contents.copyWithAmount(want),
                IFluidHandler.FluidAction.SIMULATE);
        if (accepted <= 0) {
            // 这种流体这三只罐都不收（罐自己的校验器说了算）—— 说清楚是哪一种
            player.displayClientMessage(Component.translatable(
                    "gui.potato_s_t.canning.pour.rejected", contents.getHoverName()), true);
            return ItemInteractionResult.sidedSuccess(false);
        }
        FluidStack drained = held.drain(accepted, IFluidHandler.FluidAction.EXECUTE);
        int moved = be.getFluidHandler().fill(drained, IFluidHandler.FluidAction.EXECUTE);
        if (moved > 0) {
            player.setItemInHand(hand, held.getContainer());
            level.playSound(null, pos, SoundEvents.BUCKET_EMPTY, SoundSource.BLOCKS, 1.0F, 1.0F);
            player.displayClientMessage(Component.translatable(
                    "gui.potato_s_t.canning.pour.poured", contents.getHoverName(), moved), true);
        }
        return ItemInteractionResult.sidedSuccess(false);
    }

    /** 空手右键 = 开界面（与其它机器一致）。 */
    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hitResult) {
        if (!level.isClientSide && player instanceof ServerPlayer serverPlayer
                && level.getBlockEntity(pos) instanceof BeverageCanningMachineBlockEntity be) {
            serverPlayer.openMenu(be);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    /** 破坏/爆炸/被替换时把四个槽里的东西全掉出来（必须在 super.onRemove 之前取方块实体，§4.13）。 */
    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {
        if (!state.is(newState.getBlock())
                && level.getBlockEntity(pos) instanceof BeverageCanningMachineBlockEntity be) {
            MachineDrops.dropInventory(level, pos, be.getInventory());
        }
        super.onRemove(state, level, pos, newState, movedByPiston);
    }

    @Override
    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        return List.of(new ItemStack(this));
    }
}
