package com.potatost.mod;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.BucketItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.JukeboxSong;
import net.minecraft.world.item.PickaxeItem;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.SwordItem;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;
import java.util.List;
import net.minecraft.world.item.TooltipFlag;

public class ModItems {

    public static final DeferredRegister.Items ITEMS =
            DeferredRegister.createItems(PotatoST.MODID);

    public static final DeferredRegister<CreativeModeTab> CREATIVE_MODE_TABS =
            DeferredRegister.create(Registries.CREATIVE_MODE_TAB, PotatoST.MODID);

    // ========== 8 个物品（注册名 = 材质文件名，全小写） ==========
    public static final DeferredItem<Item> ALUMINUM_INGOT =
            ITEMS.register("aluminum_ingot", () -> new Item(new Item.Properties()));

    public static final DeferredItem<Item> CARBON =
            ITEMS.register("carbon", () -> new Item(new Item.Properties()));

    public static final DeferredItem<Item> COBALT_INGOT =
            ITEMS.register("cobalt_ingot", () -> new Item(new Item.Properties()));

    public static final DeferredItem<Item> HIGH_CARBON_STEEL =
            ITEMS.register("high_carbon_steel", () -> new Item(new Item.Properties()));

    public static final DeferredItem<Item> NICKEL_INGOT =
            ITEMS.register("nickel_ingot", () -> new Item(new Item.Properties()));

    public static final DeferredItem<Item> SILVER_INGOT =
            ITEMS.register("silver_ingot", () -> new Item(new Item.Properties()));

    public static final DeferredItem<Item> TONER =
            ITEMS.register("toner", () -> new Item(new Item.Properties()));

    public static final DeferredItem<Item> URANIUM_INGOT =
            ITEMS.register("uranium_ingot", () -> new Item(new Item.Properties()));
    // ========== 硅（0.10，微型粉碎机产物）==========
    /**
     * 硅：微型粉碎机把紫水晶（碎片/块）与石英（下界石英/石英建材）粉碎得到。
     * 贴图目前借用原版火药（见 models/item/silicon.json 的 layer0），等美术 pass 再换。
     */
    public static final DeferredItem<Item> SILICON =
            ITEMS.register("silicon", () -> new Item(new Item.Properties()));
    // ========== 锂（0.10 ZF15）==========
    /**
     * 锂矿精粉：微型粉碎机粉碎<b>粗锂</b>的产物（2~4 个 / 12s / 20 FE/t）。
     * 上游是锂矿石（挖出来掉粗锂），下游进高炉烧成碳酸锂。
     *
     * <p>贴图借用原版糖（见 {@code models/item/lithium_concentrate.json} 的 layer0）—— 用户指定，
     * 等美术 pass 再换。数据包不给它挂 {@code c:} 标签：按既定口径，
     * 「其他物品」不做跨 mod 兼容，只有矿物/合金/矿物锭默认兼容。</p>
     */
    public static final DeferredItem<Item> LITHIUM_CONCENTRATE =
            ITEMS.register("lithium_concentrate", () -> new Item(new Item.Properties()));

    /** 碳酸锂：锂矿精粉进<b>高炉</b>烧出来的产物。贴图同样借用原版糖（用户指定）。 */
    public static final DeferredItem<Item> LITHIUM_CARBONATE =
            ITEMS.register("lithium_carbonate", () -> new Item(new Item.Properties()));

    /**
     * 锂电池原件（0.11 ZF112）—— 锂电池构造间的产物，也是<b>三元聚合物锂电池方块配方里的那一样</b>。
     *
     * <p>用户原话：「加一个锂电池构造间 … 30s后产出一个锂电池原件 不消耗电
     * 三元锂配方里的碳酸锂改成锂电池原件」。⚠ 与方块 {@code lithium_battery}
     * （显示名「三元聚合物锂电池」）区分：这个是**中间件**，装进方块配方里。</p>
     */
    public static final DeferredItem<Item> LITHIUM_BATTERY_COMPONENT =
            ITEMS.register("lithium_battery_component", () -> new Item(new Item.Properties()));
    // ========== 板材（0.10 ZF16）==========
    /**
     * 6 种板材：铁 / 镍 / 钴 / 银 / 铝 / 钢。
     *
     * <p><b>贴图（0.11 ZF90 起）</b>：铁 / 钢 / 铜三件各用用户画的
     * {@code textures/item/{iron,steel,copper}_plate.png}（ZF83/ZF86）；
     * <b>银 / 铝 / 镍 / 钴四件一并指向 {@code textures/item/iron_plate.png}</b> ——
     * 用户原话「其它锭板子贴图都换成铁板的」⇒ 这四件**在背包里跟铁板长得一模一样**，
     * 这是照做的结果不是失误；原先它们共用那张通用 {@code plate.png}，ZF90 已删。
     * 哪天想按金属上色：{@code build/zftools/PngRecolor.py} 一条命令能改色，
     * 再把各模型的 {@code layer0} 指过去即可（锂矿那两张就是这么来的）。</p>
     *
     * <p><b>按长期规则不挂 {@code c:} 标签</b>：用户口径是"默认只兼容 矿物 / 粗矿 / 矿石 / 锭"，
     * 板材属于"其他物品"，要兼容得用户点名。
     * （{@code c:plates/*} 是社区约定，**NeoForge 的 universal.jar 里并没有预置**，
     * 所以挂上去也不会自动桥接到别的命名空间。）</p>
     */
    public static final DeferredItem<Item> IRON_PLATE =
            ITEMS.register("iron_plate", () -> new Item(new Item.Properties()));

    public static final DeferredItem<Item> NICKEL_PLATE =
            ITEMS.register("nickel_plate", () -> new Item(new Item.Properties()));

    public static final DeferredItem<Item> COBALT_PLATE =
            ITEMS.register("cobalt_plate", () -> new Item(new Item.Properties()));

    public static final DeferredItem<Item> SILVER_PLATE =
            ITEMS.register("silver_plate", () -> new Item(new Item.Properties()));

