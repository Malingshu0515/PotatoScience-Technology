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
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;

/**
 * ZF166 临时探针（0.13：流体转化器 —— 同标签流体跨 mod 互转）。
 *
 * <p>验的是**装了沉浸工程 / 沉浸原油的真服务端**：</p>
 * <ul>
 *   <li><b>A 事实</b>：`c:diesel` 里既有我们的柴油、也有别人家的柴油；`sharesCTag` 对它们为真，
 *       对清水为假（负对照）。</li>
 *   <li><b>B 真转化</b>：方块能力登记齐（能收电、能灌流体）；输入罐 3000 mB 我们的柴油 +
 *       输出罐 1000 mB 样板；跑 20 tick ⇒ 输入 −1000、输出 +1000（**1:1**）、电 −600，
 *       而且输出罐里**还是样板那一种**（证明"转化"真的换了流体种类，而不是把我们的柴油搬过去）。</li>
 *   <li><b>C 手倒</b>：原版**水桶**倒进输出罐（= 设样板）⇒ 输出罐拿到 1000 mB 水、
 *       手里那件变成**空桶**（走 NeoForge 物品流体能力 + getContainer 写回）；
 *       负对照：钻石倒不进去。</li>
 *   <li><b>D 能力语义</b>：管道能力是"进的一律进输入罐、抽的一律从输出罐出"。</li>
 * </ul>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class Zf166Check {

    private static final String TAG = "[A166] ";
    private static final Path REPORT = Path.of("E:\\PotatoST\\build\\zftools\\_zf166_probe_utf8.txt");

    private static final List<String> LINES = new ArrayList<>();
    private static int passed = 0;
    private static int failed = 0;

    private Zf166Check() {
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
            ServerLevel level = server.overworld();
            Fluid ours = BuiltInRegistries.FLUID.get(ResourceLocation.parse("potato_s_t:diesel"));
            Fluid theirs = facts(ours);
            if (theirs != null) {
                convert(level, ours, theirs);
                handPour(level);
                capabilities(level, ours, theirs);
            }
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

    private static Fluid facts(Fluid ours) {
        LINES.add("== A 段：标签事实 ==");
        check(ModList.get().isLoaded("immersiveengineering"), "A1 沉浸工程已加载");
        check(ModList.get().isLoaded("immersivepetroleum"), "A2 沉浸原油已加载");
        TagKey<Fluid> diesel = TagKey.create(Registries.FLUID, ResourceLocation.parse("c:diesel"));
        List<String> members = new ArrayList<>();
        Fluid theirs = null;
        var held = BuiltInRegistries.FLUID.getTag(diesel);
        if (held.isPresent()) {
            for (var h : held.get()) {
                ResourceLocation id = BuiltInRegistries.FLUID.getKey(h.value());
                members.add(id.toString());
                String ns = id.getNamespace();
                if (!ns.equals("potato_s_t") && !ns.equals("minecraft") && !id.getPath().startsWith("flowing")
                        && theirs == null) {
                    theirs = h.value();
                }
            }
        }
        LINES.add("   c:diesel 成员 = " + members);
        check(members.contains("potato_s_t:diesel"), "A3 我们的柴油在 c:diesel 里");
        check(theirs != null, "A4 c:diesel 里也有别人家的柴油（用来当样板）",
                theirs == null ? "没有" : BuiltInRegistries.FLUID.getKey(theirs).toString());
        if (theirs == null) {
            return null;
        }
        check(FluidConverterBlockEntity.sharesCTag(ours, theirs),
                "A5 sharesCTag(我们的柴油, 他们的柴油) = true");
        check(!FluidConverterBlockEntity.sharesCTag(ours, Fluids.WATER),
                "A6 负对照：sharesCTag(我们的柴油, 清水) = false");
        LINES.add("   调试：样板 = " + BuiltInRegistries.FLUID.getKey(theirs));
        return theirs;
    }

    // ================= B 真转化 =================

    private static BlockPos place(ServerLevel level) {
        BlockPos pos = level.getSharedSpawnPos().offset(10, 14, 10);
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
        level.setBlock(pos, ModBlocks.FLUID_CONVERTER.get().defaultBlockState(), 3);
        return pos;
    }

    private static void convert(ServerLevel level, Fluid ours, Fluid theirs) {
        LINES.add("== B 段：真转化（我们的柴油 → 他们的柴油，1:1）==");
        BlockPos pos = place(level);
        if (!(level.getBlockEntity(pos) instanceof FluidConverterBlockEntity be)) {
            check(false, "B0 流体转化器方块实体建出来了");
            return;
        }
        IFluidHandler handler = level.getCapability(Capabilities.FluidHandler.BLOCK, pos, null);
        check(handler != null, "B1 方块流体能力登记了（管道接得上）");
        IEnergyStorage energy = level.getCapability(Capabilities.EnergyStorage.BLOCK, pos, null);
        check(energy != null, "B2 方块能量能力登记了（能收电）");

        // 用"管道那条路"把我们的柴油灌进去（进的一律进输入罐）
        int accepted = handler == null ? 0 : handler.fill(new FluidStack(ours, 3000), IFluidHandler.FluidAction.EXECUTE);
        check(accepted == 3000 && be.getInputTank().getFluidAmount() == 3000,
                "B3 方块能力把 3000 mB 我们的柴油灌进了**输入罐**",
                "accepted=" + accepted + " 输入罐=" + be.getInputTank().getFluidAmount());
        // 样板：白盒放进输出罐（手倒那条路在 C 段单独验）
        be.getOutputTank().fill(new FluidStack(theirs, 1000), IFluidHandler.FluidAction.EXECUTE);
        if (energy != null) {
            energy.receiveEnergy(FluidConverterBlockEntity.MAX_ENERGY, false);
        }
        int e0 = be.getEnergy();
        int in0 = be.getInputTank().getFluidAmount();
        int out0 = be.getOutputTank().getFluidAmount();
        for (int t = 0; t < 20; t++) {
            FluidConverterBlockEntity.tick(level, pos, level.getBlockState(pos), be);
        }
        int in1 = be.getInputTank().getFluidAmount();
        int out1 = be.getOutputTank().getFluidAmount();
        check(in0 - in1 == 1000, "B4 20 tick 从输入罐搬走 1000 mB（20 × 50 mB/t）", "实际 " + (in0 - in1));
        check(out1 - out0 == 1000, "B5 输出罐正好多了 1000 mB（**1:1**）", "实际 " + (out1 - out0));
        check(in0 - in1 == out1 - out0, "B6 质量守恒：输入减少量 == 输出增加量");
        check(e0 - be.getEnergy() == 20 * FluidConverterBlockEntity.ENERGY_PER_TICK,
                "B7 电按 tick 计扣了 600 FE", "扣了 " + (e0 - be.getEnergy()));
        check(be.getOutputTank().getFluid().getFluid() == theirs,
                "B8 输出罐里**还是样板那一种**（确实换了流体种类，不是把我们的柴油搬过去）",
                BuiltInRegistries.FLUID.getKey(be.getOutputTank().getFluid().getFluid()).toString());
        check(be.getInputTank().getFluid().getFluid() == ours, "B9 输入罐里仍是我们的柴油");
        LINES.add("   调试：stateOf() = " + be.stateOf() + "（跑之前应是 RUNNING）");
    }

    // ================= C 手倒 =================

    private static void handPour(ServerLevel level) {
        LINES.add("== C 段：手倒（原版水桶 = 别人家的容器）==");
        BlockPos pos = place(level);
        if (!(level.getBlockEntity(pos) instanceof FluidConverterBlockEntity be)) {
            return;
        }
        FluidConverterBlockEntity.Pour pour =
                be.pourFrom(new ItemStack(Items.WATER_BUCKET), true, FluidConverterBlockEntity.POUR_PER_CLICK);
        check(pour.moved() == 1000 && be.getOutputTank().getFluidAmount() == 1000
                        && be.getOutputTank().getFluid().getFluid() == Fluids.WATER,
                "C1 水桶倒进输出罐（= 设样板）拿到 1000 mB 水",
                "moved=" + pour.moved() + " 输出罐=" + be.getOutputTank().getFluidAmount()
                        + " " + BuiltInRegistries.FLUID.getKey(be.getOutputTank().getFluid().getFluid()));
        check(pour.container().is(Items.BUCKET),
                "C2 倒完手里那件变成**空桶**（getContainer 写回）", pour.container().toString());
        FluidConverterBlockEntity.Pour bad =
                be.pourFrom(new ItemStack(Items.DIAMOND), true, FluidConverterBlockEntity.POUR_PER_CLICK);
        check(bad.moved() == 0 && bad.container().is(Items.DIAMOND),
                "C3 负对照：钻石倒不进去（容器原样还回来）");
    }

    // ================= D 能力语义 =================

    private static void capabilities(ServerLevel level, Fluid ours, Fluid theirs) {
        LINES.add("== D 段：管道能力语义 ==");
        BlockPos pos = place(level);
        if (!(level.getBlockEntity(pos) instanceof FluidConverterBlockEntity be)) {
            return;
        }
        IFluidHandler handler = level.getCapability(Capabilities.FluidHandler.BLOCK, pos, null);
        if (handler == null) {
            check(false, "D0 方块流体能力不在");
            return;
        }
        handler.fill(new FluidStack(ours, 500), IFluidHandler.FluidAction.EXECUTE);
        be.getOutputTank().fill(new FluidStack(theirs, 700), IFluidHandler.FluidAction.EXECUTE);
        check(be.getInputTank().getFluidAmount() == 500 && be.getOutputTank().getFluidAmount() == 700,
                "D1 灌进去的进输入罐、抽出来的从输出罐出（两边各自独立）",
                "输入=" + be.getInputTank().getFluidAmount() + " 输出=" + be.getOutputTank().getFluidAmount());
        FluidStack drained = handler.drain(200, IFluidHandler.FluidAction.EXECUTE);
        check(drained.getAmount() == 200 && drained.getFluid() == theirs
                        && be.getInputTank().getFluidAmount() == 500,
                "D2 drain 只动输出罐（拿到的是样板那种流体，输入罐一分不少）",
                drained.getAmount() + " " + BuiltInRegistries.FLUID.getKey(drained.getFluid()));
    }
}
