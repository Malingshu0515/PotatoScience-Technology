package com.potatost.mod;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Collection;
import java.util.Optional;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF119 的临时探针）</b>：振金锭（新物品 / 动画贴图 / 没配方）。
 *
 * <p>用户原话：「加个振金锭（目前没配方）这是振金锭贴图 做成动态贴图 3t播放一帧」。</p>
 *
 * <p>探针分四段，缺一不可：</p>
 * <ol>
 *   <li><b>物品真的注册了</b>，而且**名字念得出来**（`getHoverName()` 走的是四语言表 ⇒
 *       顺带证明 `item.potato_s_t.vibranium_ingot` 这个键真的被游戏吃到了）；</li>
 *   <li><b>三个 c: 标签都挂上了</b>（`c:ingots/vibranium` / `c:vibranium_ingots` / 父 `c:ingots`）——
 *       这三条只有真服务端读得到数据包标签；</li>
 *   <li><b>没有配方</b>：把整个配方表扫一遍，任何 recipe 的产物都不许是它（用户明说"目前没配方"）；</li>
 *   <li><b>资源真的在 classpath 上且几何对</b>：从 classpath 读贴图（解 IHDR 头 ⇒ 32×320 = 10 帧 × 32）、
 *       读 `.mcmeta`（`animation.frametime` 必须是 **3** = 用户原话「3t播放一帧」）、读模型（layer0 指向自己）。
 *       ⚠ 动画**长什么样**是客户端的事，无头服务端验不了 —— 那一条留给用户看。</li>
 * </ol>
 *
 * <p>挂载方式：`PotatoST` 构造器末尾加一行 `Zf119Check.register();`，跑完用
 * {@code _zf119_unprobe.py} 摘掉，并逐字节核对 `PotatoST.java` 回到改前件。
 * 存档先抄到 {@code build/zftools/check/} **再**从 {@code src} 删（§10.1）。</p>
 */
public final class Zf119Check {

    private static final String TAG = "[R119] ";
    private static final String NS = PotatoST.MODID;
    private static final String ITEM = "vibranium_ingot";
    private static final String RES = "/assets/potato_s_t/";

    private static boolean registered;
    private static int failed;

    private static final StringBuilder REPORT = new StringBuilder();
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf119_probe_utf8.txt";

    private Zf119Check() {
    }

    private static void say(String line) {
        System.out.println(line);
        REPORT.append(line).append('\n');
    }

