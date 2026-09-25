package com.potatost.mod;

import java.util.function.IntConsumer;
import java.util.function.IntSupplier;

import net.neoforged.neoforge.energy.IEnergyStorage;

/**
 * 机器共用的「只收不放」能量缓冲（0.09 提取）。
 *
 * <p><b>为什么会有这个类：</b>0.03~0.08 期间，同一个匿名 {@code IEnergyStorage} 实现
 * 在 8 个方块实体里各抄了一份，合计约 500 行重复代码。审计后按语义分组发现：
 * <ul>
 *   <li><b>逐字相同、只是容量常量不同</b>：灌装机(3000) / 晒盐机(210) / 电解器(20000)
 *       —— 这三个提取到本类；</li>
 *   <li><b>语义确实不同，不强行套同一抽象</b>（各自保留原实现，避免"为复用而扭曲"）：
 *       发电机（只放不取，且有 PUSH_RATE 单次上限）、
 *       创造线缆（无限，且 {@code extractEnergy} 不写 setChanged）、
 *       流体泵（容量是动态的 {@code effectiveCapacity()}，且 getter 会夹取）、
 *       接线端子（收发方向由 {@code mode} 决定）、
 *       锂电池（long 运算，且 canExtract/canReceive 随电量变化）。</li>
 * </ul>
 *
 * <p>行为与提取前<b>逐字等价</b>：{@code received = min(maxReceive, 容量-当前)}，
 * 非正数直接返回 0，模拟态不落盘，落盘时调 setter（setter 内部负责 {@code setChanged()}）。
 *
 * <p><b>0.10 ZF22 追加「只放不收」：</b>太阳能板需要的是反向的那种（只出不进）。
 * 它本来是第 6 个匿名 {@code IEnergyStorage}，被 Audit 的 <b>D 项</b>当场点出来
 * （"超过基准 5：可能有新的复制粘贴，考虑复用 MachineEnergyStorage"）——
 * 于是这里加一个方向开关，两种极性共用同一份实现。</p>
 */
public final class MachineEnergyStorage implements IEnergyStorage {

    private final IntSupplier capacity;
    private final IntSupplier stored;
    private final IntConsumer setter;
    /** true = 只收不放（机器缓冲）；false = 只放不收（发电机类） */
    private final boolean receives;

    private MachineEnergyStorage(IntSupplier capacity, IntSupplier stored, IntConsumer setter, boolean receives) {
        this.capacity = capacity;
        this.stored = stored;
        this.setter = setter;
        this.receives = receives;
    }

    /**
     * 造一个「只收不放」的储能：{@code canReceive()} 恒真，{@code canExtract()} 恒假，
     * {@code extractEnergy(...)} 恒返回 0。
     *
     * @param capacity 容量上限（用 supplier 是为了兼容未来可能的动态容量）
     * @param stored   当前已存量
     * @param setter   写入已存量，<b>实现方负责在里面调 {@code setChanged()}</b>
     */
    public static MachineEnergyStorage receiveOnly(IntSupplier capacity, IntSupplier stored, IntConsumer setter) {
        return new MachineEnergyStorage(capacity, stored, setter, true);
    }

    /**
     * 造一个「只放不收」的储能：{@code canExtract()} 恒真，{@code canReceive()} 恒假，
     * {@code receiveEnergy(...)} 恒返回 0。给发电机类方块用（太阳能板）。
     *
     * <p>与发电机自己那份匿名实现的差别：<b>这里没有单次抽取上限</b>。
     * 太阳能板缓冲本来就只有 512 FE，再加个上限只是徒增复杂度。</p>
     */
    public static MachineEnergyStorage extractOnly(IntSupplier capacity, IntSupplier stored, IntConsumer setter) {
        return new MachineEnergyStorage(capacity, stored, setter, false);
    }

    @Override
    public int receiveEnergy(int maxReceive, boolean simulate) {
        if (!this.receives) {
            return 0;
        }
        int current = this.stored.getAsInt();
        int space = this.capacity.getAsInt() - current;
        if (maxReceive <= 0 || space <= 0) {
            return 0;
        }
        int accepted = Math.min(maxReceive, space);
        if (!simulate) {
            this.setter.accept(current + accepted);
        }
        return accepted;
    }

    @Override
    public int extractEnergy(int maxExtract, boolean simulate) {
        if (this.receives) {
            return 0;
        }
        int current = this.stored.getAsInt();
        int taken = Math.min(maxExtract, current);
        if (taken <= 0) {
            return 0;
        }
        if (!simulate) {
            this.setter.accept(current - taken);
        }
        return taken;
    }

    @Override
    public int getEnergyStored() {
        return this.stored.getAsInt();
    }

    @Override
    public int getMaxEnergyStored() {
        return this.capacity.getAsInt();
    }

    @Override
    public boolean canExtract() {
        return !this.receives;
    }

    @Override
    public boolean canReceive() {
        return this.receives;
    }
}
