package com.potatost.mod;

import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.material.Fluid;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.fluids.FluidStack;

import mekanism.api.MekanismAPI;
import mekanism.api.chemical.ChemicalStack;
import mekanism.api.chemical.IChemicalHandler;
import mekanism.common.capabilities.Capabilities;

/**
 * ZF164 临时探针（0.13：灌装机 × Mekanism 化学品/气体兼容）。
 *
 * <p>验的是**装了 Mek 的真服务端**：</p>
 * <ul>
 *   <li><b>A 事实</b>：Mek 在；{@code mekanism:jetpack} 真的挂着物品化学品能力；
 *       我们的氢/氧/氯流体身上有 {@code c:hydrogen/oxygen/chlorine} 标签，而 Mek 注册表里
 *       有同名的 {@code mekanism:hydrogen/oxygen/chlorine} 化学品（= 桥的映射前提）；
 *       负对照：我们的原油在 Mek 那边没有同名化学品。</li>
 *   <li><b>B 真灌装</b>：罐里放我们的氢、槽里放一个**全新的喷气背包**，跑 20 tick ⇒
 *       背包里的化学品 +100 mB、罐 −100 mB、电 −1200 FE（质量守恒逐条对）。</li>
 *   <li><b>C 负对照</b>：不是化学品容器的物品照旧 UNSUPPORTED；罐里放原油时灌不了；
 *       自家高压气罐/油桶那两条老规矩一个字节没变；没电时不灌。</li>
 * </ul>
 *
 * <p>⚠ 报告在 {@code ServerStartedEvent} 里**立即**写（ZF160 §4.168① 的教训：别等 tick）。</p>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class Zf164Check {

    private static final String TAG = "[A164] ";
    private static final Path REPORT = Path.of("E:\\PotatoST\\build\\zftools\\_zf164_probe_utf8.txt");

    private static final List<String> LINES = new ArrayList<>();
    /** 「我们挂了 c: 标签、Mek 那边没有同名化学品」的那些流体名（A 段查出来给 C 段用）。 */
    private static final List<String> NO_CHEM = new ArrayList<>();
    private static int passed = 0;
    private static int failed = 0;

    private Zf164Check() {
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
            fill(server.overworld());
            negatives(server.overworld());
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

    // ================= A 事实 =================

    private static void facts() {
        LINES.add("== A 段：Mek 与标签/化学品的事实 ==");
        check(ModList.get().isLoaded("mekanism"), "A1 Mekanism 已加载");
        Item jetpack = BuiltInRegistries.ITEM.get(ResourceLocation.parse("mekanism:jetpack"));
        check(jetpack != net.minecraft.world.item.Items.AIR, "A2 物品 mekanism:jetpack 在注册表里");
        ItemStack jp = new ItemStack(jetpack);
        IChemicalHandler h = jp.getCapability(Capabilities.CHEMICAL.item());
        check(h != null, "A3 喷气背包挂着物品化学品能力（mekanism:chemical_handler）");
        if (h != null) {
            LINES.add("   调试：喷气背包化学品罐数 = " + h.getChemicalTanks()
                    + "，容量 = " + (h.getChemicalTanks() > 0 ? h.getChemicalTankCapacity(0) : -1)
                    + "，现有 = " + (h.getChemicalTanks() > 0 ? h.getChemicalInTank(0).getAmount() : -1));
        }
        for (String gas : new String[]{"hydrogen", "oxygen", "chlorine"}) {
            Fluid ours = fluidOf("potato_s_t:" + gas);
            boolean tagged = ours != null && BuiltInRegistries.FLUID.wrapAsHolder(ours)
                    .is(TagKey.create(Registries.FLUID, ResourceLocation.parse("c:" + gas)));
            var chem = mekChemical("mekanism:" + gas);
            boolean chemOk = chem != null && chem == MekanismAPI.CHEMICAL_REGISTRY
                    .get(ResourceLocation.parse("mekanism:" + gas));
            check(tagged && chemOk, "A4 我们的 " + gas + " 挂着 c:" + gas + " 且 Mek 有 mekanism:" + gas,
                    "标签=" + tagged + " 化学品=" + (chem == null ? "无" : chem.getTranslationKey()));
        }
        Fluid oil = fluidOf("potato_s_t:crude_oil");
        boolean oilTagged = oil != null && BuiltInRegistries.FLUID.wrapAsHolder(oil)
                .is(TagKey.create(Registries.FLUID, ResourceLocation.parse("c:crude_oil")));
        var oilChem = mekChemical("mekanism:crude_oil");
        LINES.add("   调试：原油：c:crude_oil=" + oilTagged + "，Mek 同名化学品="
                + (oilChem == null ? "无" : MekanismAPI.CHEMICAL_REGISTRY.getKey(oilChem)));
        // 找一件"我们挂了 c: 标签、Mek 那边**没有**同名化学品"的流体当负对照（逐条列出来）
        
        for (String f : new String[]{"diesel", "naphtha", "lpg", "gasoline", "bitumen", "sulfuric_acid"}) {
            Fluid ours = fluidOf("potato_s_t:" + f);
            if (ours == null) {
                continue;
            }
            boolean tagged = BuiltInRegistries.FLUID.wrapAsHolder(ours)
                    .is(TagKey.create(Registries.FLUID, ResourceLocation.parse("c:" + f)));
            var chem = mekChemical("mekanism:" + f);
            LINES.add("   调试：我们的 " + f + "：c:" + f + "=" + tagged + "，Mek 同名化学品="
                    + (chem == null ? "无" : MekanismAPI.CHEMICAL_REGISTRY.getKey(chem)));
            if (tagged && chem == null) {
                NO_CHEM.add(f);
            }
        }
        check(!NO_CHEM.isEmpty(),
                "A5 至少有一种「我们挂了 c: 标签但 Mek 没有同名化学品」的流体（映射查不到 ⇒ 灌不了）",
                "候选 " + NO_CHEM);
        LINES.add("   调试：Mek 化学品注册表条目数 = " + MekanismAPI.CHEMICAL_REGISTRY.size());
    }

    /** ⚠ 必须带 getKey 反查：DefaultedRegistry 查不到时会回默认值（`mekanism:empty`），直接 get 会误判"有"。 */
    private static mekanism.api.chemical.Chemical mekChemical(String id) {
        ResourceLocation rl = ResourceLocation.parse(id);
        var c = MekanismAPI.CHEMICAL_REGISTRY.get(rl);
        return c != null && rl.equals(MekanismAPI.CHEMICAL_REGISTRY.getKey(c)) ? c : null;
    }

    private static Fluid fluidOf(String id) {
        return BuiltInRegistries.FLUID.get(ResourceLocation.parse(id));
    }

    // ================= B 真灌装 =================

    private static void fill(ServerLevel level) {
        LINES.add("== B 段：罐里的我们的氢 → 喷气背包（真方块实体）==");
        BlockPos pos = level.getSharedSpawnPos().offset(8, 14, 8);
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
        level.setBlock(pos, ModBlocks.FILLING_MACHINE.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(pos) instanceof FillingMachineBlockEntity be)) {
            check(false, "B0 灌装机方块实体建出来了");
            return;
        }
        FakePlayer fake = FakePlayerFactory.getMinecraft(level);
        FillingMachineMenu menu = new FillingMachineMenu(0, fake.getInventory(), be);
        ItemStack jet = new ItemStack(BuiltInRegistries.ITEM.get(ResourceLocation.parse("mekanism:jetpack")));
        check(be.getInventory().isItemValid(0, jet) && menu.slots.get(0).mayPlace(jet),
                "B1 三道门对喷气背包都放行（ZF162 的口径没退）");

        be.getTank(0).fill(new FluidStack(ModFluids.HYDROGEN.get(), 5000),
                net.neoforged.neoforge.fluids.capability.IFluidHandler.FluidAction.EXECUTE);
        be.getEnergyStorage().receiveEnergy(FillingMachineBlockEntity.MAX_ENERGY, false);
        int e0 = be.getEnergy();
        be.getInventory().setStackInSlot(0, jet);
        for (int t = 0; t < 20; t++) {
            FillingMachineBlockEntity.tick(level, pos, level.getBlockState(pos), be);
        }
        ItemStack after = be.getInventory().getStackInSlot(0);
        long chem = chemicalAmount(after);
        int left = be.getTank(0).getFluidAmount();
        check(chem == 100, "B2 喷气背包里多出 100 mB 的 Mek 化学品（20 tick × 5 mB）", "实际 " + chem);
        check(left == 4900, "B3 罐里剩 4900 mB 我们的氢", "实际 " + left);
        check(e0 - be.getEnergy() == 20 * FillingMachineBlockEntity.ENERGY_PER_TANK,
                "B4 电按罐计扣了 1200 FE", "扣了 " + (e0 - be.getEnergy()));
        check(5000 - left == chem, "B5 质量守恒：罐减少的量 == 物品里增加的量",
                "罐 −" + (5000 - left) + " / 物品 +" + chem);
        check(be.stateOf(0) == FillingMachineBlockEntity.SlotState.FULL
                        || be.stateOf(0) == FillingMachineBlockEntity.SlotState.NO_POWER
                        || be.stateOf(0) == FillingMachineBlockEntity.SlotState.FILLING,
                "B6 诊断不再把喷气背包说成「灌不了」", "state=" + be.stateOf(0));
        LINES.add("   调试：物品里的化学品 = " + chemicalName(after) + " × " + chem
                + "（用户要的就是 mekanism:hydrogen）");
    }

    private static long chemicalAmount(ItemStack stack) {
        IChemicalHandler h = stack.getCapability(Capabilities.CHEMICAL.item());
        if (h == null) {
            return -1;
        }
        long total = 0;
        for (int i = 0; i < h.getChemicalTanks(); i++) {
            total += h.getChemicalInTank(i).getAmount();
        }
        return total;
    }

    private static String chemicalName(ItemStack stack) {
        IChemicalHandler h = stack.getCapability(Capabilities.CHEMICAL.item());
        if (h == null) {
            return "(没有化学品能力)";
        }
        ChemicalStack s = h.getChemicalInTank(0);
        return s.isEmpty() ? "(空)" : String.valueOf(MekanismAPI.CHEMICAL_REGISTRY.getKey(s.getChemical()));
    }

    // ================= C 负对照 =================

    private static void negatives(ServerLevel level) {
        LINES.add("== C 段：负对照 ==");
        BlockPos pos = level.getSharedSpawnPos().offset(8, 14, 8);
        if (!(level.getBlockEntity(pos) instanceof FillingMachineBlockEntity be)) {
            return;
        }
        be.getInventory().setStackInSlot(0, ItemStack.EMPTY);
        be.getInventory().setStackInSlot(0, new ItemStack(net.minecraft.world.item.Items.EMERALD));
        int e = be.getEnergy();
        int a = be.getTank(0).getFluidAmount();
        for (int t = 0; t < 3; t++) {
            FillingMachineBlockEntity.tick(level, pos, level.getBlockState(pos), be);
        }
        check(be.stateOf(0) == FillingMachineBlockEntity.SlotState.UNSUPPORTED
                        && be.getTank(0).getFluidAmount() == a && be.getEnergy() == e,
                "C1 绿宝石（既不是流体容器也不是化学品容器）⇒ UNSUPPORTED，罐电不动",
                "state=" + be.stateOf(0));
        be.getInventory().setStackInSlot(0, ItemStack.EMPTY);

        // 罐 1 放"我们挂了 c: 标签、Mek 没有同名化学品"的那种流体 + 槽 1 放喷气背包 ⇒ 灌不了
        Fluid orphan = fluidOf("potato_s_t:" + (NO_CHEM.isEmpty() ? "diesel" : NO_CHEM.get(0)));
        be.getTank(1).fill(new FluidStack(orphan, 3000),
                net.neoforged.neoforge.fluids.capability.IFluidHandler.FluidAction.EXECUTE);
        ItemStack jet2 = new ItemStack(BuiltInRegistries.ITEM.get(ResourceLocation.parse("mekanism:jetpack")));
        be.getInventory().setStackInSlot(1, jet2);
        int a2 = be.getTank(1).getFluidAmount();
        int e2 = be.getEnergy();
        for (int t = 0; t < 3; t++) {
            FillingMachineBlockEntity.tick(level, pos, level.getBlockState(pos), be);
        }
        check(be.getTank(1).getFluidAmount() == a2 && be.getEnergy() == e2
                        && chemicalAmount(be.getInventory().getStackInSlot(1)) <= 0,
                "C2 Mek 没有同名化学品的那种流体 ⇒ 灌不进喷气背包（罐与电一个字节没动）",
                "流体=" + BuiltInRegistries.FLUID.getKey(orphan) + " 罐=" + be.getTank(1).getFluidAmount()
                        + " 电=" + be.getEnergy() + " 化学品=" + chemicalAmount(be.getInventory().getStackInSlot(1)));
        be.getInventory().setStackInSlot(1, ItemStack.EMPTY);

        // 罐 2 放原油 + 槽 2 放喷气背包：映射有（mekanism:crude_oil）但**喷气背包只收氢** ⇒ 拒收
        be.getTank(2).fill(new FluidStack(ModFluids.CRUDE_OIL.get(), 3000),
                net.neoforged.neoforge.fluids.capability.IFluidHandler.FluidAction.EXECUTE);
        be.getInventory().setStackInSlot(2, new ItemStack(
                BuiltInRegistries.ITEM.get(ResourceLocation.parse("mekanism:jetpack"))));
        int a3 = be.getTank(2).getFluidAmount();
        for (int t = 0; t < 3; t++) {
            FillingMachineBlockEntity.tick(level, pos, level.getBlockState(pos), be);
        }
        check(be.getTank(2).getFluidAmount() == a3
                        && chemicalAmount(be.getInventory().getStackInSlot(2)) <= 0,
                "C3 罐里放原油（Mek 没有同名化学品）⇒ 喷气背包收不到东西，罐不动",
                "罐=" + be.getTank(2).getFluidAmount() + " 化学品="
                        + chemicalAmount(be.getInventory().getStackInSlot(2)));
        be.getInventory().setStackInSlot(2, ItemStack.EMPTY);

        // 自家气罐：罐 0（我们的氢）⇒ 能灌；罐 2（原油）⇒ 拒收（用户点名"这两个不要动"）
        be.getInventory().setStackInSlot(0, new ItemStack(ModItems.HIGH_PRESSURE_TANK.get()));
        check(be.stateOf(0) == FillingMachineBlockEntity.SlotState.FILLING
                        || be.stateOf(0) == FillingMachineBlockEntity.SlotState.NO_POWER
                        || be.stateOf(0) == FillingMachineBlockEntity.SlotState.FULL,
                "C4 自家高压气罐在氢气罐上仍是「能灌」（老规矩没变）", "state=" + be.stateOf(0));
        be.getInventory().setStackInSlot(0, ItemStack.EMPTY);
        be.getInventory().setStackInSlot(2, new ItemStack(ModItems.HIGH_PRESSURE_TANK.get()));
        check(be.stateOf(2) == FillingMachineBlockEntity.SlotState.REJECTED,
                "C5 自家高压气罐在**原油**罐上仍是拒收", "state=" + be.stateOf(2));
        be.getInventory().setStackInSlot(2, ItemStack.EMPTY);

        check(FillingMachineBlockEntity.ENERGY_PER_TANK == 60 && FillingMachineBlockEntity.FILL_RATE == 5,
                "C6 锁定数字没动（60 FE/罐/t、5 mB/t）");
    }
}
