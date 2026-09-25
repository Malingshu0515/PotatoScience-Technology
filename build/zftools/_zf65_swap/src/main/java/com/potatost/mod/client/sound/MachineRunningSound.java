package com.potatost.mod.client.sound;

import java.util.HashMap;
import java.util.Map;

import net.minecraft.client.Minecraft;
import net.minecraft.client.resources.sounds.AbstractTickableSoundInstance;
import net.minecraft.core.BlockPos;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.entity.BlockEntity;

/** 机器运行中的循环音：运行=响，停止/被拆=停。 */
public class MachineRunningSound extends AbstractTickableSoundInstance {
    private static final Map<BlockPos, MachineRunningSound> ACTIVE = new HashMap<>();

    private final BlockEntity be;
    private final BlockPos pos;

    private MachineRunningSound(BlockEntity be, SoundEvent event) {
        super(event, SoundSource.BLOCKS, RandomSource.create());
        this.be = be;
        this.pos = be.getBlockPos();
        this.looping = true;
        this.volume = 1.0F;
        this.pitch = 1.0F;
        this.x = this.pos.getX() + 0.5D;
        this.y = this.pos.getY() + 0.5D;
        this.z = this.pos.getZ() + 0.5D;
    }

    /** 每 tick 调用一次即可（幂等）：running 为 true 时循环播放，否则停止。 */
    public static void update(BlockEntity be, boolean running, SoundEvent event) {
        if (be == null || be.getLevel() == null || !be.getLevel().isClientSide()) {
            return;
        }
        BlockPos key = be.getBlockPos();
        MachineRunningSound s = ACTIVE.get(key);
        if (s != null && (s.isStopped() || s.be.isRemoved())) {
            // ZF65：不能只把它从表里删掉 —— 表和声音引擎是两回事，删表不等于消音。先 stop() 再删。
            s.stop();
            ACTIVE.remove(key);
            s = null;
        }
        if (running) {
            if (s == null) {
                MachineRunningSound created = new MachineRunningSound(be, event);
                ACTIVE.put(key, created);
                Minecraft.getInstance().getSoundManager().play(created);
            }
        } else if (s != null) {
            s.stop();
            ACTIVE.remove(key);
        }
    }

    @Override
    public void tick() {
        // ZF65：不能只看 isRemoved()。再加一条"那格已经不是这个方块实体了"（挖掉 ⇒ 空气、换方块 ⇒ 另一个实例），
        // 两条中任一成立就停 —— 循环音一旦卡住是没有别的机会停的（方块没了就再没有 tick 去纠正它）。
        // 用 isLoaded 挡一下：区块没加载时 getBlockEntity 会是 null，那不是"方块没了"。
        net.minecraft.world.level.Level level = this.be.getLevel();
        boolean gone = this.be.isRemoved()
                || level == null
                || (level.isLoaded(this.pos) && level.getBlockEntity(this.pos) != this.be);
        if (gone) {
            this.stop();
            ACTIVE.remove(this.pos, this);
        }
    }
}
