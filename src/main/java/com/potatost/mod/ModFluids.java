package com.potatost.mod;

import java.util.List;

import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.common.Tags;
import net.neoforged.neoforge.fluids.BaseFlowingFluid;
import net.neoforged.neoforge.fluids.FluidType;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.NeoForgeRegistries;

/**
 * 氧气 / 氢气 / 氯气 / **氮气** / **氨气** / **原油** / **分馏产物（柴油·石脑油·汽油·液化石油气）** 流体注册。
 *
 * <p>五种**气体**只注册流体本体与流体类型（供管道/储罐/JEI 使用）：
 *   - 没有 bucket 物品、没有可放置的液体方块（气体不该往地上倒）；
 *   - 以后想要气体桶/能倒进世界，再单独加 LiquidBlock + BucketItem + 资源。</p>
 *
 * <p><b>0.11 ZF97 加了两种气体</b>（氮气 / 氨气，两台新机器要用）：新加气体时
 * <b>四处一起改</b> —— ① 本文件的注册 + {@link #isGas} 正向白名单；②
 * {@code PotatoSTClient.registerFluidTextures} 的贴图注册；③ `data/c/tags/fluid/` 里的
 * 同名标签 + {@code gaseous.json} 追加两行；④ 四份 lang 的 {@code fluid_type.*} 键。</p>
 *
 * <p><b>原油（0.11 ZF73）不一样</b>：它有实体方块 {@link ModBlocks#CRUDE_OIL}（油田湖要装它，
 * 而且流体泵只认 {@code LiquidBlock} 实例），但不无限、也没有 {@code .bucket(...)} 映射
 * （原版空桶舀不走，只能被 {@link OilBucketItem} 舀）。</p>
 *
 * <p>贴图路径：assets/potato_s_t/textures/block/chlorine_still.png 等（16x16）。
 * <b>0.11 ZF85 起，贴图的"客户端注册"搬到了 {@code PotatoSTClient#onRegisterClientExtensions}</b>
 * （用 {@code RegisterClientExtensionsEvent}）—— 原先那 5 个 {@code initializeClient} 匿名覆盖
 * 在 NeoForge 21.1 里已经"弃用并标记为移除"，IDE 会当成报错。本文件从此**只做注册**，
 * 不引用任何客户端类。</p>
 *
 * <p>2026-09-13 配方改版：电解器产物由氧气改为氯气，本文件新增 chlorine。
 * 氧气保留注册不删（旧存档/管道里可能还有氧气，删掉会报缺注册）。</p>
 */
public class ModFluids {

    public static final DeferredRegister<FluidType> FLUID_TYPES =
            DeferredRegister.create(NeoForgeRegistries.Keys.FLUID_TYPES, PotatoST.MODID);
    public static final DeferredRegister<Fluid> FLUIDS =
            DeferredRegister.create(Registries.FLUID, PotatoST.MODID);

    // ================= 氧气 =================

    public static final DeferredHolder<FluidType, FluidType> OXYGEN_TYPE =
            FLUID_TYPES.register("oxygen", () -> new FluidType(FluidType.Properties.create()
                    .density(-25)      // 气体：负密度（方向语义=向上浮），纯风味属性
                    .viscosity(200)));

    public static final DeferredHolder<Fluid, BaseFlowingFluid.Source> OXYGEN =
            FLUIDS.register("oxygen", () -> new BaseFlowingFluid.Source(oxygenProperties()));
    public static final DeferredHolder<Fluid, BaseFlowingFluid.Flowing> FLOWING_OXYGEN =
            FLUIDS.register("flowing_oxygen", () -> new BaseFlowingFluid.Flowing(oxygenProperties()));

    private static BaseFlowingFluid.Properties oxygenProperties() {
        return new BaseFlowingFluid.Properties(OXYGEN_TYPE, OXYGEN, FLOWING_OXYGEN);
    }

    // ================= 氢气 =================

