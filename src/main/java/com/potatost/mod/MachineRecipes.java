package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;

/**
 * 机器配方目录（0.10 ZF19 新增）。
 *
 * <p><b>为什么要有这一层：</b>本项目的机器配方一直写在 Java 里（{@link MicroCrusherRecipes}、
 * 电解器/晒盐机/灌装机的常量），JEI 看不到。要让"现在和以后"的机器都能被 JEI 查到，
 * 就不能每加一台机器就抄一遍 JEI 代码 —— 所以把配方**先归一成与展示无关的数据**，
 * JEI 插件只做"把这份数据画出来"。</p>
 *
 * <p><b>红线：本类里一个 JEI 类型都不许出现。</b>
 * JEI 是 {@code compileOnly} 依赖，玩家完全可能没装；一旦本类引用了 JEI 的类，
 * 没装 JEI 的客户端在加载本类时就会 {@code NoClassDefFoundError}。
 * JEI 相关的代码只允许待在 {@code com.potatost.mod.client.jei} 包下的两个文件里。</p>
 *
 * <p><b>加一台新机器要做什么：</b>① 在 {@link #build()} 里把它的配方塞进这个列表；
 * ② 在 {@code PotatoSTJeiPlugin.MACHINES} 里加一行机器 id（机器 id 必须等于方块注册名，
 * 标题直接复用 {@code block.potato_s_t.<id>}）。除此之外不用碰 JEI 代码。</p>
 *
 * <p><b>⚠ 静态初始化的雷（§4.1）：</b>本类读 {@code ModFluids.*.get()}、{@code ModItems.*.get()}，
 * 所以**只能懒加载** —— 写成 {@code static final} 字段会在注册完成前触发
 * {@code Trying to access unbound value} 启动崩溃。</p>
 */
public final class MachineRecipes {

    /** 一种流体的用量。 */
    public record FluidAmount(Fluid fluid, int mb) {
    }

    /**
     * 一条"机器配方"的展示形态。
     *
     * @param machineId 机器 id，等于方块注册名（标题复用 {@code block.potato_s_t.<id>}）
     * @param itemIn    物品输入；空列表 = 这一步没有物品输入
     * @param itemOut   物品输出
     * @param fluidIn   流体输入
     * @param fluidOut  流体输出
     * @param info      展示在配方下方的说明行（耗时 / 耗电 / 产出范围…）
     */
    public record Entry(String machineId,
                        List<ItemStack> itemIn,
                        List<ItemStack> itemOut,
                        List<FluidAmount> fluidIn,
                        List<FluidAmount> fluidOut,
                        List<Component> info) {
    }

    /** 懒加载；null = 还没建过（理由见类注释） */
    private static List<Entry> entries;

    private MachineRecipes() {
    }

    /** 全部机器配方。第一次调用时才建表。 */
    public static List<Entry> all() {
        if (entries == null) {
            entries = build();
        }
        return entries;
    }

    private static List<Entry> build() {
        List<Entry> out = new ArrayList<>();

        buildMicroCrusher(out);
        buildElectrolyzer(out);
        buildSaltDryer(out);
        buildFillingMachine(out);
        buildHydraulicPress(out);
        buildSaltDecomposer(out);
        buildBlastFurnace(out);
        buildAlloySmelter(out);
        buildHydrodesulfurizationChamber(out);
        buildAirSeparator(out);
        buildAmmoniaSynthesisChamber(out);

        return List.copyOf(out);
    }

