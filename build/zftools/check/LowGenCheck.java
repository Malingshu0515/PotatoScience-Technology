package com.potatost.mod;

import java.lang.reflect.Method;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF38 临时文件，验证完必须删）</b>：验低级发电机的整条数值链。
 *
 * <p>为什么需要它：这台机器的每个数字都是"看起来对就行"的那种错法 ——
 * 45 秒写成 45 tick、100 FE/t 写成 10、缓冲满了把燃料白烧掉、红石忘了拦……
 * <b>读代码全都看不出来</b>，只有真的跑 900 tick 数能量才作数。</p>
 *
 * <p>做法：把方块真的放进 {@code ServerLevel}，然后**手动**调 {@code tick} 驱动它，
 * 这样既走的是真逻辑（含红石判断、端子推送），又不必等服务器真的 tick 900 次。</p>
 *
 * <p><b>用法</b>：临时放进 {@code com.potatost.mod}、在 {@code PotatoST} 构造器里
 * {@code LowGenCheck.register()}，然后 {@code gradlew runServer}；
 * 日志出现 {@code [LOWGEN]} 若干行后自动关服。<b>验证完连同注册行一起删掉。</b></p>
 */
public final class LowGenCheck {

    private static final String TAG = "[LOWGEN] ";
    private static boolean registered;

