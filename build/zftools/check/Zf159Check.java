package com.potatost.mod;

import java.io.IOException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.material.Fluid;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.server.ServerAboutToStartEvent;
import net.neoforged.neoforge.fluids.FluidStack;

/**
 * ZF159 一次性取证探针（只读；跑完由 {@code _zf159_unprobe.py} 拆掉）。
 *
 * <p><b>要回答的三个问题</b>（用户原话：「兼容一下沉浸工程和通用机械中与本mod同名的所有流体配方…
 * 本mod的碳粉 铁粉与其它mod通用」）：</p>
 * <ol>
 *   <li><b>同名流体真的接上了吗</b>：我们的 oxygen / hydrogen / chlorine / sulfuric_acid /
 *       crude_oil / diesel / gasoline / naphtha 到底有没有落在那几张 {@code c:} 标签里
 *       （连别的 mod 的成员一起数出来）；</li>
 *   <li><b>通用机械那条"流体↔气体"的路通不通</b>：Mekanism 的 {@code mekanism:rotary} 配方
 *       写在 jar 里、`fluid_input` 是 {@code #c:oxygen}。这里把它**加载后的那条**取出来，
 *       直接喂一桶<b>我们的氧气</b>，看 {@code test(FluidStack)} 是不是 true、
 *       {@code getChemicalOutput(我们的氧气)} 出的是不是 {@code mekanism:oxygen}。
 *       —— 这一步是"标签在运行期真的解析成了我们的流体"的**行为级证据**，
 *          静态扫 jar 只能证明"上游写了这个标签"。</li>
 *   <li><b>便携式发电机的燃料表</b>：{@code immersiveengineering:generator_fuel} 这个类型里
 *       到底有多少条、吃哪些标签（我们补的汽油/石脑油/液化气那三条在不在）。</li>
 * </ol>
 *
 * <p>⚠ <b>全程用反射碰 Mekanism</b>：不是不能用它的 API，而是**不能在编译期依赖它**
 * （我们的 build.gradle 里没有 Mekanism，为此改构建脚本不划算）。反射失败只影响第 ② 项，
 * 前三项照样出报告。</p>
 */
public final class Zf159Check {

    /** 我们 8 种「与别家同名」的流体（材料/名字 → 我们自己的流体 id）。 */
    private static final String[][] FLUIDS = {
            {"oxygen", "potato_s_t:oxygen"},
            {"hydrogen", "potato_s_t:hydrogen"},
            {"chlorine", "potato_s_t:chlorine"},
            {"nitrogen", "potato_s_t:nitrogen"},
            {"sulfuric_acid", "potato_s_t:sulfuric_acid"},
            {"crude_oil", "potato_s_t:crude_oil"},
            {"diesel", "potato_s_t:diesel"},
            {"gasoline", "potato_s_t:gasoline"},
            {"naphtha", "potato_s_t:naphtha"},
            {"lpg", "potato_s_t:lpg"},
    };

    private static final Path OUT = Path.of("build", "zftools", "_zf159_probe.txt");
    private static volatile boolean done = false;

    private Zf159Check() {
    }

    public static void register() {
        NeoForge.EVENT_BUS.addListener(Zf159Check::onAboutToStart);
    }

    private static void log(List<String> out, String line) {
        out.add(line);
        System.out.println("[ZF159] " + line);
    }