    /**
     * ⑩ 空气分离器（0.11 ZF97 新增）—— 用户原话「空气分离器：gui只有两个储罐（不接受被灌入 只能泵出）
     * 一个工作指示灯 储能5000fe 耗能 200fe/t 30s产出 8mB 氮气 2mB氧气」。
     *
     * <p>没有物品输入（原料是空气）⇒ {@code itemIn} 空；两个产物都是<b>流体输出</b>
     * （氮气 8 mB / 氧气 2 mB），JEI 会把它们画成两根罐柱。</p>
     */
    private static void buildAirSeparator(List<Entry> out) {
        out.add(new Entry("air_separator",
                List.of(), List.of(),
                List.of(),
                List.of(new FluidAmount(ModFluids.NITROGEN.get(), AirSeparatorBlockEntity.NITROGEN_PER_BATCH),
                        new FluidAmount(ModFluids.OXYGEN.get(), AirSeparatorBlockEntity.OXYGEN_PER_BATCH)),
                List.of(Component.translatable("gui.potato_s_t.jei.time",
                                AirSeparatorBlockEntity.DURATION_TICKS / 20),
                        Component.translatable("gui.potato_s_t.jei.energy",
                                AirSeparatorBlockEntity.ENERGY_PER_TICK))));
    }

    /**
     * ⑪ 氨气组成室（0.11 ZF97 新增）—— 用户原话「每t消耗1mB氮气 1mB氢气 200Fe/t 产出1mB氨气
     * 催化剂不消耗」。
     *
     * <p>这是本工程**第一条"每 tick 连续、两种流体进、一种流体出"**的配方 ⇒ 说明行用
     * {@code jei.continuous}（与电解器同一句），并如实写出催化剂槽要放铁粉、而且不消耗。</p>
     */
    private static void buildAmmoniaSynthesisChamber(List<Entry> out) {
        out.add(new Entry("ammonia_synthesis_chamber",
                List.of(new ItemStack(ModItems.IRON_POWDER.get())),
                List.of(),
                List.of(new FluidAmount(ModFluids.NITROGEN.get(),
                                AmmoniaSynthesisChamberBlockEntity.NITROGEN_PER_TICK),
                        new FluidAmount(ModFluids.HYDROGEN.get(),
                                AmmoniaSynthesisChamberBlockEntity.HYDROGEN_PER_TICK)),
                List.of(new FluidAmount(ModFluids.AMMONIA.get(),
                        AmmoniaSynthesisChamberBlockEntity.AMMONIA_PER_TICK)),
                List.of(Component.translatable("gui.potato_s_t.jei.continuous"),
                        Component.translatable("gui.potato_s_t.jei.energy",
                                AmmoniaSynthesisChamberBlockEntity.ENERGY_PER_TICK),
                        Component.translatable("gui.potato_s_t.jei.catalyst"))));
    }

    /**
     * ⑨ 加氢脱硫反应仓（0.11 ZF96 新增）—— 用户原话「加一个 加氢脱硫反应仓 GUI 一个氢气罐
     * 左侧放沥青 每16个沥青 消耗1000mB氢气 10s  产出一个 硫」。
     *
     * <p>一条配方，四样东西各归各位：<b>物品输入 = 16 个沥青</b>（数量直接画在图标上）、
     * <b>流体输入 = 1000 mB 氢气</b>（会画成一根罐柱）、<b>物品输出 = 1 个硫</b>、
     * 说明行 = 耗时 + <b>"不耗电"</b>。</p>
     *
     * <p><b>为什么明写"不耗电"</b>：本工程别的机器说明行里都有「%s FE/t」，
     * 少了那一行玩家会以为是漏写、或者猜它耗电。这台机器的能耗数用户没给 ⇒ 本轮不耗电，
     * 所以如实写一行 {@code gui.potato_s_t.jei.no_energy}（不是占位、不是待补）。</p>
     */
    private static void buildHydrodesulfurizationChamber(List<Entry> out) {
        out.add(new Entry("hydrodesulfurization_chamber",
                List.of(new ItemStack(ModItems.BITUMEN.get(),
                        HydrodesulfurizationChamberBlockEntity.BITUMEN_PER_OPERATION)),
                List.of(new ItemStack(ModItems.SULFUR.get(),
                        HydrodesulfurizationChamberBlockEntity.SULFUR_PER_OPERATION)),
                List.of(new FluidAmount(ModFluids.HYDROGEN.get(),
                        HydrodesulfurizationChamberBlockEntity.HYDROGEN_PER_OPERATION)),
                List.of(),
                List.of(Component.translatable("gui.potato_s_t.jei.time",
                                HydrodesulfurizationChamberBlockEntity.DURATION_TICKS / 20),
                        Component.translatable("gui.potato_s_t.jei.no_energy"))));
    }

