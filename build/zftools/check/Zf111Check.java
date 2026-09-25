package com.potatost.mod;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF111 的临时探针）</b>：合金冶炼炉的**第三条配方**（星璨钢锭）。
 *
 * <p>用户原话：「星璨钢加合金冶炼配方 下界合金锭+4高碳钢+钴锭+银锭+铜锭 再消耗1个深层钴矿石
 * 1个末影水晶 产出三个星璨钢钢 12000FE/t」。</p>
 *
 * <p>三段，缺一不可：</p>
 * <ol>
 *   <li><b>五个锭标签真的存在而且非空</b> —— 这是本轮最危险的一条：输入走
 *       {@code c:ingots/<材料>}，其中 {@code netherite} / {@code copper} 是**原版/NeoForge
 *       提供的**（不是我们生成的）。标签不存在或者里头没有那件东西，配方就<b>永远开不了工</b>，
 *       而且静态检查看不出来（表里写的只是个 TagKey）。所以在这里逐个查"非空 + 认到预期物品"；</li>
 *   <li><b>配方表第三条本身</b>：5 个输入（高碳钢要 4 个）、2 个消耗品（深层钴矿石 + 末影水晶）、
 *       产物 3 个星璨钢锭、每 tick 12000 FE、一轮 600 tick（= 7,200,000 FE）；</li>
 *   <li><b>真机器跑一轮</b>（照 ZF62 那套：程序搭出 4 层结构 + 自动成型 + 直接连调
 *       {@code craftTick()}）：缺消耗品 ⇒ 不开工、一度电都不许扣；齐了 ⇒ 跑满 600 tick
 *       正好扣 7,200,000 FE，输入槽与消耗槽按数目扣干净、输出槽里正好 3 个星璨钢锭；
 *       另外验消耗槽的门禁（垃圾进不去、配方要的东西进得去）。</li>
 * </ol>
 *
 * <p>⚠ 期望值一律写**用户说的字面量**（4 / 3 / 12000 / 600 / 7200000），不从被测常量抄 ——
 * 抄的话改坏常数探针也跟着变，等于没检查（§4.27）。</p>
 *
 * <p>挂载方式：`PotatoST` 构造器末尾加一行 `Zf111Check.register();`，跑完用 `_zf111_unprobe.py`
 * 摘掉（**先抄进 `build/zftools/check/` 再删** —— ZF107 那次省了这步，吃了重建的苦）。</p>
 */
public final class Zf111Check {

    private static final String TAG = "[A111] ";
    private static final Direction FACING = Direction.SOUTH;
    private static final BlockPos C = new BlockPos(352, 260, 176);

    /** §4.50：runServer 的日志按 GBK 打，中文会变乱码 ⇒ 自己攒一份 UTF-8 报告，路径必须绝对。 */
    private static final StringBuilder REPORT = new StringBuilder();
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf111_probe_utf8.txt";

    private static boolean registered;
    private static int passed;
    private static int failed;

    private Zf111Check() {
    }

    private static void say(String line) {
        System.out.println(line);
        REPORT.append(line).append('\n');
    }

    private static int check(String name, boolean ok) {
        if (ok) {
            passed++;
        } else {
            failed++;
        }
        say(TAG + (ok ? "[OK]   " : "[FAIL] ") + name);
        return ok ? 0 : 1;
    }