    public static final DeferredItem<Item> ALUMINUM_PLATE =
            ITEMS.register("aluminum_plate", () -> new Item(new Item.Properties()));

    /**
     * 高碳钢的板材 = <b>钢板</b>（用户指定）。
     *
     * <p>高碳钢本身**已经**挂在 {@code c:ingots/steel} + {@code c:steel_ingots} 里，父标签
     * {@code c:ingots} 也在——所以用户那句"如果以前高碳钢的标签不是钢那也改成钢"**无需改动**，
     * 已解包核实（0.10 ZF16）。</p>
     */
    public static final DeferredItem<Item> STEEL_PLATE =
            ITEMS.register("steel_plate", () -> new Item(new Item.Properties()));

    // ========== 铜板（0.10 ZF30）==========
    /**
     * 铜板：液压机把<b>铜锭</b>压出来的板材（用户指名要）。
     *
     * <p><b>贴图单独一张</b> {@code textures/item/copper_plate.png}（用户给的三张素材之一）——
     * 不再和其余板材共用。原因：铜是**唯一有专属色**的那种，
     * 混在一起玩家分不出"这是铜板还是铁板"。</p>
     *
     * <p>按长期规则**不挂 {@code c:} 标签**：板材属于"其他物品"，
     * 要跨 mod 兼容得用户点名（口径见 {@link #IRON_PLATE} 的注释）。</p>
     */
    public static final DeferredItem<Item> COPPER_PLATE =
            ITEMS.register("copper_plate", () -> new Item(new Item.Properties()));

    // ========== 粉末 / 磁铁 / 热力金属 / 光伏原件（0.10 ZF45）==========
    /**
     * 铁粉：<b>微型粉碎机</b>把铁锭磨出来的粉（用户指定：20 秒、70 FE/t、出 1 个）。
     *
     * <p>下游只有一条，在<b>电力高炉</b>里：铁粉 + 碳粉 → 高碳钢；铁粉 + 沙砾 → 磁铁
     * （两条"双输入"配方的实现见 {@link BlastFurnaceRecipes#findPair}）。</p>
     *
     * <p><b>贴图</b>是碳粉那张粉尘图改的灰色（{@code build/zftools/_zf45_textures.py}，
     * 形状复用、只抬亮度）—— 用户原话「新物品材质你简单画一下或者用原版相近的代替」。
     * 之所以不直接借原版火药：那会和碳粉长得一模一样，背包里分不出哪个是铁。</p>
     *
     * <p><b>按长期规则不挂 {@code c:dusts/iron}</b>：默认兼容范围是"矿物 / 粗矿 / 矿石 / 锭"，
     * 粉末属于"其他物品"，要跨 mod 兼容得用户点名（口径见 {@link #IRON_PLATE} 的注释）。</p>
     */
    public static final DeferredItem<Item> IRON_POWDER =
            ITEMS.register("iron_powder", () -> new Item(new Item.Properties()));

    /**
     * 磁铁：<b>电力高炉</b>里用铁粉 + 沙砾烧出来的东西（用户指定），
     * 下游是<b>发电机</b>的两条配方（每台发电机要 2 个）。
     *
     * <p><b>贴图手画</b>（马蹄形：灰磁极 + 红磁体），没有相近的原版物品可借。</p>
     */
    public static final DeferredItem<Item> MAGNET =
            ITEMS.register("magnet", () -> new Item(new Item.Properties()));

    /**
     * 热力金属：6 银锭 + 3 铜板的 3×3 合成产物（用户指定），
     * 下游是<b>加热装置</b>那台装饰方块（要 3 个）。
     *
     * <p><b>贴图</b>借银锭的锭形改色成"烧红"的橙金（同 {@code _zf45_textures.py}）——
     * 亮度关系原样保留，所以高光/阴影看着还是同一块金属。</p>
     */
    public static final DeferredItem<Item> THERMAL_METAL =
            ITEMS.register("thermal_metal", () -> new Item(new Item.Properties()));

    /**
     * 光伏原件：3 玻璃板 + 3 硅 + 铝板/银锭/铝板 合成（用户指定），
     * 下游是<b>太阳能板</b>（每块要 2 个）。
     *
     * <p>名字按用户原文写「光伏原件」（不是"元件"）—— 用户两次都这么写，
     * 所以照抄；要改是一个 lang 键的事。</p>
     *
     * <p><b>贴图手画</b>（深蓝电池片 + 铝框 + 两个触点）。</p>
     */
    public static final DeferredItem<Item> PHOTOVOLTAIC_COMPONENT =
            ITEMS.register("photovoltaic_component", () -> new Item(new Item.Properties()));

    // ========== 钛（0.10 ZF48）==========
    /**
     * 钛锭：<b>电力高炉</b>把钛粉烧出来的产物（用户原话：「钛粉再由电力高炉烧制出钛锭」）。
     *
     * <p>锭属于长期规则里"默认兼容别的 mod"的那一类 ⇒ 由 {@code GenCommonTags.py} 挂
     * {@code c:ingots/titanium} + {@code c:titanium_ingots}。</p>
     *
     * <p><b>⚠ 贴图是借的</b>：用户原话「贴图暂时都用原版铁的」⇒ 直接指原版
     * {@code minecraft:item/iron_ingot}，<b>和铁锭长得一模一样</b>（照做的，不是失误）。
     * 等美术素材来了改 {@code models/item/titanium_ingot.json} 的 layer0 即可。</p>
     */
    public static final DeferredItem<Item> TITANIUM_INGOT =
            ITEMS.register("titanium_ingot", () -> new Item(new Item.Properties()));