    /**
     * ⑧ 合金冶炼炉（0.10 ZF62 新增）—— 这台机器 ZF49 立起来时用户说「先不做配方」，
     * ZF62 给了第一条：「铝+钛+银 30s 5800fe/t → 轻质钛合金」。
     *
     * <p><b>三个输入槽怎么展示：</b>{@code MachineRecipeCategory} 会把 {@code itemIn} 里每个栈
     * 各画一个输入槽（双输入的电力高炉就是这么做的）⇒ 三个原料并排画出来，一眼能看出"要三样"。</p>
     *
     * <p>输入按 {@code c:ingots/<材料>} 标签认，但这里**不展开标签里的所有锭** ——
     * 三个输入槽是"同时需要"的关系，展开成多行会变成"每种锭都能当三种用"，反而误导。
     * 画我们自己的三种锭（铝/钛/银）就够。</p>
     *
     * <p><b>ZF64：说明行里那条"输入按通用锭标签（c:ingots）判定…"被用户删了</b> ——
     * 原话「所有的这种文字可以删掉 给玩家看没必要列出来 还占空间 不美观」。
     * 现在只留 <b>耗时 / 耗电</b> 两行（客观数值），标签怎么认属于实现细节，玩家不需要知道。</p>
     */
    private static void buildAlloySmelter(List<Entry> out) {
        for (AlloySmelterRecipes.Smelt smelt : AlloySmelterRecipes.all()) {
            List<ItemStack> inputs = new ArrayList<>();
            for (AlloySmelterRecipes.Need need : smelt.needs()) {
                for (var holder : net.minecraft.core.registries.BuiltInRegistries.ITEM
                        .getTagOrEmpty(need.tag())) {
                    inputs.add(new ItemStack(holder.value(), need.count()));
                    break;                               // 每种原料只画"我们自己的那一个"（见方法注释）
                }
            }
            // 0.11 ZF111：消耗品（深层钴矿石 / 末影水晶）也画出来 —— 它们要放进机器的 2 个消耗槽。
            // 不加新说明行（说明行只放客观数值那条规矩、加一行就多一个语言键），
            // 靠 tooltip 与界面上的「消耗槽」标签告诉玩家放哪儿。
            for (AlloySmelterRecipes.Consume consume : smelt.consumes()) {
                inputs.add(new ItemStack(consume.item(), consume.count()));
            }
            List<Component> info = List.of(
                    Component.translatable("gui.potato_s_t.jei.time", smelt.durationTicks() / 20),
                    Component.translatable("gui.potato_s_t.jei.energy", smelt.energyPerTick()));
            out.add(new Entry("alloy_smelter",
                    List.copyOf(inputs),
                    List.of(smelt.result().copy()),
                    List.of(), List.of(),
                    info));
        }
    }

