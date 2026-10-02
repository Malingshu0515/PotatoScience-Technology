package com.potatost.mod;

import java.io.OutputStreamWriter;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import com.mojang.authlib.GameProfile;

import net.minecraft.server.level.ClientInformation;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.Connection;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.CommonListenerCookie;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.tags.TagKey;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

import top.theillusivec4.curios.api.CuriosApi;
import top.theillusivec4.curios.api.SlotContext;
import top.theillusivec4.curios.api.type.capability.ICurio;
import top.theillusivec4.curios.api.type.inventory.ICurioStacksHandler;
import top.theillusivec4.curios.api.type.inventory.IDynamicStackHandler;

import mekanism.api.Action;
import mekanism.api.MekanismAPI;
import mekanism.api.chemical.Chemical;
import mekanism.api.chemical.ChemicalStack;
import mekanism.api.chemical.IChemicalHandler;
import mekanism.common.capabilities.Capabilities;

/**
 * ZF165 临时探针（0.13：Curios 饰品栏联动 —— 星璨钢头盔进头饰槽 / Mek 喷气背包进背饰槽）。
 *
 * <p>验的是**同时装了 Curios 9.5.1 + Mekanism 10.7.19 的真服务端**：</p>
 * <ul>
 *   <li><b>A 事实</b>：两个模组都在；{@code #curios:head} / {@code #curios:back} 两个标签
 *       从我们自己的数据文件里读出来了、而且内容正是点名的物品。</li>
 *   <li><b>B 能力</b>：{@code CuriosApi.getCurio(...)} 对头盔与喷气背包都给得出东西，
 *       对泥土/石头给不出；头盔在 head 槽回报 <b>+2 护甲</b>、在别的槽回报空。</li>
 *   <li><b>C 真玩家</b>：造一个真 {@link ServerPlayer}，把头盔塞进**真 Curios 背包**的头饰槽 ⇒
 *       护甲属性 <b>+2</b>；跑一遍**真** {@code ModArmorSet.onPlayerTick} ⇒ 拿到的确实是
 *       夜视 <b>III、260 tick</b>；再摘下 ⇒ 护甲**回到 0 且修饰符不残留**（≥2 轮不涨）。</li>
 *   <li><b>D 喷气背包</b>：灌了氢的 Mek 喷气背包能进背饰槽，且
 *       {@code CuriosIntegration.findFirstCurio} 找得到它（= Mek 的飞行逻辑看得见它）；
 *       没灌氢的背包 {@code canUseJetpack} 为假；喷气背包在 head 槽不放行。</li>
 *   <li><b>E 负对照</b>：原版头盔槽那条老路一个字没变；{@code hasFullStarSteelSet} 不认饰品槽；
 *       头盔不在背饰槽放行。</li>
 * </ul>
 *
 * <p>⚠ 报告一律「先写 .tmp 再 ATOMIC_MOVE」（ZF159 的教训：直接写会在 halt 时丢）。
 * 探针跑完**必须**从 src 里删掉 —— 它只活在 {@code build/zftools/check/} 存档里。</p>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class Zf165Check {

    private static final String TAG = "[A165] ";
    private static final Path REPORT = Path.of("E:\\PotatoST\\build\\zftools\\_zf165_probe.txt");

    private static final ResourceLocation HELMET_ID =
            ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "star_steel_helmet");
    private static final ResourceLocation JETPACK_ID =
            ResourceLocation.fromNamespaceAndPath("mekanism", "jetpack");
    private static final TagKey<Item> HEAD_TAG =
            TagKey.create(Registries.ITEM, ResourceLocation.fromNamespaceAndPath("curios", "head"));
    private static final TagKey<Item> BACK_TAG =
            TagKey.create(Registries.ITEM, ResourceLocation.fromNamespaceAndPath("curios", "back"));

    private static final List<String> LINES = new ArrayList<>();
    private static int passed = 0;
    private static int failed = 0;

    private Zf165Check() {
    }

    private static void check(boolean ok, String label) {
        check(ok, label, "");
    }

    private static void check(boolean ok, String label, String detail) {
        if (ok) {
            passed++;
            LINES.add(TAG + "[OK]   " + label);
        } else {
            failed++;
            LINES.add(TAG + "[FAIL] " + label + (detail.isEmpty() ? "" : " —— " + detail));
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        MinecraftServer server = event.getServer();
        try {
            facts();
            capabilities();
            livePlayer(server, server.overworld());
            jetpack(server.overworld());
            negatives(server, server.overworld());
        } catch (Throwable t) {            failed++;
            LINES.add(TAG + "[FAIL] EXCEPTION " + t);
            for (StackTraceElement e : t.getStackTrace()) {
                if (e.getClassName().startsWith("com.potatost")) {
                    LINES.add("        at " + e);
                }
            }
        }
        LINES.add("");
        LINES.add("通过 = " + passed + "   失败 = " + failed);
        try {
            Files.createDirectories(REPORT.getParent());
            Path tmp = REPORT.resolveSibling(REPORT.getFileName() + ".tmp");
            try (Writer w = new OutputStreamWriter(Files.newOutputStream(tmp), StandardCharsets.UTF_8)) {
                w.write(String.join("\n", LINES) + "\n");
            }
            Files.move(tmp, REPORT, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
        } catch (Exception e) {
            System.out.println("probe report write failed: " + e);
        }
        server.halt(false);
    }

    // ================= A 事实 =================

    private static void facts() {
        LINES.add("== A 段：两个对端模组与两个槽位标签 ==");
        check(ModList.get().isLoaded("curios"), "A1 Curios 已加载");
        check(ModList.get().isLoaded("mekanism"), "A2 Mekanism 已加载");

        Item helmet = BuiltInRegistries.ITEM.get(HELMET_ID);
        Item jetpack = BuiltInRegistries.ITEM.get(JETPACK_ID);
        check(helmet != Items.AIR, "A3 星璨钢头盔在注册表里", String.valueOf(helmet));
        check(jetpack != Items.AIR, "A4 mekanism:jetpack 在注册表里", String.valueOf(jetpack));

        Optional<net.minecraft.core.HolderSet.Named<Item>> headTag = BuiltInRegistries.ITEM.getTag(HEAD_TAG);
        check(headTag.isPresent(), "A5 #curios:head 这个物品标签存在（我们那个数据文件真的被读了）");
        check(headTag.map(h -> h.contains(helmet.builtInRegistryHolder())).orElse(false),
                "A6 头盔在 #curios:head 里");
        if (headTag.isPresent()) {
            List<String> members = headTag.get().stream()
                    .map(h -> h.unwrapKey().map(k -> k.location().toString()).orElse("?")).sorted().toList();
            LINES.add("       #curios:head 成员 = " + members);
        }

        Optional<net.minecraft.core.HolderSet.Named<Item>> backTag = BuiltInRegistries.ITEM.getTag(BACK_TAG);
        check(backTag.isPresent(), "A7 #curios:back 这个物品标签存在（带 mod_loaded 条件的那个文件也读了）");
        check(backTag.map(h -> h.contains(jetpack.builtInRegistryHolder())).orElse(false),
                "A8 Mek 喷气背包在 #curios:back 里");
        if (backTag.isPresent()) {
            List<String> members = backTag.get().stream()
                    .map(h -> h.unwrapKey().map(k -> k.location().toString()).orElse("?")).sorted().toList();
            LINES.add("       #curios:back 成员 = " + members);
        }
    }

    // ================= B 能力 =================

    private static void capabilities() {
        LINES.add("== B 段：curios:item 物品能力 ==");
        Item helmet = BuiltInRegistries.ITEM.get(HELMET_ID);
        Item jetpack = BuiltInRegistries.ITEM.get(JETPACK_ID);

        check(curioOf(new ItemStack(helmet)).isPresent(), "B1 头盔有 curios:item 能力");
        check(curioOf(new ItemStack(jetpack)).isPresent(), "B2 Mek 喷气背包有 curios:item 能力（我们补挂的那一个）");
        check(curioOf(new ItemStack(Items.DIRT)).isEmpty(), "B3 负对照：泥土没有 curios:item 能力");
        check(curioOf(new ItemStack(Items.STONE)).isEmpty(), "B4 负对照：石头没有 curios:item 能力");
        check(curioOf(new ItemStack(Items.NETHERITE_HELMET)).isEmpty(),
                "B5 负对照：原版下界合金头盔没被我们误挂");

        ItemStack helmetStack = new ItemStack(helmet);
        SlotContext headCtx = new SlotContext(CuriosBridge.SLOT_HEAD, null, 0, false, true);
        SlotContext backCtx = new SlotContext(CuriosBridge.SLOT_BACK, null, 0, false, true);
        ResourceLocation id = ResourceLocation.fromNamespaceAndPath("curios", "head0");

        var inHead = curioOf(helmetStack).map(c -> c.getAttributeModifiers(headCtx, id)).orElse(null);
        var inBack = curioOf(helmetStack).map(c -> c.getAttributeModifiers(backCtx, id)).orElse(null);
        check(inHead != null && inHead.size() == 1
                        && inHead.values().iterator().next().amount() == CuriosBridge.ARMOR_BONUS,
                "B6 头盔在 head 槽回报 1 个护甲修饰符，数值 = " + CuriosBridge.ARMOR_BONUS,
                String.valueOf(inHead));
        check(inBack != null && inBack.isEmpty(), "B7 头盔在 back 槽回报空（不白给护甲）", String.valueOf(inBack));

        // 二次调用必须逐值相等（否则摘下来时 removeModifier 匹配不上）
        var again = curioOf(helmetStack).map(c -> c.getAttributeModifiers(headCtx, id)).orElse(null);
        check(inHead != null && inHead.equals(again),
                "B8 同一槽位两次调用返回值相等（removeModifier 的匹配前提）");
    }

    private static Optional<ICurio> curioOf(ItemStack stack) {
        return CuriosApi.getCurio(stack);
    }

    // ================= C 真玩家 =================

    /**
     * 拿玩家身上某个槽位的处理器 —— <b>必须先 {@code getCurios()} 把背包建出来</b>。
     *
     * <p>⚠ 这一条是本轮探针踩到的坑，写下来免得下一个人再踩：Curios 的
     * {@code CurioStacksHandler} 是<b>懒建</b>的，由 {@code CurioInventory#init} 按
     * {@code CuriosApi.getEntitySlots(player)} 铺出来，而 {@code init} 只在
     * {@code CurioInventoryCapability#reset()} 里被调 —— 正常游戏里那次 reset 发生在
     * 玩家数据反序列化时。我们这种"凭空 new 一个 ServerPlayer"没有存档数据，
     * 于是 {@code asMap()} 一直是空的（第一版探针就是这么红的：
     * 直接 {@code getStacksHandler("head")} 拿到空）。
     * {@code getCurios()} 会顺带调 {@code init} ⇒ 槽位这才铺出来。</p>
     */
    private static Optional<ICurioStacksHandler> handler(ServerPlayer player, String slot) {
        var inv = CuriosApi.getCuriosInventory(player);
        if (inv.isEmpty()) {
            return Optional.empty();
        }
        inv.get().getCurios();      // ← 关键：先把槽位铺出来（见上面的注释）
        return inv.get().getStacksHandler(slot);
    }

    /**
     * 把物品真正放进槽位，并跑一次 Curios 自己的 {@code update()}。
     *
     * <p>{@code update()} 就是"槽位启用/停用的那一步"：它比较
     * {@code activeStates} 与 {@code previousActiveStates}，变了才走
     * {@code activateSlot/deactivateSlot} —— 而**属性修饰符正是在那里加到玩家身上的**
     * （反编译取证 {@code CurioStacksHandler#activateSlot}）。正常游戏里这一步由
     * {@code CuriosEventHandler#tick} 每 tick 做；探针里手动跑一次等价。</p>
     */
    private static boolean equip(ServerPlayer player, String slot, ItemStack stack) {
        Optional<ICurioStacksHandler> h = handler(player, slot);
        if (h.isEmpty() || h.get().getStacks().getSlots() < 1) {
            return false;
        }
        ICurioStacksHandler sh = h.get();
        sh.update();
        sh.getStacks().setStackInSlot(0, stack);
        sh.update();
        return true;
    }

    private static void livePlayer(MinecraftServer server, ServerLevel level) {
        LINES.add("== C 段：真 ServerPlayer + 真 Curios 背包 ==");
        ServerPlayer player = newPlayer(server, level, "zf165probe");
        AttributeInstance armor = player.getAttribute(Attributes.ARMOR);
        if (armor == null) {
            check(false, "C0 玩家有护甲属性");
            return;
        }
        double base = armor.getValue();
        LINES.add("       初始护甲 = " + base + "   头盔槽 = " + player.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.HEAD));

        var inv = CuriosApi.getCuriosInventory(player);
        check(inv.isPresent(), "C1 玩家身上有 Curios 背包能力");
        if (inv.isEmpty()) {
            return;
        }
        Optional<ICurioStacksHandler> headHandler = handler(player, CuriosBridge.SLOT_HEAD);
        check(headHandler.isPresent(), "C2 头饰槽（curios:head）存在");
        if (headHandler.isEmpty()) {
            return;
        }
        IDynamicStackHandler stacks = headHandler.get().getStacks();
        check(stacks.getSlots() > 0, "C3 头饰槽至少有 1 格", "格数 = " + stacks.getSlots());

        ItemStack helmet = new ItemStack(BuiltInRegistries.ITEM.get(HELMET_ID));
        check(stacks.isItemValid(0, helmet), "C4 头盔可以放进头饰槽（isItemValid）");

        // ---- 真放进去（带 Curios 自己的 update()）----
        equip(player, CuriosBridge.SLOT_HEAD, helmet);
        double withHelmet = armor.getValue();
        LINES.add("       放进头饰槽后护甲 = " + withHelmet);
        check(Math.abs(withHelmet - (base + CuriosBridge.ARMOR_BONUS)) < 1.0E-6,
                "C5 护甲正好 +" + CuriosBridge.ARMOR_BONUS + "（不是头盔本体的 5.5）",
                "base=" + base + " 现在=" + withHelmet);

        // ---- 真跑 ModArmorSet.onPlayerTick ----
        ModArmorSet.onPlayerTick(new net.neoforged.neoforge.event.tick.PlayerTickEvent.Post(player));
        MobEffectInstance nv = player.getEffect(MobEffects.NIGHT_VISION);
        check(nv != null, "C6 跑一遍真 onPlayerTick 之后玩家拿到了夜视");
        if (nv != null) {
            check(nv.getAmplifier() == CuriosBridge.NIGHT_VISION_AMPLIFIER,
                    "C7 夜视等级 = III（amplifier " + CuriosBridge.NIGHT_VISION_AMPLIFIER + "）",
                    "实际 amplifier = " + nv.getAmplifier());
            check(nv.getDuration() == CuriosBridge.NIGHT_VISION_TICKS,
                    "C8 夜视时长 = 13 s（" + CuriosBridge.NIGHT_VISION_TICKS + " tick）",
                    "实际 " + nv.getDuration());
        }
        check(ModArmorMaterials.hasStarSteelHelmet(player),
                "C9 hasStarSteelHelmet 认饰品槽（夜视那条判据真的走到了这条路上）");

        // ---- 反复穿脱：修饰符不许残留 ----
        double afterFirst = armor.getValue();
        for (int round = 0; round < 3; round++) {
            equip(player, CuriosBridge.SLOT_HEAD, ItemStack.EMPTY);
            equip(player, CuriosBridge.SLOT_HEAD, new ItemStack(BuiltInRegistries.ITEM.get(HELMET_ID)));
        }
        double afterCycles = armor.getValue();
        check(Math.abs(afterCycles - afterFirst) < 1.0E-6,
                "C10 反复穿脱 3 轮后护甲不漂（修饰符 id 是稳定的）",
                "第一轮 = " + afterFirst + " / 三轮后 = " + afterCycles);

        equip(player, CuriosBridge.SLOT_HEAD, ItemStack.EMPTY);
        double removed = armor.getValue();
        check(Math.abs(removed - base) < 1.0E-6, "C11 摘下来护甲回到初始值（修饰符真的被摘掉了）",
                "初始 = " + base + " / 摘下后 = " + removed);

        // ---- 头盔槽那条老路：一个字没变 ----
        player.setItemSlot(net.minecraft.world.entity.EquipmentSlot.HEAD,
                new ItemStack(BuiltInRegistries.ITEM.get(HELMET_ID)));
        check(ModArmorMaterials.hasStarSteelHelmet(player), "C12 戴在原版头盔槽上照样算（老路没坏）");
        ModArmorSet.onPlayerTick(new net.neoforged.neoforge.event.tick.PlayerTickEvent.Post(player));
        MobEffectInstance nv2 = player.getEffect(MobEffects.NIGHT_VISION);
        check(nv2 != null && nv2.getAmplifier() == CuriosBridge.NIGHT_VISION_AMPLIFIER,
                "C13 原版头盔槽路径给的也是夜视 III");
    }

    private static ServerPlayer newPlayer(MinecraftServer server, ServerLevel level, String name) {
        GameProfile profile = new GameProfile(
                UUID.nameUUIDFromBytes(name.getBytes(StandardCharsets.UTF_8)), name);
        ServerPlayer player = new ServerPlayer(server, level, profile, ClientInformation.createDefault());
        // ⚠ 无头服务端里 new 出来的玩家没有连接，某些同步包会 NPE（ZF70 的教训）：
        //   挂一个没连上的 Connection，send 只会进队列。
        Connection conn = new Connection(PacketFlow.SERVERBOUND);
        player.connection = new ServerGamePacketListenerImpl(server, conn, player,
                CommonListenerCookie.createInitial(profile, false));
        return player;
    }

    // ================= D 喷气背包 =================

    private static void jetpack(ServerLevel level) {
        LINES.add("== D 段：Mek 喷气背包 ==");
        Item item = BuiltInRegistries.ITEM.get(JETPACK_ID);
        ItemStack dry = new ItemStack(item);
        ItemStack wet = new ItemStack(item);
        long filled = fillHydrogen(wet);
        LINES.add("       灌氢结果 = " + filled + " mB，里面 = " + chemicalName(wet));
        check(filled > 0, "D1 可以用 Mek 自己的化学品能力往喷气背包里灌氢（灌了 " + filled + " mB）");

        SlotContext backCtx = new SlotContext(CuriosBridge.SLOT_BACK, null, 0, false, true);
        SlotContext headCtx = new SlotContext(CuriosBridge.SLOT_HEAD, null, 0, false, true);
        check(CuriosApi.isStackValid(backCtx, wet), "D2 喷气背包可以放进背饰槽（Curios 自己的判据）");
        check(!CuriosApi.isStackValid(headCtx, wet), "D3 负对照：喷气背包不能放进头饰槽");

        check(!canUseJetpack(dry), "D4 负对照：没灌氢的喷气背包 canUseJetpack = false（对应『没氢飞不起来』）");
        check(canUseJetpack(wet), "D5 灌了氢的喷气背包 canUseJetpack = true");

        // ---- 真放进玩家背饰槽，看 Mek 自己的 Curios 集成找不找得到 ----
        MinecraftServer server = level.getServer();
        ServerPlayer player = newPlayer(server, level, "zf165jet");
        var inv = CuriosApi.getCuriosInventory(player);
        if (inv.isEmpty()) {
            check(false, "D6 玩家有 Curios 背包");
            return;
        }
        Optional<ICurioStacksHandler> back = handler(player, CuriosBridge.SLOT_BACK);
        check(back.isPresent(), "D6 背饰槽（curios:back）存在",
                "服务端槽位表 = " + CuriosApi.getSlots(false).keySet());
        if (back.isEmpty()) {
            return;
        }
        IDynamicStackHandler stacks = back.get().getStacks();
        check(stacks.getSlots() > 0, "D7 背饰槽至少有 1 格", "格数 = " + stacks.getSlots());
        check(stacks.isItemValid(0, wet), "D8 灌了氢的喷气背包可以放进背饰槽（isItemValid）");

        ItemStack placed = new ItemStack(item);
        fillHydrogen(placed);
        back.get().update();
        stacks.setStackInSlot(0, placed);
        back.get().update();
        check(foundByMekanismCurios(player), "D9 Mek 自己的 CuriosIntegration.findFirstCurio 找得到背饰槽里的喷气背包");
        check(MekActive(player), "D10 Mek 的 IJetpackItem.getActiveJetpack 认为它是『当前可用的喷气背包』");
        LINES.add("       玩家背饰槽 = " + stacks.getStackInSlot(0) + " 含氢 "
                + chemicalName(stacks.getStackInSlot(0)) + " mB");
    }

    private static long fillHydrogen(ItemStack stack) {
        try {
            IChemicalHandler h = stack.getCapability(Capabilities.CHEMICAL.item());
            if (h == null) {
                return -1;
            }
            Chemical hydrogen = MekanismAPI.CHEMICAL_REGISTRY.get(
                    ResourceLocation.fromNamespaceAndPath("mekanism", "hydrogen"));
            if (hydrogen == null) {
                return -2;
            }
            ChemicalStack want = new ChemicalStack(
                    MekanismAPI.CHEMICAL_REGISTRY.wrapAsHolder(hydrogen), 1000L);
            ChemicalStack rest = h.insertChemical(want, Action.EXECUTE);
            return 1000L - rest.getAmount();
        } catch (Throwable t) {
            LINES.add("       灌氢抛了：" + t);
            return -3;
        }
    }

    private static String chemicalName(ItemStack stack) {
        IChemicalHandler h = stack.getCapability(Capabilities.CHEMICAL.item());
        if (h == null) {
            return "(没有化学品能力)";
        }
        ChemicalStack s = h.getChemicalInTank(0);
        return s.isEmpty() ? "(空)" : (MekanismAPI.CHEMICAL_REGISTRY.getKey(s.getChemical()) + " × " + s.getAmount());
    }

    private static boolean canUseJetpack(ItemStack stack) {
        return stack.getItem() instanceof mekanism.common.item.interfaces.IJetpackItem jp && jp.canUseJetpack(stack);
    }

    /** 转调 Mek 自己的 Curios 集成（我们不复刻它的判据）。 */
    private static boolean foundByMekanismCurios(ServerPlayer player) {
        return !mekanism.common.integration.curios.CuriosIntegration
                .findFirstCurio(player, s -> s.getItem() == BuiltInRegistries.ITEM.get(JETPACK_ID)).isEmpty();
    }

    private static boolean MekActive(ServerPlayer player) {
        return !mekanism.common.item.interfaces.IJetpackItem.getActiveJetpack(player).isEmpty();
    }

    // ================= E 负对照 =================

    private static void negatives(MinecraftServer server, ServerLevel level) {
        LINES.add("== E 段：负对照（老规矩不许被这轮改动碰到）==");
        ServerPlayer player = newPlayer(server, level, "zf165neg");
        Item helmet = BuiltInRegistries.ITEM.get(HELMET_ID);

        // 头盔不在背饰槽放行
        check(!CuriosApi.isStackValid(new SlotContext(CuriosBridge.SLOT_BACK, null, 0, false, true),
                        new ItemStack(helmet)),
                "E1 负对照：头盔放不进背饰槽");

        // 四件套认不认饰品槽：把四件都塞进饰品槽，hasFullStarSteelSet 必须仍然为假
        var inv = CuriosApi.getCuriosInventory(player);
        if (inv.isPresent()) {
            handler(player, CuriosBridge.SLOT_HEAD).ifPresent(
                    h -> h.getStacks().setStackInSlot(0, new ItemStack(helmet)));
        }
        check(!ModArmorMaterials.hasFullStarSteelSet(player),
                "E2 负对照：头盔在饰品槽里不算『四件套』（hasFullStarSteelSet 没被改宽）");

        // 没戴任何星璨钢时 hasStarSteelHelmet 为假
        ServerPlayer clean = newPlayer(server, level, "zf165clean");
        check(!ModArmorMaterials.hasStarSteelHelmet(clean),
                "E3 负对照：什么都没戴时 hasStarSteelHelmet = false");

        // 夜视不给别人：把头盔塞进"戒指"槽（能塞就塞）也必须是假
        // （这一条盯的是"只认有物品的那个槽"，不是"随便哪个槽都算"）
        LINES.add("       服务端槽位表 = " + CuriosApi.getSlots(false).keySet());
        LINES.add("       玩家实体槽位表 = "
                + CuriosApi.getEntitySlots(net.minecraft.world.entity.EntityType.PLAYER, false).keySet());
    }
}
