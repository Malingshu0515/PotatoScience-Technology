package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/**
 * 合金冶炼炉的配方表（0.10 ZF62 新增 —— 这台机器从 ZF49 立起来之后一直"先不做配方"）。
 *
 * <p>用户原话：「<b>铝+钛+银在合金冶炼炉 30s 5800fe/t产出一个 轻质钛合金 用钛锭的贴图</b>」
 * ⇒ 一条配方：铝锭 ×1 + 钛锭 ×1 + 银锭 ×1 → 轻质钛合金 ×1，30 秒（600 tick）、每 tick 5800 FE。
 * 一件总耗电 = 5800 × 600 = <b>3,480,000 FE</b>（照字面值实现，没替他"顺手调小"）。</p>
 *
 * <p><b>为什么是 Java 表而不是数据包配方</b>：与 {@link MicroCrusherRecipes} 同一个理由 ——
 * 自定义 {@code RecipeType} 要额外注册序列化器 + 每个配方一份 JSON，而 JEI 展示
 * 靠的是 {@link MachineRecipes}（与配方存在哪无关）。</p>
 *
 * <p><b>输入一律走 {@code c:ingots/<材料>} 标签</b>（长期规则：锭默认兼容别的 mod）：
 * 铝 / 钛 / 银三种锭的标签由 {@code GenCommonTags.py} 生成，我们自己的锭也在里面
 * ⇒ 别的 mod 的铝锭/钛锭/银锭一样能烧。</p>
 *
 * <p><b>⚠ 静态初始化的雷（§4.1）</b>：产物读 {@code ModItems.LIGHT_TITANIUM_ALLOY.get()}，
 * 所以整张表**懒加载**（第一次查询时才建）——写成 {@code static final} 会在注册完成前
 * 触发 {@code Trying to access unbound value} 启动崩溃。</p>
 */
public final class AlloySmelterRecipes {

    /** 一轮 30 秒（用户指定）。 */
    public static final int DURATION_TICKS = 30 * 20;

    /**
     * 工作时每 tick 的耗电。
     *
     * <p><b>0.10 ZF63 由用户改的数</b>：ZF62 先按他最早给的 5800 FE/t 实现
     * （一件 348 万 FE，而本模组低级发电机只有 100 FE/t ⇒ 要跑 9.7 小时，机器 32768 的缓冲
     * 只够 5.6 tick），我把这笔账算给他看之后，他的答复是「<b>行吧改成800</b>」
     * ⇒ 一件 = 800 × 600 = <b>480,000 FE</b>（缓冲里的电够跑 41 tick）。</p>
     */
    public static final int ENERGY_PER_TICK = 800;

    /** 原料标签：{@code c:ingots/<材料>}。 */
    private static TagKey<Item> ingot(String material) {
        return TagKey.create(Registries.ITEM,
                ResourceLocation.fromNamespaceAndPath("c", "ingots/" + material));
    }

    /**
     * 一条输入需求。
     *
     * @param tag   认这个标签（含我们自己的锭）
     * @param count 要几个
     */
    public record Need(TagKey<Item> tag, int count) {
    }

    /**
     * 一条合金配方。
     *
     * @param needs         输入需求（每种各要几个；<b>互不相同</b>——判定时按"每种原料在输入槽里都有够"算）
     * @param result        产物（个数写在栈里）
     * @param durationTicks 一轮多少 tick
     * @param energyPerTick 每 tick 耗电
     */
    public record Smelt(List<Need> needs, ItemStack result, int durationTicks, int energyPerTick) {

        /** 一轮总耗电（JEI 说明行用）。 */
        public long totalEnergy() {
            return (long) this.durationTicks * this.energyPerTick;
        }
    }

    private static List<Smelt> table;

    private AlloySmelterRecipes() {
    }

    /** 全部配方（懒加载，理由见类注释）。 */
    public static List<Smelt> all() {
        if (table == null) {
            build();
        }
        return table;
    }

    private static void build() {
        List<Smelt> list = new ArrayList<>();

        // ① 铝锭 + 钛锭 + 银锭 → 1 轻质钛合金，30s，5800 FE/t（0.10 ZF62，用户指定）
        list.add(new Smelt(
                List.of(new Need(ingot("aluminum"), 1),
                        new Need(ingot("titanium"), 1),
                        new Need(ingot("silver"), 1)),
                new ItemStack(ModItems.LIGHT_TITANIUM_ALLOY.get()),
                DURATION_TICKS, ENERGY_PER_TICK));

        // ② 轻质钛合金 + 高碳钢 + 镍锭 → 1 硬质钛合金（0.11 ZF104，用户口述）
        //    用户原话：「合金冶炼炉配方；轻质钛合金+高碳钢+镍锭」⇒ 三种料各 1 个。
        //    时长/能耗沿用本机器的规格（30 秒、800 FE/t），用户没给新数。
        list.add(new Smelt(
                List.of(new Need(ingot("titanium_alloy"), 1),
                        new Need(ingot("steel"), 1),
                        new Need(ingot("nickel"), 1)),
                new ItemStack(ModItems.HARD_TITANIUM_ALLOY.get()),
                DURATION_TICKS, ENERGY_PER_TICK));

        table = List.copyOf(list);
    }
}