    public static final DeferredHolder<FluidType, FluidType> HYDROGEN_TYPE =
            FLUID_TYPES.register("hydrogen", () -> new FluidType(FluidType.Properties.create()
                    .density(-50)      // 比氧更轻
                    .viscosity(200)));

    public static final DeferredHolder<Fluid, BaseFlowingFluid.Source> HYDROGEN =
            FLUIDS.register("hydrogen", () -> new BaseFlowingFluid.Source(hydrogenProperties()));
    public static final DeferredHolder<Fluid, BaseFlowingFluid.Flowing> FLOWING_HYDROGEN =
            FLUIDS.register("flowing_hydrogen", () -> new BaseFlowingFluid.Flowing(hydrogenProperties()));

    private static BaseFlowingFluid.Properties hydrogenProperties() {
        return new BaseFlowingFluid.Properties(HYDROGEN_TYPE, HYDROGEN, FLOWING_HYDROGEN);
    }

    // ================= 氯气 =================

    public static final DeferredHolder<FluidType, FluidType> CHLORINE_TYPE =
            FLUID_TYPES.register("chlorine", () -> new FluidType(FluidType.Properties.create()
                    .density(-30)      // 气体：负密度
                    .viscosity(200)));

    public static final DeferredHolder<Fluid, BaseFlowingFluid.Source> CHLORINE =
            FLUIDS.register("chlorine", () -> new BaseFlowingFluid.Source(chlorineProperties()));
    public static final DeferredHolder<Fluid, BaseFlowingFluid.Flowing> FLOWING_CHLORINE =
            FLUIDS.register("flowing_chlorine", () -> new BaseFlowingFluid.Flowing(chlorineProperties()));

    private static BaseFlowingFluid.Properties chlorineProperties() {
        return new BaseFlowingFluid.Properties(CHLORINE_TYPE, CHLORINE, FLOWING_CHLORINE);
    }

    // ================= 原油（0.11 ZF73）=================

    /**
     * 原油：本工程**第一个有实体方块的流体**（3 种气体故意没有方块）。
     *
     * <p>参数按用户要求与岩浆对齐（已从原版 {@code LavaFluid} 源码核对：非超热维度下
     * {@code getTickDelay=30}、{@code getSlopeFindDistance=2}、{@code getDropOff=2}），
     * 并明确 {@code canConvertToSource(false)} —— 用户原话「原油不可以像水变成无限的！」。</p>
     *
     * <p>另外 {@code canHydrate(false)}：不设的话原油会把耕地润湿（NeoForge 默认 true）。</p>
     */
    public static final DeferredHolder<FluidType, FluidType> CRUDE_OIL_TYPE =
            FLUID_TYPES.register("crude_oil", () -> new FluidType(FluidType.Properties.create()
                    .density(800)               // 比水（1000）轻：风味属性
                    .viscosity(3000)            // 黏
                    .temperature(300)
                    .canConvertToSource(false)  // ★ 不能像水一样变无限
                    .canHydrate(false)          // ★ 不润湿耕地
                    .canExtinguish(false)       // 不灭火
                    .supportsBoating(false)));

    public static final DeferredHolder<Fluid, BaseFlowingFluid.Source> CRUDE_OIL =
            FLUIDS.register("crude_oil", () -> new BaseFlowingFluid.Source(crudeOilProperties()));
    public static final DeferredHolder<Fluid, BaseFlowingFluid.Flowing> FLOWING_CRUDE_OIL =
            FLUIDS.register("flowing_crude_oil",
                    () -> new BaseFlowingFluid.Flowing(crudeOilProperties()));

