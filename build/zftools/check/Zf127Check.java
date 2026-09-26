package com.potatost.mod;

import java.util.List;
import java.util.Map;

import com.mojang.authlib.GameProfile;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.NonNullList;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.LongTag;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠️ <b>诊断工具（ZF127 的临时探针）</b>：<b>银线 / 银线轴</b>。
 *
 * <p>用户原话：「加一个银线轴 和铜线轴一致（先搞银线 配方什么的都一致只不过铜的换成银的）
 * 材质先不画 连接线缆还是一样的像素大小 只不过变成银白色的 传输速率 16134Fe/t」。</p>
 *
 * <p>要证的不是"常量改成了 16134"，而是<b>这一档线真的按 16134 在跑</b>：</p>
 * <ol>
 *   <li>物品与常量：两个物品注册了、银线轴耐久 32（与铜线轴一致）、16134 / 2048 / 2048 都在；</li>
 *   <li>两条配方在<b>真服务端</b>里能摆出来（拿游戏自己的 RecipeManager 匹配 + 产出数量），
 *       并带"少一块料 / 拿铜线冒充银线"的反向对照；</li>
 *   <li>连线走<b>真物品</b>（FakePlayer 拿银线轴右键两次）⇒ 两端记的速率都是 16134、耐久 −1；
 *       铜线轴连出来的那一对仍然是 2048；</li>
 *   <li><b>一 tick 真的传 16134</b>（满缓冲的 INPUT 端对空的 OUTPUT 端），
 *       而铜线那一对一 tick 传 1024 —— 与 ZF126 之前的行为<b>逐字一致</b>（回归证据）；</li>
 *   <li>上游补不满时按"差额一半"降档（8067）—— 这是规则本身，如实写出来；</li>
 *   <li>铜线那对再用银线轴连一次 ⇒ 就地升级成 16134（且拿铜线轴连不回去）；</li>
 *   <li>银线拆掉之后端子缓冲缩回 2048，且电量被夹到不超过上限；</li>
 *   <li><b>老存档的 NBT</b>（ListTag&lt;LongTag&gt; 那种）读进来连接还在、速率按铜线算、电量夹到 2048。</li>
 * </ol>
 *
 * <p>挂载方式：`PotatoST` 构造器末尾加一行 `Zf127Check.register();`，跑完用
 * {@code _zf127_unprobe.py} 摘掉（**先抄进 `build/zftools/check/` 再删**）。</p>
 */
public final class Zf127Check {

    private static final String TAG = "[A127] ";
    /** 银线：单线速率（用户给的数） */
    private static final int SILVER = 16_134;
    /** 铜线档（ZF126 时的全部） */
    private static final int COPPER = 2_048;
    /** 别踩 ZF125（384,260,176）/ ZF126（384,300,176）的现场 */
    private static final int FX = 400;
    private static final int FY = 300;
    private static final int FZ = 240;

    private static final StringBuilder REPORT = new StringBuilder();
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf127_probe_utf8.txt";

    private static boolean registered;
    private static int passed;
    private static int failed;

    private Zf127Check() {
    }

    private static void say(String line) {
        System.out.println(line);
        REPORT.append(line).append('\n');
    }

    private static void check(String name, boolean ok) {
        if (ok) {
            passed++;
        } else {
            failed++;
        }
        say(TAG + (ok ? "[OK]   " : "[FAIL] ") + name);
    }