    /**
     * ⑦ 电力高炉（0.10 ZF45 新增）。
     *
     * <p><b>为什么要给高炉做 JEI：</b>两条 ZF45 的新配方是<b>双输入</b>的
     * （铁粉 + 碳粉 → 高碳钢、铁粉 + 沙砾 → 磁铁），玩家在机器面板里看不到任何提示 ——
     * 不加 JEI 就只能靠说明文字或者试。这里把三条来源都摊开：</p>
     * <ul>
     *   <li>本模组的粗矿（×2）、矿石方块（3~6，逐个随机）；</li>
     *   <li>沙子 → 硅；</li>
     *   <li>两条双输入配方。</li>
     * </ul>
     *
     * <p><b>为什么不列原版高炉那 24 条：</b>那是"高炉本来就会的东西"，列出来会把
     * 本模组自己的矿物处理淹掉；改成一条说明行（{@code gui.potato_s_t.jei.ebf_vanilla}）如实告诉玩家。</p>
     */
    private static void buildBlastFurnace(List<Entry> out) {
        List<Component> single = List.of(
                Component.translatable("gui.potato_s_t.jei.time", ElectricBlastFurnaceBlockEntity.DURATION_TICKS / 20),
                Component.translatable("gui.potato_s_t.jei.energy_per_item",
                        ElectricBlastFurnaceBlockEntity.ENERGY_PER_ITEM),
                Component.translatable("gui.potato_s_t.jei.ebf_vanilla"));

        for (Map.Entry<Item, BlastFurnaceRecipes.Recipe> e : BlastFurnaceRecipes.rawRecipes().entrySet()) {
            out.add(new Entry("electric_blast_furnace",
                    List.of(new ItemStack(e.getKey())),
                    List.of(new ItemStack(e.getValue().output(), e.getValue().count())),
                    List.of(), List.of(), single));
        }
        for (Map.Entry<Block, BlastFurnaceRecipes.Recipe> e : BlastFurnaceRecipes.oreRecipes().entrySet()) {
            List<Component> info = List.of(
                    Component.translatable("gui.potato_s_t.jei.time", ElectricBlastFurnaceBlockEntity.DURATION_TICKS / 20),
                    Component.translatable("gui.potato_s_t.jei.energy_per_item",
                            ElectricBlastFurnaceBlockEntity.ENERGY_PER_ITEM),
                    Component.translatable("gui.potato_s_t.jei.range",
                            BlastFurnaceRecipes.ORE_MIN, BlastFurnaceRecipes.ORE_MAX));
            out.add(new Entry("electric_blast_furnace",
                    List.of(new ItemStack(e.getKey().asItem())),
                    List.of(new ItemStack(e.getValue().output(), BlastFurnaceRecipes.ORE_MIN)),
                    List.of(), List.of(), info));
        }
        out.add(new Entry("electric_blast_furnace",
                List.of(new ItemStack(Items.SAND), new ItemStack(Items.RED_SAND)),
                List.of(new ItemStack(ModItems.SILICON.get())),
                List.of(), List.of(), single));
        // 双输入：两个输入槽都画出来（JEI 那侧会自动把输入槽数撑到 2）
        for (BlastFurnaceRecipes.Pair pair : BlastFurnaceRecipes.pairs()) {
            out.add(new Entry("electric_blast_furnace",
                    List.of(new ItemStack(pair.a()), new ItemStack(pair.b())),
                    List.of(new ItemStack(pair.output(), pair.count())),
                    List.of(), List.of(), single));
        }
    }

    /**
     * ⑥ 盐分解构器：烧海盐 → 氯化钠（0.10 ZF32）。
     *
     * <p><b>怎么展示"概率产出"</b>：JEI 的分类只认"输入/输出槽 + 说明行"，
     * 没有概率条这种东西。所以这里就**如实写进说明行**（60% 返还 / 5% 粗矿 / 100% 氯化钠），
     * 输出槽只放<b>必定产出</b>的氯化钠 —— 另外两样是概率性的，画成"必然输出"会骗人。
     * 海盐返还与 5 种…（7 种）粗矿的可能性都写在说明里，玩家看得到。</p>
     */
    private static void buildSaltDecomposer(List<Entry> out) {
        List<Component> info = List.of(
                Component.translatable("gui.potato_s_t.jei.time", SaltDecomposerRecipes.DURATION_TICKS / 20),
                Component.translatable("gui.potato_s_t.jei.energy", SaltDecomposerRecipes.ENERGY_PER_TICK),
                Component.translatable("gui.potato_s_t.jei.salt_return",
                        SaltDecomposerRecipes.SALT_RETURN_PERCENT, SaltDecomposerRecipes.SALT_INPUT),
                Component.translatable("gui.potato_s_t.jei.raw_ore_chance",
                        SaltDecomposerRecipes.RAW_ORE_PERCENT));
        out.add(new Entry("salt_decomposer",
                List.of(new ItemStack(ModItems.SEA_SALT.get(), SaltDecomposerRecipes.SALT_INPUT)),
                List.of(new ItemStack(ModItems.SODIUM_CHLORIDE.get())),
                List.of(), List.of(),
                info));
    }

