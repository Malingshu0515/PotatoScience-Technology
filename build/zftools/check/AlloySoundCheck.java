package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

import com.potatost.mod.sound.ModSounds;

/**
 * ⚠⚠ <b>诊断工具（ZF64 临时文件，验证完必须删）</b>：验合金冶炼炉"运行中循环电机声"这条链路，
 * 外加进度箭头要用到的 {@code running} 同步。
 *
 * <p>为什么需要它（这些坏法<b>一个都不报错</b>，ZF36 给液压机验过一次同样的链路）：</p>
 * <ul>
 *   <li>音效没注册 / 注册名打错 ⇒ 游戏里静默无声；</li>
 *   <li>{@code getTicker} 在客户端 {@code return null} ⇒ 客户端根本没有 ticker，
 *       驱动循环音效的代码永远不执行（<b>注册、sounds.json、ogg 全对，就是没声音</b>）；</li>
 *   <li>{@code getUpdateTag} 没带上 {@code running} ⇒ 客户端永远看不到"在烧"，声音永远不响；</li>
 *   <li>{@code running} 的语义错（断电时还响 / 原料拿走了还响）⇒ 声音骗玩家。</li>
 * </ul>
 *
 * <p><b>期望值一律是字面量</b>（600 tick / 800 FE/t 来自用户的话），不从被测常量抄（§4.27）。</p>
 *
 * <p>⚠ <b>本探针验不了的东西</b>：真正"好不好听、响不响"要人在游戏里听；客户端那一句
 * {@code MachineRunningSound.update(...)} 在专用服务端跑不到（客户端类），只能靠文本级检查 + 人工试听。</p>
 */
public final class AlloySoundCheck {

    private static final String TAG = "[SND] ";
    private static final Direction FACING = Direction.SOUTH;
    private static final BlockPos C = new BlockPos(400, 260, 200);
    private static boolean registered;