    /**
     * 原油的流动参数：与岩浆同值（tickRate 30 / slopeFindDistance 2 / levelDecreasePerBlock 2）。
     *
     * <p>⚠ <b>故意不调 {@code .bucket(...)}</b>：{@code BaseFlowingFluid.getBucket()} 在不设 bucket 时
     * 返回 {@code Items.AIR}，原版空桶走 {@code BucketPickup}（{@code LiquidBlock.pickupBlock}）
     * 就舀不走原油 —— 否则「一个原版空桶右键一下 = 一整桶 3000 mB 原油」会白送三倍。
     * 原油只能被 {@link OilBucketItem} 舀（用户规则）。</p>
     *
     * <p>方块由 {@link ModBlocks#CRUDE_OIL} 提供（供应商，不在这里 .get()，
     * 避免静态初始化期访问未绑定的注册项）。</p>
     */
    private static BaseFlowingFluid.Properties crudeOilProperties() {
        return new BaseFlowingFluid.Properties(CRUDE_OIL_TYPE, CRUDE_OIL, FLOWING_CRUDE_OIL)
                .block(ModBlocks.CRUDE_OIL)
                .tickRate(30)
                .slopeFindDistance(2)
                .levelDecreasePerBlock(2)
                .explosionResistance(100.0F);
    }

    // ================= 分馏产物（0.11 ZF78）=================

    /**
     * 造一个"只在罐子里存在"的液体流体类型（0.11 ZF78）：油菜/石脑油/汽油/液化石油气共用。
     *
     * <p>这四种都是分馏塔的产物，<b>故意不注册液体方块</b>（没地方倒，也没人往地上倒），
     * 于是照三种气体的老样子：只有 FluidType + Source/Flowing 两个流体本体，
     * 没有 {@code .block(...)}、没有 {@code .bucket(...)}（{@code getBucket()} 返回空气 ⇒
     * 原版空桶舀不走，和原油同一条规矩）。</p>
     *
     * <p><b>为什么抽成一个工厂方法</b>：这四种类型的参数逐字相同（只有密度/黏度不同），
     * 抄四遍就是四份 {@code initializeClient} 匿名类；审计的 D 项专门盯复制粘贴，
     * 所以这里只留一份实现。</p>
     *
     * <p>⚠ {@code canHydrate(false)} 必须显式写：NeoForge 默认 true，不写的话
     * 以后一旦给它们加了液体方块就会把耕地润湿（原油就是这么踩到的，见档案 §4.45）。</p>
     *
     * @param name        流体注册名（同时决定贴图 {@code block/<name>_still|_flow}）
     * @param density     密度（比水 1000 小 = 浮在水上）
     * @param viscosity   黏度
     */
    private static FluidType liquidType(String name, int density, int viscosity) {
        return new FluidType(FluidType.Properties.create()
                .density(density)
                .viscosity(viscosity)
                // 温度固定 300（NeoForge 默认也是 300）：四种产物本来就一样，
                // 原先做成形参 ⇒ 四个调用点全传 300，IDE 直接报「形参的值始终为 300」（ZF85 去掉）
                .temperature(300)
                .canConvertToSource(false)   // 不能像水一样变无限
                .canHydrate(false)           // 不润湿耕地
                .canExtinguish(false)        // 不灭火
                .supportsBoating(false));
    }

    /**
     * 柴油（用户给的第 1 张 16x16 贴图）。密度 830：比水轻、比汽油重。
     *
     * <p><b>不是气体</b>：{@link #isGas} 只正向列举那 6 个气体本体 + {@code #c:gaseous}，
     * 所以液化石油气也不会被当气体（用户原话是"液化"）。</p>
     */
    public static final DeferredHolder<FluidType, FluidType> DIESEL_TYPE =
            FLUID_TYPES.register("diesel", () -> liquidType("diesel", 830, 1200));

    public static final DeferredHolder<Fluid, BaseFlowingFluid.Source> DIESEL =
            FLUIDS.register("diesel", () -> new BaseFlowingFluid.Source(dieselProperties()));
    public static final DeferredHolder<Fluid, BaseFlowingFluid.Flowing> FLOWING_DIESEL =
            FLUIDS.register("flowing_diesel", () -> new BaseFlowingFluid.Flowing(dieselProperties()));