    /**
     * 轻质钛合金（0.10 ZF62）：<b>合金冶炼炉的第一条产物</b>。
     *
     * <p>用户原话：「铝+钛+银在合金冶炼炉 30s 5800fe/t产出一个 轻质钛合金 用钛锭的贴图」
     * ⇒ 配方在 {@link AlloySmelterRecipes}，一件总耗电 5800 × 600 = <b>3,480,000 FE</b>。</p>
     *
     * <p><b>贴图照用户说的用钛锭那张</b>（{@code potato_s_t:item/titanium_ingot}，
     * 也就是 {@code models/item/light_titanium_alloy.json} 的 layer0 直接指它）——
     * 所以两样东西在物品栏里长得一样，这是<b>照做的</b>，不是漏了贴图。
     * 等有独立素材时改那一行 layer0 即可。</p>
     *
     * <p><b>按长期规则挂 {@code c:} 标签</b>：它属于"合金/锭"那一类（与高碳钢同口径）
     * ⇒ {@code c:ingots} + {@code c:ingots/titanium_alloy} + {@code c:titanium_alloy_ingots}
     * （名字由 {@code GenCommonTags.py} 生成）。挂进 {@code c:ingots} 的副作用是
     * <b>合金炉的输入槽也收它</b>（输入槽只认 {@code #c:ingots}）—— 这是有意的，和别的锭一致。</p>
     */
    public static final DeferredItem<Item> LIGHT_TITANIUM_ALLOY =
            ITEMS.register("light_titanium_alloy", () -> new Item(new Item.Properties()));

    /**
     * 硬质钛合金（0.11 ZF104，用户口述）：「硬质钛合金」——
     * 由**合金冶炼炉**烧出来（轻质钛合金 + 高碳钢 + 镍锭，见 {@link AlloySmelterRecipes}），
     * 再拿去合**稳定金属块**。
     *
     * <p><b>贴图先用钛锭那张</b>（用户原话「其中硬质钛合金还是钛锭的贴图」）⇒
     * 物品模型直接指向 {@code potato_s_t:item/titanium_ingot}，本轮**不新增任何 PNG**，
     * 公告里"还在借原版贴图的模型"那个数也不变。</p>
     */
    public static final DeferredItem<Item> HARD_TITANIUM_ALLOY =
            ITEMS.register("hard_titanium_alloy", () -> new Item(new Item.Properties()));

    // ========== 钛合金工具（0.10 ZF66）==========
    /**
     * 钛合金剑：<b>耐久 2048、显示攻击伤害 6.5</b>（用户给的数）。
     *
     * <p>数值全部落在 {@link ModTiers#TITANIUM_ALLOY_SWORD} 里，这里只负责把原版那套
     * 属性写法照抄一遍（{@code SwordItem.createAttributes(tier, 3, -2.4F)} —— 与钻石剑同一行写法，
     * 换的只有档位）⇒ 显示总伤害 = 玩家基础 1 + (3 + 档位伤害 2.5) = <b>6.5</b>。</p>
     *
     * <p><b>贴图是用户给的</b>：{@code textures/item/titanium_alloy_sword.png}
     * （原名"钛合金剑_001.png"，按 §4.24 改成 ASCII，改名前后哈希一致）。</p>
     *
     * <p><b>不做 Shift 详细说明</b>（用户原话「工具就不需要 shift 查看详细介绍了」）——
     * 所以这里没有 {@code appendHoverText}，说明行只有原版自己的"攻击伤害 / 攻击速度"。</p>
     */
    public static final DeferredItem<Item> TITANIUM_ALLOY_SWORD =
            ITEMS.register("titanium_alloy_sword",
                    () -> new SwordItem(ModTiers.TITANIUM_ALLOY_SWORD, new Item.Properties()
                            .attributes(SwordItem.createAttributes(ModTiers.TITANIUM_ALLOY_SWORD, 3, -2.4F))));

    /**
     * 钛合金镐：<b>耐久 4219、显示攻击伤害 4、挖掘等级＝下界合金</b>（用户给的数）。
     *
     * <p>属性写法照抄原版镐那一行（{@code PickaxeItem.createAttributes(tier, 1.0F, -2.8F)}）⇒
     * 显示总伤害 = 1 + (1 + 档位伤害 2.0) = <b>4</b>；挖掘等级由档位的
     * {@code INCORRECT_FOR_NETHERITE_TOOL} 决定（古代残骸那种"只有下界合金能挖"的方块照挖）。</p>
     *
     * <p>贴图同上（用户给的 {@code titanium_alloy_pickaxe.png}）；同样<b>没有 Shift 说明</b>。</p>
     */
    public static final DeferredItem<Item> TITANIUM_ALLOY_PICKAXE =
            ITEMS.register("titanium_alloy_pickaxe",
                    () -> new PickaxeItem(ModTiers.TITANIUM_ALLOY_PICKAXE, new Item.Properties()
                            .attributes(PickaxeItem.createAttributes(ModTiers.TITANIUM_ALLOY_PICKAXE, 1.0F, -2.8F))));

    /**
     * 钛粉：<b>微型粉碎机</b>把粗钛磨出来的粉（用户指定：6 秒、300 FE/t ⇒ 一件 36000 FE）。
     *
     * <p>它是<b>唯一</b>能烧出钛锭的东西；粗钛本身熔炉/高炉都烧不了 ——
     * 这是用户指定的链条：粗钛 →粉碎→ 钛粉 →电力高炉→ 钛锭。</p>
     *
     * <p><b>⚠ 贴图是借的</b>：用户原话「钛粉用火药」⇒ 直接指原版 {@code minecraft:item/gunpowder}
     * （和硅最初那次借贴图同一个做法）。</p>
     *
     * <p><b>按长期规则不挂 {@code c:dusts/titanium}</b>：粉末属于"其他物品"，
     * 要跨 mod 兼容得用户点名（口径见 {@link #IRON_PLATE} 的注释）。</p>
     */
    public static final DeferredItem<Item> TITANIUM_POWDER =
            ITEMS.register("titanium_powder", () -> new Item(new Item.Properties()));