    private static void flushReport() {
        try (java.io.OutputStreamWriter w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), java.nio.charset.StandardCharsets.UTF_8)) {
            w.write("ZF119 探针报告（振金锭：注册 / 名字 / 标签 / 没配方 / 资源几何）× UTF-8 · §4.50\n");
            w.write("生成时间：" + java.time.LocalDateTime.now() + "\n");
            w.write("判词：" + (failed == 0 ? "全绿" : failed + " 条 FAIL") + "\n\n");
            w.write(REPORT.toString());
        } catch (Throwable t) {
            say(TAG + "report write failed: " + t);
        }
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf119Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        failed = 0;
        try {
            ServerLevel level = event.getServer().overworld();
            Item item = BuiltInRegistries.ITEM.get(ResourceLocation.fromNamespaceAndPath(NS, ITEM));
            checkItem(item);
            checkTags(item);
            checkNoRecipe(event, item);
            checkResources();
        } catch (Throwable t) {
            say(TAG + "exception: " + t);
            java.io.StringWriter sw = new java.io.StringWriter();
            t.printStackTrace(new java.io.PrintWriter(sw));
            for (String line : sw.toString().split("\n")) {
                say(TAG + "    " + line);
            }
            failed++;
        } finally {
            say(TAG + "verdict: " + (failed == 0 ? "ALL OK" : "**" + failed + " FAILED**"));
            say(TAG + "done, halting server");
            flushReport();
            event.getServer().halt(false);
        }
    }

    // ============================================================
    //  ① 注册 + 名字
    // ============================================================
    private static void checkItem(Item item) {
        say(TAG + "① item registered and its name resolves");
        failed += check("注册表里有 " + NS + ":" + ITEM, item != Items.AIR);
        if (item == Items.AIR) {
            return;
        }
        ItemStack st = new ItemStack(item);
        String name = st.getHoverName().getString();
        say(TAG + "    名字（服务端语言）= " + name);
        failed += check("名字不是占位（不是 item.potato_s_t... 原文）",
                !name.startsWith("item.") && !name.isBlank());
        failed += check("名字 = Vibranium Ingot（en_us 键生效）", "Vibranium Ingot".equals(name));
        failed += check("不是方块物品（就是一件普通物品）", !(item instanceof net.minecraft.world.item.BlockItem));
        // 创造页（§4.82）：无头服务端里内容可能还没构建，构建过就必须有它
        try {
            CreativeModeTab tab = BuiltInRegistries.CREATIVE_MODE_TAB.get(
                    ResourceLocation.fromNamespaceAndPath(NS, "potato_s_t_tab"));
            failed += check("注册表里有本模组的创造页", tab != null);
            if (tab != null) {
                Collection<ItemStack> items = tab.getDisplayItems();
                if (items.isEmpty()) {
                    say(TAG + "    （创造页内容在无头服务端里还没构建 ⇒ 这条只看静态检查："
                            + "_zf119_verify.py 的 B2）");
                } else {
                    boolean has = items.stream().anyMatch(s -> s.is(item));
                    failed += check("创造页里有它（该页共 " + items.size() + " 项）", has);
                }
            }
        } catch (Throwable t) {
            say(TAG + "    （创造页查询跳过：" + t + "）");
        }
    }

    // ============================================================
    //  ② c: 标签
    // ============================================================
    private static void checkTags(Item item) {
        say(TAG + "② c: tags");
        ItemStack st = new ItemStack(item);
        String[][] tags = {{"c", "ingots/vibranium"}, {"c", "vibranium_ingots"}, {"c", "ingots"}};
        for (String[] t : tags) {
            TagKey<Item> k = TagKey.create(Registries.ITEM,
                    ResourceLocation.fromNamespaceAndPath(t[0], t[1]));
            boolean in = !st.isEmpty() && st.is(k);
            failed += check("#" + t[0] + ":" + t[1] + " 收下它", in);
        }
    }

    // ============================================================
    //  ③ 没有配方
    // ============================================================
    private static void checkNoRecipe(ServerStartedEvent event, Item item) {
        say(TAG + "③ no recipe produces it (the user said so)");
        int total = 0;
        String hit = null;
        for (RecipeHolder<?> h : event.getServer().getRecipeManager().getRecipes()) {
            total++;
            ItemStack out;
            try {
                out = h.value().getResultItem(event.getServer().registryAccess());
            } catch (Throwable t) {
                continue;
            }
            if (!out.isEmpty() && out.is(item)) {
                hit = h.id().toString();
            }
        }
        say(TAG + "    配方表共 " + total + " 条");
        failed += check("没有任何配方产出振金锭（实际：" + (hit == null ? "没有" : hit) + "）", hit == null);
    }

    // ============================================================
    //  ④ 资源几何（classpath 上的真资源）
    // ============================================================
    private static byte[] resource(String path) {
        try (InputStream in = Zf119Check.class.getResourceAsStream(path)) {
            return in == null ? null : in.readAllBytes();
        } catch (Throwable t) {
            return null;
        }
    }

    private static void checkResources() {
        say(TAG + "④ resources on the classpath: png geometry + mcmeta + model");
        // 贴图：解 IHDR 头（前 8 字节签名 + 4 长度 + 4 类型 + 4 宽 + 4 高）
        byte[] png = resource(RES + "textures/item/" + ITEM + ".png");
        failed += check("classpath 上有 textures/item/" + ITEM + ".png", png != null);
        if (png != null) {
            say(TAG + "    贴图 %d B，文件头 %02x %02x %02x %02x"
                    .formatted(png.length, png[0], png[1], png[2], png[3]));
            failed += check("是 PNG（签名对）",
                    png.length > 24 && (png[0] & 0xFF) == 0x89 && png[1] == 'P' && png[2] == 'N' && png[3] == 'G');
            int w = ((png[16] & 0xFF) << 24) | ((png[17] & 0xFF) << 16) | ((png[18] & 0xFF) << 8) | (png[19] & 0xFF);
            int h = ((png[20] & 0xFF) << 24) | ((png[21] & 0xFF) << 16) | ((png[22] & 0xFF) << 8) | (png[23] & 0xFF);
            say(TAG + "    IHDR：宽 " + w + " 高 " + h);
            failed += check("宽 = 32（帧边长）", w == 32);
            failed += check("高 = 320 = 32 × 10 帧", h == 320);
        }
        // mcmeta
        byte[] mc = resource(RES + "textures/item/" + ITEM + ".png.mcmeta");
        failed += check("classpath 上有 " + ITEM + ".png.mcmeta", mc != null);
        if (mc != null) {
            String text = new String(mc, StandardCharsets.UTF_8);
            say(TAG + "    mcmeta = " + text.trim().replace("\n", " "));
            int frametime = -1;
            try {
                JsonObject o = JsonParser.parseString(text).getAsJsonObject()
                        .getAsJsonObject("animation");
                if (o != null && o.has("frametime")) {
                    frametime = o.get("frametime").getAsInt();
                }
            } catch (Throwable t) {
                say(TAG + "    mcmeta 解析失败：" + t);
            }
            failed += check("animation.frametime = 3（用户原话「3t播放一帧」，实际 " + frametime + "）",
                    frametime == 3);
        }
        // 模型
        byte[] model = resource(RES + "models/item/" + ITEM + ".json");
        failed += check("classpath 上有 models/item/" + ITEM + ".json", model != null);
        if (model != null) {
            String layer = "(读不出)";
            try {
                JsonObject o = JsonParser.parseString(new String(model, StandardCharsets.UTF_8))
                        .getAsJsonObject();
                layer = o.getAsJsonObject("textures").get("layer0").getAsString();
            } catch (Throwable t) {
                say(TAG + "    模型解析失败：" + t);
            }
            say(TAG + "    模型 layer0 = " + layer);
            failed += check("layer0 指向自己（" + NS + ":item/" + ITEM + "）",
                    (NS + ":item/" + ITEM).equals(layer));
        }
        say(TAG + "    ⚠ 动画**长什么样**是客户端的事：无头服务端只能验到这里，肉眼那一关留给你");
    }

    private static int check(String name, boolean pass) {
        say(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