    /**
     * 柴油的流动参数。
     *
     * <p>⚠ 流动参数必须走<b>方法</b>（与上面三种气体同一个写法）：直接在字段初始化式里写
     * {@code new BaseFlowingFluid.Properties(DIESEL_TYPE, DIESEL, FLOWING_DIESEL)} 会同时触发
     * 「自引用」与「非法前向引用」两个编译错误（FLOWING_DIESEL 还没声明）。</p>
     *
     * <p><b>0.11 ZF82 起柴油有桶也有方块了</b>（用户原话：新进「柴油桶」，
     * 「和原版水桶一致 可以倒出相应的流体返回空桶 并可以被空桶收回源头液体」）：</p>
     * <ul>
     *   <li>{@code .block(ModBlocks.DIESEL)} —— 桶倒出来才有东西可放；</li>
     *   <li>{@code .bucket(...)} —— <b>这一条决定了原版空桶能不能舀</b>：
     *       {@code LiquidBlock#pickupBlock} 返回的就是 {@code fluid.getBucket()}；
     *       反过来「容器换流器」也正是靠这个把罐里的流体变成对应的桶。</li>
     * </ul>
     * <p>⚠ 与原油相反：原油**故意不设** {@code .bucket(...)}（一桶 3000 mB 会白送三倍，见 §4.45），
     * 柴油/汽油是用户点名的两种"有桶形式"的流体。</p>
     */
    private static BaseFlowingFluid.Properties dieselProperties() {
        // ⚠ 这里**只放流动参数**：canConvertToSource / canHydrate / canExtinguish / supportsBoating
        //   是 FluidType.Properties 上的开关（本文件的 liquidType(...) 已经设全），
        //   写到这条链上会报"找不到符号"（ZF82 我踩过）。
        // ⚠ `.bucket(...)` 放链尾：它决定原版空桶能不能舀、以及"容器换流器"产出的桶是哪个。
        return new BaseFlowingFluid.Properties(DIESEL_TYPE, DIESEL, FLOWING_DIESEL)
                .block(ModBlocks.DIESEL)
                .tickRate(30)
                .slopeFindDistance(2)
                .levelDecreasePerBlock(2)
                .bucket(ModItems.DIESEL_BUCKET);
    }

    /** 石脑油（用户给的第 2 张 16x16 贴图）：最轻的液态馏分。 */
    public static final DeferredHolder<FluidType, FluidType> NAPHTHA_TYPE =
            FLUID_TYPES.register("naphtha", () -> liquidType("naphtha", 700, 700));

    public static final DeferredHolder<Fluid, BaseFlowingFluid.Source> NAPHTHA =
            FLUIDS.register("naphtha", () -> new BaseFlowingFluid.Source(naphthaProperties()));
    public static final DeferredHolder<Fluid, BaseFlowingFluid.Flowing> FLOWING_NAPHTHA =
            FLUIDS.register("flowing_naphtha", () -> new BaseFlowingFluid.Flowing(naphthaProperties()));

    private static BaseFlowingFluid.Properties naphthaProperties() {
        return new BaseFlowingFluid.Properties(NAPHTHA_TYPE, NAPHTHA, FLOWING_NAPHTHA);
    }

    /** 汽油（用户给的第 3 张 16x16 贴图）。0.11 ZF82 起同样有方块 + 桶（理由见柴油那一节）。 */
    public static final DeferredHolder<FluidType, FluidType> GASOLINE_TYPE =
            FLUID_TYPES.register("gasoline", () -> liquidType("gasoline", 750, 600));

    public static final DeferredHolder<Fluid, BaseFlowingFluid.Source> GASOLINE =
            FLUIDS.register("gasoline", () -> new BaseFlowingFluid.Source(gasolineProperties()));
    public static final DeferredHolder<Fluid, BaseFlowingFluid.Flowing> FLOWING_GASOLINE =
            FLUIDS.register("flowing_gasoline", () -> new BaseFlowingFluid.Flowing(gasolineProperties()));

    private static BaseFlowingFluid.Properties gasolineProperties() {
        // 与柴油同一套写法与理由（见上面那一节）：只放流动参数，`.bucket(...)` 放链尾。
        return new BaseFlowingFluid.Properties(GASOLINE_TYPE, GASOLINE, FLOWING_GASOLINE)
                .block(ModBlocks.GASOLINE)
                .tickRate(30)
                .slopeFindDistance(2)
                .levelDecreasePerBlock(2)
                .bucket(ModItems.GASOLINE_BUCKET);
    }

