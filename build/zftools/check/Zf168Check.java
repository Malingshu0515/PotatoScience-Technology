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
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;

/**
 * ZF168 临时探针（0.13：修「转换器的输出储罐改不了」）。
 *
 * <p>用户实测报「转换器的输出储罐好像改不了」。病根：{@code FluidTank} 对**异种流体一律拒收**，
 * 而原来只有"容器 → 机器"一条路 ⇒ 样板一旦定下就再也换不掉。本轮加的就是反方向那条
 * {@code fillContainerFrom}（手拿空容器右键 = 从罐装进容器）。</p>
 *
 * <p>探针验的是**真服务端**上的完整换样板流程（用有桶的两种流体：水与岩浆，桶一定是原版的，
 * 免得踩"这个 mod 没给桶"的坑）：</p>
 * <ol>
 *   <li><b>A</b> 首次设样板：水桶 ⇒ 输出罐 1000 mB 水；</li>
 *   <li><b>B</b> 想直接换成岩浆 ⇒ <b>被拒</b>（输出罐一滴不动），而且 {@code targetBlocked} 为真
 *       ⇒ 机器会明说"先拿空容器把样板装走"；</li>
 *   <li><b>C</b> 空桶右键 ⇒ 从输出罐装走 1000 mB（输出罐空、手里变水桶）；</li>
 *   <li><b>D</b> 罐空了再倒岩浆 ⇒ <b>成功</b>（这就是"改得了了"）；</li>
 *   <li><b>E</b> 负对照：空罐装不出来、钻石装不出来、输入罐（我们的柴油）一分不动。</li>
 * </ol>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class Zf168Check {

    private static final String TAG = "[A168] ";
    private static final Path REPORT = Path.of("E:\\PotatoST\\build\\zftools\\_zf168_probe_utf8.txt");

    private static final List<String> LINES = new ArrayList<>();
    private static int passed = 0;
    private static int failed = 0;

    private Zf168Check() {
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

    private static void run(ServerLevel level) {
        BlockPos pos = level.getSharedSpawnPos().offset(12, 14, 12);
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
        level.setBlock(pos, ModBlocks.FLUID_CONVERTER.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(pos) instanceof FluidConverterBlockEntity be)) {
            check(false, "A0 流体转化器方块实体建出来了", "");
            return;
        }
        Fluid ours = BuiltInRegistries.FLUID.get(ResourceLocation.parse("potato_s_t:diesel"));
        be.getInputTank().fill(new FluidStack(ours, 2000), IFluidHandler.FluidAction.EXECUTE);

        LINES.add("== A 段：首次设样板（输出罐）==");
        FluidConverterBlockEntity.Pour a =
                be.pourFrom(new ItemStack(Items.WATER_BUCKET), true, FluidConverterBlockEntity.POUR_PER_CLICK);
        check(a.moved() == 1000 && be.getOutputTank().getFluid().getFluid() == Fluids.WATER,
                "A1 水桶倒进输出罐 1000 mB（样板 = 水）",
                "moved=" + a.moved() + " 罐=" + be.getOutputTank().getFluidAmount());

        LINES.add("== B 段：直接换样板应当**被拒**并给出提示 ==");
        ItemStack lavaBucket = new ItemStack(Items.LAVA_BUCKET);
        FluidConverterBlockEntity.Pour b =
                be.pourFrom(lavaBucket, true, FluidConverterBlockEntity.POUR_PER_CLICK);
        check(b.moved() == 0 && be.getOutputTank().getFluidAmount() == 1000
                        && be.getOutputTank().getFluid().getFluid() == Fluids.WATER,
                "B1 岩浆倒不进已有的水样板（异种流体一律拒收）—— 这就是用户遇到的那堵墙",
                "moved=" + b.moved() + " 罐=" + be.getOutputTank().getFluidAmount());
        check(be.targetBlocked(lavaBucket, true),
                "B2 targetBlocked() 为真 ⇒ 机器会明说「先拿空容器右键把样板装走」（本轮新加的那句话）",
                "heldFluid=" + FluidConverterBlockEntity.heldFluid(lavaBucket)
                        + " 桶能力=" + (lavaBucket.copyWithCount(1).getCapability(
                                net.neoforged.neoforge.capabilities.Capabilities.FluidHandler.ITEM) != null)
                        + " 罐=" + BuiltInRegistries.FLUID.getKey(be.getOutputTank().getFluid().getFluid()));
        check(!be.targetBlocked(new ItemStack(Items.DIAMOND), true),
                "B3 负对照：手里不是流体容器时不给那句提示");

        LINES.add("== C 段：空容器右键 = 从输出罐装走（本轮新加的路径）==");
        FluidConverterBlockEntity.Pour c =
                be.fillContainerFrom(new ItemStack(Items.BUCKET), true,
                        FluidConverterBlockEntity.POUR_PER_CLICK);
        check(c.moved() == 1000 && be.getOutputTank().getFluidAmount() == 0,
                "C1 空桶从输出罐装走 1000 mB（罐空了）",
                "moved=" + c.moved() + " 罐=" + be.getOutputTank().getFluidAmount());
        check(c.container().is(Items.WATER_BUCKET),
                "C2 手里那件变成**满桶**（水桶，内容物正确）", c.container().toString());
        check(be.getInputTank().getFluidAmount() == 2000,
                "C3 输入罐（我们的柴油）一分没动", "输入=" + be.getInputTank().getFluidAmount());

        LINES.add("== D 段：罐空了 ⇒ 样板换得掉了 ==");
        FluidConverterBlockEntity.Pour d =
                be.pourFrom(lavaBucket, true, FluidConverterBlockEntity.POUR_PER_CLICK);
        check(d.moved() == 1000 && be.getOutputTank().getFluid().getFluid() == Fluids.LAVA,
                "D1 现在岩浆倒得进去（样板成功换成岩浆）—— 用户的诉求达成",
                "moved=" + d.moved() + " 罐=" + BuiltInRegistries.FLUID.getKey(be.getOutputTank().getFluid().getFluid()).toString());

        LINES.add("== E 段：负对照与守恒 ==");
        FluidConverterBlockEntity.Pour e1 =
                be.fillContainerFrom(new ItemStack(Items.DIAMOND), true,
                        FluidConverterBlockEntity.POUR_PER_CLICK);
        check(e1.moved() == 0 && e1.container().is(Items.DIAMOND), "E1 钻石装不出流体（原样还回来）");
        int outBefore = be.getOutputTank().getFluidAmount();
        FluidConverterBlockEntity.Pour e2 =
                be.fillContainerFrom(new ItemStack(Items.BUCKET), true,
                        FluidConverterBlockEntity.POUR_PER_CLICK);
        check(e2.moved() == 1000 && e2.container().is(Items.LAVA_BUCKET)
                        && outBefore - be.getOutputTank().getFluidAmount() == 1000,
                "E2 岩浆也能装走（满桶），且**罐减少量 == 桶里拿到的量**（一滴不凭空消失/多出）",
                "moved=" + e2.moved() + " 罐减少=" + (outBefore - be.getOutputTank().getFluidAmount()));
        FluidConverterBlockEntity.Pour e3 =
                be.fillContainerFrom(new ItemStack(Items.BUCKET), true,
                        FluidConverterBlockEntity.POUR_PER_CLICK);
        check(e3.moved() == 0, "E3 空罐装不出东西（0 mB，不产生假桶）");
        FluidConverterBlockEntity.Pour e4 =
                be.pourFrom(new ItemStack(Items.WATER_BUCKET), false,
                        FluidConverterBlockEntity.POUR_PER_CLICK);
        check(e4.moved() == 0 && be.getInputTank().getFluidAmount() == 2000,
                "E4 负对照：往**输入罐**倒水也进不去（罐里已经是我们的柴油），一滴不动");
    }
}
