package com.potatost.mod;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.ShapelessRecipe;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import vazkii.patchouli.api.PatchouliAPI;
import vazkii.patchouli.common.book.Book;
import vazkii.patchouli.common.book.BookRegistry;
import vazkii.patchouli.common.item.PatchouliDataComponents;
import vazkii.patchouli.common.item.PatchouliItems;

/**
 * ZF148 临时探针（0.12：帕秋莉教程手册）—— 真 {@code runServer} 上跑，跑完自摘。
 *
 * <p>验的是「帕秋莉到底有没有把我们这本书记进去」这件事本身，而不是「文件写没写对」：
 * 书定义能不能被 {@link BookRegistry} 认下来、字段是不是我们写的那几个、
 * 书堆是不是 {@code patchouli:guide_book} + 组件、配方产物是不是同一堆、
 * 图标与配方页引用的东西是不是真的存在、正文键在五份语言里是不是都有。</p>
 *
 * <p>⚠ §4.50：`runServer` 的 stdout 是 GBK，中文会变乱码 ⇒ 自己写一份 UTF-8 报告，
 * 路径必须绝对，并且要在 {@code halt()} **之前**写。</p>
 */
public final class Zf148Check {

    private static final String TAG = "[A148] ";
    private static final String NS = PotatoST.MODID;
    private static final String BOOK = "guide";
    private static final String BOOK_KEY = "item.potato_s_t.guide_book";
    private static final String LANDING_KEY = "potato_s_t.guide.landing";
    private static final String SUBTITLE_KEY = "potato_s_t.guide.subtitle";
    private static final String TAB = "potato_s_t:potato_s_t_tab";
    private static final String MODEL = "potato_s_t:item/guide_book";
    private static final String[] LANGS = {"zh_cn", "en_us", "ja_jp", "ru_ru", "lzh"};
    private static final int[] KEYS = {579, 579, 579, 579, 581};

    private static final String BOOK_DIR = "patchouli_books/" + BOOK + "/en_us/";
    private static final String[] CATEGORIES =
            {"getting_started", "power", "materials", "oil", "starfall", "faq"};
    private static final String[][] ENTRIES = {
            {"getting_started", "start"}, {"getting_started", "rules"},
            {"getting_started", "first_line"},
            {"power", "wiring"}, {"power", "generation"}, {"power", "storage"}, {"power", "fluids"},
            {"materials", "ore_chain"}, {"materials", "blast_alloy"}, {"materials", "salt"},
            {"oil", "crude"}, {"oil", "distillation"}, {"oil", "chemistry"}, {"oil", "diesel_gen"},
            {"starfall", "sky_and_star"}, {"starfall", "star_steel"},
            {"faq", "machine"}, {"faq", "fluid"},
    };
    private static final String[] CRAFT_RECIPES = {
            "potato_s_t:micro_crusher", "potato_s_t:hydraulic_press", "potato_s_t:star_chart_tome"};

    private static boolean registered;
    private static int failed;
    private static int checks;

    private static final StringBuilder REPORT = new StringBuilder();
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf148_probe_utf8.txt";

    private Zf148Check() {
    }

    private static void say(String line) {
        System.out.println(line);
        REPORT.append(line).append('\n');
    }

