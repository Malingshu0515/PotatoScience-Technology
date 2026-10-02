package com.potatost.mod;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.material.Fluid;
import net.neoforged.fml.ModList;
import net.neoforged.neoforge.fluids.FluidStack;

import mekanism.api.Action;
import mekanism.api.MekanismAPI;
import mekanism.api.chemical.Chemical;
import mekanism.api.chemical.ChemicalStack;
import mekanism.api.chemical.IChemicalHandler;
import mekanism.common.capabilities.Capabilities;

/**
 * 「我们的流体 → Mekanism 的化学品（气体）」这条桥（0.13 ZF164）。
 *
 * <p><b>为什么需要它</b>：Mek 的喷气背包吃的是 Mek 自己的<strong>化学品</strong>
 * （10.7 起气体已并进化学品 API，物品能力名是 {@code mekanism:chemical_handler}），
 * 而我们机器里装的是<strong>流体</strong> —— 两条系统。用户原话：
 * 「mek喷气背包还是不可以灌本mod的氢 你看看能不能做一下兼容」。</p>
 *
 * <p><b>怎么映射（这就是"同标签"那条口径）</b>：流体身上的 {@code c:<名字>} 标签 ⇒
 * 到 Mek 的化学品注册表里找<strong>同路径</strong>的那一个（我们的氢挂在 {@code c:hydrogen}、
 * Mek 有 {@code mekanism:hydrogen}）。<b>我们一个气体名都不硬写</b>：找得到就灌、找不到就当灌不了。
 * 这与 Mek 自己的旋转冷凝器配方（{@code FluidChemicalToChemicalRecipe}）是同一件事
 * —— ZF159 那轮已实测 {@code RotaryRecipe#test(我们的氧气)} = true、
 * {@code getChemicalOutput} = {@code 1 mekanism:oxygen}，即 1:1。</p>
 *
 * <p><b>软依赖怎么保证不炸</b>：本类是唯一 import {@code mekanism.*} 的地方，
 * 而它的公开方法签名里<strong>只有原版 / NeoForge 类型</strong>（{@code ItemStack} / {@code FluidStack} /
 * {@code int} / {@code boolean}）⇒ 灌装机那边只在 {@link #present()} 为真时才调它，
 * 没装 Mek 的实例根本不会加载本类（JVM 惰性解析），也就不会 {@code NoClassDefFoundError}。
 * {@code build.gradle} 里它是 {@code compileOnly}，<b>不进产物 jar</b>。</p>
 */
public final class MekChemicalBridge {

    /** 流体 → 化学品（查一次缓存一次；{@code Optional.empty()} = 这个流体在 Mek 那边没有对得上的化学品）。 */
    private static final Map<Fluid, Optional<Chemical>> CACHE = new HashMap<>();

    private MekChemicalBridge() {
    }

    /** Mek 在不在 —— 这是灌装机唯一允许先问的一句话。 */
    public static boolean present() {
        return ModList.get().isLoaded(MekanismAPI.MEKANISM_MODID);
    }

    /** 槽里那件东西是不是 Mek 的化学品容器（喷气背包走的就是这一路）。 */
    public static boolean canHandle(ItemStack stack) {
        return handlerOf(stack) != null;
    }

    /**
     * 这件东西此刻还能装多少 mB 的 {@code fluid}（−1 = 灌不了：不是 Mek 容器 / 没对得上的化学品）。
     *
     * <p>用 <b>SIMULATE</b> 问 Mek 自己：插进去多少、退回来多少，差值就是装得下的量。</p>
     */
    public static int spaceFor(ItemStack stack, FluidStack fluid) {
        IChemicalHandler handler = handlerOf(stack);
        Chemical chemical = chemicalFor(fluid);
        if (handler == null || chemical == null || fluid.isEmpty()) {
            return -1;
        }
        int want = Math.min(fluid.getAmount(), 100_000);
        ChemicalStack rest = handler.insertChemical(stackFor(chemical, want), Action.SIMULATE);
        return (int) (want - rest.getAmount());
    }