    private AlloySoundCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(AlloySoundCheck.class);
            System.out.println(TAG + "hook registered");
        } catch (Throwable t) {
            System.out.println(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        int failed = 0;
        try {
            failed = run(event);
        } catch (Throwable t) {
            System.out.println(TAG + "exception: " + t);
            t.printStackTrace();
            failed++;
        } finally {
            System.out.println(TAG + "verdict: " + (failed == 0 ? "ALL OK" : "**" + failed + " FAILED**"));
            System.out.println(TAG + "done, halting server");
            event.getServer().halt(false);
        }
    }

    private static int run(ServerStartedEvent event) {
        int failed = 0;
        ServerLevel level = event.getServer().overworld();
        var registries = event.getServer().registryAccess();

        // ---------- ① 音效事件真的在注册表里，且就是代码引用的那一个 ----------
        System.out.println(TAG + "(1) sound event registration");
        ResourceLocation soundId = ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "alloy_smelter_running");
        failed += check("SOUND_EVENT registry contains " + soundId,
                BuiltInRegistries.SOUND_EVENT.containsKey(soundId));
        failed += check("ModSounds.ALLOY_SMELTER_RUNNING points at " + soundId,
                ModSounds.ALLOY_SMELTER_RUNNING.get().getLocation().equals(soundId));

        // ---------- ② 客户端也拿得到 ticker（ZF36 那个坑：客户端 return null ⇒ 永远没声音）----------
        System.out.println(TAG + "(2) both-sided ticker");
        BlockState state = ModBlocks.ALLOY_SMELTER.get().defaultBlockState();
        BlockEntityTicker<?> ticker = null;
        String tickerErr = "";
        try {
            ticker = ((EntityBlock) ModBlocks.ALLOY_SMELTER.get())
                    .getTicker((net.minecraft.world.level.Level) null, state, ModBlocks.ALLOY_SMELTER_BE.get());
        } catch (Throwable t) {
            tickerErr = " (threw " + t.getClass().getSimpleName() + ")";
        }
        failed += check("getTicker(null, ...) returns non-null => no client/server split" + tickerErr,
                ticker != null);

        // ---------- ③ 造一台真机器，量 running 标记 ----------
        System.out.println(TAG + "(3) running flag behaviour on a real machine");
        clear(level);
        for (int y = 0; y < AlloySmelterStructure.HEIGHT; y++) {
            buildLayer(level, y);
        }
        AlloySmelterBlock.tryAutoForm(level, C);
        if (!(level.getBlockEntity(C) instanceof AlloySmelterBlockEntity be)) {
            return failed + check("controller block entity exists", false);
        }
        failed += check("machine formed", be.isFormed());
        failed += check("idle machine is not 'running'", !be.isRunning());

        CompoundTag idleTag = be.getUpdateTag(registries);
        failed += check("getUpdateTag carries running=false while idle",
                idleTag.contains("running") && !idleTag.getBoolean("running"));

        int in = AlloySmelterBlockEntity.INPUT_FIRST;
        be.getInventory().setStackInSlot(in, new ItemStack(ModItems.ALUMINUM_INGOT.get(), 1));
        be.getInventory().setStackInSlot(in + 1, new ItemStack(ModItems.TITANIUM_INGOT.get(), 1));
        be.getInventory().setStackInSlot(in + 2, new ItemStack(ModItems.SILVER_INGOT.get(), 1));

        be.craftTick();
        failed += check("no energy: not 'running' (got " + be.isRunning() + ")", !be.isRunning());
        failed += check("no energy: progress stays 0 (got " + be.getProgress() + ")", be.getProgress() == 0);

        // 真实 ticker 入口走一遍（不是直接调 craftTick —— 要确认双端分支没把服务端也吞掉）
        fill(be, 40_000L);
        AlloySmelterBlockEntity.tick(level, C, level.getBlockState(C), be);
        failed += check("through the real ticker (server branch): 'running' is true", be.isRunning());
        failed += check("through the real ticker: progress is 1 (got " + be.getProgress() + ")",
                be.getProgress() == 1);

        CompoundTag busyTag = be.getUpdateTag(registries);
        failed += check("getUpdateTag carries running=true while crafting (this is all the client sees)",
                busyTag.contains("running") && busyTag.getBoolean("running"));

        // ---------- ④ 断电停住：声音要停，但进度绝不能清（29 秒的活不能白干）----------
        System.out.println(TAG + "(4) brownout: sound stops, progress holds");
        int guard = 0;
        while (be.getEnergyStored() >= 800 && guard++ < 2000) {
            be.craftTick();
        }
        int held = be.getProgress();
        failed += check("buffer drained after " + guard + " ticks (buffer now " + be.getEnergyStored() + ")",
                be.getEnergyStored() < 800);
        be.craftTick();
        failed += check("not enough energy: not 'running' (got " + be.isRunning() + ")", !be.isRunning());
        failed += check("not enough energy: progress holds at " + held + " (got " + be.getProgress() + ")",
                be.getProgress() == held);

        // ---------- ⑤ 原料拿走：声音停 + 进度归零 ----------
        System.out.println(TAG + "(5) ingredient removed: sound stops, progress resets");
        be.getInventory().setStackInSlot(in, ItemStack.EMPTY);
        be.craftTick();
        failed += check("ingredient removed: not 'running' (got " + be.isRunning() + ")", !be.isRunning());
        failed += check("ingredient removed: progress back to 0 (got " + be.getProgress() + ")",
                be.getProgress() == 0);

        // ---------- ⑥ 客户端重建：running 必须读得回来 ----------
        System.out.println(TAG + "(6) client-side rebuild from the update tag");
        AlloySmelterBlockEntity clientCopy = new AlloySmelterBlockEntity(C, state);
        clientCopy.loadAdditional(busyTag, registries);
        failed += check("rebuilt from a 'busy' tag => isRunning() true", clientCopy.isRunning());
        AlloySmelterBlockEntity idleCopy = new AlloySmelterBlockEntity(C, state);
        idleCopy.loadAdditional(idleTag, registries);
        failed += check("rebuilt from an 'idle' tag => isRunning() false (reverse assertion)",
                !idleCopy.isRunning());

        // ---------- ⑦ 箭头进度条的数据源：菜单要把 进度 / 满值 暴露出来 ----------
        System.out.println(TAG + "(7) numbers the progress arrow reads");
        failed += check("progress max = 600 ticks (30 s, user's number) (got "
                        + AlloySmelterBlockEntity.DURATION_TICKS + ")",
                AlloySmelterBlockEntity.DURATION_TICKS == 600);
        failed += check("per-tick draw is still 800 FE/t (got "
                        + AlloySmelterBlockEntity.ENERGY_PER_TICK + ")",
                AlloySmelterBlockEntity.ENERGY_PER_TICK == 800);
        failed += check("ContainerData still exposes progress at index 3 (got "
                        + AlloySmelterBlockEntity.DATA_PROGRESS + ")",
                AlloySmelterBlockEntity.DATA_PROGRESS == 3);
        failed += check("ContainerData slot count is 4 (got " + be.getContainerData().getCount() + ")",
                be.getContainerData().getCount() == 4);

        clear(level);
        return failed;
    }

    // ==================== 工具 ====================
    /** 往缓冲里塞电，返回真正收下的量（收电接口只进不出，探针只能靠"刚好够"控制余额）。 */
    private static long fill(AlloySmelterBlockEntity be, long amount) {
        var storage = be.getEnergyStorage();
        if (storage == null) {
            return 0;
        }
        long accepted = 0;
        while (accepted < amount) {
            int got = storage.receiveEnergy((int) Math.min(amount - accepted, 1_000_000L), false);
            if (got <= 0) {
                break;
            }
            accepted += got;
        }
        return accepted;
    }

    private static void buildLayer(ServerLevel level, int y) {
        for (int j = 0; j < AlloySmelterStructure.DEPTH; j++) {
            for (int i = 0; i < AlloySmelterStructure.WIDTH; i++) {
                AlloySmelterStructure.Kind kind = AlloySmelterStructure.kindAt(y, j, i);
                BlockState st = kind == AlloySmelterStructure.Kind.CONTROLLER
                        ? ModBlocks.ALLOY_SMELTER.get().defaultBlockState()
                                .setValue(AlloySmelterBlock.FACING, FACING)
                        : AlloySmelterStructure.blockFor(kind).defaultBlockState();
                level.setBlock(AlloySmelterStructure.offset(C, FACING, y, j, i), st, 3);
            }
        }
    }

    private static void clear(ServerLevel level) {
        level.setBlock(C, Blocks.AIR.defaultBlockState(), 3);
        for (BlockPos p : AlloySmelterStructure.positions(C, FACING)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
        }
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
