package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 分馏塔控制器的方块实体（0.11 ZF78）：<b>数塔 + 把数量推给相邻操作器</b>。
 *
 * <p>三条约定的执行顺序（都是省算力的）：</p>
 * <ol>
 *   <li><b>先看有没有相邻操作器</b>：一个都没有就直接不扫 —— 没人要这个数，
 *       扫一遍 3364 个锚点是白烧 CPU；</li>
 *   <li>扫描周期 20 tick（1 秒）：塔建好/拆掉最多 1 秒后数字跟上；</li>
 *   <li>{@link #requestRescan()} 可以让下一次 tick 立刻重扫（控制器自己的邻居变了时用）。</li>
 * </ol>
 *
 * <p><b>数量不存盘</b>：它是算出来的，读档/区块加载后由第一次扫描重建
 * （方块实体一造出来 {@code rescanRequested} 就是 true）。
 * 这样旧存档、被拆了一半的塔都不会残留一个假数字。</p>
 */
public class DistillationControllerBlockEntity extends BlockEntity {

    /** 扫描周期（tick） */
    public static final int SCAN_INTERVAL = 20;

    private int towerCount;
    private int cooldown;
    private boolean rescanRequested = true;

    public DistillationControllerBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.DISTILLATION_CONTROLLER_BE.get(), pos, state);
    }

    public static void tick(Level level, BlockPos pos, BlockState state, DistillationControllerBlockEntity controller) {
        if (level.isClientSide) {
            return;
        }
        controller.serverTick();
    }

    private void serverTick() {
        if (this.level == null) {
            return;
        }
        if (this.cooldown > 0) {
            this.cooldown--;
        }
        if (!this.rescanRequested && this.cooldown > 0) {
            return;
        }
        this.rescanRequested = false;
        this.cooldown = SCAN_INTERVAL;
        this.rescan();
    }

    /** 让下一次 tick 立刻重扫（而不是等满 20 tick）。 */
    public void requestRescan() {
        this.rescanRequested = true;
    }

    /**
     * 数一遍周围的塔并把数量推给**每一个**相邻的操作器。
     *
     * <p>相邻可以有多台操作器（用户没说只能一台），一台控制器带多台是允许的 ——
     * 它们各自独立分馏，共用同一份"塔数"。</p>
     */
    private void rescan() {
        List<DistillationOperatorBlockEntity> operators = new ArrayList<>(6);
        for (Direction dir : Direction.values()) {
            if (this.level.getBlockEntity(this.worldPosition.relative(dir))
                    instanceof DistillationOperatorBlockEntity operator) {
                operators.add(operator);
            }
        }
        if (operators.isEmpty()) {
            this.towerCount = 0;
            return;
        }
        int count = DistillationTowerStructure.countTowers(this.level, this.worldPosition);
        this.towerCount = count;
        for (DistillationOperatorBlockEntity operator : operators) {
            operator.setTowerCount(count);
        }
    }

    /** 上一次扫描数到的塔数（未夹取，可能大于 4 —— 操作器那边才夹到 4）。 */
    public int getTowerCount() {
        return this.towerCount;
    }
}
