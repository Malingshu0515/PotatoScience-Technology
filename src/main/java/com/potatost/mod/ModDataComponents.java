package com.potatost.mod;

import com.mojang.serialization.Codec;

import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.codec.ByteBufCodecs;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * 数据组件注册（0.11 ZF122）—— 本工程**第一次用 1.21 的 DataComponent**。
 *
 * <p>为什么星仪图之章要一个组件、而不是像星轨坠那样用网络包：
 * <b>组件是跟着物品栈自动同步的</b>（`networkSynchronized` 那一行就是干这个的）。
 * 天空盒编号存在书自己的 NBT 里 ⇒ ① 存档重启后还在；② 换到别的书可以是别的天；
 * ③ 客户端读手上那本书就能知道该画哪张天 —— **一个自定义包都不用发**。</p>
 *
 * <p>⚠ 本类必须在模组构造期被碰一下（档案 §4.72）：见 `PotatoST` 构造器里
 * {@code ModDataComponents.DATA_COMPONENTS.register(modEventBus)} 那一行。</p>
 */
public class ModDataComponents {

    public static final DeferredRegister<DataComponentType<?>> DATA_COMPONENTS =
            DeferredRegister.create(Registries.DATA_COMPONENT_TYPE, PotatoST.MODID);

    /**
     * 星仪图当前选中的天空盒编号：<b>0 = 原版</b>，1~4 = 四张星图。
     *
     * <p>{@code persistent(Codec.INT)} ⇒ 存进物品 NBT；
     * {@code networkSynchronized(ByteBufCodecs.VAR_INT)} ⇒ 自动同步给客户端。</p>
     */
    public static final DeferredHolder<DataComponentType<?>, DataComponentType<Integer>> SKY_INDEX =
            DATA_COMPONENTS.register("sky_index", () -> DataComponentType.<Integer>builder()
                    .persistent(Codec.INT)
                    .networkSynchronized(ByteBufCodecs.VAR_INT)
                    .build());

    private ModDataComponents() {
    }
}