    private LowGenCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(LowGenCheck.class);
            System.out.println(TAG + "诊断钩子已注册（game 总线）");
        } catch (Throwable t) {
            System.out.println(TAG + "注册失败（不影响正式功能）：" + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        int failed = 0;
        try {
            failed = run(event);
        } catch (Throwable t) {
            System.out.println(TAG + "验算抛异常：" + t);
            t.printStackTrace();
            failed = 1;
        } finally {
            System.out.println(TAG + "结论：" + (failed == 0 ? "数值链全部成立" : "**有 " + failed + " 项不符**"));
            System.out.println(TAG + "诊断结束，请求关服");
            event.getServer().halt(false);
        }
    }

    // 高空、区块已加载、测完还原成空气 ⇒ 不污染任何存档
    private static final BlockPos POS = new BlockPos(0, 250, 0);

    /**
     * 期望值**照用户原话硬写**，绝不从被测常量里读。
     *
     * <p><b>为什么：这是注入 bug 试出来的。</b>第一版探针把期望写成
     * {@code LowGeneratorBlockEntity.BURN_TICKS * LowGeneratorBlockEntity.ENERGY_PER_TICK}，
     * 于是把 {@code BURN_TICKS} 从 {@code 45 * 20} 改成 {@code 45}（"45 秒写成 45 tick"这个经典 bug）之后，
     * <b>29 项断言依然全过、一项都没抓到</b> —— 因为两边一起变了，断言成了同义反复。
     * 探针里出现被测常量，等于没有探针。</p>
     */
    private static final int SPEC_BURN_SECONDS = 45;
    private static final int SPEC_FE_PER_TICK = 100;
    private static final int SPEC_MAX_ENERGY = 1000;
    private static final int SPEC_BURN_TICKS = SPEC_BURN_SECONDS * 20;

    private static int run(ServerStartedEvent event) {
        int failed = 0;
        ServerLevel level = event.getServer().overworld();
        HolderLookup.Provider regs = event.getServer().registryAccess();

        ResourceLocation id = ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "low_generator");
        BlockState state = ModBlocks.LOW_GENERATOR.get().defaultBlockState();

        // ⓪ 先核对常量本身等于用户给的那三个数（这一条才是真正防"45 写成 45 tick"的）
        failed += check("BURN_TICKS = 45 秒 × 20 = " + SPEC_BURN_TICKS + "（实际 "
                + LowGeneratorBlockEntity.BURN_TICKS + "）",
                LowGeneratorBlockEntity.BURN_TICKS == SPEC_BURN_TICKS);
        failed += check("ENERGY_PER_TICK = " + SPEC_FE_PER_TICK + "（实际 "
                + LowGeneratorBlockEntity.ENERGY_PER_TICK + "）",
                LowGeneratorBlockEntity.ENERGY_PER_TICK == SPEC_FE_PER_TICK);
        failed += check("MAX_ENERGY = " + SPEC_MAX_ENERGY + "（实际 "
                + LowGeneratorBlockEntity.MAX_ENERGY + "）",
                LowGeneratorBlockEntity.MAX_ENERGY == SPEC_MAX_ENERGY);

        // ① 注册
        failed += check("BLOCK 注册表含 " + id, BuiltInRegistries.BLOCK.containsKey(id));
        failed += check("ITEM 注册表含 " + id, BuiltInRegistries.ITEM.containsKey(id));
        failed += check("MENU 注册表含 potato_s_t:low_generator",
                BuiltInRegistries.MENU.containsKey(id));

        // ② 两张原版标签（漏了 = 挖了什么都不掉）
        failed += check("在 #minecraft:mineable/pickaxe 里", state.is(BlockTags.MINEABLE_WITH_PICKAXE));
        failed += check("在 #minecraft:needs_stone_tool 里（requireCorrectToolForDrops）",
                state.is(BlockTags.NEEDS_STONE_TOOL));

        // ③ 双端 ticker（客户端拿不到 ⇒ 循环音效永远不响，§4.26）
        BlockEntityTicker<?> ticker = null;
        String tickerErr = "";
        try {
            ticker = ((net.minecraft.world.level.block.EntityBlock) ModBlocks.LOW_GENERATOR.get())
                    .getTicker((net.minecraft.world.level.Level) null, state, ModBlocks.LOW_GENERATOR_BE.get());
        } catch (Throwable t) {
            tickerErr = "（抛 " + t.getClass().getSimpleName() + " ⇒ level 参数仍在被解引用）";
        }
        failed += check("getTicker(null, ...) 返回非 null ⇒ 客户端也会拿到 ticker" + tickerErr, ticker != null);

        // ④ 把方块真的放进世界
        level.setBlock(POS, state, 3);
        if (!(level.getBlockEntity(POS) instanceof LowGeneratorBlockEntity gen)) {
            failed += check("方块实体已创建", false);
            level.setBlock(POS, Blocks.AIR.defaultBlockState(), 3);
            return failed;
        }
        failed += check("方块实体已创建", true);

        // ⑤ 燃料门：煤炭 / 木炭可放，别的不行
        failed += check("煤炭可放", gen.getInventory().isItemValid(0, new ItemStack(Items.COAL)));
        failed += check("木炭可放", gen.getInventory().isItemValid(0, new ItemStack(Items.CHARCOAL)));
        failed += check("红石不可放（反向断言）",
                !gen.getInventory().isItemValid(0, new ItemStack(Items.REDSTONE)));
        failed += check("熔炉不可放（反向断言）",
                !gen.getInventory().isItemValid(0, new ItemStack(Items.FURNACE)));

        // ---- 试验 A：边烧边抽 ⇒ 一块煤应当恰好给出 900 tick × 100 FE = 90000 FE ----
        gen.getInventory().setStackInSlot(0, new ItemStack(Items.COAL, 1));
        long total = 0;
        int ticksRun = 0;
        for (int i = 0; i < SPEC_BURN_TICKS + 50; i++) {
            LowGeneratorBlockEntity.tick(level, POS, state, gen);
            ticksRun++;
            int got = gen.getEnergyStorage().extractEnergy(Integer.MAX_VALUE, false);
            total += got;
            if (gen.getContainerData().get(LowGeneratorBlockEntity.DATA_BURN) <= 0 && got == 0) {
                break;
            }
        }
        long expected = (long) SPEC_BURN_TICKS * SPEC_FE_PER_TICK;
        System.out.println(TAG + "  试验A：跑了 " + ticksRun + " tick，抽出 " + total + " FE（期望 " + expected + "）");
        failed += check("一块煤总量 = " + SPEC_BURN_TICKS + " tick × " + SPEC_FE_PER_TICK
                + " FE = " + expected + " FE", total == expected);
        failed += check("烧完输入槽空了", gen.getInventory().getStackInSlot(0).isEmpty());
        failed += check("剩余燃烧时间归零",
                gen.getContainerData().get(LowGeneratorBlockEntity.DATA_BURN) == 0);

        // ---- 试验 B：不抽 ⇒ 缓冲满了应当**暂停**（burnTime 不再减少），而不是把燃料白烧掉 ----
        gen.getInventory().setStackInSlot(0, new ItemStack(Items.COAL, 1));
        for (int i = 0; i < 20; i++) {
            LowGeneratorBlockEntity.tick(level, POS, state, gen);
        }
        int storedB = gen.getEnergyStored();
        int burnB = gen.getContainerData().get(LowGeneratorBlockEntity.DATA_BURN);
        int expectBurnB = SPEC_BURN_TICKS - SPEC_MAX_ENERGY / SPEC_FE_PER_TICK;
        System.out.println(TAG + "  试验B：20 tick 后 存量=" + storedB + " 剩余燃烧=" + burnB
                + "（期望 " + SPEC_MAX_ENERGY + " / " + expectBurnB + "）");
        failed += check("不抽电时存量停在 " + SPEC_MAX_ENERGY, storedB == SPEC_MAX_ENERGY);
        failed += check("缓冲满后**暂停燃烧**（burnTime 停在 " + expectBurnB + "）", burnB == expectBurnB);
        failed += check("缓冲满后不再增加（< " + SPEC_MAX_ENERGY + " 就是漏了上限）",
                storedB <= SPEC_MAX_ENERGY);

        // 反向：抽走一点应当**恢复**燃烧
        gen.getEnergyStorage().extractEnergy(SPEC_FE_PER_TICK, false);
        LowGeneratorBlockEntity.tick(level, POS, state, gen);
        int burnResume = gen.getContainerData().get(LowGeneratorBlockEntity.DATA_BURN);
        failed += check("腾出空间后恢复燃烧（" + burnB + " → " + burnResume + "）", burnResume == burnB - 1);

        // 顺带把"缓冲满 = 不算在发电"这条**有意的语义**钉住：
        // isRunning() 是"这一 tick 真的产了电"，所以缓冲满被暂停时它是 false
        // ⇒ 客户端的循环音效会停。这正是我选的行为（听得出来"没在出力"），写成断言免得以后被当 bug 改掉。
        // ⚠ 第二版这里又写错一次：抽空之后**只 tick 一次**就断言"又满了"，可 1000/100 = **10 tick** 才填满，
        //    第 2 tick 当然还在发电。断言要照着容量算，别凭印象写。
        gen.getEnergyStorage().extractEnergy(Integer.MAX_VALUE, false);
        int fillTicks = SPEC_MAX_ENERGY / SPEC_FE_PER_TICK;
        for (int i = 0; i < fillTicks; i++) {
            LowGeneratorBlockEntity.tick(level, POS, state, gen);
        }
        failed += check("填满的这 " + fillTicks + " tick 里 isRunning() 为真", gen.isRunning());
        LowGeneratorBlockEntity.tick(level, POS, state, gen);      // 再一 tick 已无空间 → 暂停
        failed += check("填满后下一 tick isRunning() 转假（有意的语义：音效跟着停）", !gen.isRunning());

        // ---- 试验 C：红石信号 = 停机 ----
        level.setBlock(POS.east(), Blocks.REDSTONE_BLOCK.defaultBlockState(), 3);
        int burnC = gen.getContainerData().get(LowGeneratorBlockEntity.DATA_BURN);
        int energyC = gen.getEnergyStored();
        for (int i = 0; i < 5; i++) {
            LowGeneratorBlockEntity.tick(level, POS, state, gen);
        }
        failed += check("红石信号下燃烧时间不变（" + burnC + " → "
                + gen.getContainerData().get(LowGeneratorBlockEntity.DATA_BURN) + "）",
                gen.getContainerData().get(LowGeneratorBlockEntity.DATA_BURN) == burnC);
        failed += check("红石信号下不再发电（" + energyC + " → " + gen.getEnergyStored() + "）",
                gen.getEnergyStored() == energyC);
        failed += check("红石信号下 isRunning() 为假（反向断言）", !gen.isRunning());
        level.setBlock(POS.east(), Blocks.AIR.defaultBlockState(), 3);

        // ---- 试验 D：同步包里带 running ----
        // ⚠ 第一版这里写错了（2 项 [FAIL] 全是探针自己的锅，不是机器的）：
        //    我直接往槽里塞木炭再 tick 一次就断言 isRunning() 为真，可此时**缓冲还是满的**
        //    （前一步刚抽走 100 又被这一 tick 填回去了）⇒ 正当地处于"暂停"状态。
        //    修法：先用 loadAdditional(空 tag) 把整台机器**归零**，做成一个自足的场景。
        gen.loadAdditional(new CompoundTag(), regs);
        gen.getInventory().setStackInSlot(0, new ItemStack(Items.CHARCOAL, 1));
        LowGeneratorBlockEntity.tick(level, POS, state, gen);
        failed += check("发电时 isRunning() 为真", gen.isRunning());
        failed += check("烧了一 tick 后存量 = " + SPEC_FE_PER_TICK,
                gen.getEnergyStored() == SPEC_FE_PER_TICK);
        CompoundTag out = gen.getUpdateTag(regs);
        failed += check("getUpdateTag 带 running=true 与 burnTime=" + (SPEC_BURN_TICKS - 1),
                out.getBoolean("running")
                        && out.getInt("burnTime") == SPEC_BURN_TICKS - 1);
        failed += check("getUpdateTag / getUpdatePacket 都是本类覆写",
                declares("getUpdateTag") && declares("getUpdatePacket"));

        // ---- 试验 E：掉落表掉自己 ----
        var drops = Block.getDrops(state, level, POS, null, null,
                new ItemStack(Items.DIAMOND_PICKAXE));
        failed += check("掉落表掉 1 个自己（实际 " + drops.size() + " 项）",
                drops.size() == 1 && drops.get(0).getItem() == ModBlocks.LOW_GENERATOR_ITEM.get());

        // ---- 收尾：还原世界 ----
        level.setBlock(POS, Blocks.AIR.defaultBlockState(), 3);
        failed += check("测完已还原成空气", level.getBlockState(POS).isAir());
        return failed;
    }

    private static boolean declares(String method) {
        try {
            Method m = LowGeneratorBlockEntity.class.getMethod(method, HolderLookup.Provider.class);
            return m.getDeclaringClass() == LowGeneratorBlockEntity.class;
        } catch (NoSuchMethodException e) {
            try {
                Method m = LowGeneratorBlockEntity.class.getMethod(method);
                return m.getDeclaringClass() == LowGeneratorBlockEntity.class;
            } catch (NoSuchMethodException e2) {
                return false;
            }
        }
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
