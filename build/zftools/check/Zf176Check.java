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
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;

/**
 * ZF176 临时探针（0.13：让**样板可以只用泵/管道就给上**）。
 *
 * <p>用户实测反馈：「**还是不可以 要不然试试样本只能通过泵输入呢**」。</p>
 *
 * <p>本轮把对外句柄按**接入面**分了工（见 {@code FluidConverterBlockEntity.handlerFor}）：</p>
 * <ul>
 *   <li><b>上 / 下面</b>：只碰<b>输出罐（样板）</b>；</li>
 *   <li><b>四个侧面</b>：<code>fill</code> 进<b>输入罐（原料）</b>，<code>drain</code> 从<b>输出罐</b>出。</li>
 * </ul>
 *
 * <p>探针在真服务端上按面查询能力并灌/抽，验的就是"泵能不能把样板灌上"。</p>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class Zf176Check {

    private static final String TAG = "[A176] ";
    private static final Path REPORT = Path.of("E:\\PotatoST\\build\\zftools\\_zf176_probe_utf8.txt");

    private static final List<String> LINES = new ArrayList<>();
    private static int passed = 0;
    private static int failed = 0;

    private Zf176Check() {
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
        BlockPos pos = level.getSharedSpawnPos().offset(16, 14, 16);
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
        level.setBlock(pos, ModBlocks.FLUID_CONVERTER.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(pos) instanceof FluidConverterBlockEntity be)) {
            check(false, "A0 方块实体建出来了", "");
            return;
        }
        Fluid ours = BuiltInRegistries.FLUID.get(ResourceLocation.parse("potato_s_t:diesel"));

        LINES.add("== A 段：**上/下面 = 样板罐**（用户要的：泵给样板）==");
        IFluidHandler up = level.getCapability(Capabilities.FluidHandler.BLOCK, pos, Direction.UP);
        IFluidHandler down = level.getCapability(Capabilities.FluidHandler.BLOCK, pos, Direction.DOWN);
        check(up != null && down != null, "A1 上面/下面的能力都在");
        if (up == null) {
            return;
        }
        check(up.getTanks() == 1, "A2 上/下面那句柄只有 1 个罐（就是样板罐）", "tanks=" + up.getTanks());
        int a = up.fill(new FluidStack(Fluids.WATER, 1000), IFluidHandler.FluidAction.EXECUTE);
        check(a == 1000 && be.getOutputTank().getFluid().getFluid() == Fluids.WATER
                        && be.getOutputTank().getFluidAmount() == 1000,
                "A3 **从上面泵进来的水直接进了输出罐 = 样板定上了**（两个罐原本都是空的）",
                "灌进=" + a + " 输出罐=" + be.getOutputTank().getFluidAmount());
        check(be.getInputTank().isEmpty(), "A4 输入罐没被这一笔碰到（还是空的）");
        int a2 = up.fill(new FluidStack(ours, 500), IFluidHandler.FluidAction.EXECUTE);
        check(a2 == 0 && be.getOutputTank().getFluid().getFluid() == Fluids.WATER,
                "A5 负对照：样板已定时，从上面灌**别的**流体进不去（0 mB，样板不被顶掉）", "灌进=" + a2);

        LINES.add("== B 段：四个侧面 = 原料罐（喂料）==");
        IFluidHandler north = level.getCapability(Capabilities.FluidHandler.BLOCK, pos, Direction.NORTH);
        check(north != null && north.getTanks() == 2, "B1 侧面句柄有 2 个罐（输入在前、输出在后）");
        if (north == null) {
            return;
        }
        int b = north.fill(new FluidStack(ours, 2000), IFluidHandler.FluidAction.EXECUTE);
        check(b == 2000 && be.getInputTank().getFluidAmount() == 2000
                        && be.getOutputTank().getFluid().getFluid() == Fluids.WATER,
                "B2 从侧面泵进来的我们的柴油进了**输入罐**，样板没被动",
                "灌进=" + b + " 输入罐=" + be.getInputTank().getFluidAmount());

        LINES.add("== C 段：抽出来的永远是产物（输出罐）==");
        FluidStack d1 = north.drain(300, IFluidHandler.FluidAction.EXECUTE);
        check(d1.getAmount() == 300 && d1.getFluid() == Fluids.WATER
                        && be.getInputTank().getFluidAmount() == 2000,
                "C1 从侧面抽：抽到的是**输出罐里的产物（水）**，输入罐一分不少",
                d1.getAmount() + " " + BuiltInRegistries.FLUID.getKey(d1.getFluid()));
        FluidStack d2 = up.drain(200, IFluidHandler.FluidAction.EXECUTE);
        check(d2.getAmount() == 200 && d2.getFluid() == Fluids.WATER,
                "C2 从上面抽：同样是输出罐（700 − 300 − 200 = 500 应剩）",
                "剩=" + be.getOutputTank().getFluidAmount());
        check(be.getOutputTank().getFluidAmount() == 500, "C3 输出罐剩 500 mB（账对得上）",
                "剩=" + be.getOutputTank().getFluidAmount());
    }
}