    /**
     * 液化石油气（用户给的第 4 张 16x16 贴图）。
     *
     * <p><b>按"液体"注册</b>（用户原话是"液化"石油气，且规格里它是操作器那 4 个
     * 2.5 桶产品罐之一）⇒ 密度取 500（加压液化后的常见量级），
     * <b>不挂 {@code c:gaseous}</b>，所以 {@link #isGas} 判它是液体、油桶肯收它。
     * 要改成气体只需把它的 {@code data/c/tags/fluid/lpg.json} 挪进 gaseous，属一个标签的事。</p>
     */
    public static final DeferredHolder<FluidType, FluidType> LPG_TYPE =
            FLUID_TYPES.register("lpg", () -> liquidType("lpg", 500, 400));

    public static final DeferredHolder<Fluid, BaseFlowingFluid.Source> LPG =
            FLUIDS.register("lpg", () -> new BaseFlowingFluid.Source(lpgProperties()));
    public static final DeferredHolder<Fluid, BaseFlowingFluid.Flowing> FLOWING_LPG =
            FLUIDS.register("flowing_lpg", () -> new BaseFlowingFluid.Flowing(lpgProperties()));

    private static BaseFlowingFluid.Properties lpgProperties() {
        return new BaseFlowingFluid.Properties(LPG_TYPE, LPG, FLOWING_LPG);
    }

    // ================= 氮气 / 氨气（0.11 ZF97）=================

    /**
     * 氮气：用户原话「空气分离器 … 30s产出 8mB 氮气 2mB氧气」。
     *
     * <p>与另外三种气体一样：<b>只注册流体本体与流体类型</b> —— 没有 bucket、没有可放置的
     * 液体方块（气体不该往地上倒）。贴图路径走 {@code block/nitrogen_still.png} /
     * {@code block/nitrogen_flow.png}（本轮程序生成的占位），客户端注册在
     * {@link PotatoSTClient#registerFluidTextures}。</p>
     *
     * <p>密度取 −22（空气里氮气占大头，比氧气（−25）略"沉"一点点），纯风味属性。</p>
     */
    public static final DeferredHolder<FluidType, FluidType> NITROGEN_TYPE =
            FLUID_TYPES.register("nitrogen", () -> new FluidType(FluidType.Properties.create()
                    .density(-22)
                    .viscosity(200)));

    public static final DeferredHolder<Fluid, BaseFlowingFluid.Source> NITROGEN =
            FLUIDS.register("nitrogen", () -> new BaseFlowingFluid.Source(nitrogenProperties()));
    public static final DeferredHolder<Fluid, BaseFlowingFluid.Flowing> FLOWING_NITROGEN =
            FLUIDS.register("flowing_nitrogen", () -> new BaseFlowingFluid.Flowing(nitrogenProperties()));

    private static BaseFlowingFluid.Properties nitrogenProperties() {
        return new BaseFlowingFluid.Properties(NITROGEN_TYPE, NITROGEN, FLOWING_NITROGEN);
    }

    /**
     * 氨气：用户原话「氨气组成室 … 每t消耗1mB氮气 1mB氢气 200Fe/t 产出1mB氨气」。
     *
     * <p>同样是"只有流体、没有桶与方块"的气体。密度取 −35（氨气比空气轻）。</p>
     */
    public static final DeferredHolder<FluidType, FluidType> AMMONIA_TYPE =
            FLUID_TYPES.register("ammonia", () -> new FluidType(FluidType.Properties.create()
                    .density(-35)
                    .viscosity(200)));

