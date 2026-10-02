package com.potatost.mod;

import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.Enchantments;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ZF180 临时探针（0.14：修「振金/星璨钢装备无法附魔 —— 附魔台 / 铁砧 / 附魔灌注台都不行」）。
 *
 * <p>病根：1.21 的附魔能不能上到某件装备，看的是**附魔自己的 {@code supported_items}**；而原版
 * {@code data/minecraft/tags/item/enchantable/*} 全是按**原版装备类型标签**（{@code #minecraft:head_armor}、
 * {@code #minecraft:swords}、{@code #minecraft:axes} …）定义的。我们此前只挂了 {@code swords}
 * （仅钛合金剑）与 {@code pickaxes}（仅钛合金镐）⇒ 振金/星璨钢护甲与其它工具**没有任何附魔支持它们**，
 * 于是附魔台什么都不给、铁砧插不上书、别的 mod 的附魔台同理。</p>
 *
 * <p>本探针在真服务端上逐件断言（这就是附魔台/铁砧真正查的那几样）：</p>
 * <ol>
 *   <li>A：20 件装备 {@code stack.isEnchantable()} 为真、附魔权重 &gt; 0；</li>
 *   <li>B：**该装备该有的附魔** 的 {@code supported_items} 命中（护甲→保护、剑/斧→锋利、工具→效率、
 *       全体→耐久与经验修补）；</li>
 *   <li>C：负对照 —— 非装备（锭/钻石）不被"保护/锋利"支持；护甲不被"效率"支持（不是挂得越多越好）。</li>
 * </ol>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class Zf180Check {

    private static final String TAG = "[A180] ";
    private static final Path REPORT = Path.of("E:\\PotatoST\\build\\zftools\\_zf180_probe_utf8.txt");

    private static final List<String> LINES = new ArrayList<>();
    private static int passed = 0;
    private static int failed = 0;

    private Zf180Check() {
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

    private static void check(boolean ok, String label) {
        check(ok, label, "");
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        MinecraftServer server = event.getServer();
        try {
            run(server.overworld());
        } catch (Throwable t) {
            failed++;
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
            try (Writer w = new OutputStreamWriter(Files.newOutputStream(REPORT), StandardCharsets.UTF_8)) {
                w.write(String.join("\n", LINES) + "\n");
            }
        } catch (IOException e) {
            System.out.println("probe report write failed: " + e);
        }
        server.halt(false);
    }

    /** 每件装备：id → 该有的附魔（键是原版附魔的注册名）。 */
    private static Map<String, String[]> plan() {
        Map<String, String[]> m = new LinkedHashMap<>();
        for (String mat : new String[] {"titanium_alloy", "star_steel", "vibranium"}) {
            for (String piece : new String[] {"helmet", "chestplate", "leggings", "boots"}) {
                m.put(mat + "_" + piece, new String[] {"protection", "unbreaking", "mending"});
            }
        }
        for (String mat : new String[] {"star_steel", "titanium_alloy"}) {
            m.put(mat + "_pickaxe", new String[] {"efficiency", "unbreaking", "mending"});
        }
        m.put("star_steel_axe", new String[] {"sharpness", "efficiency", "unbreaking", "mending"});
        m.put("star_steel_shovel", new String[] {"efficiency", "unbreaking", "mending"});
        m.put("star_steel_hoe", new String[] {"efficiency", "unbreaking", "mending"});
        m.put("star_steel_sword", new String[] {"sharpness", "unbreaking", "mending"});
        m.put("vibranium_sword", new String[] {"sharpness", "unbreaking", "mending"});
        m.put("titanium_alloy_sword", new String[] {"sharpness", "unbreaking", "mending"});
        return m;
    }

    private static ResourceLocation enchId(String name) {
        return ResourceLocation.withDefaultNamespace(name);
    }

    private static void run(ServerLevel level) {
        var enchReg = level.registryAccess().registryOrThrow(Registries.ENCHANTMENT);
        Map<String, Holder<Enchantment>> ench = new LinkedHashMap<>();
        for (String n : new String[] {"protection", "efficiency", "sharpness", "unbreaking", "mending"}) {
            ench.put(n, enchReg.getHolderOrThrow(
                    net.minecraft.resources.ResourceKey.create(Registries.ENCHANTMENT, enchId(n))));
        }

        LINES.add("== A 段：逐件装备（isEnchantable + 附魔权重）==");
        Map<String, String[]> plan = plan();
        int badA = 0, badB = 0;
        StringBuilder detailA = new StringBuilder();
        StringBuilder detailB = new StringBuilder();
        for (Map.Entry<String, String[]> e : plan.entrySet()) {
            Item item = net.minecraft.core.registries.BuiltInRegistries.ITEM.get(
                    ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, e.getKey()));
            if (item == Items.AIR) {
                badA++;
                detailA.append(e.getKey()).append("(物品不在) ");
                continue;
            }
            ItemStack stack = new ItemStack(item);
            boolean enchantable = stack.isEnchantable();
            int value = stack.getEnchantmentValue();
            if (!enchantable || value <= 0) {
                badA++;
                detailA.append(String.format("%s(enchantable=%s,weight=%d) ", e.getKey(), enchantable, value));
            }
            for (String en : e.getValue()) {
                Holder<Enchantment> h = ench.get(en);
                HolderSet<Item> supported = h.value().getSupportedItems();
                if (!supported.contains(stack.getItemHolder())) {
                    badB++;
                    detailB.append(e.getKey()).append("/").append(en).append(" ");
                }
            }
        }
        check(badA == 0, "A1 20 件装备全部 isEnchantable 且附魔权重 > 0", detailA.toString().trim());
        check(badB == 0, "B1 每件装备都能被它该有的附魔支持（保护/锋利/效率/耐久/经验修补）",
                detailB.toString().trim());
        LINES.add("   调试：检查了 " + plan.size() + " 件装备 × 各自应有的附魔");

        LINES.add("== C 段：负对照 ==");
        ItemStack ingot = new ItemStack(net.minecraft.core.registries.BuiltInRegistries.ITEM.get(
                ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "star_steel_ingot")));
        check(!ench.get("protection").value().getSupportedItems().contains(ingot.getItemHolder()),
                "C1 星璨钢锭**不**被「保护」支持（不是什么都往里塞）");
        ItemStack helmet = new ItemStack(net.minecraft.core.registries.BuiltInRegistries.ITEM.get(
                ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "vibranium_helmet")));
        check(!ench.get("efficiency").value().getSupportedItems().contains(helmet.getItemHolder()),
                "C2 振金头盔**不**被「效率」支持（护甲不该进工具标签）");
        check(!ench.get("sharpness").value().getSupportedItems()
                        .contains(new ItemStack(Items.DIRT).getItemHolder()),
                "C3 泥土不被「锋利」支持（原版负对照）");
    }
}
