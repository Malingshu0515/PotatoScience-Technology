package com.potatost.mod;

import com.mojang.serialization.Codec;

import net.minecraft.advancements.CriterionTrigger;
import net.minecraft.advancements.critereon.PlayerTrigger;
import net.minecraft.advancements.critereon.SimpleCriterionTrigger;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * 「电力高炉装配成功」这个进度判据的触发器（0.13 ZF162 新立）。
 *
 * <p><b>为什么要有它</b>：进度 {@code potato_s_t:blast_furnace}（标题「砌一座高炉」）原来靠
 * {@code minecraft:inventory_changed} + 物品 {@code potato_s_t:electric_blast_furnace} 完成 ——
 * 而 ZF162 按用户要求把**物品形态整个删掉了**（「物品形式的电力高炉……有bug没必要修了」），
 * 那条判据就永远不可能完成。电力高炉真正发生的事情是**「围着原版高炉把 3×3×3 搭起来、空手
 * Shift 右键点成型」**，原版没有任何触发器能表达它（{@code minecraft:location} 只看玩家脚下那一格，
 * 而高炉/部件格都是实心方块，站不进去）⇒ 只能自建一个触发器。</p>
 *
 * <p><b>为什么复用 {@link PlayerTrigger.TriggerInstance}</b>：本判据不需要任何条件
 * （装配成功 = 装配成功，不看玩家状态）。那个 record 是 {@code SimpleCriterionTrigger.SimpleInstance}
 * 的公开实现、恰好"零条件"，直接拿它当判据类型即可 —— 省一份自己的 record 与它的 codec，
 * 而 JSON 里 {@code "conditions": {}} 就能解析。</p>
 *
 * <p>触发点只有一处：{@link BlastFurnaceAssembly#form} 的两个调用方（原版高炉那条主路 +
 * 老存档裸控制器那条老路），装配真的成功之后各触发一次。</p>
 */
public final class EbfFormedTrigger extends SimpleCriterionTrigger<PlayerTrigger.TriggerInstance> {

    /** 触发器的注册器（vanilla 的 {@code BuiltInRegistries.TRIGGER_TYPES}，原版也是这样登记的）。 */
    public static final DeferredRegister<CriterionTrigger<?>> TRIGGERS =
            DeferredRegister.create(BuiltInRegistries.TRIGGER_TYPES, PotatoST.MODID);

    public static final DeferredHolder<CriterionTrigger<?>, EbfFormedTrigger> EBF_FORMED =
            TRIGGERS.register("ebf_formed", EbfFormedTrigger::new);

    @Override
    public Codec<PlayerTrigger.TriggerInstance> codec() {
        return PlayerTrigger.TriggerInstance.CODEC;
    }

    /** 给这个玩家把这条进度判据记一次（没在听这条判据的玩家什么也不会发生）。 */
    public void trigger(ServerPlayer player) {
        this.trigger(player, instance -> true);
    }
}
