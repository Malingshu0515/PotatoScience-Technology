package com.potatost.mod.client.jei;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.potatost.mod.MachineRecipes;
import com.potatost.mod.ModBlocks;
import com.potatost.mod.PotatoST;

import mezz.jei.api.IModPlugin;
import mezz.jei.api.JeiPlugin;
import mezz.jei.api.helpers.IGuiHelper;
import mezz.jei.api.recipe.RecipeType;
import mezz.jei.api.recipe.category.IRecipeCategory;
import mezz.jei.api.registration.IRecipeCatalystRegistration;
import mezz.jei.api.registration.IRecipeCategoryRegistration;
import mezz.jei.api.registration.IRecipeRegistration;

import com.mojang.logging.LogUtils;
import org.slf4j.Logger;

import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;

/**
 * PotatoS&amp;T 的 JEI 插件（0.10 ZF19 新增）。
 *
 * <p><b>怎么被加载的：</b>JEI 自己扫描所有 mod 的类找 {@link JeiPlugin} 注解。
 * 所以<b>没装 JEI 的客户端根本不会加载本类</b> —— 这也是为什么 JEI 类型只允许出现在
 * {@code client.jei} 包下：本包之外任何一个类引用到 JEI，没装 JEI 的玩家就会崩（见
 * {@link MachineRecipes} 的红线说明）。</p>
 *
 * <p><b>加一台新机器：</b>在 {@link #MACHINES} 加一行机器 id（= 方块注册名）即可 ——
 * 分类、图标、催化剂、标题全都是从这一行推出来的，不用再写 JEI 代码。
 * 配方数据来自 {@link MachineRecipes#all()}（按 {@code machineId} 过滤）。</p>
 */
@JeiPlugin
public class PotatoSTJeiPlugin implements IModPlugin {