    /**
     * ⑤ 液压机：矿物锭 → 板材（0.10 ZF30）。
     *
     * <p><b>为什么把标签展开成多条：</b>{@code MachineRecipeCategory} 只吃 {@code List<ItemStack>}
     * 里的**单个**栈（{@code addItemStack} 一个槽一个物品），而一条配方要展示"这些锭都行"。
     * 与其改 JEI 排版，不如**把标签里的每个物品各出一行** —— 玩家看到的就是
     * "铁锭→铁板、铜锭→铜板…"这样最直白的并列关系，也顺带把"别的 mod 的锭也能用"展示出来。
     * 标签为空时（理论上不会）退回兜底物品，保证至少有一行。</p>
     */
    private static void buildHydraulicPress(List<Entry> out) {
        for (PressRecipes.Recipe recipe : PressRecipes.all()) {
            List<Component> info = List.of(
                    Component.translatable("gui.potato_s_t.jei.time", PressRecipes.DURATION_TICKS / 20),
                    Component.translatable("gui.potato_s_t.jei.energy", PressRecipes.ENERGY_PER_TICK));
            List<ItemStack> inputs = new ArrayList<>();
            if (recipe.inputTag() != null) {
                for (var holder : net.minecraft.core.registries.BuiltInRegistries.ITEM
                        .getTagOrEmpty(recipe.inputTag())) {
                    inputs.add(new ItemStack(holder.value(), recipe.inputCount()));
                }
            }
            if (inputs.isEmpty()) {
                // 没有通用标签（例如沥青）或标签为空 ⇒ 用兜底物品；数量照配方（JEI 图标上会显示 12）
                inputs.add(new ItemStack(recipe.fallback(), recipe.inputCount()));
            }
            for (ItemStack input : inputs) {
                out.add(new Entry("hydraulic_press",
                        List.of(input),
                        List.of(recipe.createOutput()),
                        List.of(), List.of(),
                        info));
            }
        }
    }

    /** ① 微型粉碎机：输入 → 产物。配方本体仍在 {@link MicroCrusherRecipes}，这里只做转换。 */
    private static void buildMicroCrusher(List<Entry> out) {
        for (MicroCrusherRecipes.DisplayGroup group : MicroCrusherRecipes.displayGroups()) {
            MicroCrusherRecipes.Crush crush = group.crush();
            List<Component> info = new ArrayList<>();
            info.add(Component.translatable("gui.potato_s_t.jei.time", crush.durationTicks() / 20));
            info.add(Component.translatable("gui.potato_s_t.jei.energy", crush.energyPerTick()));
            if (crush.countMin() != crush.countMax()) {
                info.add(Component.translatable("gui.potato_s_t.jei.range", crush.countMin(), crush.countMax()));
            }
            out.add(new Entry("micro_crusher",
                    group.inputs(),
                    List.of(new ItemStack(crush.result(), crush.countMin())),
                    List.of(), List.of(),
                    List.copyOf(info)));
        }
    }

