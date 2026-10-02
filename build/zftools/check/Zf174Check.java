package com.potatost.mod;

import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import com.mojang.authlib.GameProfile;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;

/**
 * ZF174 临时探针（0.13：修「shift+右键会把流体倒出来」）。
 *
 * <p>用户实测原话：「**shift+右键会把流体倒出来 而不是倒进版样**」（截图里手里是一铁桶汽油，
 * 屏幕角落还写着「铁桶: 倒空」）。病根：机器这一下**没吃下交互**却返回了
 * {@code PASS_TO_DEFAULT_BLOCK_INTERACTION} ⇒ 原版接着跑 {@code BucketItem#useOn}，
 * 把桶里的流体**倒进世界**（凭空丢流体）。</p>
 *
 * <p>探针在**真服务端**上直接调方块的 {@code useItemOn}（用 NeoForge 的 FakePlayer + 真
 * {@link BlockHitResult}），验的就是"这次交互到底有没有被吃掉"：</p>
 * <ol>
 *   <li><b>A</b> 满桶岩浆对着"水样板"潜行右键 ⇒ 结果**必须 consumesAction**（原版没机会倒世界）、
 *       输出罐与水样板**一分不动**、手里的岩浆桶**还在**；</li>
 *   <li><b>B</b> 负对照：手里是**钻石**（不是流体容器）⇒ 必须**不**吃下（PASS），别挡原版；</li>
 *   <li><b>C</b> 空桶右键 ⇒ 吃下 + 输出罐被装走 1000 mB + 手里变满桶；</li>
 *   <li><b>D</b> 不潜行 + 满桶汽油对着"输入罐已有我们的柴油" ⇒ 同样被吃下、输入罐不动。</li>
 * </ol>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class Zf174Check {

    private static final String TAG = "[A174] ";
    private static final Path REPORT = Path.of("E:\\PotatoST\\build\\zftools\\_zf174_probe_utf8.txt");

    private static final List<String> LINES = new ArrayList<>();
    private static int passed = 0;
    private static int failed = 0;

    private Zf174Check() {
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
                if (e.getClassName().startsWith("com.potatost") || e.getClassName().contains("FakePlayer")) {
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
        BlockPos pos = level.getSharedSpawnPos().offset(14, 14, 14);
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
        level.setBlock(pos, ModBlocks.FLUID_CONVERTER.get().defaultBlockState(), 3);
        BlockState state = level.getBlockState(pos);
        if (!(level.getBlockEntity(pos) instanceof FluidConverterBlockEntity be)) {
            check(false, "A0 流体转化器方块实体建出来了", "");
            return;
        }
        Fluid ours = BuiltInRegistries.FLUID.get(ResourceLocation.parse("potato_s_t:diesel"));
        Player player = FakePlayerFactory.get(level, new GameProfile(UUID.randomUUID(), "zf172probe"));
        BlockHitResult hit = new BlockHitResult(new Vec3(pos.getX() + 0.5, pos.getY() + 1.0,
                pos.getZ() + 0.5), net.minecraft.core.Direction.UP, pos, false);

        // 样板 = 水；输入罐 = 我们的柴油（两边都"占着"，好触发那条"倒不进去"的路径）
        be.getOutputTank().fill(new FluidStack(Fluids.WATER, 1000), IFluidHandler.FluidAction.EXECUTE);
        be.getInputTank().fill(new FluidStack(ours, 2000), IFluidHandler.FluidAction.EXECUTE);

        LINES.add("== A 段：倒不进去时**必须吃下交互**（用户那条 bug）==");
        player.setShiftKeyDown(true);
        ItemStack lavaBucket = new ItemStack(Items.LAVA_BUCKET);
        ItemInteractionResult a = state
                .useItemOn(lavaBucket, level, player, InteractionHand.MAIN_HAND, hit);
        check(a.consumesAction(),
                "A1 满桶岩浆潜行右键 ⇒ 交互被**吃下**（原版再没机会把岩浆倒进世界）",
                "result=" + a);
        check(be.getOutputTank().getFluid().getFluid() == Fluids.WATER
                        && be.getOutputTank().getFluidAmount() == 1000,
                "A2 水样板一分不动（没被岩浆顶掉）",
                "罐=" + be.getOutputTank().getFluidAmount());
        check(lavaBucket.is(Items.LAVA_BUCKET), "A3 手里的岩浆桶还在（流体没被倒掉）", lavaBucket.toString());
        check(be.getInputTank().getFluidAmount() == 2000, "A4 输入罐也没动");

        LINES.add("== B 段：负对照（不是流体容器就别多管闲事）==");
        ItemInteractionResult b = state
                .useItemOn(new ItemStack(Items.DIAMOND), level, player, InteractionHand.MAIN_HAND, hit);
        check(!b.consumesAction(), "B1 手里是钻石 ⇒ **不**吃下这次交互（原版该怎么用还怎么用）",
                "result=" + b);

        LINES.add("== C 段：空桶右键 = 从输出罐装走（ZF168 那条路，block 级复验）==");
        ItemStack emptyBucket = new ItemStack(Items.BUCKET);
        int outBefore = be.getOutputTank().getFluidAmount();
        ItemInteractionResult c = state
                .useItemOn(emptyBucket, level, player, InteractionHand.MAIN_HAND, hit);
        check(c.consumesAction() && be.getInputTank().getFluidAmount() == 2000,
                "C1 被吃下（shift ⇒ 输出罐），输入罐不动", "result=" + c);
        int outAfter = be.getOutputTank().getFluidAmount();
        check(outBefore - outAfter == 1000 && outAfter == 0,
                "C2 输出罐被装走 1000 mB（腾空样板）", "变化=" + (outBefore - outAfter));
        // 空桶那件物品是"手里那件"的副本，机器改的是玩家的手持物 —— 这里用玩家手上那件来核
        ItemStack inHand = player.getItemInHand(InteractionHand.MAIN_HAND);
        check(inHand.is(Items.WATER_BUCKET),
                "C3 玩家手里那件变成**水桶**（装到的正是样板那一种）", inHand.toString());

        LINES.add("== D 段：不潜行 ⇒ 输入罐（喂料方向）同样被吃下 ==");
        player.setShiftKeyDown(false);
        ItemStack gasoline = new ItemStack(Items.LAVA_BUCKET);
        ItemInteractionResult d = state
                .useItemOn(gasoline, level, player, InteractionHand.MAIN_HAND, hit);
        check(d.consumesAction() && be.getInputTank().getFluidAmount() == 2000,
                "D1 不潜行 + 目标罐被别的流体占着 ⇒ 吃下且输入罐不动（诊断会说明原因）",
                "result=" + d);
    }
}