    /** 这件东西收不收这一种（判据同样是"Mek 自己说了算"）。 */
    public static boolean accepts(ItemStack stack, FluidStack fluid) {
        if (handlerOf(stack) == null || chemicalFor(fluid) == null) {
            return false;
        }
        return spaceFor(stack, fluid) >= 0;
    }

    /**
     * 真灌：往这件东西里插 {@code max} mB 对应的化学品，返回<strong>真的插进去多少 mB</strong>。
     *
     * <p>顺序与"绝不凭空吞流体"这条老规矩对齐：先 SIMULATE 算出能进多少 → 再 EXECUTE 就插那么多
     * → 只有 EXECUTE 一点没剩（{@code remainder} 为空）才算成功。灌装机那边<strong>只按这个返回值扣罐扣电</strong>。</p>
     *
     * <p>⚠ Mek 的物品句柄是<strong>就地改物品</strong>的（化学品存在物品的数据组件里），所以这里直接改
     * 传进来的那份 {@code stack}（灌装机传的就是槽里那一份）。</p>
     */
    public static int fill(ItemStack stack, FluidStack fluid, int max) {
        IChemicalHandler handler = handlerOf(stack);
        Chemical chemical = chemicalFor(fluid);
        if (handler == null || chemical == null || fluid.isEmpty() || max <= 0) {
            return 0;
        }
        int want = Math.min(max, fluid.getAmount());
        ChemicalStack simRest = handler.insertChemical(stackFor(chemical, want), Action.SIMULATE);
        int canTake = (int) (want - simRest.getAmount());
        if (canTake <= 0) {
            return 0;
        }
        ChemicalStack rest = handler.insertChemical(stackFor(chemical, canTake), Action.EXECUTE);
        if (!rest.isEmpty()) {
            // 不该发生（刚 SIMULATE 过）；真发生了就按"实际插进去的那部分"结算，绝不吞
            return (int) Math.max(0, canTake - rest.getAmount());
        }
        return canTake;
    }

    // ================= 内部：能力与映射 =================

    private static IChemicalHandler handlerOf(ItemStack stack) {
        if (stack.isEmpty() || stack.getCount() != 1) {
            return null;
        }
        return stack.getCapability(Capabilities.CHEMICAL.item());
    }

    /** 造一份化学品栈（走带 Holder 的构造器：{@code (Chemical, long)} 那个已被 Mek 标成待删除）。 */
    private static ChemicalStack stackFor(Chemical chemical, long amount) {
        return new ChemicalStack(MekanismAPI.CHEMICAL_REGISTRY.wrapAsHolder(chemical), amount);
    }

    /** 流体 → 化学品：按**同名 c: 标签**去 Mek 的注册表里找同路径的那一个（查一次缓存一次）。 */
    private static Chemical chemicalFor(FluidStack fluid) {
        return fluid.isEmpty() ? null : chemicalFor(fluid.getFluid());
    }

    private static Chemical chemicalFor(Fluid fluid) {
        Optional<Chemical> hit = CACHE.get(fluid);
        if (hit == null) {
            Chemical found = null;
            for (TagKey<Fluid> tag : BuiltInRegistries.FLUID.wrapAsHolder(fluid).tags().toList()) {
                if (!tag.location().getNamespace().equals("c")) {
                    continue;
                }
                ResourceLocation wanted = ResourceLocation.fromNamespaceAndPath(MekanismAPI.MEKANISM_MODID,
                        tag.location().getPath());
                Chemical candidate = MekanismAPI.CHEMICAL_REGISTRY.get(wanted);
                // ⚠ 只认"注册表里真挂在这个 id 上"的那一个：DefaultedRegistry 查不到时会回默认值（空化学品），
                //   所以拿 getKey(candidate) 反查一遍 —— 比直接比"空化学品"更准，也不碰已废弃的那两个常量。
                if (candidate != null && wanted.equals(MekanismAPI.CHEMICAL_REGISTRY.getKey(candidate))) {
                    found = candidate;
                    break;
                }
            }
            hit = Optional.ofNullable(found);
            CACHE.put(fluid, hit);
        }
        return hit.orElse(null);
    }
}
