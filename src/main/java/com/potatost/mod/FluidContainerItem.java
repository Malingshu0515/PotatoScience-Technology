package com.potatost.mod;

import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.material.Fluid;
import net.neoforged.neoforge.fluids.FluidStack;

/**
 * 「能被灌装机灌装的流体容器物品」接口（0.11 ZF73 立）。
 *
 * <p><b>为什么要有这个接口</b>：灌装机原先把 {@link HighPressureTankItem} **写死**在三处
 * （槽位校验 {@code isItemValid}、灌装 {@code tryFillSlot}、完成音判定 {@code isDoneFilling}），
 * 每加一种容器就得改三处。抽成接口之后机器只认接口，而
 * <b>「收不收某种流体」由容器自己说了算</b> —— 这正是用户规则：高压气罐只收气体、
 * 油桶只收液体（还不能混装），机器不替它们把关。</p>
 *
 * <p>⚠ 这也是 §4.44 那条雷的正解：原先"是不是气体"写成「非水非岩浆」的负向判定，
 * 一加原油，气罐就会把原油当气体收下。现在判定收在 {@link ModFluids#isGas} 里正向列举。</p>
 */
public interface FluidContainerItem {

    /** 还能装多少 mB。 */
    int space(ItemStack stack);

    /** 收不收这种流体（气体 / 液体之分在这里）。 */
    boolean accepts(Fluid fluid);

    /**
     * 往容器里塞流体。
     *
     * @return 实际塞进去的 mB（0 = 一滴没进）
     */
    int fill(ItemStack stack, FluidStack fluid, int maxAmount);

    /** 容器是不是空的。 */
    boolean isEmpty(ItemStack stack);

    // ================= 取出来（0.11 ZF78 补：右键倒流体）=================

    /**
     * 容器里现在装着什么（空容器返回 {@link FluidStack#EMPTY}）。
     *
     * <p>ZF78 加的：操作器要支持「手上拿容器右键 ⇒ 倒进机器」，机器就得先知道
     * 容器里有什么、再决定倒多少 —— 这就是灌装（{@link #fill}）的反方向。</p>
     */
    FluidStack contents(ItemStack stack);

    /**
     * 从容器里取出最多 {@code maxAmount} mB（<b>允许只取一部分</b>：倒的时候按对面罐的余量取）。
     *
     * @return 取出来的流体（{@link FluidStack#EMPTY} = 空容器 / 一点没取出）
     */
    FluidStack drain(ItemStack stack, int maxAmount);
}