    private static void flushReport() {
        try (java.io.OutputStreamWriter w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), java.nio.charset.StandardCharsets.UTF_8)) {
            w.write("ZF127 探针报告（银线 / 银线轴：单线 16134 FE/t）· UTF-8 · §4.50\n");
            w.write("生成时间：" + java.time.LocalDateTime.now() + "\n");
            w.write("判词：" + (failed == 0 ? "全绿" : failed + " 条 FAIL") + "（通过 " + passed + "）\n\n");
            w.write(REPORT.toString());
        } catch (Throwable t) {
            say(TAG + "report write failed: " + t);
        }
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf127Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        passed = 0;
        failed = 0;
        ServerLevel level = event.getServer().overworld();
        try {
            clear(level);
            run(level);
            clear(level);
        } catch (Throwable t) {
            failed++;
            say(TAG + "[FAIL] 探针自己抛异常：" + t);
            t.printStackTrace(System.out);
        }
        say(TAG + "done, halting server");
        flushReport();
        event.getServer().halt(false);
    }

    private static void run(ServerLevel level) {
        say(TAG + "① 物品与常量");
        check("SILVER_TRANSFER_RATE == 16134（用户给的数）",
                TerminalBlockEntity.SILVER_TRANSFER_RATE == SILVER);
        check("铜线两档没被顺手改掉（TRANSFER_RATE == 2048、MAX_ENERGY == 2048）",
                TerminalBlockEntity.TRANSFER_RATE == COPPER && TerminalBlockEntity.MAX_ENERGY == COPPER);
        check("capacityFor(2048) == 2048（**纯铜端子与 ZF126 逐字一致**）",
                TerminalBlockEntity.capacityFor(COPPER) == COPPER);
        check("capacityFor(16134) == 32268（= 2 × 单线速率：差额一半要 2 倍才传得满）",
                TerminalBlockEntity.capacityFor(SILVER) == SILVER * 2);
        ItemStack silverSpool = new ItemStack(ModItems.SILVER_WIRE_SPOOL.get());
        ItemStack copperSpool = new ItemStack(ModItems.COPPER_WIRE_SPOOL.get());
        check("银线轴耐久 32（与铜线轴 " + copperSpool.getMaxDamage() + " 一致）",
                silverSpool.getMaxDamage() == 32 && copperSpool.getMaxDamage() == 32);
        check("银线 / 银线轴都注册了（注册 id 对得上）",
                idOf(new ItemStack(ModItems.SILVER_WIRE.get())).equals("potato_s_t:silver_wire")
                        && idOf(new ItemStack(ModItems.SILVER_WIRE_SPOOL.get()))
                                .equals("potato_s_t:silver_wire_spool"));

        say(TAG + "② 两条配方在真服务端上摆得出来");
        ItemStack silverIngot = new ItemStack(ModItems.SILVER_INGOT.get());
        ItemStack emptySpool = new ItemStack(ModItems.EMPTY_SPOOL.get());
        ItemStack copperWire = new ItemStack(ModItems.COPPER_WIRE.get());
        ItemStack silverWire = new ItemStack(ModItems.SILVER_WIRE.get());

        check("crafting：2 个银锭（2×1）⇒ 4 根银线",
                craft(level, "potato_s_t:silver_wire", 2, 1,
                        NonNullList.of(ItemStack.EMPTY, silverIngot, silverIngot),
                        "potato_s_t:silver_wire", 4));
        check("crafting：只给 1 个银锭 ⇒ **不许**成立（负向对照）",
                !craftable(level, "potato_s_t:silver_wire", 2, 1,
                        NonNullList.of(ItemStack.EMPTY, silverIngot, ItemStack.EMPTY)));

        NonNullList<ItemStack> grid = NonNullList.withSize(9, ItemStack.EMPTY);
        for (int i = 0; i < 9; i++) {
            if (i != 4) {
                grid.set(i, silverWire.copy());
            }
        }
        grid.set(4, emptySpool.copy());
        check("crafting：8 根银线围 1 个空线轴（3×3）⇒ 1 个银线轴",
                craft(level, "potato_s_t:silver_wire_spool", 3, 3, grid,
                        "potato_s_t:silver_wire_spool", 1));

        NonNullList<ItemStack> bad = NonNullList.withSize(9, ItemStack.EMPTY);
        for (int i = 0; i < 9; i++) {
            if (i != 4) {
                bad.set(i, copperWire.copy());
            }
        }
        bad.set(4, emptySpool.copy());
        // ⚠ 第一版这条写成"这个摆法不匹配任何配方" ⇒ 假 FAIL：8 根铜线围空线轴**本来就**能出
        //   铜线轴（那是另一条正当配方）。改成"这个摆法做出来的是**铜线轴**、不是银线轴"。
        check("crafting：拿**铜线**围空线轴 ⇒ 出来的是铜线轴，**不是**银线轴（负向对照）",
                craftResultId(level, 3, 3, bad).equals("potato_s_t:copper_wire_spool"));

        say(TAG + "③ 拿真物品连线（FakePlayer 右键两次）");
        TerminalBlockEntity t1 = place(level, FX, FZ);          // 银线对：INPUT
        TerminalBlockEntity t2 = place(level, FX, FZ + 4);      // 银线对：OUTPUT
        TerminalBlockEntity t3 = place(level, FX, FZ + 10);     // 铜线对：INPUT
        TerminalBlockEntity t4 = place(level, FX, FZ + 14);     // 铜线对：OUTPUT
        check("四只端子都立起来了", t1 != null && t2 != null && t3 != null && t4 != null);
        if (t1 == null || t2 == null || t3 == null || t4 == null) {
            return;
        }

        FakePlayer player = FakePlayerFactory.get(level, new GameProfile(
                java.util.UUID.nameUUIDFromBytes("zf127".getBytes()), "zf127probe"));
        player.setGameMode(GameType.SURVIVAL);

        player.setItemInHand(InteractionHand.MAIN_HAND, silverSpool);
        int before = silverSpool.getDamageValue();
        click(level, player, t1);
        check("第一次右键只是**选中**（还没连线）", t1.getConnections().isEmpty());
        click(level, player, t2);
        check("第二次右键连上了：两端各记一条", t1.getConnections().size() == 1
                && t2.getConnections().size() == 1);
        check("银线轴耐久 −1（" + before + " → " + silverSpool.getDamageValue() + "）",
                silverSpool.getDamageValue() == before + 1);
        check("两端记的速率都是 16134（真物品走出来的，不是直接调 API 摆的）",
                rateTo(t1, t2) == SILVER && rateTo(t2, t1) == SILVER);
        check("银线端子的 lineRate / capacity = 16134 / 32268",
                t1.lineRate() == SILVER && t1.capacity() == SILVER * 2
                        && t1.getEnergyStorage().getMaxEnergyStored() == SILVER * 2);

        player.setItemInHand(InteractionHand.MAIN_HAND, copperSpool);
        click(level, player, t3);
        click(level, player, t4);
        check("铜线轴连出来的那一对：速率 2048、容量 2048（**回归**：铜线一个字节没变）",
                rateTo(t3, t4) == COPPER && t3.lineRate() == COPPER && t3.capacity() == COPPER
                        && t3.getEnergyStorage().getMaxEnergyStored() == COPPER);
        check("铜线轴也照旧扣了 1 点耐久（" + copperSpool.getDamageValue() + "）",
                copperSpool.getDamageValue() == 1);

        say(TAG + "④ 一 tick 到底传多少（用户那个 16134 的意义）");
        t1.cycleMode();     // NONE -> INPUT
        t2.cycleMode();     // NONE -> INPUT
        t2.cycleMode();     // INPUT -> OUTPUT
        t3.cycleMode();     // INPUT
        t4.cycleMode();
        t4.cycleMode();     // OUTPUT
        check("t1 是 INPUT、t2 是 OUTPUT（t2 会主动往外推，所以它留不住电）",
                t1.getMode() == TerminalBlockEntity.Mode.INPUT
                        && t2.getMode() == TerminalBlockEntity.Mode.OUTPUT);

        int filledSilver = refill(t1);
        check("银线端子**分多次**灌满到 32268（每次最多 16134/tick 的口径，实得 " + filledSilver + "）",
                filledSilver == SILVER * 2 && t1.getEnergyStored() == SILVER * 2);
        t2.getEnergyStorage().extractEnergy(999_999, false);
        tick(level, t1);
        int movedSilver = t1.capacity() - t1.getEnergyStored();
        check("**一 tick 传了 " + movedSilver + " FE**（银线 16134）", movedSilver == SILVER);
        check("对面收到的是同一个数（t2 = " + t2.getEnergyStored() + "）", t2.getEnergyStored() == SILVER);

        int filledCopper = refill(t3);
        t4.getEnergyStorage().extractEnergy(999_999, false);
        tick(level, t3);
        int movedCopper = t3.capacity() - t3.getEnergyStored();
        check("铜线那一对同样条件下**一 tick 传 " + movedCopper + " FE**（= ZF126 时的行为，回归）",
                movedCopper == Math.min(COPPER, (filledCopper + 1) / 2) && movedCopper == 1024);
        check("银线 / 铜线一 tick = " + movedSilver + " / " + movedCopper
                + "（同一套规则、只是速率不同）", movedSilver == SILVER && movedCopper == 1024);

        say(TAG + "⑤ 上游补得满时，连着跑 3 tick 每 tick 都是 16134");
        boolean steady = true;
        for (int i = 0; i < 3; i++) {
            t2.getEnergyStorage().extractEnergy(999_999, false);   // 下游每 tick 抽干
            refill(t1);                                            // 上游（发电机）每 tick 补满
            int was = t1.getEnergyStored();
            tick(level, t1);
            steady &= (was - t1.getEnergyStored()) == SILVER;
        }
        check("3 tick 每 tick 都传出 16134（不是只第一 tick 好看）", steady);

        t2.getEnergyStorage().extractEnergy(999_999, false);
        refill(t1);
        tick(level, t1);
        t2.getEnergyStorage().extractEnergy(999_999, false);
        int was = t1.getEnergyStored();
        tick(level, t1);
        int half = was - t1.getEnergyStored();
        check("⚠ **上游供不上时按「差额一半」走**（16134 → " + half + "）：这是均衡规则本身，如实记",
                half == (SILVER + 1) / 2);

        say(TAG + "⑥ 铜线那对再用银线轴连一次 ⇒ 就地升级");
        TerminalBlockEntity t5 = place(level, FX, FZ + 20);
        TerminalBlockEntity t6 = place(level, FX, FZ + 24);
        player.setItemInHand(InteractionHand.MAIN_HAND, copperSpool);
        click(level, player, t5);
        click(level, player, t6);
        check("先连成铜线（2048）", t5.lineRate() == COPPER && t6.lineRate() == COPPER);
        int beforeUp = silverSpool.getDamageValue();
        player.setItemInHand(InteractionHand.MAIN_HAND, silverSpool);
        click(level, player, t5);
        click(level, player, t6);
        check("换银线轴再连一次 ⇒ 两端都升级到 16134",
                t5.lineRate() == SILVER && t6.lineRate() == SILVER && rateTo(t5, t6) == SILVER);
        check("升级也扣了 1 点耐久（" + beforeUp + " → " + silverSpool.getDamageValue() + "）",
                silverSpool.getDamageValue() == beforeUp + 1);
        player.setItemInHand(InteractionHand.MAIN_HAND, copperSpool);
        click(level, player, t5);
        click(level, player, t6);
        check("拿**铜线轴**再连一次不会把它降级回 2048", t5.lineRate() == SILVER
                && t6.lineRate() == SILVER && rateTo(t5, t6) == SILVER);

        say(TAG + "⑦ 银线拆掉之后：容量缩回、电量不超上限");
        t5.cycleMode();                       // INPUT
        refill(t5);
        check("拆之前 t5 存着 32268（银线档）", t5.getEnergyStored() == SILVER * 2);
        level.destroyBlock(t6.getBlockPos(), false);
        tick(level, t5);
        check("拆掉对端之后 capacity 缩回 2048（" + t5.capacity() + "）", t5.capacity() == COPPER);
        check("电量被夹到不超过上限（" + t5.getEnergyStored() + " ≤ " + t5.capacity() + "）",
                t5.getEnergyStored() <= t5.capacity());

        say(TAG + "⑧ 存档：新格式往返 + 老格式（ZF126 及以前）照读");
        CompoundTag saved = t1.saveWithoutMetadata(level.registryAccess());
        ListTag conn = saved.getList("connections", Tag.TAG_COMPOUND);
        check("存盘是 CompoundTag 列表（pos + rate）", conn.size() == 1
                && conn.getCompound(0).contains("pos") && conn.getCompound(0).getInt("rate") == SILVER);
        TerminalBlockEntity t7 = place(level, FX, FZ + 30);
        TerminalBlockEntity t8 = place(level, FX, FZ + 34);
        t7.addConnection(t8.getBlockPos(), SILVER);
        t8.addConnection(t7.getBlockPos(), SILVER);
        CompoundTag round = t7.saveWithoutMetadata(level.registryAccess());
        TerminalBlockEntity t9 = place(level, FX, FZ + 40);
        t9.loadWithComponents(round, level.registryAccess());
        check("新格式往返：连接与速率原样读回来",
                t9.lineRate() == SILVER && rateTo(t9, t8) == SILVER);

        CompoundTag legacy = new CompoundTag();
        legacy.putString("mode", "INPUT");
        legacy.putInt("energy", 5000);
        ListTag legacyList = new ListTag();
        legacyList.add(LongTag.valueOf(t8.getBlockPos().asLong()));
        legacy.put("connections", legacyList);
        TerminalBlockEntity t10 = place(level, FX, FZ + 44);
        t10.loadWithComponents(legacy, level.registryAccess());
        check("**老存档**（ListTag<LongTag>）读进来：连接还在、按铜线 2048 算",
                t10.getConnections().size() == 1 && t10.lineRate() == COPPER
                        && rateTo(t10, t8) == COPPER);
        check("老存档里超过铜线上限的电量被夹到 2048（与 ZF126 同一口径）",
                t10.getEnergyStored() == COPPER);
        Map<BlockPos, Integer> map = t10.getConnections();
        check("老格式读出来的 map 值就是 TRANSFER_RATE",
                map.containsValue(TerminalBlockEntity.TRANSFER_RATE));

        say(TAG + "⑨ 银线轴耗尽时也返还空线轴（与铜线轴**同一条路**）");
        TerminalBlockEntity tA = place(level, FX, FZ + 48);
        TerminalBlockEntity tB = place(level, FX, FZ + 52);
        ItemStack worn = new ItemStack(ModItems.SILVER_WIRE_SPOOL.get());
        worn.setDamageValue(worn.getMaxDamage() - 1);          // 就差最后一点耐久
        player.setItemInHand(InteractionHand.MAIN_HAND, worn);
        click(level, player, tA);
        click(level, player, tB);
        check("用最后一点耐久也能把线拉好（" + rateTo(tA, tB) + "）", rateTo(tA, tB) == SILVER);
        ItemStack inHand = player.getItemInHand(InteractionHand.MAIN_HAND);
        // ⚠ 第一版把这条写成"手里那格必须是空的" ⇒ 假 FAIL：破损回调先把空线轴塞回背包，
        //   而刚空出来的那一格就是第一个空位 ⇒ 手里拿着的**正是那个空线轴**（正常的原版行为）。
        check("用完的银线轴没了（手里那格现在是空的、或直接补成了空线轴：item=" + idOf(inHand)
                + " count=" + inHand.getCount() + "）",
                inHand.isEmpty() || idOf(inHand).equals("potato_s_t:empty_spool"));
        check("背包里多出一个**空线轴**（与铜线轴同一套 giveEmptySpoolBack）",
                player.getInventory().contains(new ItemStack(ModItems.EMPTY_SPOOL.get())));

        say(TAG + "⑩ 混着接：同一个端子上一根银线一根铜线（每条线各按各的速率）");
        TerminalBlockEntity t11 = place(level, FX, FZ + 8);      // ⚠ 必须 ≤ 16 格（第一版放到 FZ+56 太远，连不上）
        player.setItemInHand(InteractionHand.MAIN_HAND, copperSpool);
        click(level, player, t2);
        click(level, player, t11);
        check("t2 同时接着银线（去 t1）和铜线（去 t11）", t2.getConnections().size() == 2);
        check("t2 的 lineRate 取最高的 16134（端子能力按高档算）",
                t2.lineRate() == SILVER && t2.capacity() == SILVER * 2);
        check("两条线各记各的速率（银 16134 / 铜 2048）",
                rateTo(t2, t1) == SILVER && rateTo(t2, t11) == COPPER);

        t2.getEnergyStorage().extractEnergy(999_999, false);
        t11.cycleMode();                       // ⚠ 不灌电就测不出东西（第一版忘了这步 ⇒ 铜线那根传了 0）
        refill(t11);
        int wasCu = t11.getEnergyStored();
        tick(level, t11);
        int edgeCopper = wasCu - t11.getEnergyStored();
        t2.getEnergyStorage().extractEnergy(999_999, false);
        refill(t1);
        int wasAg = t1.getEnergyStored();
        tick(level, t1);
        int edgeSilver = wasAg - t1.getEnergyStored();
        check("**同一个对端**：银线那根一 tick " + edgeSilver + "、铜线那根一 tick " + edgeCopper
                + "（每条线按自己的速率，不是按端子的）",
                edgeSilver == SILVER && edgeCopper == 1024);
    }

    // ================= 工具 =================

    /** 灌到灌不动为止，返回总共灌进去多少（端子一次最多收 lineRate()，所以要连着来几次） */
    private static int refill(TerminalBlockEntity terminal) {
        int total = 0;
        for (int i = 0; i < 4; i++) {
            int got = terminal.getEnergyStorage().receiveEnergy(999_999, false);
            total += got;
            if (got <= 0) {
                break;
            }
        }
        return total;
    }

    private static int rateTo(TerminalBlockEntity from, TerminalBlockEntity to) {
        Integer r = from.getConnections().get(to.getBlockPos());
        return r == null ? -1 : r;
    }

    private static TerminalBlockEntity place(ServerLevel level, int x, int z) {
        BlockPos support = new BlockPos(x, FY, z);
        BlockPos p = support.above();
        level.setBlock(support, Blocks.STONE.defaultBlockState(), 3);
        level.setBlock(p, ModBlocks.TERMINAL.get().defaultBlockState()
                .setValue(TerminalBlock.FACING, Direction.UP), 3);
        return level.getBlockEntity(p) instanceof TerminalBlockEntity be ? be : null;
    }

    /**
     * 拿手里的东西右键端子（走**玩家真正走的那条路**：`ServerPlayerGameMode.useItemOn`）。
     *
     * <p>⚠ 不能直接调 `block.useItemOn(...)` —— 它在 {@code BlockBehaviour} 里是 protected，
     * 而本探针与 `Block` 不同包、也不是它的子类（Java 的 protected 规则）⇒ 编译期就挡下来。
     * 走 gameMode 这条路反而更真：它就是服务端处理"玩家右键方块"的那个入口。</p>
     */
    private static void click(ServerLevel level, FakePlayer player, TerminalBlockEntity terminal) {
        BlockPos p = terminal.getBlockPos();
        ItemStack stack = player.getItemInHand(InteractionHand.MAIN_HAND);
        player.gameMode.useItemOn(player, level, stack, InteractionHand.MAIN_HAND,
                new BlockHitResult(Vec3.atCenterOf(p), Direction.UP, p, false));
    }

    private static void tick(ServerLevel level, TerminalBlockEntity terminal) {
        BlockPos p = terminal.getBlockPos();
        BlockState state = level.getBlockState(p);
        TerminalBlockEntity.tick(level, p, state, terminal);
    }

    /** 拿游戏自己的合成表匹配 + 产出：对得上才算过 */
    @SuppressWarnings("unchecked")
    private static boolean craft(ServerLevel level, String recipeId, int w, int h,
                                 List<ItemStack> grid, String expectId, int expectCount) {
        RecipeHolder<?> holder = level.getRecipeManager()
                .byKey(ResourceLocation.parse(recipeId)).orElse(null);
        if (holder == null) {
            say(TAG + "        （配方 " + recipeId + " 不在 RecipeManager 里）");
            return false;
        }
        Recipe<CraftingInput> recipe = (Recipe<CraftingInput>) holder.value();
        CraftingInput input = CraftingInput.of(w, h, grid);
        if (!recipe.matches(input, level)) {
            say(TAG + "        （配方 " + recipeId + " 摆出来的样子不匹配）");
            return false;
        }
        ItemStack out = recipe.assemble(input, level.registryAccess());
        return idOf(out).equals(expectId) && out.getCount() == expectCount;
    }

    private static boolean craftable(ServerLevel level, String recipeId, int w, int h,
                                     List<ItemStack> grid) {
        return level.getRecipeManager()
                .getRecipeFor(RecipeType.CRAFTING, CraftingInput.of(w, h, grid), level).isPresent();
    }

    /** 这个摆法在游戏里**做出来的是什么**（没有配方就返回空串）—— 用于负向对照 */
    private static String craftResultId(ServerLevel level, int w, int h, List<ItemStack> grid) {
        return level.getRecipeManager()
                .getRecipeFor(RecipeType.CRAFTING, CraftingInput.of(w, h, grid), level)
                .map(holder -> idOf(holder.value().getResultItem(level.registryAccess())))
                .orElse("");
    }

    private static String idOf(ItemStack stack) {
        return stack.isEmpty() ? "<空>" : BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
    }

    private static void clear(ServerLevel level) {
        for (int dz = -6; dz <= 62; dz++) {
            for (int dy = 0; dy <= 2; dy++) {
                level.setBlock(new BlockPos(FX, FY + dy, FZ + dz), Blocks.AIR.defaultBlockState(), 3);
            }
        }
    }
}