    public static final DeferredHolder<Fluid, BaseFlowingFluid.Source> AMMONIA =
            FLUIDS.register("ammonia", () -> new BaseFlowingFluid.Source(ammoniaProperties()));
    public static final DeferredHolder<Fluid, BaseFlowingFluid.Flowing> FLOWING_AMMONIA =
            FLUIDS.register("flowing_ammonia", () -> new BaseFlowingFluid.Flowing(ammoniaProperties()));

    private static BaseFlowingFluid.Properties ammoniaProperties() {
        return new BaseFlowingFluid.Properties(AMMONIA_TYPE, AMMONIA, FLOWING_AMMONIA);
    }

    /**
     * 二氧化碳：用户原话「一个二氧化碳罐10000mB（输出）… 所有原木单个反应后生成10mB二氧化碳 …
     * 一桶柴油/汽油反应30s 产生200mB二氧化碳 … 其余物品只产出5mb二氧化碳」
     * （0.11 ZF100 燃烧反应室的输出气体）。
     *
     * <p>同样是"只有流体、没有桶与方块"的气体。密度取 −44（二氧化碳比空气重、也比我加过的
     * 其它气体重 —— 氮 −22 / 氧 −25 / 氯 −30 / 氨 −35，纯风味属性）。</p>
     */
    public static final DeferredHolder<FluidType, FluidType> CARBON_DIOXIDE_TYPE =
            FLUID_TYPES.register("carbon_dioxide", () -> new FluidType(FluidType.Properties.create()
                    .density(-44)
                    .viscosity(200)));

    public static final DeferredHolder<Fluid, BaseFlowingFluid.Source> CARBON_DIOXIDE =
            FLUIDS.register("carbon_dioxide", () -> new BaseFlowingFluid.Source(carbonDioxideProperties()));
    public static final DeferredHolder<Fluid, BaseFlowingFluid.Flowing> FLOWING_CARBON_DIOXIDE =
            FLUIDS.register("flowing_carbon_dioxide",
                    () -> new BaseFlowingFluid.Flowing(carbonDioxideProperties()));

    private static BaseFlowingFluid.Properties carbonDioxideProperties() {
        return new BaseFlowingFluid.Properties(CARBON_DIOXIDE_TYPE, CARBON_DIOXIDE, FLOWING_CARBON_DIOXIDE);
    }

    // ================= 三种酸（0.11 ZF101 酸性反应室）=================

    /**
     * 碳酸：用户原话「1.10mb二氧化碳+1mb水 产出1mb碳酸」（酸性反应室 1 号配方）。
     *
     * <p><b>⚠ 是液体不是气体</b>：不进 {@link #isGas} 那张正向白名单 ⇒ 油桶肯收它、
     * 高压气罐拒收它（与本工程"气体/液体"的既有口径一致）。
     * 与分馏产物同款：<b>没有液体方块、没有桶</b>，只在罐子里存在（{@link #liquidType}）。</p>
     */
    public static final DeferredHolder<FluidType, FluidType> CARBONIC_ACID_TYPE =
            FLUID_TYPES.register("carbonic_acid", () -> liquidType("carbonic_acid", 1050, 1000));

    public static final DeferredHolder<Fluid, BaseFlowingFluid.Source> CARBONIC_ACID =
            FLUIDS.register("carbonic_acid", () -> new BaseFlowingFluid.Source(carbonicAcidProperties()));
    public static final DeferredHolder<Fluid, BaseFlowingFluid.Flowing> FLOWING_CARBONIC_ACID =
            FLUIDS.register("flowing_carbonic_acid",
                    () -> new BaseFlowingFluid.Flowing(carbonicAcidProperties()));

    private static BaseFlowingFluid.Properties carbonicAcidProperties() {
        return new BaseFlowingFluid.Properties(CARBONIC_ACID_TYPE, CARBONIC_ACID, FLOWING_CARBONIC_ACID);
    }

    /** 硝酸：用户原话「2.1mb氧气+1mb氨气 产出1mb硝酸」。密度取 1510（比水重）。 */
    public static final DeferredHolder<FluidType, FluidType> NITRIC_ACID_TYPE =
            FLUID_TYPES.register("nitric_acid", () -> liquidType("nitric_acid", 1510, 1000));