    /**
     * ② 电解器：两个配方，都是"每 tick 持续产出"（所以没有"耗时"，只有每 tick 的量）。
     *
     * <p>纯水制氧：水 10 mB/t → 氧气 3 + 氢气 6，1000 FE/t。<br>
     * 加海盐制氯：水 10 mB/t + 海盐（每 500 mB 水耗 1 个）→ 氯气 3 + 氢气 6，1000 FE/t。</p>
     */
    private static void buildElectrolyzer(List<Entry> out) {
        List<Component> oxygenInfo = List.of(
                Component.translatable("gui.potato_s_t.jei.energy", ElectrolyzerBlockEntity.ENERGY_PER_TICK_OXYGEN),
                Component.translatable("gui.potato_s_t.jei.continuous"));
        out.add(new Entry("electrolyzer",
                List.of(), List.of(),
                List.of(new FluidAmount(Fluids.WATER, ElectrolyzerBlockEntity.WATER_PER_TICK)),
                List.of(new FluidAmount(ModFluids.OXYGEN.get(), ElectrolyzerBlockEntity.OXYGEN_PER_TICK),
                        new FluidAmount(ModFluids.HYDROGEN.get(), ElectrolyzerBlockEntity.HYDROGEN_PER_TICK)),
                oxygenInfo));

        List<Component> chlorineInfo = List.of(
                Component.translatable("gui.potato_s_t.jei.energy", ElectrolyzerBlockEntity.ENERGY_PER_TICK_CHLORINE),
                Component.translatable("gui.potato_s_t.jei.continuous"),
                Component.translatable("gui.potato_s_t.jei.per_salt", ElectrolyzerBlockEntity.WATER_PER_SALT));
        out.add(new Entry("electrolyzer",
                List.of(new ItemStack(ModItems.SEA_SALT.get())), List.of(),
                List.of(new FluidAmount(Fluids.WATER, ElectrolyzerBlockEntity.WATER_PER_TICK)),
                List.of(new FluidAmount(ModFluids.CHLORINE.get(), ElectrolyzerBlockEntity.CHLORINE_PER_TICK),
                        new FluidAmount(ModFluids.HYDROGEN.get(), ElectrolyzerBlockEntity.HYDROGEN_PER_TICK)),
                chlorineInfo));
    }

    /**
     * ③ 晒盐机：没有输入，被动很慢、通电快。
     *
     * <p>通电时间用 {@code PROGRESS_MAX / POWERED_SPEED} 算出来（而不是写死 400），
     * 这样以后调常数不会让 JEI 里的数字和实际对不上。</p>
     */
    private static void buildSaltDryer(List<Entry> out) {
        out.add(new Entry("salt_dryer",
                List.of(), List.of(new ItemStack(ModItems.SEA_SALT.get())),
                List.of(), List.of(),
                List.of(Component.translatable("gui.potato_s_t.jei.time",
                                SaltDryerBlockEntity.PROGRESS_MAX / 20),
                        Component.translatable("gui.potato_s_t.jei.passive"))));
        out.add(new Entry("salt_dryer",
                List.of(), List.of(new ItemStack(ModItems.SEA_SALT.get())),
                List.of(), List.of(),
                List.of(Component.translatable("gui.potato_s_t.jei.time",
                                SaltDryerBlockEntity.PROGRESS_MAX / SaltDryerBlockEntity.POWERED_SPEED / 20),
                        Component.translatable("gui.potato_s_t.jei.energy", SaltDryerBlockEntity.ENERGY_PER_TICK))));
    }

    /**
     * ④ 灌装机：空罐 + 气体 → 灌好的罐。三种气体各出一条。
     *
     * <p>进口和出口都是"高压气罐"同一个物品（进去是空的、出来装了气），
     * JEI 里两边图标一样是**如实反映**，靠说明行区分。</p>
     */
    private static void buildFillingMachine(List<Entry> out) {
        // 0.11 ZF97：气体从 3 种加到 5 种（+氮气/氨气）—— 不列出来的话，玩家在 JEI 里
        // 看不到"气罐也能装氮气/氨气"，只能靠试。
        // 0.11 ZF100：再加二氧化碳（燃烧反应室的输出气）⇒ 6 种。
        for (Fluid gas : List.of(ModFluids.OXYGEN.get(), ModFluids.HYDROGEN.get(), ModFluids.CHLORINE.get(),
                ModFluids.NITROGEN.get(), ModFluids.AMMONIA.get(), ModFluids.CARBON_DIOXIDE.get())) {
            out.add(new Entry("filling_machine",
                    List.of(new ItemStack(ModItems.HIGH_PRESSURE_TANK.get())),
                    List.of(new ItemStack(ModItems.HIGH_PRESSURE_TANK.get())),
                    List.of(new FluidAmount(gas, FillingMachineBlockEntity.FILL_RATE)),
                    List.of(),
                    List.of(Component.translatable("gui.potato_s_t.jei.continuous"),
                            Component.translatable("gui.potato_s_t.jei.energy_per_tank",
                                    FillingMachineBlockEntity.ENERGY_PER_TANK))));
        }
    }
}
