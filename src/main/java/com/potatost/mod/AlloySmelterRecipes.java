package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

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
 *
 * <p><b>0.11 ZF111 新增第三条配方（星璨钢锭）+ 一个新概念「消耗品」</b>。用户原话：
 * 「星璨钢加合金冶炼配方 下界合金锭+4高碳钢+钴锭+银锭+铜锭 再消耗1个深层钴矿石
 * 1个末影水晶 产出三个星璨钢钢 12000FE/t」。两件事同时发生：</p>
 * <ul>
 *   <li><b>{@code Smelt} 多了 {@code consumes} 字段</b>（{@link Consume}）—— 那两样东西
 *       要放进机器上一直锁着的 <b>2 个消耗槽</b>（ZF49 立的规矩：「以后出类似于沉浸电弧炉
 *       石墨电极的东西」时再放开，见 {@code AlloySmelterBlockEntity} 的槽位注释）；</li>
 *   <li><b>每 tick 耗电第一次出现"不是 800"的配方</b>（12000）⇒ 方块实体不能再读
 *       {@code ENERGY_PER_TICK} 那个全局常量，改成读 {@code smelt.energyPerTick()}
 *       （其实 ZF62 写表时就说过"多条配方各带各的"，只是只有一条配方时没人去动它）。</li>
 * </ul>
 *
 * <p>⚠ <b>时长用户没给</b>：沿用本机规格 <b>30 秒（600 tick）</b> ⇒ 一件总耗电
 * <b>12000 × 600 = 7,200,000 FE</b>。这个数是"按本机规格补的"，不是用户说的 ——
 * 要改就改这条配方最后一个参数（或者 {@link #DURATION_TICKS}）。</p>
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

    /**
     * 全表里**最贵**的一条配方每 tick 要多少电（0.11 ZF111 新增）。
     *
     * <p><b>为什么要单独列一个纯 int 常量</b>：方块实体里那条 ZF42 静态守卫
     * （"单 tick 耗电绝不能超过储能"）跑在 <b>static 初始化块</b>里 —— 那一刻
     * {@link #all()} 还不能碰（懒加载就是为了躲 §4.1 那个"注册还没完成就取物品"的启动崩溃）。
     * 所以最贵的那个数在这里写成字面量：守卫读它、配方表也读它，两边永远一致。</p>
     */
    public static final int MAX_ENERGY_PER_TICK = 12_000;

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
     * 一条**消耗品**需求（0.11 ZF111 新增）：放在机器那 2 个消耗槽里的东西。
     *
     * <p>与 {@link Need} 的区别：{@code Need} 走 {@code c:ingots/<材料>} 标签（别的 mod 的
     * 同名锭也算数），消耗品按<b>具体物品</b>认 —— 用户点的就是"1 个深层钴矿石 + 1 个末影水晶"
     * 这两样具体东西，没说要让别的 mod 的钴矿顶替。要放开就把这里的 {@code Item} 换成
     * {@code TagKey}（一处改动 + 匹配函数一行）。</p>
     */
    public record Consume(Item item, int count) {
    }

    /**
     * 一条合金配方。
     *
     * @param needs         输入需求（每种各要几个；<b>互不相同</b>——判定时按"每种原料在输入槽里都有够"算）
     * @param consumes      消耗品需求（0.11 ZF111 起；没有就写 {@code List.of()}）
     * @param result        产物（个数写在栈里）
     * @param durationTicks 一轮多少 tick
     * @param energyPerTick 每 tick 耗电
     */
    public record Smelt(List<Need> needs, List<Consume> consumes, ItemStack result,
                        int durationTicks, int energyPerTick) {

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
                List.of(),
                new ItemStack(ModItems.LIGHT_TITANIUM_ALLOY.get()),
                DURATION_TICKS, ENERGY_PER_TICK));

        // ② 轻质钛合金 + 高碳钢 + 镍锭 → 1 硬质钛合金（0.11 ZF104，用户口述）
        //    用户原话：「合金冶炼炉配方；轻质钛合金+高碳钢+镍锭」⇒ 三种料各 1 个。
        //    时长/能耗沿用本机器的规格（30 秒、800 FE/t），用户没给新数。
        list.add(new Smelt(
                List.of(new Need(ingot("titanium_alloy"), 1),
                        new Need(ingot("steel"), 1),
                        new Need(ingot("nickel"), 1)),
                List.of(),
                new ItemStack(ModItems.HARD_TITANIUM_ALLOY.get()),
                DURATION_TICKS, ENERGY_PER_TICK));

        // ③ 下界合金锭 + 4 高碳钢 + 钴锭 + 银锭 + 铜锭，再消耗 1 深层钴矿石 + 1 末影水晶
        //    → 3 星璨钢锭（0.11 ZF111，用户口述）
        //    用户原话：「星璨钢加合金冶炼配方 下界合金锭+4高碳钢+钴锭+银锭+铜锭 再消耗1个深层钴矿石
        //              1个末影水晶 产出三个星璨钢钢 12000FE/t」
        //    ⚠ 时长用户**没给** ⇒ 沿用本机规格 30 秒（600 tick）⇒ 一件 12000 × 600 = 7,200,000 FE。
        //    下界合金锭与铜锭走原版/NeoForge 提供的 c:ingots/netherite、c:ingots/copper
        //    （已用 javap + 解包核过：neoforge 的 data/c/tags/item/ingots/ 里有这两个文件）。
        list.add(new Smelt(
                List.of(new Need(ingot("netherite"), 1),
                        new Need(ingot("steel"), 4),
                        new Need(ingot("cobalt"), 1),
                        new Need(ingot("silver"), 1),
                        new Need(ingot("copper"), 1)),
                List.of(new Consume(PotatoSTOres.DEEPSLATE_COBALT_ORE.get().asItem(), 1),
                        new Consume(Items.END_CRYSTAL, 1)),
                new ItemStack(ModArmorItems.STAR_STEEL_INGOT.get(), 3),
                DURATION_TICKS, MAX_ENERGY_PER_TICK));

        table = List.copyOf(list);
    }
}