    private static void onAboutToStart(ServerAboutToStartEvent event) {
        if (done) {
            return;
        }
        done = true;
        MinecraftServer server = event.getServer();
        List<String> out = new ArrayList<>();
        try {
            log(out, "=== ZF159 流体/粉尘跨模组兼容取证 ===");
            log(out, "");

            // ---------- ① 同名流体落在哪张 c: 标签里 ----------
            log(out, "--- ① c:<名字> 流体标签的成员（我们的在里面吗？别的 mod 有谁？）");
            for (String[] pair : FLUIDS) {
                TagKey<Fluid> tag = TagKey.create(Registries.FLUID,
                        ResourceLocation.fromNamespaceAndPath("c", pair[0]));
                List<String> mine = new ArrayList<>();
                List<String> theirs = new ArrayList<>();
                int total = 0;
                for (var holder : BuiltInRegistries.FLUID.getTagOrEmpty(tag)) {
                    total++;
                    ResourceLocation id = BuiltInRegistries.FLUID.getKey(holder.value());
                    if (id == null) {
                        continue;
                    }
                    if (id.getNamespace().equals(PotatoST.MODID)) {
                        mine.add(id.getPath());
                    } else {
                        theirs.add(id.toString());
                    }
                }
                log(out, String.format("  %-18s 成员 %-2d  我方 %-2d %s   别家: %s",
                        "c:" + pair[0], total, mine.size(),
                        mine.isEmpty() ? "[!! 不在里面]" : "[已就位]",
                        theirs.isEmpty() ? "（无）" : String.join(", ", theirs)));
            }

            // ---------- ② 粉尘标签 ----------
            log(out, "");
            log(out, "--- ② c:dusts/* 的成员（碳粉/铁粉/钛粉挂对了没有）");
            for (String d : new String[]{"carbon", "iron", "titanium", "coal"}) {
                TagKey<Item> tag = TagKey.create(Registries.ITEM,
                        ResourceLocation.fromNamespaceAndPath("c", "dusts/" + d));
                List<String> all = new ArrayList<>();
                for (var holder : BuiltInRegistries.ITEM.getTagOrEmpty(tag)) {
                    ResourceLocation id = BuiltInRegistries.ITEM.getKey(holder.value());
                    if (id != null) {
                        all.add(id.toString());
                    }
                }
                boolean mine = all.stream().anyMatch(s -> s.startsWith(PotatoST.MODID + ":"));
                log(out, String.format("  %-18s 成员 %-2d %s  %s", "c:dusts/" + d, all.size(),
                        mine ? "[我方已就位]" : "[我方不在]", String.join(", ", all)));
            }

            // ---------- ③ 我们自己的燃料表（行为级：直接问 Java 判定） ----------
            log(out, "");
            log(out, "--- ③ 大型柴油发电机的燃料判定（直接调用，不看标签静态内容）");
            for (String[] pair : new String[][]{
                    {"我们的柴油", "potato_s_t:diesel"},
                    {"我们的汽油", "potato_s_t:gasoline"},
                    {"我们的石脑油", "potato_s_t:naphtha"},
                    {"我们的液化石油气", "potato_s_t:lpg"},
                    {"沉浸原油的柴油", "immersivepetroleum:diesel"},
                    {"沉浸工程的生物柴油", "immersiveengineering:biodiesel"},
                    {"沉浸原油的汽油", "immersivepetroleum:gasoline"},
                    {"原版水（必须不是燃料）", "minecraft:water"},
                    {"原版岩浆（必须不是燃料）", "minecraft:lava"},
                    {"Mekanism 的氧气（必须不是燃料）", "mekanism:oxygen"},
            }) {
                Fluid f = BuiltInRegistries.FLUID.get(ResourceLocation.parse(pair[1]));
                if (f == null) {
                    log(out, String.format("  %-26s [这个流体不存在]", pair[0]));
                    continue;
                }
                FluidStack st = new FluidStack(f, 1000);
                DieselGeneratorBlockEntity.FuelClass cls = DieselGeneratorBlockEntity.fuelClassOf(st);
                log(out, String.format("  %-26s -> %s", pair[0],
                        cls == null ? "不是燃料" : cls + "（" + cls.energyPerTick() + " FE/t）"));
            }

            // ---------- ④ IE 的 generator_fuel 表（便携式发电机烧什么） ----------
            log(out, "");
            log(out, "--- ④ immersiveengineering:generator_fuel 类型里加载了多少条");
            RecipeType<?> gf = BuiltInRegistries.RECIPE_TYPE.get(
                    ResourceLocation.fromNamespaceAndPath("immersiveengineering", "generator_fuel"));
            if (gf == null) {
                log(out, "  沉浸工程没装 => 这个类型不存在（我们那三条带守卫的配方也不加载，预期行为）");
            } else {
                List<RecipeHolder<?>> list = (List<RecipeHolder<?>>) (List<?>)
                        server.getRecipeManager().getAllRecipesFor((RecipeType) gf);
                int ours = 0;
                for (RecipeHolder<?> h : list) {
                    boolean isOurs = h.id().getNamespace().equals(PotatoST.MODID);
                    if (isOurs) {
                        ours++;
                    }
                    log(out, "  " + (isOurs ? "[我方] " : "       ") + h.id());
                }
                log(out, "  共 " + list.size() + " 条，其中我方 " + ours + " 条（预期 3：汽油 / 石脑油 / 液化气）");
            }

            // ---------- ⑤ Mekanism 的 rotary：拿**我们的氧气**喂它 ----------
            log(out, "");
            log(out, "--- ⑤ 通用机械 mekanism:rotary —— 我们的氧气能不能被它认成氧气气体");
            probeMekanismRotary(server, out);

            log(out, "");
            log(out, "=== 取证结束 ===");
        } catch (Throwable t) {
            log(out, "!! 探针自己抛异常了：" + t);
            for (StackTraceElement e : t.getStackTrace()) {
                log(out, "    at " + e);
            }
        } finally {
            try {
                Files.createDirectories(OUT.getParent());
                Path tmp = OUT.resolveSibling(OUT.getFileName() + ".tmp");
                Files.write(tmp, out, StandardCharsets.UTF_8);
                try {
                    Files.move(tmp, OUT, java.nio.file.StandardCopyOption.REPLACE_EXISTING,
                            java.nio.file.StandardCopyOption.ATOMIC_MOVE);
                } catch (java.nio.file.AtomicMoveNotSupportedException ex) {
                    Files.move(tmp, OUT, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                }
                System.out.println("[ZF159] 取证结果已落盘: " + OUT.toAbsolutePath());
            } catch (IOException e) {
                System.out.println("[ZF159] 写日志失败：" + e);
            }
            server.halt(false);
        }
    }

    /**
     * 用反射走一遍 Mekanism 的旋转冷凝器配方：把**我们的氧气**喂给加载后的那条配方。
     *
     * <p>为什么值得这么麻烦：`c:oxygen` 标签里同时有我们的氧气和 Mekanism 的氧气，
     * 静态看只证明"标签里有"，**证明不了** Mekanism 的 {@code FluidStackIngredient}
     * 在运行期能解析到我们那一份。而 {@code test(FluidStack)} 是它自己的判定函数 ——
     * 它返回 true，就是"它认了"。</p>
     */
    private static void probeMekanismRotary(MinecraftServer server, List<String> out) {
        try {
            Class<?> recipeCls = Class.forName("mekanism.api.recipes.RotaryRecipe");
            RecipeType<?> type = BuiltInRegistries.RECIPE_TYPE.get(
                    ResourceLocation.fromNamespaceAndPath("mekanism", "rotary"));
            if (type == null) {
                log(out, "  通用机械没装 => 这个类型不存在（跳过）");
                return;
            }
            List<RecipeHolder<?>> all = (List<RecipeHolder<?>>) (List<?>)
                    server.getRecipeManager().getAllRecipesFor((RecipeType) type);
            log(out, "  mekanism:rotary 共加载 " + all.size() + " 条");

            Method test = recipeCls.getMethod("test", FluidStack.class);
            Method getOut = recipeCls.getMethod("getChemicalOutput", FluidStack.class);
            Method hasF2C = recipeCls.getMethod("hasFluidToChemical");

            String[] probes = {"potato_s_t:oxygen", "potato_s_t:hydrogen", "potato_s_t:chlorine",
                    "potato_s_t:sulfuric_acid", "potato_s_t:diesel"};
            for (String id : probes) {
                Fluid f = BuiltInRegistries.FLUID.get(ResourceLocation.parse(id));
                if (f == null) {
                    log(out, "  " + id + " [流体不存在]");
                    continue;
                }
                FluidStack st = new FluidStack(f, 1000);
                List<String> matched = new ArrayList<>();
                String output = null;
                for (RecipeHolder<?> h : all) {
                    Object recipe = h.value();
                    if (!recipeCls.isInstance(recipe)) {
                        continue;
                    }
                    Object ok = test.invoke(recipe, st);
                    if (Boolean.TRUE.equals(ok)) {
                        matched.add(h.id().toString());
                        Object chem = getOut.invoke(recipe, st);
                        output = String.valueOf(chem);
                        Object f2c = hasF2C.invoke(recipe);
                        output = output + "  (hasFluidToChemical=" + f2c + ")";
                    }
                }
                log(out, String.format("  %-26s -> %s", id,
                        matched.isEmpty() ? "**没有任何 rotary 配方认它**"
                                : "命中 " + matched + "  产物=" + output));
            }

            // 反向再验一条：Mekanism 自己的氧气也必须命中同一条（两边应当一致）
            Fluid mekO = BuiltInRegistries.FLUID.get(ResourceLocation.parse("mekanism:oxygen"));
            if (mekO != null) {
                FluidStack st = new FluidStack(mekO, 1000);
                List<String> matched = new ArrayList<>();
                for (RecipeHolder<?> h : all) {
                    if (recipeCls.isInstance(h.value()) && Boolean.TRUE.equals(test.invoke(h.value(), st))) {
                        matched.add(h.id().toString());
                    }
                }
                log(out, "  对照：mekanism:oxygen 自己命中 " + matched);
            }
        } catch (ClassNotFoundException e) {
            log(out, "  [SKIP] 找不到 Mekanism 的类（它没装）：" + e.getMessage());
        } catch (Throwable t) {
            log(out, "  [FAIL] 反射调 Mekanism 时出错：" + t);
            for (StackTraceElement e : t.getStackTrace()) {
                log(out, "      at " + e);
            }
        }
    }
}
