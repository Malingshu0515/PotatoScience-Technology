package com.potatost.mod;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.tags.ItemTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ZF150 板材兼容的**一次性**取证探针（只读；跑完自删，见 {@code build/zftools/_zf150_probe.py}）。
 *
 * <p>它存在的唯一理由：0.12 起我们把 7 种板材挂进了 {@code c:plates/*}，而"挂上去到底有没有接上
 * 别人的配方"**只能在真服务端上查**（标签要等注册表绑好才有成员、配方要等数据包加载完才存在）。
 * 静态扫 jar 只能证明"上游写了 #c:plates/X"，证明不了"我们的板真的落在那张标签里"。</p>
 *
 * <p><b>行为</b>：只在 {@code ServerStartedEvent} 上跑一次，结果写进日志文件，然后
 * <b>关掉这个集成服务端</b>（它就是为这次取证起的）。不碰存档里的任何方块、不生成区块。</p>
 */
public final class Zf150Check {

    /** 我们有的 7 种板材（材料名 → 物品 id）；与 {@code data/c/tags/item/plates/*} 一一对应。 */
    private static final String[] MATERIALS = {
            "iron", "copper", "aluminum", "silver", "nickel", "cobalt", "steel"
    };

    /** 上游（别的 mod）声称会吃 c:plates/* 的配方类型。 */
    private static final String[] UPSTREAM_RECIPE_TYPES = {
            "create:pressing",
            "create:cutting",
            "create:milling",
            "createdieselgenerators:wire_cutting",
            "createdieselgenerators:hammering",
            "create_new_age:energising",
            "immersiveengineering:metal_press",
    };

    private static final Path OUT = Path.of("build", "zftools", "_zf150_probe.txt");

    /** 已经跑过就不再跑（两条事件都挂上，谁先到谁跑）。 */
    private static volatile boolean done = false;

    private Zf150Check() {
    }

    public static void register() {
        // 挂在**两条**事件上：正常情况 ServerAboutToStartEvent 先到（那时数据包已加载完、
        // 配方表可用，但世界还没开始生成），取证更快也更稳；
        // 万一某个版本上第一条不来，ServerStartedEvent 兜底。
        NeoForge.EVENT_BUS.addListener(Zf150Check::onAboutToStart);
        NeoForge.EVENT_BUS.addListener(Zf150Check::onServerStarted);
    }

    private static void onAboutToStart(net.neoforged.neoforge.event.server.ServerAboutToStartEvent event) {
        run(event.getServer());
    }

    private static void onServerStarted(ServerStartedEvent event) {
        run(event.getServer());
    }

    private static void log(List<String> out, String line) {
        out.add(line);
        System.out.println("[ZF150] " + line);
    }

    @SuppressWarnings("unchecked")
    private static void run(MinecraftServer server) {
        if (done) {
            return;
        }
        done = true;
        List<String> out = new ArrayList<>();

        try {
            log(out, "=== ZF150 板材兼容取证（" + server.getServerVersion() + "）===");
            log(out, "");

            // ---------- ① 我们的 7 种板材是否真的落在 c:plates/<mat> 里 ----------
            log(out, "--- ① c:plates/<材料> 的成员（左边=我们，右边=别的 mod）");
            for (String mat : MATERIALS) {
                TagKey<Item> tag = TagKey.create(Registries.ITEM,
                        ResourceLocation.fromNamespaceAndPath("c", "plates/" + mat));
                List<String> names = new ArrayList<>();
                for (var holder : BuiltInRegistries.ITEM.getTagOrEmpty(tag)) {
                    names.add(holder.value().getDescriptionId());
                }
                boolean mine = names.stream().anyMatch(n -> n.contains("potato_s_t"));
                log(out, String.format("  %-9s 成员 %-2d  %s   %s",
                        "c:plates/" + mat, names.size(), mine ? "[我方已就位]" : "[!! 我方不在里面]",
                        String.join(", ", names)));
            }

            // ---------- ② 父标签 c:plates ----------
            TagKey<Item> parent = TagKey.create(Registries.ITEM,
                    ResourceLocation.fromNamespaceAndPath("c", "plates"));
            int pc = 0;
            for (var holder : BuiltInRegistries.ITEM.getTagOrEmpty(parent)) {
                pc++;
            }
            log(out, "  父标签 c:plates 成员数 = " + pc);

            // ---------- ③ 配方类型普查：c: 相关类型各有多少条，其中吃我们标签的有几条 ----------
            log(out, "");
            log(out, "--- ② 上游配方类型普查（总数 / 输入含 c:plates 的条数）");
            for (String typeId : UPSTREAM_RECIPE_TYPES) {
                ResourceLocation id = ResourceLocation.tryParse(typeId);
                RecipeType<?> type = id == null ? null : BuiltInRegistries.RECIPE_TYPE.get(id);
                if (type == null) {
                    log(out, String.format("  %-38s [这个类型没注册 = 对应的 mod 没装]", typeId));
                    continue;
                }
                List<RecipeHolder<?>> recipes = (List<RecipeHolder<?>>) (List<?>)
                        server.getRecipeManager().getAllRecipesFor((RecipeType) type);
                TagKey<Item> anyPlate = TagKey.create(Registries.ITEM,
                        ResourceLocation.fromNamespaceAndPath("c", "plates"));
                int plates = 0;
                for (RecipeHolder<?> holder : recipes) {
                    boolean hit = false;
                    for (var ing : holder.value().getIngredients()) {
                        for (ItemStack st : ing.getItems()) {
                            if (st.is(anyPlate)) {
                                hit = true;
                                break;
                            }
                        }
                        if (hit) {
                            break;
                        }
                    }
                    if (hit) {
                        plates++;
                    }
                }
                log(out, String.format("  %-38s 共 %-4d 条，其中输入沾 c:plates 的 %d 条",
                        typeId, recipes.size(), plates));
            }

            // ---------- ④ 我们自己的 7 条 create:pressing 是否加载 ----------
            log(out, "");
            log(out, "--- ③ 我们写的 create:pressing 是否被加载（没装机械动力时这一段必然为空）");
            RecipeType<?> press = BuiltInRegistries.RECIPE_TYPE.get(
                    ResourceLocation.fromNamespaceAndPath("create", "pressing"));
            if (press == null) {
                log(out, "  机械动力没装 => 我们那 7 条带 neoforge:mod_loaded=create 守卫的配方全部不加载（预期行为）");
            } else {
                int ours = 0;
                List<RecipeHolder<?>> pressRecipes = (List<RecipeHolder<?>>) (List<?>)
                        server.getRecipeManager().getAllRecipesFor((RecipeType) press);
                for (RecipeHolder<?> holder : pressRecipes) {
                    if (holder.id().getNamespace().equals(PotatoST.MODID)) {
                        ours++;
                        // getResultItem 走的是 CommonRecipe 的默认实现，个别配方可能没覆写 =>
                        // 单条失败不能把整段取证带崩（所以这里自己 try 一次，不外抛）
                        String res;
                        try {
                            ItemStack st = holder.value().getResultItem(server.registryAccess());
                            res = st.isEmpty() ? "(空)" : st.getItem().getDescriptionId();
                        } catch (Throwable t) {
                            res = "(读产物失败: " + t.getClass().getSimpleName() + ")";
                        }
                        log(out, "  " + holder.id() + "  ->  " + res);
                    }
                }
                log(out, "  我方 create:pressing 共 " + ours + " 条（预期 7 条）");
            }

            log(out, "");
            log(out, "=== 取证结束，准备关闭这个集成服务端（只为取证而起的）===");
        } catch (Throwable t) {
            log(out, "!! 探针自己抛异常了：" + t);
            for (StackTraceElement e : t.getStackTrace()) {
                log(out, "    at " + e);
            }
        } finally {
            // 先写临时文件、再改名。理由：`server.halt()` 会让进程**立刻**退出，
            // 上一轮就是"日志打印出来了、文件却没落盘"（实测 13:43 那次）。
            // 原子改名保证磁盘上只会出现"完整的那一份"，绝不会留下半截。
            try {
                Files.createDirectories(OUT.getParent());
                Path tmp = OUT.resolveSibling(OUT.getFileName() + ".tmp");
                Files.write(tmp, out, StandardCharsets.UTF_8,
                        StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING,
                        StandardOpenOption.WRITE);
                try {
                    Files.move(tmp, OUT, java.nio.file.StandardCopyOption.REPLACE_EXISTING,
                            java.nio.file.StandardCopyOption.ATOMIC_MOVE);
                } catch (java.nio.file.AtomicMoveNotSupportedException ex) {
                    Files.move(tmp, OUT, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                }
                System.out.println("[ZF150] 取证结果已落盘: " + OUT.toAbsolutePath());
            } catch (IOException e) {
                System.out.println("[ZF150] 写日志失败：" + e);
            }
            server.halt(false);
        }
    }
}