    private static final ResourceLocation PLUGIN_UID =
            ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "jei_plugin");

    /**
     * 本项目第一个 logger。
     *
     * <p><b>为什么要打日志：</b>JEI 只在插件"慢"的时候才打点（{@code PluginCallerTimerRunnable}），
     * 我们这种小插件**成功加载时日志里一个字都没有** —— 也就是说"没报错"根本不能证明集成是活的。
     * 打两行 INFO 之后，"JEI 到底有没有发现我们"就变成可取证的事（0.10 ZF19 加）。</p>
     */
    private static final Logger LOGGER = LogUtils.getLogger();

    /**
     * 有配方的机器，顺序即 JEI 里的分类顺序。
     * <b>id 必须等于方块注册名</b>（标题复用 {@code block.potato_s_t.<id>}）。
     */
    private static final List<String> MACHINES =
            List.of("micro_crusher", "electrolyzer", "salt_dryer", "filling_machine", "hydraulic_press",
                    "salt_decomposer", "electric_blast_furnace", "alloy_smelter",
                    "hydrodesulfurization_chamber", "air_separator", "ammonia_synthesis_chamber",
                    "lithium_battery_plant");

    /** 机器 id → JEI 配方类型（纯静态工厂，不读注册表，放 static final 安全）。 */
    private static final Map<String, RecipeType<MachineRecipes.Entry>> TYPES = buildTypes();

    private static Map<String, RecipeType<MachineRecipes.Entry>> buildTypes() {
        Map<String, RecipeType<MachineRecipes.Entry>> map = new LinkedHashMap<>();
        for (String machine : MACHINES) {
            map.put(machine, RecipeType.create(PotatoST.MODID, machine, MachineRecipes.Entry.class));
        }
        return Map.copyOf(map);
    }

    @Override
    public ResourceLocation getPluginUid() {
        return PLUGIN_UID;
    }

    /** 机器方块本身作为 JEI 图标（读注册表 ⇒ 只能在回调里取，不能放 static final，见 §4.1）。 */
    private static ItemStack iconFor(String machine) {
        return switch (machine) {
            case "micro_crusher" -> new ItemStack(ModBlocks.MICRO_CRUSHER_ITEM.get());
            case "electrolyzer" -> new ItemStack(ModBlocks.ELECTROLYZER_ITEM.get());
            case "salt_dryer" -> new ItemStack(ModBlocks.SALT_DRYER_ITEM.get());
            case "filling_machine" -> new ItemStack(ModBlocks.FILLING_MACHINE_ITEM.get());
            case "hydraulic_press" -> new ItemStack(ModBlocks.HYDRAULIC_PRESS_ITEM.get());
            case "salt_decomposer" -> new ItemStack(ModBlocks.SALT_DECOMPOSER_ITEM.get());
            case "electric_blast_furnace" -> new ItemStack(ModBlocks.ELECTRIC_BLAST_FURNACE_ITEM.get());
            case "alloy_smelter" -> new ItemStack(ModBlocks.ALLOY_SMELTER_ITEM.get());
            case "hydrodesulfurization_chamber" -> new ItemStack(ModBlocks.HYDRODESULFURIZATION_CHAMBER_ITEM.get());
            case "air_separator" -> new ItemStack(ModBlocks.AIR_SEPARATOR_ITEM.get());
            case "ammonia_synthesis_chamber" -> new ItemStack(ModBlocks.AMMONIA_SYNTHESIS_CHAMBER_ITEM.get());
            // ⚠ 0.11 ZF123 补：ZF112 把 `lithium_battery_plant` 加进 MACHINES 时**漏了这个 case**
            //   ⇒ 返回 ItemStack.EMPTY ⇒ JEI 抛 "Ingredient is invalid … 0 minecraft:air"
            //   ⇒ **整个插件的分类与配方全被丢弃**（12 台机器一台的 JEI 页面都没有，2026-09-25 22:19 起）。
            case "lithium_battery_plant" -> new ItemStack(ModBlocks.LITHIUM_BATTERY_PLANT_ITEM.get());
            default -> ItemStack.EMPTY;
        };
    }

    /** 取这台机器的全部配方（`registerCategories` 算尺寸、`registerRecipes` 上报都要用）。 */
    private static List<MachineRecipes.Entry> forMachine(String machine) {
        List<MachineRecipes.Entry> mine = new ArrayList<>();
        for (MachineRecipes.Entry entry : MachineRecipes.all()) {
            if (entry.machineId().equals(machine)) {
                mine.add(entry);
            }
        }
        return mine;
    }

    @Override
    public void registerCategories(IRecipeCategoryRegistration registration) {
        IGuiHelper gui = registration.getJeiHelpers().getGuiHelper();
        List<IRecipeCategory<?>> categories = new ArrayList<>();
        List<String> served = new ArrayList<>();
        List<String> skipped = new ArrayList<>();
        for (String machine : MACHINES) {
            // ★ 分类尺寸按这台机器「最坏的一条配方」算。
            //   写死高度会让输入多的配方画出框外 —— "石英建材"那组有 6 个输入，6×20=120px 直接爆框（ZF20 修）。
            List<MachineRecipes.Entry> mine = forMachine(machine);
            int maxInItems = 0;
            int maxInFluids = 0;
            int maxOutItems = 0;
            int maxOutFluids = 0;
            int maxInfo = 0;
            for (MachineRecipes.Entry entry : mine) {
                maxInItems = Math.max(maxInItems, entry.itemIn().size());
                maxInFluids = Math.max(maxInFluids, entry.fluidIn().size());
                maxOutItems = Math.max(maxOutItems, entry.itemOut().size());
                maxOutFluids = Math.max(maxOutFluids, entry.fluidOut().size());
                maxInfo = Math.max(maxInfo, entry.info().size());
            }
            // ⚠ 0.11 ZF123 兜底：icon 为空**只跳过这一台**，绝不让 JEI 把整个插件的结果丢掉。
            //   以前这里直接把 ItemStack.EMPTY 交给 JEI ⇒ 它抛异常 ⇒ **所有**机器的 JEI 页面一起消失
            //   （ZF112 漏一个 case 就够整个模组的 JEI 全灭，而且服务端探针一条都查不到 —— 见档案 §4.101）。
            ItemStack icon = iconFor(machine);
            if (icon.isEmpty()) {
                LOGGER.error("[potato_s_t] JEI SKIPPED '{}': iconFor() has no case for this machine (returned an empty item)"
                        + " —— add it to PotatoSTJeiPlugin.iconFor switch, otherwise this machine is invisible in JEI", machine);
                skipped.add(machine);
                continue;
            }
            categories.add(new MachineRecipeCategory(
                    TYPES.get(machine),
                    Component.translatable("block.potato_s_t." + machine),
                    gui.createDrawableItemStack(icon),
                    gui, maxInItems, maxInFluids, maxOutItems, maxOutFluids, maxInfo));
            served.add(machine);
            LOGGER.info("[potato_s_t] JEI category {}: {} recipes, worst case in={}item/{}fluid out={}item/{}fluid info={} lines",
                    machine, mine.size(), maxInItems, maxInFluids, maxOutItems, maxOutFluids, maxInfo);
        }
        registration.addRecipeCategories(categories.toArray(new IRecipeCategory<?>[0]));
        if (skipped.isEmpty()) {
            LOGGER.info("[potato_s_t] JEI: registered {} machine recipe categories {}",
                    served.size(), served);
        } else {
            LOGGER.error("[potato_s_t] JEI: {} categories registered, {} SKIPPED {}(see the ERROR lines above)",
                    served.size(), skipped.size(), skipped);
        }
    }

    @Override
    public void registerRecipes(IRecipeRegistration registration) {
        List<MachineRecipes.Entry> all = MachineRecipes.all();
        int categories = 0;
        for (String machine : MACHINES) {
            List<MachineRecipes.Entry> mine = forMachine(machine);
            if (!mine.isEmpty()) {
                registration.addRecipes(TYPES.get(machine), List.copyOf(mine));
                categories++;
            }
        }
        LOGGER.info("[potato_s_t] JEI: registered {} machine recipes across {} categories", all.size(), categories);
    }

    /** 把机器方块挂成催化剂：在 JEI 里对着机器按 R 就能直接跳到对应分类。 */
    @Override
    public void registerRecipeCatalysts(IRecipeCatalystRegistration registration) {
        for (String machine : MACHINES) {
            // ⚠ 0.11 ZF123：同 registerCategories 的兜底 —— 空 icon 会让 JEI 抛
            //   "Recipe catalyst must be a valid ingredient"，一样是**整个插件**一起没。
            ItemStack icon = iconFor(machine);
            if (icon.isEmpty()) {
                LOGGER.error("[potato_s_t] JEI catalyst SKIPPED '{}'(iconFor returned an empty item)", machine);
                continue;
            }
            registration.addRecipeCatalyst(icon, TYPES.get(machine));
        }
    }
}
