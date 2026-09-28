package com.potatost.mod;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.mojang.logging.LogUtils;
import com.mojang.serialization.JsonOps;
import java.util.ArrayList;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import net.minecraft.ChatFormatting;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.RegistryOps;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SmithingTemplateItem;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeManager;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.SmithingTransformRecipe;
import net.minecraft.world.item.crafting.SmithingTrimRecipe;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.crafting.CompoundIngredient;
import net.neoforged.neoforge.event.OnDatapackSyncEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import org.slf4j.Logger;

/**
 * 通用升级模板（0.12 ZF155）—— 让**全游戏**「需要升级模板的升级」都能用同一件模板。
 *
 * <p>用户原话：「能不能加个通用升级模板 所有mod需要升级模板升级都可以用它
 * 如果有冲突则不可以使用（然后给振金剑加个配方 钛合金剑用这个和振金升级
 * 之前所有的振金装备下界合金模板也改成这个）获取方式；下界合金升级模板 围一圈铝锭」。
 * 拍板结果：**真·通用**（含原版下界合金）＋**有冲突就不许用**。</p>
 *
 * <p><b>怎么做到「真·通用」</b>：不改别人的数据文件，而是在**服务端装好配方表之后**，
 * 把每一条「模板槽要东西」的 {@code minecraft:smithing_transform} 配方**原地换掉**：
 * 模板槽由「原来那件模板」加宽成「原来那件模板 <b>或</b> 通用升级模板」
 * （{@link CompoundIngredient}），id 一个字都不变。于是</p>
 * <ul>
 *   <li>原版下界合金 9 条升级（{@code data/minecraft/recipe/netherite_*_smithing.json}）
 *       —— 钻石装 + 下界合金锭 + **通用升级模板** 照样出下界合金装；</li>
 *   <li>本 mod 自己的 5 条（4 件振金护甲 + 振金剑）本来就把模板写成了通用模板；</li>
 *   <li>其他 mod 只要用的是原版 {@code smithing_transform} 类型，一并生效。</li>
 * </ul>
 *
 * <p><b>为什么原地换而不是加一条新的</b>：加副本会让 JEI 里出现两条一模一样的升级，
 * 而且 id 会翻倍；原地换之后 id、配方书解锁、进度判定全都不动，玩家看到的就是原来那一条，
 * 只是模板槽多收一件东西。</p>
 *
 * <h2>四条钉在源码上的事实（本类为什么这么写）</h2>
 * <ol>
 *   <li><b>换表的官方口子</b>：{@code RecipeManager#replaceRecipes(Iterable)} 是
 *       NeoForge 加的 **public** 方法（{@code RecipeManager.java:165}），
 *       内部重建 {@code byType}/{@code byName} 两张表 —— 不用反射、不用 Mixin。</li>
 *   <li><b>挂点必须在配方同步之前</b>：{@code OnDatapackSyncEvent} 的 javadoc 原文
 *       「Fires when a player joins the server or when the reload command is ran,
 *       before tags and crafting recipes are sent to the client」；两条路径都实证过：
 *       登录 {@code PlayerList.java:208-209}、{@code /reload} {@code PlayerList.java:916-921}
 *       —— 事件先发，配方包后发。所以在这里换表，客户端（含 JEI）拿到的是**换过之后**的表。</li>
 *   <li><b>{@code /reload} 会换掉整个 RecipeManager 实例</b>（{@code MinecraftServer.java:1532}
 *       {@code this.resources = p_335203_}），所以每次都要重新取表、重新装。</li>
 *   <li><b>纹饰注定不能通用</b>：{@code TrimPatterns.getFromTemplate} 是
 *       {@code template.is(pattern.templateItem())}（{@code TrimPatterns.java:59}），
 *       图案与模板物品一一绑定；通用模板没有图案，{@code SmithingTrimRecipe.assemble}
 *       必返 {@code ItemStack.EMPTY}。所以 {@code smithing_trim} 一律不碰（记
 *       {@code trim-pattern-bound}），免得界面上出现「匹配得上却出不了东西」的假配方。</li>
 * </ol>
 *
 * <h2>「如果有冲突则不可以使用」是怎么落的</h2>
 * <p>两条升级如果**底物能对得上同一件东西、附加物也能对得上同一件东西、结果却不一样**，
 * 那玩家把通用模板放进去时游戏没法判断他要哪一个 —— 这就是冲突。冲突里的每一条
 * **都不加宽**（照旧只认它自己那件模板），并记 {@code conflict} 与 {@code |} 连起来的那一对 id。
 * 判定用**物品级重合**（底物集合相交 ∩ 附加物集合相交 ∩ 结果不同），比「配方签名相等」更严 ——
 * 宁可保守也不放一条会出错的进去。</p>
 *
 * <h2>保真复核（为什么敢用 JSON 往返）</h2>
 * <p>要造「加宽副本」得先拿到三个槽的 {@link Ingredient}，而
 * {@code SmithingTransformRecipe} 的三个字段是**包私有 final**（本类在 {@code com.potatost.mod}，
 * 拿不到），所以走官方编解码器往返：{@code RecipeSerializer.SMITHING_TRANSFORM.codec()}
 * 编码成 JSON → {@code Ingredient.CODEC} 解回来。往返**一定**要复核：
 * 对注册表里**每一件物品**逐一比对「原件判定」与「解回来的判定」是否同真同假
 * （三个槽都比），任何一处不一致就整条放弃（记 {@code fidelity-*}）。
 * 结果槽不走 JSON，直接用 {@code getResultItem()} —— 那就是原件里那一份，原样复制。</p>
 *
 * <p>⚠ 已知边界：只认**恰好是** {@code SmithingTransformRecipe} 这个类的配方
 * （子类走的是别的序列化器，JSON 往返会丢字段，记 {@code foreign-serializer}）；
 * 三个槽的保真复核用的是「每件物品的默认堆」，靠组件区分的花式原料（例如「带某附魔的剑」）
 * 只能验到物品级 —— 这类原料在锻造配方里极罕见，遇到也不会静默改语义（复核必红 ⇒ 放弃）。</p>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class UniversalUpgradeTemplate {

    /** 换表后那张表的 id 前缀（{@code potato_s_t:universal/<命名空间>/<原路径>}）。 */
    public static final String GENERATED_PREFIX = "universal/";

    private static final Logger LOGGER = LogUtils.getLogger();

    /** 幂等缓存：同一个表 + 同一个内容签名 ⇒ 已经装过，直接返回上次的计划。 */
    private static RecipeManager cachedManager;
    private static long cachedSignature = Long.MIN_VALUE;
    private static Plan cachedPlan = Plan.EMPTY;

    private UniversalUpgradeTemplate() {
    }

    // ------------------------------------------------------------------ 物品

    /**
     * 造出通用升级模板这件物品。
     *
     * <p>用原版的 {@link SmithingTemplateItem}：tooltip 会自动长出「升级 / 适用于 / 原料」
     * 三段式（{@code appendHoverText}），锻造台界面还会用下面这两串图标画出槽位提示
     * （{@code SmithingScreen} 读 {@code getBaseSlotEmptyIcons}/{@code getBaseSlotDescription}）。
     * 图标给的是「全套盔甲 + 全套工具 + 锭」，意思就是**什么升级都行**。</p>
     */
    public static SmithingTemplateItem createTemplateItem() {
        return new Template(
                Component.translatable("item.potato_s_t.universal_upgrade_template.applies_to")
                        .withStyle(ChatFormatting.BLUE),
                Component.translatable("item.potato_s_t.universal_upgrade_template.ingredients")
                        .withStyle(ChatFormatting.BLUE),
                Component.translatable("item.potato_s_t.universal_upgrade_template.desc"),
                Component.translatable("item.potato_s_t.universal_upgrade_template.base_slot"),
                Component.translatable("item.potato_s_t.universal_upgrade_template.additions_slot"),
                List.of(
                        vanillaIcon("empty_armor_slot_helmet"),
                        vanillaIcon("empty_armor_slot_chestplate"),
                        vanillaIcon("empty_armor_slot_leggings"),
                        vanillaIcon("empty_armor_slot_boots"),
                        vanillaIcon("empty_slot_sword"),
                        vanillaIcon("empty_slot_pickaxe"),
                        vanillaIcon("empty_slot_axe"),
                        vanillaIcon("empty_slot_shovel"),
                        vanillaIcon("empty_slot_hoe")),
                List.of(vanillaIcon("empty_slot_ingot")));
    }

    /** 原版空槽图标名：盔甲那四个带 {@code empty_armor_slot_} 前缀，工具与锭是 {@code empty_slot_}。 */
    private static ResourceLocation vanillaIcon(String name) {
        return ResourceLocation.withDefaultNamespace("item/" + name);
    }

    /**
     * 原版模板物品 + 一行规则说明。
     *
     * <p>继承而不是另起炉灶：{@code SmithingTemplateItem#appendHoverText} 那段
     * 「升级 / 适用于 / 原料」是原版自己的排版，白拿；这里只在末尾补一行
     * {@code .rule} —— 把「纹饰不吃」与「有冲突不许用」直接写在脸上，
     * 省得玩家去翻手册才知道为什么放进去没反应。</p>
     */
    private static final class Template extends SmithingTemplateItem {

        private static final Component RULE =
                Component.translatable("item.potato_s_t.universal_upgrade_template.rule")
                        .withStyle(ChatFormatting.DARK_GRAY);

        private Template(Component appliesTo, Component ingredients, Component upgradeDescription,
                Component baseSlotDescription, Component additionsSlotDescription,
                List<ResourceLocation> baseSlotEmptyIcons, List<ResourceLocation> additionalSlotEmptyIcons) {
            super(appliesTo, ingredients, upgradeDescription, baseSlotDescription,
                    additionsSlotDescription, baseSlotEmptyIcons, additionalSlotEmptyIcons);
        }

        @Override
        public void appendHoverText(ItemStack stack, TooltipContext context,
                List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
            super.appendHoverText(stack, context, tooltipComponents, tooltipFlag);
            tooltipComponents.add(Component.empty());
            tooltipComponents.add(RULE);
        }
    }

    // ------------------------------------------------------------------ 挂点

    /** 开服就装一次：世界加载完、**任何玩家进来之前**（所以不用等登录）。 */
    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        install(event.getServer());
    }

    /**
     * 登录与 {@code /reload} 都会走这里，而且**在配方包发出之前**。
     *
     * <p>{@code /reload} 会把整个 RecipeManager 换成新实例（表回到原样），
     * 所以这里必须再装一次；靠 {@link #install} 里的幂等缓存，
     * 单纯登录时这次调用是一顿饭钱的空转。</p>
     */
    @SubscribeEvent
    public static void onDatapackSync(OnDatapackSyncEvent event) {
        install(event.getPlayerList().getServer());
    }

    /**
     * 把「通用模板可用」这件事装进当前配方表（幂等）。
     *
     * @return 本次实际算出来的计划（装过了就直接返回上次那份，不重复扫表）
     */
    public static Plan install(MinecraftServer server) {
        RecipeManager manager = server.getRecipeManager();
        List<RecipeHolder<?>> current = List.copyOf(manager.getRecipes());
        long signature = signature(current);
        if (manager == cachedManager && signature == cachedSignature) {
            return cachedPlan;
        }

        Plan plan = plan(current, server.registryAccess());
        if (!plan.replacements().isEmpty()) {
            Map<ResourceLocation, RecipeHolder<?>> byId = new LinkedHashMap<>();
            for (RecipeHolder<?> holder : current) {
                byId.put(holder.id(), holder);
            }
            for (RecipeHolder<?> holder : plan.replacements()) {
                byId.put(holder.id(), holder);
            }
            manager.replaceRecipes(byId.values());
        }

        cachedManager = manager;
        cachedSignature = signature(List.copyOf(manager.getRecipes()));
        cachedPlan = plan;
        report(plan);
        return plan;
    }

    // ------------------------------------------------------------------ 计划

    /**
     * 算出「该把哪些配方换成加宽版」——**纯函数**（只看传进来的表），探针可以直接喂假表来验规则。
     *
     * @param recipes    当前全部配方（通常是 {@code RecipeManager#getRecipes()}）
     * @param registries 注册表访问（编码/解码原料要用它）
     */
    public static Plan plan(Iterable<RecipeHolder<?>> recipes, HolderLookup.Provider registries) {
        RegistryOps<JsonElement> ops = RegistryOps.create(JsonOps.INSTANCE, registries);
        Item universalItem = ModItems.UNIVERSAL_UPGRADE_TEMPLATE.get();
        ItemStack universalStack = new ItemStack(universalItem);
        Ingredient universalIngredient = Ingredient.of(universalItem);

        List<RecipeHolder<?>> all = new ArrayList<>();
        recipes.forEach(all::add);
        Set<ResourceLocation> existingIds = new LinkedHashSet<>();
        for (RecipeHolder<?> holder : all) {
            existingIds.add(holder.id());
        }

        List<Candidate> candidates = new ArrayList<>();
        List<Candidate> already = new ArrayList<>();
        List<String> skipped = new ArrayList<>();

        for (RecipeHolder<?> holder : all) {
            Recipe<?> value = holder.value();
            if (value instanceof SmithingTrimRecipe) {
                // 图案与模板物品绑定，通用模板没有图案 ⇒ 加宽只会造出「匹配得上却出不了东西」的假配方
                skipped.add(holder.id() + "|trim-pattern-bound");
                continue;
            }
            if (!(value instanceof SmithingTransformRecipe transform)) {
                continue;
            }
            if (value.getClass() != SmithingTransformRecipe.class) {
                skipped.add(holder.id() + "|foreign-serializer");
                continue;
            }
            boolean alreadyUniversal = transform.isTemplateIngredient(universalStack);
            Candidate candidate = read(holder, transform, ops, registries, skipped);
            if (candidate == null) {
                continue;
            }
            if (alreadyUniversal) {
                already.add(candidate);
            } else {
                candidates.add(candidate);
            }
        }

        // 冲突：底物重合 ∩ 附加物重合 ∩ 结果不同 ⇒ 通用模板判断不了要哪一个 ⇒ 都不许用
        List<Candidate> universe = new ArrayList<>(already);
        universe.addAll(candidates);
        Set<Candidate> conflicted = Collections.newSetFromMap(new IdentityHashMap<>());
        Set<String> conflicts = new LinkedHashSet<>();
        for (int i = 0; i < universe.size(); i++) {
            for (int j = i + 1; j < universe.size(); j++) {
                Candidate a = universe.get(i);
                Candidate b = universe.get(j);
                if (!overlap(a.baseItems(), b.baseItems()) || !overlap(a.additionItems(), b.additionItems())) {
                    continue;
                }
                if (ItemStack.isSameItemSameComponents(a.result(), b.result())) {
                    continue;
                }
                conflicted.add(a);
                conflicted.add(b);
                conflicts.add(a.holder().id() + "|" + b.holder().id());
            }
        }

        List<RecipeHolder<?>> replacements = new ArrayList<>();
        List<String> widened = new ArrayList<>();
        for (Candidate candidate : candidates) {
            ResourceLocation id = candidate.holder().id();
            if (conflicted.contains(candidate)) {
                skipped.add(id + "|conflict");
                continue;
            }
            if (candidate.template().hasNoItems()) {
                // 模板槽本来就「什么都不收」的配方，加宽等于改变它的语义 ⇒ 不碰
                skipped.add(id + "|empty-template");
                continue;
            }
            Ingredient widenedTemplate = CompoundIngredient.of(candidate.template(), universalIngredient);
            if (!widenedTemplate.test(universalStack)) {
                skipped.add(id + "|widen-failed");
                continue;
            }
            ResourceLocation generated = generatedId(id);
            if (existingIds.contains(generated)) {
                skipped.add(id + "|id-taken");
                continue;
            }
            replacements.add(new RecipeHolder<>(id, new SmithingTransformRecipe(
                    widenedTemplate, candidate.base(), candidate.addition(), candidate.result().copy())));
            widened.add(id.toString());
        }

        List<String> alreadyIds = new ArrayList<>();
        for (Candidate candidate : already) {
            alreadyIds.add(candidate.holder().id().toString());
        }
        return new Plan(List.copyOf(replacements), List.copyOf(widened), List.copyOf(conflicts),
                List.copyOf(skipped), List.copyOf(alreadyIds));
    }

    /**
     * 读一条配方：编码成 JSON → 解回三个原料 → **逐物品保真复核** → 攒成候选。
     *
     * @return 复核不通过就返回 {@code null}（原因已记进 {@code skipped}）
     */
    private static Candidate read(RecipeHolder<?> holder, SmithingTransformRecipe transform,
            RegistryOps<JsonElement> ops, HolderLookup.Provider registries, List<String> skipped) {
        Optional<JsonElement> encoded =
                RecipeSerializer.SMITHING_TRANSFORM.codec().codec().encodeStart(ops, transform).result();
        if (encoded.isEmpty() || !encoded.get().isJsonObject()) {
            skipped.add(holder.id() + "|encode-failed");
            return null;
        }
        JsonObject json = encoded.get().getAsJsonObject();
        Ingredient template = decode(ops, json, "template");
        Ingredient base = decode(ops, json, "base");
        Ingredient addition = decode(ops, json, "addition");
        if (template == null || base == null || addition == null) {
            skipped.add(holder.id() + "|decode-failed");
            return null;
        }
        String mismatch = fidelity(transform, template, base, addition);
        if (mismatch != null) {
            skipped.add(holder.id() + "|" + mismatch);
            return null;
        }
        ItemStack result = transform.getResultItem(registries);
        return new Candidate(holder, template, base, addition, result,
                itemSet(base), itemSet(addition));
    }

    private static Ingredient decode(RegistryOps<JsonElement> ops, JsonObject json, String key) {
        JsonElement element = json.get(key);
        if (element == null) {
            return null;
        }
        return Ingredient.CODEC.parse(ops, element).result().orElse(null);
    }

    /**
     * 保真复核：解回来的三个槽必须在**注册表里每一件物品**上与原件同真同假。
     *
     * <p>这是「JSON 往返没丢信息」的实证，也是本类唯一敢给别的 mod 配方动手的理由。</p>
     */
    private static String fidelity(SmithingTransformRecipe original, Ingredient template,
            Ingredient base, Ingredient addition) {
        for (Item item : BuiltInRegistries.ITEM) {
            ItemStack stack = new ItemStack(item);
            if (original.isTemplateIngredient(stack) != template.test(stack)) {
                return "fidelity-template";
            }
            if (original.isBaseIngredient(stack) != base.test(stack)) {
                return "fidelity-base";
            }
            if (original.isAdditionIngredient(stack) != addition.test(stack)) {
                return "fidelity-addition";
            }
        }
        return null;
    }

    /** 一件原料「收哪些物品」：默认堆实测 ∪ 它自报的展示堆（后者兜住按组件匹配的花式原料）。 */
    private static Set<Item> itemSet(Ingredient ingredient) {
        Set<Item> items = new LinkedHashSet<>();
        for (Item item : BuiltInRegistries.ITEM) {
            if (ingredient.test(new ItemStack(item))) {
                items.add(item);
            }
        }
        for (ItemStack stack : ingredient.getItems()) {
            if (!stack.isEmpty()) {
                items.add(stack.getItem());
            }
        }
        return items;
    }

    private static boolean overlap(Set<Item> a, Set<Item> b) {
        Set<Item> small = a.size() <= b.size() ? a : b;
        Set<Item> big = small == a ? b : a;
        for (Item item : small) {
            if (big.contains(item)) {
                return true;
            }
        }
        return false;
    }

    /** 换表后那张表的 id：{@code potato_s_t:universal/<命名空间>/<原路径>}。 */
    public static ResourceLocation generatedId(ResourceLocation original) {
        return ResourceLocation.fromNamespaceAndPath(PotatoST.MODID,
                GENERATED_PREFIX + original.getNamespace() + "/" + original.getPath());
    }

    private static long signature(List<RecipeHolder<?>> recipes) {
        long hash = 1125899906842597L;
        for (RecipeHolder<?> holder : recipes) {
            hash = 31L * hash + holder.id().hashCode();
        }
        return hash;
    }

    private static void report(Plan plan) {
        if (plan.widened().isEmpty() && plan.conflicts().isEmpty() && plan.replacements().isEmpty()) {
            return;
        }
        LOGGER.info("[potato_s_t] universal upgrade template: widened={} conflict={} skipped={} already={}",
                plan.widened().size(), plan.conflicts().size(), plan.skipped().size(), plan.already().size());
        for (String pair : plan.conflicts()) {
            LOGGER.warn("[potato_s_t] universal template NOT usable (conflict): {}", pair);
        }
        Map<String, List<String>> byReason = new LinkedHashMap<>();
        for (String entry : plan.skipped()) {
            int cut = entry.lastIndexOf('|');
            if (cut < 0) {
                continue;
            }
            byReason.computeIfAbsent(entry.substring(cut + 1), key -> new ArrayList<>())
                    .add(entry.substring(0, cut));
        }
        byReason.forEach((reason, ids) -> LOGGER.info(
                "[potato_s_t] universal template skipped ({}): {} {}",
                reason, ids.size(), ids.size() > 4 ? ids.subList(0, 4) + " ..." : ids));
    }

    /** 一条候选升级：原配方 + 解回来的三个槽 + 底物/附加物的物品集合。 */
    private record Candidate(RecipeHolder<?> holder, Ingredient template, Ingredient base,
            Ingredient addition, ItemStack result, Set<Item> baseItems, Set<Item> additionItems) {
    }

    /**
     * 本次计划：{@code replacements} 是**同 id** 的加宽版（原版换原版，数量可能为 0）。
     *
     * @param replacements 要拿去替换的加宽版（id 与原配方相同）
     * @param widened      成功加宽的配方 id（给人看的）
     * @param conflicts    冲突对（{@code 甲|乙}，两条都不许用通用模板）
     * @param skipped      其余跳过项（{@code id|原因码}）
     * @param already      本来就认通用模板的配方 id（本 mod 数据里写死的 5 条）
     */
    public record Plan(List<RecipeHolder<?>> replacements, List<String> widened, List<String> conflicts,
            List<String> skipped, List<String> already) {
        static final Plan EMPTY = new Plan(List.of(), List.of(), List.of(), List.of(), List.of());
    }
}