    // ========== 沥青（0.11 ZF78）==========
    /**
     * 沥青：<b>分馏塔操作器</b>每 5 tick（每座塔）吐出来的那一样固体产物
     * （用户原话「每5t产生一个沥青 沥青满64不清理则会停止分馏」）。
     *
     * <p>它是分馏链条里<b>目前唯一没有下游</b>的东西 —— 用户只说了"产出来、堆满 64 就停机"，
     * 没说能干什么（既没给配方，也没说是不是燃料）⇒ <b>故意不挂任何原版功能标签</b>
     * （当燃料烧、当合成材料都得用户点名，见档案 §5 待决）。</p>
     *
     * <p><b>⚠ 贴图是借的</b>：用户原话「沥青贴图暂时用火药占位」⇒ item model 直接指原版
     * {@code minecraft:item/gunpowder}（与钛粉同一个做法，见 {@link #TITANIUM_POWDER}），
     * 所以它现在和火药长得一模一样 —— 这是<b>照做的</b>，不是漏了贴图。
     * 等美术素材来了改 {@code models/item/bitumen.json} 的 layer0 即可。</p>
     */
    public static final DeferredItem<Item> BITUMEN =
            ITEMS.register("bitumen", () -> new Item(new Item.Properties()));

    // ========== 硫（0.11 ZF96）==========
    /**
     * 硫：<b>加氢脱硫反应仓</b>的产物 —— 一次反应吃 16 个沥青 + 1000 mB 氢气，
     * 10 秒后出 1 个硫（用户原话「每16个沥青 消耗1000mB氢气 10s  产出一个 硫」）。
     *
     * <p>⚠ 这个物品是<b>本轮新加的</b>：在此之前本工程<b>没有"硫"</b>（全仓 grep 不到），
     * 所以它既没有来源也没有用途 —— 现在来源是那台新机器，用途<b>还没定</b>
     * （用户只说"产出一个硫"）⇒ 与沥青同一条口径：<b>不发明用法</b>，
     * 不挂任何原版功能标签、不做任何配方把它消耗掉。</p>
     *
     * <p><b>贴图</b>：本次是<b>程序生成的占位</b>（16×16 RGBA 的黄色粉末堆，
     * 见 {@code _zf96_textures.py}）—— 不是借原版贴图，所以公告里"还在借原版贴图的模型"
     * 那个数（5）不变。要换成手绘的把 {@code textures/item/sulfur.png} 覆盖掉即可。</p>
     */
    public static final DeferredItem<Item> SULFUR =
            ITEMS.register("sulfur", () -> new Item(new Item.Properties()));

    // ========== 电容（0.10 ZF21）==========
    /**
     * 电容：<b>纯物品，放不下去</b>（用户明确要求"不可以放下"）—— 所以是 {@link Item} 而不是
     * {@code BlockItem}：没有对应方块、没有方块实体，右键地面不会放下任何东西。
     *
     * <p>配方（3×3，见 {@code data/potato_s_t/recipe/capacitor.json}）：</p>
     * <pre>
     *   ·   铜锭  ·
     *   铝板 铝板 铝板
     *   铝板 银板 铝板
     * </pre>
     *
     * <p><b>为什么原料有的用标签、有的用精确 id</b>（长期规则：默认只兼容 矿物/粗矿/矿石/锭）：
     * 铜锭属于"锭" ⇒ 用 {@code #c:ingots/copper}（已解包核实该标签含 {@code minecraft:copper_ingot}），
     * 别的 mod 的铜锭也能用；铝板/银板属于"其他物品" ⇒ 按规则<b>不挂 {@code c:} 标签</b>，用精确 id。</p>
     *
     * <p><b>⚠ 贴图是占位</b>：暂借原版<b>铁粒</b>（见 {@code models/item/capacitor.json} 的 layer0）
     * —— 与"硅曾借火药贴图"同一个做法，等美术素材来了再换。</p>
     */
    public static final DeferredItem<Item> CAPACITOR =
            ITEMS.register("capacitor", () -> new Item(new Item.Properties()));
    // ========== 氯化钠（0.10 ZF32）==========
    /**
     * 氯化钠：盐分解构器的<b>必定产出</b>（100%），每轮 1 个。
     *
     * <p><b>⚠ 贴图暂时借用原版糖</b>（见 {@code models/item/sodium_chloride.json} 的 layer0）——
     * 与"硅曾借火药、锂矿精粉借糖"同一个做法，等美术素材来了再换（用户指定）。</p>
     *
     * <p><b>按长期规则不挂 {@code c:} 标签</b>：氯化钠是化合物、不是"矿物/合金/矿物锭"，
     * 属"其他物品"，要跨 mod 兼容得用户点名（口径见 {@link #IRON_PLATE} 的注释）。
     * 与同为化合物的碳酸锂保持一致。</p>
     */
    public static final DeferredItem<Item> SODIUM_CHLORIDE =
            ITEMS.register("sodium_chloride", () -> new Item(new Item.Properties()));
    // ========== 线材与线轴 ==========
    public static final DeferredItem<Item> COPPER_WIRE =
            ITEMS.register("copper_wire", () -> new Item(new Item.Properties()));

    public static final DeferredItem<Item> EMPTY_SPOOL =
            ITEMS.register("empty_spool", () -> new Item(new Item.Properties()));

    public static final DeferredItem<Item> COPPER_WIRE_SPOOL =
            ITEMS.register("copper_wire_spool",
                    () -> new Item(new Item.Properties().durability(32)));
    /** 动力传输线缆（紫色）：连接端子传输动力，32 点耐久，耗尽返还空线轴 */
    public static final DeferredItem<Item> POWER_CABLE_SPOOL =
            ITEMS.register("power_cable_spool",
                    () -> new Item(new Item.Properties().durability(32)));

    // ===== 银线 / 银线轴（0.11 ZF127）=====
    /**
     * 银线：银线轴的原料（2 个银锭 → 4 根，与铜线逐字对应）。
     *
     * <p><b>⚠ 贴图先不画</b>（用户点名「材质先不画」）⇒ 模型借原版<b>铁粒</b>占位
     * （见 {@code models/item/silver_wire.json}），与"电容借铁粒 / 硅借火药"同一个做法。</p>
     */
    public static final DeferredItem<Item> SILVER_WIRE =
            ITEMS.register("silver_wire", () -> new Item(new Item.Properties()));