    private static void flushReport() {
        try (java.io.OutputStreamWriter w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), StandardCharsets.UTF_8)) {
            w.write("ZF148 探针报告（0.12 帕秋莉教程手册：书注册 / 书堆 / 配方 / 资源 / 五语言）× UTF-8 · §4.50\n");
            w.write("生成时间：" + java.time.LocalDateTime.now() + "\n");
            w.write("判词：" + (failed == 0 ? "ALL OK" : failed + " 条 FAIL") + "（共 " + checks + " 项）\n\n");
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
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf148Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    private static void check(String name, boolean ok) {
        checks++;
        REPORT.append(ok ? "  [OK]   " : "  [FAIL] ").append(name).append('\n');
        if (ok) {
            System.out.println(TAG + "  [OK]   " + name);
        } else {
            failed++;
            System.out.println(TAG + "  [FAIL] " + name);
        }
    }

    private static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath(NS, path);
    }

    private static ResourceLocation rl(String full) {
        return ResourceLocation.parse(full);
    }

    /** 从 mod 自己的 classpath 读资源（dev 下就是 build/resources/main）。 */
    private static String resource(String path) {
        try (InputStream in = Zf148Check.class.getResourceAsStream("/" + path)) {
            return in == null ? null : new String(in.readAllBytes(), StandardCharsets.UTF_8);
        } catch (Throwable t) {
            return null;
        }
    }

    private static JsonObject json(String path) {
        String s = resource(path);
        if (s == null) {
            return null;
        }
        try {
            return JsonParser.parseString(s).getAsJsonObject();
        } catch (Throwable t) {
            return null;
        }
    }

    private static String str(JsonObject o, String key) {
        return o != null && o.has(key) && o.get(key).isJsonPrimitive() ? o.get(key).getAsString() : null;
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        failed = 0;
        checks = 0;
        try {
            MinecraftServer server = event.getServer();
            checkPatchouli();
            checkBook();
            checkStack();
            checkRecipe(server);
            checkResources();
            checkContent(server);
            checkCrossLang();
        } catch (Throwable t) {
            say(TAG + "exception: " + t);
            for (StackTraceElement e : t.getStackTrace()) {
                say(TAG + "    at " + e);
            }
        }
        say(TAG + "done, halting server");
        flushReport();
        event.getServer().halt(false);
    }

    // ------------------------------------------------------------ A 帕秋莉本体
    private static void checkPatchouli() {
        say(TAG + "================ A 帕秋莉本体 ================");
        check("A1 帕秋莉不是 stub（真身已加载）", !PatchouliAPI.get().isStub());
        check("A2 book 注册表里有 potato_s_t:" + BOOK,
                BookRegistry.INSTANCE.books.containsKey(id(BOOK)));
        check("A3 负对照：瞎编的 id 不在注册表里",
                !BookRegistry.INSTANCE.books.containsKey(id("no_such_book_zzz")));
    }

    // ------------------------------------------------------------ B 书字段
    private static void checkBook() {
        say(TAG + "================ B 书定义字段 ================");
        Book b = BookRegistry.INSTANCE.books.get(id(BOOK));
        if (b == null) {
            check("B0 取到 Book 对象", false);
            return;
        }
        check("B0 取到 Book 对象", true);
        check("B1 id = potato_s_t:" + BOOK, id(BOOK).equals(b.id));
        check("B2 书名键 = " + BOOK_KEY, BOOK_KEY.equals(b.name));
        check("B3 落地页键 = " + LANDING_KEY, LANDING_KEY.equals(b.landingText));
        check("B4 副题键 = " + SUBTITLE_KEY, SUBTITLE_KEY.equals(b.subtitle));
        check("B5 version = 0（走 subtitle 而不是第 N 版）", "0".equals(b.version));
        check("B6 i18n = true（正文走语言键）", b.i18n);
        check("B7 use_blocky_font = true（中文不掉字）", b.useBlockyFont);
        check("B8 show_progress = false", !b.showProgress);
        check("B9 帕秋莉自己生成物品（noBook = false）", !b.noBook);
        check("B10 不是外部书（isExternal = false，内容走资源包）", !b.isExternal);
        // ⚠ 帕秋莉对 `model` 键**无条件**加 `item/` 前缀（Book 构造器字节码），
        //   所以 book.json 里写的是 potato_s_t:guide_book，这里读到的才是 potato_s_t:item/guide_book
        JsonObject bookJson = json("data/potato_s_t/patchouli_books/" + BOOK + "/book.json");
        check("B11 model 键写字面量 potato_s_t:guide_book（不带 item/）",
                bookJson != null && "potato_s_t:guide_book".equals(str(bookJson, "model")));
        check("B11b 解析后 b.model = " + MODEL + "（实测 " + b.model + "）",
                MODEL.equals(String.valueOf(b.model)));
        check("B12 creative_tab = " + TAB, TAB.equals(String.valueOf(b.creativeTab)));
        check("B13 归属 mod = potato_s_t", b.owner != null && NS.equals(b.owner.getId()));
        say(TAG + "    （记录）name=" + b.name + " / creativeTab=" + b.creativeTab
                + " / overflow=" + b.overflowMode);
    }

    // ------------------------------------------------------------ C 书堆与组件
    private static void checkStack() {
        say(TAG + "================ C 书堆与数据组件 ================");
        ItemStack fromBook = BookRegistry.INSTANCE.books.containsKey(id(BOOK))
                ? BookRegistry.INSTANCE.books.get(id(BOOK)).getBookItem() : ItemStack.EMPTY;
        ItemStack fromApi = PatchouliAPI.get().getBookStack(id(BOOK));
        check("C1 Book.getBookItem() 非空", !fromBook.isEmpty());
        check("C2 PatchouliAPI.getBookStack() 非空", !fromApi.isEmpty());
        check("C3 两者是同一件物品", !fromBook.isEmpty() && !fromApi.isEmpty()
                && fromBook.getItem() == fromApi.getItem());
        check("C4 物品就是帕秋莉的 guide_book",
                !fromBook.isEmpty() && fromBook.getItem() == PatchouliItems.BOOK);
        ResourceLocation comp = fromBook.isEmpty() ? null
                : fromBook.get(PatchouliDataComponents.BOOK);
        check("C5 patchouli:book 组件 = potato_s_t:" + BOOK, id(BOOK).equals(comp));
        check("C6 两堆逐项相同（isSameItemSameComponents）", !fromBook.isEmpty()
                && ItemStack.isSameItemSameComponents(fromBook, fromApi));
        ItemStack bare = new ItemStack(PatchouliItems.BOOK);
        check("C7 负对照：裸 guide_book 没有组件（= 一本废书）",
                bare.get(PatchouliDataComponents.BOOK) == null);
        // C8 的口径要按**实测行为**写：getBookStack 只往组件里塞 id，
        // **不查注册表**（PatchouliAPIImpl → ItemModBook.forBook）。所以负对照得看
        // 「书堆造得出来、但注册表里没有这本书」——那才是玩家真正会遇到的废书。
        ItemStack bogus = PatchouliAPI.get().getBookStack(id("no_such_book_zzz"));
        check("C8 负对照：瞎编 id 能造出书堆，但注册表里没有它（= 打不开的废书）",
                !bogus.isEmpty() && !BookRegistry.INSTANCE.books.containsKey(id("no_such_book_zzz")));
        check("C9 Java 侧常量 GuideBook.BOOK_ID 与书 id 一致",
                id(BOOK).equals(GuideBook.BOOK_ID));
        check("C10 开局赠送的前置条件成立（书堆非空）",
                !PatchouliAPI.get().getBookStack(GuideBook.BOOK_ID).isEmpty());
    }

    // ------------------------------------------------------------ D 配方
    private static void checkRecipe(MinecraftServer server) {
        say(TAG + "================ D 配方：书 + 铁锭 ================");
        Optional<RecipeHolder<?>> got = server.getRecipeManager().byKey(id("guide_book"));
        check("D1 配方 potato_s_t:guide_book 已加载", got.isPresent());
        if (got.isEmpty()) {
            return;
        }
        Object v = got.get().value();
        check("D2 类型是 crafting_shapeless", v instanceof ShapelessRecipe);
        if (!(v instanceof ShapelessRecipe sr)) {
            return;
        }
        ItemStack out = sr.getResultItem(server.registryAccess());
        ItemStack want = bookStack();
        check("D3 产物物品 = patchouli:guide_book",
                out.getItem() == PatchouliItems.BOOK);
        check("D4 产物带 patchouli:book 组件，且指向 potato_s_t:" + BOOK,
                id(BOOK).equals(out.get(PatchouliDataComponents.BOOK)));
        check("D5 产物与 PatchouliAPI 给的书堆逐项相同",
                ItemStack.isSameItemSameComponents(out, want));
        check("D6 产物数量 = 1", out.getCount() == 1);
        List<Ingredient> ings = sr.getIngredients();
        check("D7 恰好两样原料", ings.size() == 2);
        ItemStack iron = new ItemStack(net.minecraft.world.item.Items.IRON_INGOT);
        ItemStack book = new ItemStack(net.minecraft.world.item.Items.BOOK);
        ItemStack stone = new ItemStack(net.minecraft.world.item.Items.STONE);
        boolean hi = ings.stream().anyMatch(i -> i.test(iron));
        boolean hb = ings.stream().anyMatch(i -> i.test(book));
        check("D8 原料里有铁锭", hi);
        check("D9 原料里有原版书", hb);
        check("D10 负对照：石头不是原料", ings.stream().noneMatch(i -> i.test(stone)));
        check("D11 记录：Loaded recipes 里能找到它（manager 条数 > 0）",
                server.getRecipeManager().getRecipes().size() > 0);
    }

    private static ItemStack bookStack() {
        return PatchouliAPI.get().getBookStack(id(BOOK));
    }

    // ------------------------------------------------------------ E 资源
    private static void checkResources() {
        say(TAG + "================ E 资源文件 ================");
        check("E1 book.json 在且能解析",
                json("data/potato_s_t/patchouli_books/" + BOOK + "/book.json") != null);
        for (String c : CATEGORIES) {
            check("E2 分类文件在：" + c + ".json",
                    json("assets/potato_s_t/" + BOOK_DIR + "categories/" + c + ".json") != null);
        }
        for (String[] e : ENTRIES) {
            check("E3 条目文件在：" + e[0] + "/" + e[1] + ".json",
                    json("assets/potato_s_t/" + BOOK_DIR + "entries/" + e[0] + "/" + e[1] + ".json") != null);
        }
        check("E4 物品模型在", json("assets/potato_s_t/models/item/guide_book.json") != null);
        check("E5 配方 json 在", json("data/potato_s_t/recipe/guide_book.json") != null);
        byte[] png = pngBytes("assets/potato_s_t/textures/item/guide_book.png");
        check("E6 贴图在且是 PNG", png != null);
        if (png != null) {
            int w = ((png[16] & 0xFF) << 24) | ((png[17] & 0xFF) << 16) | ((png[18] & 0xFF) << 8) | (png[19] & 0xFF);
            int h = ((png[20] & 0xFF) << 24) | ((png[21] & 0xFF) << 16) | ((png[22] & 0xFF) << 8) | (png[23] & 0xFF);
            check("E7 贴图 16×16（实测 " + w + "×" + h + "）", w == 16 && h == 16);
        }
        JsonObject model = json("assets/potato_s_t/models/item/guide_book.json");
        check("E8 模型 layer0 = potato_s_t:item/guide_book",
                model != null && model.has("textures")
                        && "potato_s_t:item/guide_book".equals(
                                model.getAsJsonObject("textures").get("layer0").getAsString()));
    }

    private static byte[] pngBytes(String path) {
        try (InputStream in = Zf148Check.class.getResourceAsStream("/" + path)) {
            if (in == null) {
                return null;
            }
            byte[] d = in.readAllBytes();
            if (d.length < 24 || d[0] != (byte) 0x89 || d[1] != 'P' || d[2] != 'N' || d[3] != 'G') {
                return null;
            }
            return d;
        } catch (Throwable t) {
            return null;
        }
    }

    // ------------------------------------------------------------ F 内容自洽
    private static void checkContent(MinecraftServer server) {
        say(TAG + "================ F 内容自洽（图标 / 配方页 / 分类） ================");
        Set<String> catIds = new TreeSet<>();
        for (String c : CATEGORIES) {
            catIds.add(NS + ":" + c);
        }
        int iconMissing = 0;
        int recipeMissing = 0;
        int catBad = 0;
        int pages = 0;
        List<String> bad = new ArrayList<>();
        for (String[] e : ENTRIES) {
            JsonObject o = json("assets/potato_s_t/" + BOOK_DIR + "entries/" + e[0] + "/" + e[1] + ".json");
            if (o == null) {
                bad.add("缺文件 " + e[0] + "/" + e[1]);
                continue;
            }
            String cat = str(o, "category");
            if (cat == null || !catIds.contains(cat)) {
                catBad++;
                bad.add(e[1] + " 的 category=" + cat);
            }
            String icon = str(o, "icon");
            if (icon == null || BuiltInRegistries.ITEM.get(rl(icon)) == net.minecraft.world.item.Items.AIR) {
                iconMissing++;
                bad.add(e[1] + " 的 icon=" + icon);
            }
            JsonArray pg = o.getAsJsonArray("pages");
            if (pg == null || pg.isEmpty()) {
                bad.add(e[1] + " 没有 pages");
                continue;
            }
            for (JsonElement pe : pg) {
                JsonObject p = pe.getAsJsonObject();
                String type = str(p, "type");
                if ("patchouli:text".equals(type)) {
                    pages++;
                    String key = str(p, "text");
                    if (key == null || !key.startsWith("potato_s_t.guide.")) {
                        bad.add(e[1] + " 的正文键可疑：" + key);
                    }
                } else if ("patchouli:crafting".equals(type)) {
                    String r = str(p, "recipe");
                    if (r == null || server.getRecipeManager().byKey(rl(r)).isEmpty()) {
                        recipeMissing++;
                        bad.add(e[1] + " 引用了不存在的配方：" + r);
                    }
                }
            }
        }
        check("F1 每份条目的 category 都指向已存在的分类（坏 " + catBad + "）", catBad == 0);
        check("F2 每份条目的 icon 都是真物品（坏 " + iconMissing + "）", iconMissing == 0);
        check("F3 每个 crafting 页引用的配方都存在（坏 " + recipeMissing + "）", recipeMissing == 0);
        check("F4 文本页共 37 页（实测 " + pages + "）", pages == 37);
        for (String s : bad) {
            say(TAG + "    !! " + s);
        }
        // 分类自身的字段
        int okCat = 0;
        for (String c : CATEGORIES) {
            JsonObject o = json("assets/potato_s_t/" + BOOK_DIR + "categories/" + c + ".json");
            String icon = str(o, "icon");
            boolean good = o != null && str(o, "name") != null && str(o, "description") != null
                    && icon != null && BuiltInRegistries.ITEM.get(rl(icon)) != net.minecraft.world.item.Items.AIR;
            if (good) {
                okCat++;
            } else {
                say(TAG + "    !! 分类 " + c + " 字段不全或图标不存在：" + icon);
            }
        }
        check("F5 六个分类的 name/description/icon 齐全且图标存在（" + okCat + "/6）", okCat == 6);
        for (String r : CRAFT_RECIPES) {
            check("F6 书里引用的配方存在：" + r, server.getRecipeManager().byKey(rl(r)).isPresent());
        }
    }

    // ------------------------------------------------------------ G 五语言交叉
    private static void checkCrossLang() {
        say(TAG + "================ G 五语言：正文键一条不少 ================");
        Map<String, Map<String, String>> langs = new LinkedHashMap<>();
        for (int i = 0; i < LANGS.length; i++) {
            String raw = resource("assets/potato_s_t/lang/" + LANGS[i] + ".json");
            if (raw == null) {
                check("G0 " + LANGS[i] + " 读得到", false);
                continue;
            }
            JsonObject o = json("assets/potato_s_t/lang/" + LANGS[i] + ".json");
            Map<String, String> m = new LinkedHashMap<>();
            for (Map.Entry<String, JsonElement> en : o.entrySet()) {
                m.put(en.getKey(), en.getValue().getAsString());
            }
            langs.put(LANGS[i], m);
            check("G1 " + LANGS[i] + " 键数 = " + KEYS[i] + "（实测 " + m.size() + "）", m.size() == KEYS[i]);
        }
        // 收集本手册用到的所有键：书字段 + 分类 + 条目 + 正文页
        Set<String> need = new TreeSet<>();
        need.add(BOOK_KEY);
        need.add(LANDING_KEY);
        need.add(SUBTITLE_KEY);
        need.add("message.potato_s_t.guide_book.received");
        for (String c : CATEGORIES) {
            need.add("potato_s_t.guide.category." + c);
            need.add("potato_s_t.guide.category." + c + ".desc");
        }
        for (String[] e : ENTRIES) {
            JsonObject o = json("assets/potato_s_t/" + BOOK_DIR + "entries/" + e[0] + "/" + e[1] + ".json");
            need.add("potato_s_t.guide.entry." + e[0] + "." + e[1]);
            if (o == null) {
                continue;
            }
            for (JsonElement pe : o.getAsJsonArray("pages")) {
                JsonObject p = pe.getAsJsonObject();
                if ("patchouli:text".equals(str(p, "type"))) {
                    need.add(str(p, "text"));
                }
            }
        }
        check("G2 本手册需要的键合计 = 71（实测 " + need.size() + "）", need.size() == 71);
        int missTotal = 0;
        int emptyTotal = 0;
        int quoteTotal = 0;
        for (String lang : LANGS) {
            Map<String, String> m = langs.get(lang);
            if (m == null) {
                continue;
            }
            Set<String> miss = new TreeSet<>();
            for (String k : need) {
                String v = m.get(k);
                if (v == null) {
                    miss.add(k);
                } else if (v.trim().isEmpty()) {
                    emptyTotal++;
                } else if (v.indexOf('"') >= 0) {
                    quoteTotal++;
                }
            }
            missTotal += miss.size();
            check("G3 " + lang + "：手册要的键一条不缺（缺 " + miss.size() + "）", miss.isEmpty());
            for (String s : miss) {
                say(TAG + "    !! " + lang + " 缺 " + s);
            }
        }
        check("G4 五份都没有空值（空 " + emptyTotal + "）", emptyTotal == 0);
        check("G5 五份的值里都没有 ASCII 双引号（有 " + quoteTotal + "）", quoteTotal == 0);
        // 键集合跨语言一致：zh/en/ja/ru 四份必须完全相同，lzh 允许「四份 + 2 个语言元数据键」
        List<String> four = new ArrayList<>();
        for (String lang : LANGS) {
            if (!"lzh".equals(lang)) {
                four.add(lang);
            }
        }
        Set<String> base = new TreeSet<>(langs.get(four.get(0)).keySet());
        boolean same = true;
        for (String lang : four) {
            Set<String> b = new TreeSet<>(langs.get(lang).keySet());
            Set<String> d1 = new TreeSet<>(base);
            d1.removeAll(b);
            Set<String> d2 = new TreeSet<>(b);
            d2.removeAll(base);
            if (!(d1.isEmpty() && d2.isEmpty())) {
                same = false;
                say(TAG + "    !! " + lang + " 与 " + four.get(0) + " 键集合差：" + d1 + " / " + d2);
            }
        }
        check("G6 zh_cn / en_us / ja_jp / ru_ru 四份键集合完全一致", same);
        Set<String> lzh = new TreeSet<>(langs.get("lzh").keySet());
        Set<String> extra = new TreeSet<>(lzh);
        extra.removeAll(base);
        Set<String> lack = new TreeSet<>(base);
        lack.removeAll(lzh);
        check("G7 lzh = 四份 + 2 个语言元数据键（多的 " + extra.size() + "：" + extra
                + "，缺的 " + lack.size() + "）", extra.size() == 2 && lack.isEmpty());
    }
}