    private static void flushReport() {
        try (java.io.OutputStreamWriter w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), java.nio.charset.StandardCharsets.UTF_8)) {
            w.write("ZF111 探针报告（星璨钢配方：标签 / 配方表 / 真机器跑一轮）· UTF-8 · §4.50\n");
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
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf111Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        failed = 0;
        passed = 0;
        try {
            testTags();
            testTable();
            testInWorld(event.getServer().overworld());
        } catch (Throwable t) {
            say(TAG + "exception: " + t);
            java.io.StringWriter sw = new java.io.StringWriter();
            t.printStackTrace(new java.io.PrintWriter(sw));
            for (String line : sw.toString().split("\n")) {
                say(TAG + "    " + line);
            }
            failed++;
        } finally {
            say(TAG + "verdict: " + (failed == 0 ? "ALL OK" : "**" + failed + " FAILED**")
                    + " (passed " + passed + ")");
            say(TAG + "done, halting server");
            flushReport();
            event.getServer().halt(false);
        }
    }

    // ============================================================
    //  ① 五个锭标签
    // ============================================================
    private static void testTags() {
        say(TAG + "① item tags: c:ingots/{netherite,steel,cobalt,silver,copper}");
        tagCase("netherite", "netherite", Items.NETHERITE_INGOT);
        tagCase("steel", "steel", ModItems.HIGH_CARBON_STEEL.get());
        tagCase("cobalt", "cobalt", ModItems.COBALT_INGOT.get());
        tagCase("silver", "silver", ModItems.SILVER_INGOT.get());
        tagCase("copper", "copper", Items.COPPER_INGOT);
    }

    private static void tagCase(String label, String path, Item expected) {
        TagKey<Item> tag = TagKey.create(net.minecraft.core.registries.Registries.ITEM,
                ResourceLocation.fromNamespaceAndPath("c", "ingots/" + path));
        List<Item> got = new java.util.ArrayList<>();
        BuiltInRegistries.ITEM.getTagOrEmpty(tag).forEach(h -> got.add(h.value()));
        check("c:ingots/" + label + " 非空（" + got.size() + " 件）", !got.isEmpty());
        check("c:ingots/" + label + " 认得到 " + expected, got.contains(expected));
        check("ItemStack 判定认得它（" + label + "）",
                new ItemStack(expected).is(tag));
    }

    // ============================================================
    //  ② 配方表
    // ============================================================
    private static void testTable() {
        say(TAG + "② recipe table");
        List<AlloySmelterRecipes.Smelt> all = AlloySmelterRecipes.all();
        check("全表 3 条配方（实际 " + all.size() + "）", all.size() == 3);
        if (all.size() < 3) {
            return;
        }
        AlloySmelterRecipes.Smelt star = all.get(2);
        check("第三条是 5 种输入（实际 " + star.needs().size() + "）", star.needs().size() == 5);
        int steelCount = -1;
        for (AlloySmelterRecipes.Need need : star.needs()) {
            if (need.tag().location().getPath().equals("ingots/steel")) {
                steelCount = need.count();
            }
        }
        check("高碳钢要 4 个（实际 " + steelCount + "）", steelCount == 4);
        check("另外四种各要 1 个（实际 "
                        + star.needs().stream().filter(n -> n.count() == 1).count() + " 种）",
                star.needs().stream().filter(n -> n.count() == 1).count() == 4);
        check("2 个消耗品（实际 " + star.consumes().size() + "）", star.consumes().size() == 2);
        boolean hasOre = false;
        boolean hasCrystal = false;
        for (AlloySmelterRecipes.Consume consume : star.consumes()) {
            if (consume.item() == PotatoSTOres.DEEPSLATE_COBALT_ORE.get().asItem()
                    && consume.count() == 1) {
                hasOre = true;
            }
            if (consume.item() == Items.END_CRYSTAL && consume.count() == 1) {
                hasCrystal = true;
            }
        }
        check("消耗品里有 1 个深层钴矿石", hasOre);
        check("消耗品里有 1 个末影水晶", hasCrystal);
        check("产物是星璨钢锭（实际 " + star.result().getHoverName().getString() + "）",
                star.result().is(ModArmorItems.STAR_STEEL_INGOT.get()));
        check("产物 3 个（实际 " + star.result().getCount() + "）", star.result().getCount() == 3);
        check("每 tick 12000 FE（实际 " + star.energyPerTick() + "）", star.energyPerTick() == 12_000);
        check("一轮 600 tick（实际 " + star.durationTicks() + "）", star.durationTicks() == 600);
        check("一轮总耗电 7200000 FE（实际 " + star.totalEnergy() + "）",
                star.totalEnergy() == 7_200_000L);
        check("前两条配方的消耗品列表是空的",
                all.get(0).consumes().isEmpty() && all.get(1).consumes().isEmpty());
        check("最贵的一条 12000 ≤ 储能 32768（ZF42 守卫）",
                AlloySmelterRecipes.MAX_ENERGY_PER_TICK <= AlloySmelterBlockEntity.MAX_ENERGY);
    }

    // ============================================================
    //  ③ 真机器
    // ============================================================
    private static void testInWorld(ServerLevel level) {
        say(TAG + "③ real machine at " + C);
        clear(level);
        for (int y = 0; y < AlloySmelterStructure.HEIGHT; y++) {
            buildLayer(level, y);
        }
        AlloySmelterBlock.tryAutoForm(level, C);
        if (!(level.getBlockEntity(C) instanceof AlloySmelterBlockEntity be)) {
            check("控制器方块实体在", false);
            return;
        }
        check("机器成型了", be.isFormed());

        int in = AlloySmelterBlockEntity.INPUT_FIRST;
        int out = AlloySmelterBlockEntity.OUTPUT_FIRST;
        int con = AlloySmelterBlockEntity.CONSUME_FIRST;

        // ---------- 消耗槽门禁 ----------
        say(TAG + "③a consume-slot gate");
        check("消耗槽收深层钴矿石",
                be.getInventory().isItemValid(con, new ItemStack(
                        PotatoSTOres.DEEPSLATE_COBALT_ORE.get().asItem())));
        check("消耗槽收末影水晶", be.getInventory().isItemValid(con, new ItemStack(Items.END_CRYSTAL)));
        check("消耗槽不收圆石（垃圾进不去）",
                !be.getInventory().isItemValid(con, new ItemStack(Items.COBBLESTONE)));
        check("输入槽仍然只收锭（收铁锭）",
                be.getInventory().isItemValid(in, new ItemStack(Items.IRON_INGOT)));
        check("输入槽不收末影水晶",
                !be.getInventory().isItemValid(in, new ItemStack(Items.END_CRYSTAL)));

        // ---------- 缺消耗品 ⇒ 不开工、不扣电 ----------
        say(TAG + "③b all five ingots but NO consumables -> no craft, no draw");
        be.getInventory().setStackInSlot(in, new ItemStack(Items.NETHERITE_INGOT, 4));
        be.getInventory().setStackInSlot(in + 1, new ItemStack(ModItems.HIGH_CARBON_STEEL.get(), 8));
        be.getInventory().setStackInSlot(in + 2, new ItemStack(ModItems.COBALT_INGOT.get(), 4));
        be.getInventory().setStackInSlot(in + 3, new ItemStack(ModItems.SILVER_INGOT.get(), 4));
        be.getInventory().setStackInSlot(in + 4, new ItemStack(Items.COPPER_INGOT, 4));
        fill(be, 40_000L);
        int e0 = be.getEnergyStored();
        for (int i = 0; i < 10; i++) {
            be.craftTick();
        }
        check("缺消耗品：进度仍是 0（实际 " + be.getProgress() + "）", be.getProgress() == 0);
        check("缺消耗品：一度电都没扣（" + e0 + " → " + be.getEnergyStored() + "）",
                e0 == be.getEnergyStored());

        // ---------- 只放一半消耗品 ⇒ 仍然不开工 ----------
        be.getInventory().setStackInSlot(con, new ItemStack(
                PotatoSTOres.DEEPSLATE_COBALT_ORE.get().asItem(), 2));
        for (int i = 0; i < 5; i++) {
            be.craftTick();
        }
        check("只有钴矿石、没有末影水晶：进度仍是 0（实际 " + be.getProgress() + "）",
                be.getProgress() == 0);

        // ---------- 齐了 ⇒ 跑满一轮，账目分毫不差 ----------
        say(TAG + "③c everything present -> one full craft, exact accounting");
        be.getInventory().setStackInSlot(con + 1, new ItemStack(Items.END_CRYSTAL, 2));
        long startBalance = be.getEnergyStored();
        long injected = 0;
        int ticks = 600;                                   // 用户没给时长 ⇒ 本机规格 30 秒（字面量）
        for (int i = 0; i < ticks; i++) {
            injected += fill(be, 12_000L);                 // 正好这一 tick 的耗电（字面量）
            be.craftTick();
        }
        long spent = startBalance + injected - be.getEnergyStored();
        say(TAG + "    ticks=" + ticks + " injected=" + injected + " spent=" + spent
                + " buffer=" + be.getEnergyStored());
        check("每 tick 正好 12000 FE（实扣 " + spent + "）", spent == (long) ticks * 12_000L);
        check("一轮 = 600 × 12000 = 7200000 FE", spent == 7_200_000L);
        check("进度归零（实际 " + be.getProgress() + "）", be.getProgress() == 0);

        ItemStack result = be.getInventory().getStackInSlot(out);
        check("输出槽 = 3 个星璨钢锭（实际 " + result.getCount() + " × "
                        + result.getHoverName().getString() + "）",
                result.is(ModArmorItems.STAR_STEEL_INGOT.get()) && result.getCount() == 3);
        check("下界合金 4 → 3（实际 " + be.getInventory().getStackInSlot(in).getCount() + "）",
                be.getInventory().getStackInSlot(in).getCount() == 3);
        check("高碳钢 8 → 4（实际 " + be.getInventory().getStackInSlot(in + 1).getCount() + "）",
                be.getInventory().getStackInSlot(in + 1).getCount() == 4);
        check("钴锭 4 → 3（实际 " + be.getInventory().getStackInSlot(in + 2).getCount() + "）",
                be.getInventory().getStackInSlot(in + 2).getCount() == 3);
        check("银锭 4 → 3（实际 " + be.getInventory().getStackInSlot(in + 3).getCount() + "）",
                be.getInventory().getStackInSlot(in + 3).getCount() == 3);
        check("铜锭 4 → 3（实际 " + be.getInventory().getStackInSlot(in + 4).getCount() + "）",
                be.getInventory().getStackInSlot(in + 4).getCount() == 3);
        check("深层钴矿石 2 → 1（实际 " + be.getInventory().getStackInSlot(con).getCount() + "）",
                be.getInventory().getStackInSlot(con).getCount() == 1);
        check("末影水晶 2 → 1（实际 " + be.getInventory().getStackInSlot(con + 1).getCount() + "）",
                be.getInventory().getStackInSlot(con + 1).getCount() == 1);

        // ---------- 老两条配方没被新字段弄坏 ----------
        say(TAG + "③d the two older recipes still work (800 FE/t)");
        for (int slot = 0; slot < AlloySmelterBlockEntity.SLOT_COUNT; slot++) {
            be.getInventory().setStackInSlot(slot, ItemStack.EMPTY);
        }
        be.getInventory().setStackInSlot(in, new ItemStack(ModItems.ALUMINUM_INGOT.get(), 2));
        be.getInventory().setStackInSlot(in + 1, new ItemStack(ModItems.TITANIUM_INGOT.get(), 2));
        be.getInventory().setStackInSlot(in + 2, new ItemStack(ModItems.SILVER_INGOT.get(), 2));
        long start2 = be.getEnergyStored();
        long injected2 = 0;
        for (int i = 0; i < 600; i++) {
            injected2 += fill(be, 800L);
            be.craftTick();
        }
        long spent2 = start2 + injected2 - be.getEnergyStored();
        check("老配方仍是每 tick 800 FE（实扣 " + spent2 + "）", spent2 == 480_000L);
        ItemStack light = be.getInventory().getStackInSlot(out);
        check("老配方产物仍是 1 个轻质钛合金",
                light.is(ModItems.LIGHT_TITANIUM_ALLOY.get()) && light.getCount() == 1);

        clear(level);
    }

    // ==================== 工具（照 ZF62 那套） ====================

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
                BlockState state = kind == AlloySmelterStructure.Kind.CONTROLLER
                        ? ModBlocks.ALLOY_SMELTER.get().defaultBlockState()
                                .setValue(AlloySmelterBlock.FACING, FACING)
                        : AlloySmelterStructure.blockFor(kind).defaultBlockState();
                level.setBlock(AlloySmelterStructure.offset(C, FACING, y, j, i), state, 3);
            }
        }
    }

    private static void clear(ServerLevel level) {
        level.setBlock(C, Blocks.AIR.defaultBlockState(), 3);
        for (BlockPos p : AlloySmelterStructure.positions(C, FACING)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
        }
    }
}