    public static final DeferredHolder<Fluid, BaseFlowingFluid.Source> NITRIC_ACID =
            FLUIDS.register("nitric_acid", () -> new BaseFlowingFluid.Source(nitricAcidProperties()));
    public static final DeferredHolder<Fluid, BaseFlowingFluid.Flowing> FLOWING_NITRIC_ACID =
            FLUIDS.register("flowing_nitric_acid",
                    () -> new BaseFlowingFluid.Flowing(nitricAcidProperties()));

    private static BaseFlowingFluid.Properties nitricAcidProperties() {
        return new BaseFlowingFluid.Properties(NITRIC_ACID_TYPE, NITRIC_ACID, FLOWING_NITRIC_ACID);
    }

    /** 硫酸：用户原话「3.10个硫+100MB水 产出100MB硫酸」。密度取 1840（三种酸里最重）。 */
    public static final DeferredHolder<FluidType, FluidType> SULFURIC_ACID_TYPE =
            FLUID_TYPES.register("sulfuric_acid", () -> liquidType("sulfuric_acid", 1840, 1200));

    public static final DeferredHolder<Fluid, BaseFlowingFluid.Source> SULFURIC_ACID =
            FLUIDS.register("sulfuric_acid", () -> new BaseFlowingFluid.Source(sulfuricAcidProperties()));
    public static final DeferredHolder<Fluid, BaseFlowingFluid.Flowing> FLOWING_SULFURIC_ACID =
            FLUIDS.register("flowing_sulfuric_acid",
                    () -> new BaseFlowingFluid.Flowing(sulfuricAcidProperties()));

    private static BaseFlowingFluid.Properties sulfuricAcidProperties() {
        return new BaseFlowingFluid.Properties(SULFURIC_ACID_TYPE, SULFURIC_ACID, FLOWING_SULFURIC_ACID);
    }

    /**
     * 盐酸：用户 ZF102 原话「然后新加配方盐酸 10mb氢气+10mb氯气+5mb水 产出5mb盐酸 耗能一致」。
     *
     * <p>同样是**液体不是气体**、同样只在罐子里存在（没有液体方块、没有桶）。
     * 密度取 1150（比水重、比硝酸轻 —— 风味属性）。</p>
     */
    public static final DeferredHolder<FluidType, FluidType> HYDROCHLORIC_ACID_TYPE =
            FLUID_TYPES.register("hydrochloric_acid", () -> liquidType("hydrochloric_acid", 1150, 1000));

    public static final DeferredHolder<Fluid, BaseFlowingFluid.Source> HYDROCHLORIC_ACID =
            FLUIDS.register("hydrochloric_acid",
                    () -> new BaseFlowingFluid.Source(hydrochloricAcidProperties()));
    public static final DeferredHolder<Fluid, BaseFlowingFluid.Flowing> FLOWING_HYDROCHLORIC_ACID =
            FLUIDS.register("flowing_hydrochloric_acid",
                    () -> new BaseFlowingFluid.Flowing(hydrochloricAcidProperties()));

    private static BaseFlowingFluid.Properties hydrochloricAcidProperties() {
        return new BaseFlowingFluid.Properties(HYDROCHLORIC_ACID_TYPE, HYDROCHLORIC_ACID,
                FLOWING_HYDROCHLORIC_ACID);
    }

    // ================= 注册入口 =================
    /**
     * The three process gases, in fixed order (oxygen / hydrogen / chlorine).
     * Deliberately a METHOD, not a static field: DeferredHolder.get() only works
     * after the registry event has bound the holders, and a static initializer in
     * this class runs far earlier (ModFluids.register is called from the mod
     * constructor). A static list here crashes the whole mod at load time with
     * "Trying to access unbound value".
     */
    public static List<Fluid> gases() {
        return List.of(OXYGEN.get(), HYDROGEN.get(), CHLORINE.get());
    }

