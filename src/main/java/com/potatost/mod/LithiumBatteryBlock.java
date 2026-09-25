package com.potatost.mod;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.phys.BlockHitResult;

/**
 * 锂电池：紧贴成完整长方体时自动组成多方块储能，渲染交给 LithiumBatteryRenderer。
 *
 * 快捷放置：主手拿锂电池右键已有电池（不潜行）
 *   未填满 → 按包围盒把当前层一次铺满；
 *   已成型 → 上方（点底面则下方）再叠一整层。
 * 潜行右键 = 原版单块放置。
 */
public class LithiumBatteryBlock extends BaseEntityBlock {

    public LithiumBatteryBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(LithiumBatteryBlock::new);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new LithiumBatteryBlockEntity(pos, state);
    }

    /** 服务端每 tick：低频把电量同步给客户端 */
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        if (level.isClientSide) {
            return null;
        }
        return createTickerHelper(type, ModBlocks.LITHIUM_BATTERY_BE.get(), LithiumBatteryBlockEntity::tick);
    }

    /** 玩家放置完成：成型判定 */
    @Override
    public void setPlacedBy(Level level, BlockPos pos, BlockState state, LivingEntity placer, ItemStack stack) {
        if (!level.isClientSide) {
            LithiumBatteryBlockEntity.tryForm(level, pos);
        }
    }

    /** 旁边变了块：若新贴上来一块电池就重试成型（批量放置期间跳过，避免 O(n²)） */
    @Override
    protected void neighborChanged(BlockState state, Level level, BlockPos pos, Block neighborBlock,
                                   BlockPos neighborPos, boolean movedByPiston) {
        if (!level.isClientSide
                && !LithiumBatteryBlockEntity.isBulkPlacing()
                && neighborBlock instanceof LithiumBatteryBlock) {
            LithiumBatteryBlockEntity.tryForm(level, pos);
        }
    }

    // ================= 交互 =================

    /** 空手右键：强制重判成型 + 报告电量与尺寸 */
    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hitResult) {
        if (level.isClientSide) {
            return InteractionResult.SUCCESS;
        }
        LithiumBatteryBlockEntity.tryForm(level, pos);
        sendStatus(level, pos, player);
        return InteractionResult.SUCCESS;
    }

    /** 手持锂电池右键：快捷放置一层；潜行则放行给原版单块放置 */
    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
                                              Player player, InteractionHand hand, BlockHitResult hitResult) {
        if (!stack.is(ModBlocks.LITHIUM_BATTERY_ITEM.get()) || player.isShiftKeyDown()) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        if (!level.isClientSide) {
            placeLayer(level, pos, player, hitResult.getDirection());
        }
        return ItemInteractionResult.sidedSuccess(level.isClientSide);
    }

    /** 一键放置：未填满 → 铺满当前层；已成型 → 上/下再叠一层 */
    private void placeLayer(Level level, BlockPos clicked, Player player, Direction face) {
        // 1. 先让被点结构判定到最新状态
        LithiumBatteryBlockEntity.tryForm(level, clicked);

        // 2. BFS 连通整体，取包围盒
        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        Set<BlockPos> seen = new HashSet<>();
        List<BlockPos> members = new ArrayList<>();
        queue.add(clicked);
        seen.add(clicked);
        int minX = clicked.getX(), maxX = minX;
        int minY = clicked.getY(), maxY = minY;
        int minZ = clicked.getZ(), maxZ = minZ;
        while (!queue.isEmpty()) {
            BlockPos p = queue.poll();
            if (!(level.getBlockState(p).getBlock() instanceof LithiumBatteryBlock)) continue;
            members.add(p);
            if (members.size() > LithiumBatteryBlockEntity.MAX_BLOCKS) return;
            minX = Math.min(minX, p.getX()); maxX = Math.max(maxX, p.getX());
            minY = Math.min(minY, p.getY()); maxY = Math.max(maxY, p.getY());
            minZ = Math.min(minZ, p.getZ()); maxZ = Math.max(maxZ, p.getZ());
            for (Direction d : Direction.values()) {
                BlockPos n = p.relative(d);
                if (seen.add(n)) queue.add(n);
            }
        }

        int sx = maxX - minX + 1;
        int sy = maxY - minY + 1;
        int sz = maxZ - minZ + 1;

        int maxH = LithiumBatteryBlockEntity.maxHeightForBase(sx, sz);
        if (maxH <= 0) {
            msg(player, "message.potato_s_t.battery_base_invalid");
            return;
        }

        boolean complete = members.size() == sx * sy * sz;
        boolean bottom = face == Direction.DOWN;
        List<BlockPos> targets = new ArrayList<>();

        if (!complete) {
            // ---- 情况 A：当前层没填满 → 把被点击的这一层按包围盒铺满 ----
            int y = clicked.getY();
            for (int dx = 0; dx < sx; dx++) {
                for (int dz = 0; dz < sz; dz++) {
                    BlockPos p = new BlockPos(minX + dx, y, minZ + dz);
                    BlockState s = level.getBlockState(p);
                    if (s.is(ModBlocks.LITHIUM_BATTERY.get())) continue;
                    if (level.isOutsideBuildHeight(p) || !s.canBeReplaced()) {
                        msg(player, "message.potato_s_t.battery_layer_blocked");
                        return;
                    }
                    targets.add(p);
                }
            }
            if (targets.isEmpty()) {
                msg(player, "message.potato_s_t.battery_layer_blocked");
                return;
            }
        } else {
            // ---- 情况 B：已成型 → 上方（或点底面则下方）再叠一整层 ----
            if (maxH <= 1) {
                msg(player, "message.potato_s_t.battery_single_no_stack");
                return;
            }
            if (sy + 1 > maxH) {
                player.displayClientMessage(
                        Component.translatable("message.potato_s_t.battery_layer_no_room", maxH), true);
                return;
            }
            int y = bottom ? minY - 1 : maxY + 1;
            for (int dx = 0; dx < sx; dx++) {
                for (int dz = 0; dz < sz; dz++) {
                    BlockPos p = new BlockPos(minX + dx, y, minZ + dz);
                    if (level.isOutsideBuildHeight(p)) {
                        player.displayClientMessage(
                                Component.translatable("message.potato_s_t.battery_layer_no_room", maxH), true);
                        return;
                    }
                    if (!level.getBlockState(p).canBeReplaced()) {
                        msg(player, "message.potato_s_t.battery_layer_blocked");
                        return;
                    }
                    targets.add(p);
                }
            }
        }

        // ---- 块数上限与材料检查 ----
        int need = targets.size();
        if ((long) members.size() + need > LithiumBatteryBlockEntity.MAX_BLOCKS) {
            msg(player, "message.potato_s_t.battery_layer_blocked");
            return;
        }
        if (!player.getAbilities().instabuild
                && countItem(player, ModBlocks.LITHIUM_BATTERY_ITEM.get()) < need) {
            player.displayClientMessage(
                    Component.translatable("message.potato_s_t.battery_layer_no_items", need), true);
            return;
        }

        // ---- 放置 ----
        BlockState battery = ModBlocks.LITHIUM_BATTERY.get().defaultBlockState();
        LithiumBatteryBlockEntity.beginBulkPlacing();
        try {
            for (BlockPos p : targets) {
                level.setBlock(p, battery, Block.UPDATE_ALL);
            }
        } finally {
            LithiumBatteryBlockEntity.endBulkPlacing();
        }
        consumeItem(player, ModBlocks.LITHIUM_BATTERY_ITEM.get(), need);
        LithiumBatteryBlockEntity.tryForm(level, targets.get(0));
        level.playSound(null, clicked, SoundType.METAL.getPlaceSound(), SoundSource.BLOCKS, 1.0F, 1.0F);
        player.displayClientMessage(
                Component.translatable("message.potato_s_t.battery_layer_placed", need), true);
    }

    private static void msg(Player player, String key) {
        player.displayClientMessage(Component.translatable(key), true);
    }

    /** 背包（含快捷栏）里该物品的总数 */
    private static int countItem(Player player, Item item) {
        int found = 0;
        var inv = player.getInventory();
        for (int i = 0; i < inv.getContainerSize(); i++) {
            ItemStack s = inv.getItem(i);
            if (s.is(item)) {
                found += s.getCount();
            }
        }
        return found;
    }

    /** 从背包扣除（跨多个堆叠） */
    private static void consumeItem(Player player, Item item, int count) {
        if (player.getAbilities().instabuild) return;
        var inv = player.getInventory();
        int remaining = count;
        for (int i = 0; i < inv.getContainerSize() && remaining > 0; i++) {
            ItemStack s = inv.getItem(i);
            if (s.is(item)) {
                int take = Math.min(s.getCount(), remaining);
                s.shrink(take);
                remaining -= take;
            }
        }
        inv.setChanged();
    }

    private void sendStatus(Level level, BlockPos pos, Player player) {
        if (!(level.getBlockEntity(pos) instanceof LithiumBatteryBlockEntity be)) {
            return;
        }
        if (be.isFormed() && be.getController() != null
                && level.getBlockEntity(be.getController()) instanceof LithiumBatteryBlockEntity ctrl) {
            int sx = ctrl.getSizeX();
            int sz = ctrl.getSizeZ();
            int h = ctrl.getHeight();
            long blocks = (long) sx * sz * h;
            long cap = blocks * LithiumBatteryBlockEntity.PER_BLOCK;
            player.displayClientMessage(Component.translatable("message.potato_s_t.battery_status",
                    sx, sz, h, blocks, ctrl.getEnergyStoredLong(), cap), false);
        } else {
            player.displayClientMessage(Component.translatable("message.potato_s_t.battery_not_formed"), false);
        }
    }

    /** 结构内任意方块被移除：解散并均分能量 */
    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {
        if (!state.is(newState.getBlock())) {
            if (level.getBlockEntity(pos) instanceof LithiumBatteryBlockEntity be) {
                LithiumBatteryBlockEntity.handleRemoval(level, pos, be);
            }
        }
        super.onRemove(state, level, pos, newState, movedByPiston);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.ENTITYBLOCK_ANIMATED;
    }

    @Override
    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
        return List.of(new ItemStack(this));
    }
}