    /**
     * 银线轴：与铜线轴<b>逐项一致</b>（32 点耐久、右键连端子、耗尽返还空线轴、连接距离 16 格、
     * 线径一样粗），只有两处不同 —— ① 线缆渲染成<b>银白色</b>；② 单线速率
     * {@link TerminalBlockEntity#SILVER_TRANSFER_RATE} = <b>16134 FE/t</b>（铜线 2048）。
     *
     * <p>用户原话：「加一个银线轴 和铜线轴一致（先搞银线 配方什么的都一致只不过铜的换成银的）
     * 材质先不画 连接线缆还是一样的像素大小 只不过变成银白色的 传输速率 16134Fe/t」。</p>
     *
     * <p><b>⚠ 贴图先不画</b>：模型借原版<b>铁锭</b>占位（见 {@code models/item/silver_wire_spool.json}）。</p>
     */
    public static final DeferredItem<Item> SILVER_WIRE_SPOOL =
            ITEMS.register("silver_wire_spool",
                    () -> new Item(new Item.Properties().durability(32)));
    // ========== 海盐 ==========
    /** 海盐：晒盐机产物；扔进水里会溶解销毁（见 ModEvents） */
    public static final DeferredItem<Item> SEA_SALT =
            ITEMS.register("sea_salt", () -> new Item(new Item.Properties()) {
                @Override
                public void appendHoverText(ItemStack stack, TooltipContext context,
                                            List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                    if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                        tooltipComponents.add(Component.translatable("tooltip.potato_s_t.sea_salt"));
                    } else {
                        tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                    }
                }
            });
    // ========== 高压气罐（0.03）==========
    /** 高压气罐：不可堆叠、3500 mB 容量、可混装；只能由灌装机罐装；氢气过量遇火爆炸 */
    public static final DeferredItem<Item> HIGH_PRESSURE_TANK =
            ITEMS.register("high_pressure_tank", () -> new HighPressureTankItem(new Item.Properties()
                    .stacksTo(1)
                    .fireResistant()));
    // ========== 油桶（0.11 ZF73）==========
    /**
     * 油桶：不可堆叠、**3000 mB**、**只装一种液体**（异种流体拒收）、**装不进气体**、
     * 可在世界里右键舀任何液体（一次一格 1000 mB）。
     *
     * <p>配方：铜锭 / 铁桶 / 铜锭 + 钢板 / 铁桶 / 钢板 + 铁板 / 铝锭 / 铁板
     * ⇒ **吃 2 个铁桶、出 1 个油桶**（用户 2026-09-24 拍板）。</p>
     *
     * <p>贴图暂时借原版铁锭（用户原话「先用铁锭贴图凑合」），在 `docs/贴图清单.md` 的待画里。</p>
     */
    public static final DeferredItem<Item> OIL_BUCKET =
            ITEMS.register("oil_bucket", () -> new OilBucketItem(new Item.Properties()
                    .stacksTo(1)));

    // ========== 柴油桶 / 汽油桶（0.11 ZF82）==========
    /**
     * 柴油桶：用户原话「新进 柴油桶 汽油桶（**先用水桶贴图**）**和原版水桶一致**
     * 可以倒出相应的流体返回空桶 并可以被空桶收回源头液体」。
     *
     * <p>所以它就是原版 {@link BucketItem}（不是自定义类）：放置 / 舀取 / 音效 / 返还空桶
     * 全走原版那一套。两个前提由 `ModFluids` 侧满足：柴油/汽油有 {@code .block(...)}
     * （桶才放得出来）与 {@code .bucket(...)}（原版空桶才舀得到）。</p>
     *
     * <p>⚠ 与油桶的分工：油桶是**通用液体容器**（3000 mB、一次舀一格、能装任何液体但不是
     * 任何流体的"官方桶"）；这两种桶是**某一种流体的官方形式**，也是「容器换流器」的产物。</p>
     *
     * <p>贴图按用户吩咐先借原版水桶（`models/item/*_bucket.json` 里写
     * {@code minecraft:item/water_bucket}），在 `docs/贴图清单.md` 的待画里。</p>
     */
    public static final DeferredItem<Item> DIESEL_BUCKET =
            ITEMS.register("diesel_bucket", () -> new BucketItem(ModFluids.DIESEL.get(),
                    new Item.Properties().craftRemainder(Items.BUCKET).stacksTo(1)));

    /** 汽油桶：与柴油桶同一套理由，见上面那一节。 */
    public static final DeferredItem<Item> GASOLINE_BUCKET =
            ITEMS.register("gasoline_bucket", () -> new BucketItem(ModFluids.GASOLINE.get(),
                    new Item.Properties().craftRemainder(Items.BUCKET).stacksTo(1)));

    // ========== 音乐唱片《共和之砧》（0.04）==========
    /**
     * 曲目键：对应 data/potato_s_t/jukebox_song/anvil_of_the_republic.json。
     * 安全性说明：ResourceKey.create / ResourceLocation.fromNamespaceAndPath 都是纯静态工厂，
     * 不读取任何已冻结或未绑定的注册表、不调用 DeferredHolder.get()，所以放在 static final 里安全
     * （0.03 那次启动崩溃只源于“静态初始化期读注册表”，此处不涉及）。
     */
    public static final ResourceKey<JukeboxSong> ANVIL_OF_THE_REPUBLIC_SONG =
            ResourceKey.create(Registries.JUKEBOX_SONG,
                    ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "anvil_of_the_republic"));

    /** 音乐唱片：牢薯不想牢（Malingshu）—《共和之砧》。放进唱片机即可播放 */
    public static final DeferredItem<Item> MUSIC_DISC_ANVIL_OF_THE_REPUBLIC =
            ITEMS.register("music_disc_anvil_of_the_republic", () -> new Item(new Item.Properties()
                    .stacksTo(1)
                    .rarity(Rarity.RARE)
                    .jukeboxPlayable(ANVIL_OF_THE_REPUBLIC_SONG)));

    /**
     * 曲目键：对应 {@code data/potato_s_t/jukebox_song/jasmine_flower.json}（0.11 ZF93 第二张唱片）。
     *
     * <p>用户原话：「这是 茉莉花(管弦乐) 的音乐唱片 贴图在item里」。音频是用户给的
     * {@code Jasmine_Flower_Strings_mono.ogg}（1691739 字节）：<b>单声道 44100 Hz Ogg Vorbis</b>，
     * 实测 <b>147.102132 s</b>（{@code _zf93_ogg.py} 用 soundfile 与自解 Ogg 末页 granule 两条算法互核），
     * 所以 {@code length_in_seconds} 写 147.1。</p>
     */
    public static final ResourceKey<JukeboxSong> JASMINE_FLOWER_SONG =
            ResourceKey.create(Registries.JUKEBOX_SONG,
                    ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "jasmine_flower"));

    /** 音乐唱片：《茉莉花（管弦乐）》。放进唱片机即可播放 */
    public static final DeferredItem<Item> MUSIC_DISC_JASMINE_FLOWER =
            ITEMS.register("music_disc_jasmine_flower", () -> new Item(new Item.Properties()
                    .stacksTo(1)
                    .rarity(Rarity.RARE)
                    .jukeboxPlayable(JASMINE_FLOWER_SONG)));

    /**
     * 扳手（0.10 ZF41）：拆解电力高炉用。
     *
     * <p>用户原话：「不要改成 shift+空手拆掉了 加个扳手 手持扳手 shift+右键拆掉 材质你随意」。
     * 目前**没有合成配方**（用户没给），只能在创造模式标签页里拿 —— 已在档案 §9 标注。</p>
     */
    public static final DeferredItem<Item> WRENCH =
            ITEMS.register("wrench", () -> new Item(new Item.Properties().stacksTo(1)));

    // ========== 星轨坠 + 粗振金（0.11 ZF114）==========
    /**
     * 星轨坠：右键起手召唤一颗陨石（30 秒倒计时、前 10 秒可取消），一共 4 点耐久。
     *
     * <p>用户原话见 {@link StarfallPendantItem} 的类注释。几个要点：</p>
     * <ul>
     *   <li><b>不可附魔</b>：{@code isEnchantable} 恒 false + 不挂 {@code #minecraft:enchantable/*}
     *       任何标签（1.21.1 的 {@code Item.Properties} 里**没有** {@code enchantable(int)}，
     *       已用 javap 核过方法表 ⇒ 只能这么做）；</li>
     *   <li><b>稀有度 RARE</b>：紫名，与它的身份相称（两张唱片也是 RARE）；</li>
     *   <li><b>不可堆叠</b>：耐久道具本来就不能叠；</li>
     *   <li><b>没有合成配方</b>（用户明确"先不给配方"）⇒ 只能从创造模式拿，已记进档案 §9。</li>
     * </ul>
     */
    public static final DeferredItem<Item> STARFALL_PENDANT =
            ITEMS.register("starfall_pendant", () -> new StarfallPendantItem(new Item.Properties()
                    .stacksTo(1)
                    .durability(StarfallPendantItem.DURABILITY)
                    .rarity(Rarity.RARE)));

    /**
     * 粗振金（0.11 ZF114）：星轨坠的陨石在威力 ≥15 时**固定**喷出 3 个。
     *
     * <p>用户拍板「新增物品」：本轮只做"物品本身"（注册 + 程序生成的占位贴图 + 四语言键），
     * <b>矿石、深层变体、用途、配方都还没有</b> —— 它和"硫"当初一样，是"只有来源、没有下游"的原矿
     * （见档案 §9）。</p>
     *
     * <p>按项目规则挂在 {@code c:raw_materials/vibranium} 与父标签 {@code c:raw_materials} 上
     * （矿物/粗矿默认兼容别的 mod）⇒ 陨石"13 以上从全部粗矿里抽"那一档也有可能抽到它，
     * 这是有意的：数据驱动，以后再加粗矿不用改代码。</p>
     */
    public static final DeferredItem<Item> RAW_VIBRANIUM =
            ITEMS.register("raw_vibranium", () -> new Item(new Item.Properties()));

    // ========== 星仪图之章（0.11 ZF122）==========
    /**
     * 星仪图之章：右键顺次切换**主世界**的天空盒（原版 → 四张星图 → 循环；潜行右键往回切）。
     *
     * <p>用户原话：「星仪图之章 右键顺次切换主世界的天空盒 你看看怎么好做 图我给你了
     * 你想怎么编辑都可以 我感觉这个图真的很好看！」</p>
     *
     * <p><b>只有自己看得见</b>（用户拍板）：选中的编号存在 {@link ModDataComponents#SKY_INDEX}
     * 组件里（跟着物品栈自动同步），渲染全在客户端 —— 不发任何自定义包、不改服务器状态。
     * 默认值 0 = 原版星空，所以刚拿到的书不会一上来就把天换了。</p>
     *
     * <p>配方（0.11 ZF122）：四角纸 + 四边紫水晶碎片 + 中间荧石，图纸在
     * {@code _zf45_recipes.py} 的表里，别手改 recipe\*.json。</p>
     */
    public static final DeferredItem<Item> STAR_CHART_TOME =
            ITEMS.register("star_chart_tome", () -> new StarChartTomeItem(new Item.Properties()
                    .stacksTo(1)
                    .component(ModDataComponents.SKY_INDEX.get(), 0)));

    /**
     * 振金锭（0.11 ZF119）。用户原话：「加个振金锭（目前没配方）这是振金锭贴图 做成动态贴图 3t播放一帧」。
     *
     * <p><b>没有配方</b> —— 用户明说"目前没配方" ⇒ 盘上不许出现任何产出它的配方 JSON
     * （`_zf119_verify.py` 常驻盯着这一条）。粗振金（ZF114）→ 振金锭这条路留到以后。</p>
     *
     * <p>贴图是**动画**：`textures/item/vibranium_ingot.png`（32×320，10 帧 × 32）
     * + 同名 `.mcmeta`（`frametime = 3` ⇒ 3 tick 一帧、一轮 30 tick = 1.5 秒）。
     * 源图是用户给的 32×280 长条（10 个 32×24 的锭），重排脚本 `_zf119_texture.py`
     * 只做整行搬运（零重采样），摆位照盘上 `titanium_ingot.png`（同样 32×24 内容、上下各留 4 行）。</p>
     *
     * <p>按项目规则挂在 {@code c:ingots/vibranium} + {@code c:vibranium_ingots}
     * 与父标签 {@code c:ingots} 上（锭默认走兼容标签）。</p>
     */
    public static final DeferredItem<Item> VIBRANIUM_INGOT =
            ITEMS.register("vibranium_ingot", () -> new Item(new Item.Properties()));

    // ========== 创造模式标签页（一次拿到全部 x个物品） ==========
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> POTATO_ST_TAB =
            CREATIVE_MODE_TABS.register("potato_s_t_tab", () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.potato_s_t"))
                    // 0.11 ZF124：创造页图标 铝锭 → **星轨坠**（用户原话「创造模式标签页换成星轨坠的
                    // 物品贴图」）。`.icon(...)` 是 lambda、求值在造标签页时 ⇒ 与字段声明顺序无关
                    //（STARFALL_PENDANT 在 483 行、本行在 54x 行，静态序也本来就对）。
                    .icon(() -> new ItemStack(STARFALL_PENDANT.get()))
                    .displayItems((parameters, output) -> {
                        output.accept(ALUMINUM_INGOT.get());
                        output.accept(CARBON.get());
                        output.accept(COBALT_INGOT.get());
                        output.accept(HIGH_CARBON_STEEL.get());
                        output.accept(NICKEL_INGOT.get());
                        output.accept(SILVER_INGOT.get());
                        output.accept(TONER.get());
                        output.accept(URANIUM_INGOT.get());
                        output.accept(ModBlocks.TERMINAL_ITEM.get());
                        output.accept(COPPER_WIRE.get());
                        output.accept(EMPTY_SPOOL.get());
                        output.accept(COPPER_WIRE_SPOOL.get());
                        output.accept(SILVER_WIRE.get());            // ← 0.11 ZF127 银线
                        output.accept(SILVER_WIRE_SPOOL.get());      // ← 0.11 ZF127 银线轴
                        output.accept(ModBlocks.POWER_CAPTURER_ITEM.get());
                        output.accept(ModBlocks.GENERATOR_ITEM.get());
                        output.accept(POWER_CABLE_SPOOL.get());
                        output.accept(ModBlocks.LITHIUM_BATTERY_ITEM.get());
                        output.accept(ModBlocks.ELECTROLYZER_ITEM.get());
                        output.accept(ModBlocks.SALT_DRYER_ITEM.get());
                        output.accept(SEA_SALT.get());
                        output.accept(HIGH_PRESSURE_TANK.get());
                        output.accept(OIL_BUCKET.get());// ← 新增（0.11 ZF73 油桶）
                        output.accept(ModBlocks.FILLING_MACHINE_ITEM.get());// ← 新增
                        output.accept(ModBlocks.FLUID_PIPE_ITEM.get());
                        output.accept(ModBlocks.FLUID_PUMP_ITEM.get());
                        output.accept(ModBlocks.TEST_FLUID_TANK_ITEM.get());
                        output.accept(ModBlocks.CREATIVE_CABLE_ITEM.get());
                        output.accept(MUSIC_DISC_ANVIL_OF_THE_REPUBLIC.get());// ← 新增（0.04 音乐唱片）
                        output.accept(MUSIC_DISC_JASMINE_FLOWER.get());// ← 新增（0.11 ZF93 第二张唱片）
                        output.accept(SILICON.get());
                        output.accept(ModBlocks.MICRO_CRUSHER_ITEM.get());// ← 新增（0.10 微型粉碎机）
                        output.accept(LITHIUM_CONCENTRATE.get());// ← 新增（0.10 锂矿精粉）
                        output.accept(LITHIUM_CARBONATE.get());// ← 新增（0.10 碳酸锂）
                        output.accept(LITHIUM_BATTERY_COMPONENT.get());// ← 新增（0.11 ZF112 锂电池原件）
                        output.accept(IRON_PLATE.get());// ← 新增（0.10 板材）
                        output.accept(COPPER_PLATE.get());// ← 新增（0.10 ZF30 铜板）
                        output.accept(NICKEL_PLATE.get());
                        output.accept(COBALT_PLATE.get());
                        output.accept(SILVER_PLATE.get());
                        output.accept(ALUMINUM_PLATE.get());
                        output.accept(STEEL_PLATE.get());
                        output.accept(CAPACITOR.get());// ← 新增（0.10 电容）
                        output.accept(IRON_POWDER.get());// ← 新增（0.10 ZF45 铁粉）
                        output.accept(MAGNET.get());// ← 新增（0.10 ZF45 磁铁）
                        output.accept(THERMAL_METAL.get());// ← 新增（0.10 ZF45 热力金属）
                        output.accept(PHOTOVOLTAIC_COMPONENT.get());// ← 新增（0.10 ZF45 光伏原件）
                        output.accept(TITANIUM_INGOT.get());// ← 新增（0.10 ZF48 钛锭）
                        output.accept(LIGHT_TITANIUM_ALLOY.get());// ← 新增（0.10 ZF62 轻质钛合金）
                        output.accept(HARD_TITANIUM_ALLOY.get());// ← 新增（0.11 ZF104 硬质钛合金）
                        output.accept(TITANIUM_POWDER.get());// ← 新增（0.10 ZF48 钛粉）
                        output.accept(ModBlocks.SOLAR_PANEL_ITEM.get());// ← 新增（0.10 太阳能板）
                        output.accept(ModBlocks.HYDRAULIC_PRESS_ITEM.get());// ← 新增（0.10 ZF30 液压机）
                        output.accept(SODIUM_CHLORIDE.get());// ← 新增（0.10 ZF32 氯化钠）
                        output.accept(ModBlocks.SALT_DECOMPOSER_ITEM.get());// ← 新增（0.10 ZF32 盐分解构器）
                        output.accept(ModBlocks.COMMON_METAL_BLOCK_ITEM.get());// ← 新增（0.10 ZF34 装饰块）
                        output.accept(ModBlocks.ADVANCED_METAL_BLOCK_ITEM.get());// ← 新增（0.10 ZF34 装饰块）
                        output.accept(ModBlocks.STABLE_METAL_BLOCK_ITEM.get());// ← 新增（0.10 ZF34 装饰块）
                        output.accept(ModBlocks.HEAT_RESISTANT_METAL_BLOCK_ITEM.get());// ← 新增（0.10 ZF34 装饰块）
                        output.accept(ModBlocks.HEATER_ITEM.get());// ← 新增（0.10 ZF34 装饰块）
                        output.accept(ModBlocks.HEAT_SINK_ITEM.get());// ← 新增（0.10 ZF34 装饰块）
                        output.accept(ModBlocks.WIRING_BLOCK_ITEM.get());// ← 新增（0.10 ZF35 接线块）
                        output.accept(ModBlocks.LOW_GENERATOR_ITEM.get());// ← 新增（0.10 ZF38 低级发电机）
                        output.accept(ModBlocks.ELECTRIC_BLAST_FURNACE_ITEM.get());// ← 新增（0.10 ZF39 电力高炉）
                        output.accept(WRENCH.get());// ← 新增（0.10 ZF41 扳手）
                        output.accept(ModBlocks.ALLOY_SMELTER_ITEM.get());// ← 新增（0.10 ZF49 合金冶炼炉）
                        output.accept(TITANIUM_ALLOY_SWORD.get());// ← 新增（0.10 ZF66 钛合金剑）
                        output.accept(TITANIUM_ALLOY_PICKAXE.get());// ← 新增（0.10 ZF66 钛合金镐）
                        output.accept(ModBlocks.DISTILLATION_CONTROLLER_ITEM.get());// ← 新增（0.11 ZF78 分馏塔控制器）
                        output.accept(ModBlocks.DISTILLATION_OPERATOR_ITEM.get());// ← 新增（0.11 ZF78 分馏塔操作器）
                        output.accept(BITUMEN.get());// ← 新增（0.11 ZF78 沥青）
                        output.accept(ModBlocks.ASPHALT_BLOCK_ITEM.get());// ← 新增（0.11 ZF79 柏油块）
                        output.accept(DIESEL_BUCKET.get());// ← 新增（0.11 ZF82 柴油桶）
                        output.accept(GASOLINE_BUCKET.get());// ← 新增（0.11 ZF82 汽油桶）
                        output.accept(ModBlocks.FLUID_EXCHANGER_ITEM.get());// ← 新增（0.11 ZF82 容器换流器）
                        output.accept(SULFUR.get());// ← 新增（0.11 ZF96 硫）
                        output.accept(ModBlocks.HYDRODESULFURIZATION_CHAMBER_ITEM.get());// ← 新增（0.11 ZF96 加氢脱硫反应仓）
                        output.accept(ModBlocks.AIR_SEPARATOR_ITEM.get());// ← 新增（0.11 ZF97 空气分离器）
                        output.accept(ModBlocks.AMMONIA_SYNTHESIS_CHAMBER_ITEM.get());// ← 新增（0.11 ZF97 氨气组成室）
                        output.accept(ModBlocks.COMBUSTION_CHAMBER_ITEM.get());// ← 新增（0.11 ZF100 燃烧反应室）
                        output.accept(ModBlocks.ACIDIC_REACTION_CHAMBER_ITEM.get());// ← 新增（0.11 ZF101 酸性反应室）
                        output.accept(ModBlocks.OIL_PUMP_ITEM.get());// ← 新增（0.11 ZF109 采油机 —— ⚠ 漏过一次，见 §4.82）
                        output.accept(ModBlocks.LITHIUM_BATTERY_PLANT_ITEM.get());// ← 新增（0.11 ZF112 锂电池构造间）
                        output.accept(ModArmorItems.STAR_STEEL_INGOT.get());// ← 新增（0.11 ZF103 星璨钢锭）
                        output.accept(ModArmorItems.TITANIUM_ALLOY_HELMET.get());// ← 新增（0.11 ZF103 钛合金套）
                        output.accept(ModArmorItems.TITANIUM_ALLOY_CHESTPLATE.get());
                        output.accept(ModArmorItems.TITANIUM_ALLOY_LEGGINGS.get());
                        output.accept(ModArmorItems.TITANIUM_ALLOY_BOOTS.get());
                        output.accept(ModArmorItems.STAR_STEEL_HELMET.get());// ← 新增（0.11 ZF103 星璨钢套）
                        output.accept(ModArmorItems.STAR_STEEL_CHESTPLATE.get());
                        output.accept(ModArmorItems.STAR_STEEL_LEGGINGS.get());
                        output.accept(ModArmorItems.STAR_STEEL_BOOTS.get());
                        output.accept(STARFALL_PENDANT.get());// ← 新增（0.11 ZF114 星轨坠）
                        output.accept(RAW_VIBRANIUM.get());// ← 新增（0.11 ZF114 粗振金）
                        output.accept(VIBRANIUM_INGOT.get());// ← 新增（0.11 ZF119 振金锭）
                        output.accept(ModArmorItems.VIBRANIUM_HELMET.get());// ← 新增（0.11 ZF120 振金套）
                        output.accept(ModArmorItems.VIBRANIUM_CHESTPLATE.get());
                        output.accept(ModArmorItems.VIBRANIUM_LEGGINGS.get());
                        output.accept(ModArmorItems.VIBRANIUM_BOOTS.get());
                        output.accept(STAR_CHART_TOME.get());// ← 新增（0.11 ZF122 星仪图之章）
                        output.accept(ModBlocks.DIESEL_GENERATOR_ITEM.get());// ← 新增（0.11 ZF125 大型柴油发电机控制器）
                    })
                    .build());

}