    // ⚠ 0.11 ZF85 删掉了这里的 idOf(Fluid) / byId(int)：它们是 ZF72 时代"用 1..3 紧凑编号
    //   同步流体"的产物，ZF73 起**界面改用流体注册表 id**（BuiltInRegistries.FLUID.getId/byId），
    //   这两个方法再没有任何调用点 —— IDE 会报"方法从未使用"，删掉最干净。
    //   （档案 §4.44 那段历史记录保留：它记的是"当年为什么错"，不是"现在还有这个方法"。）

    // ================= 气体 / 液体 判定（0.11 ZF73 改成正向白名单）=================

    /**
     * 是不是**气体**（本模组的氧气/氢气/氯气）。
     *
     * <p>⚠ 这是 v0.11 ZF73 拆掉的一颗雷（档案 §4.44）：原先判定的写法是**负向**的
     * 「不是水也不是岩浆 ⇒ 气体」，在"世界上只有水和岩浆两种液体"的前提下等价，
     * 但一加原油它当场变成错的 —— 原油既不是水也不是岩浆，于是
     * {@code TankContents.fill()} 会把原油灌进高压气罐，直接违反用户规则「不可以罐装气体」。</p>
     *
     * <p>⇒ 规矩：**新增流体时一律正向列举**，负向判定视为待还的债。</p>
     *
     * @return 空/未知流体返回 false
     */
    public static boolean isGas(Fluid fluid) {
        if (fluid == null || fluid == Fluids.EMPTY) {
            return false;
        }
        // ① 本模组那 6 种（写死一遍：标签还没加载时也认得出，且不依赖数据包）
        //    ⚠ 0.11 ZF97 从 3 种加到 5 种（+氮气/氨气）、ZF100 加到 6 种（+二氧化碳）——
        //      `_zf73_verify.py` A14、`_zf74_verify.py` B1 与 `_zf97_verify.py` 都在**数**
        //      这一段的列举条数（6 → 10 → 12），加气体时三处一起改（活体数字）。
        //      ⚠ 数的时候按正则 `fluid == \w+\.get\(\)` 数 ⇒ **注释里别写出这个形状的字面量**，
        //        否则注释也会被数进去（ZF97 第一次跑就多算了 1 条）。
        if (fluid == OXYGEN.get() || fluid == FLOWING_OXYGEN.get()
                || fluid == HYDROGEN.get() || fluid == FLOWING_HYDROGEN.get()
                || fluid == CHLORINE.get() || fluid == FLOWING_CHLORINE.get()
                || fluid == NITROGEN.get() || fluid == FLOWING_NITROGEN.get()
                || fluid == AMMONIA.get() || fluid == FLOWING_AMMONIA.get()
                || fluid == CARBON_DIOXIDE.get() || fluid == FLOWING_CARBON_DIOXIDE.get()) {
            return true;
        }
        // ② 别的 mod 挂进 `#c:gaseous` 的气体也算气体（0.11 ZF74）
        //    NeoForge 上游本来就声明了这个通用标签（Tags.Fluids.GASEOUS），但默认没有条目
        //    —— 等于「各 mod 自己挂进来」，本模组已挂（data/c/tags/fluid/gaseous.json）。
        //    ⇒ 效果：别的 mod 的氧气/氢气也能灌进高压气罐，油桶也照样拒收它们。
        return fluid.defaultFluidState().is(Tags.Fluids.GASEOUS);
    }

    /**
     * 是不是**能被油桶这类"液体容器"收下的流体**：非空、且不是气体。
     *
     * <p>用户规则落地处：「油桶目前可以舀取石油在内的任何液体 … 不可以罐装气体」。
     * 水/岩浆也算液体 —— 用户没把原版液体排除在外（见 v0.11 规划 §5 待决 3 的默认值）。</p>
     */
    public static boolean isLiquid(Fluid fluid) {
        if (fluid == null || fluid == Fluids.EMPTY) {
            return false;
        }
        return !isGas(fluid);
    }

    public static void register(IEventBus modEventBus) {
        FLUID_TYPES.register(modEventBus);
        FLUIDS.register(modEventBus);
    }
}