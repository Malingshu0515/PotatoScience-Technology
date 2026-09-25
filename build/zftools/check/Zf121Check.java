package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
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
 * ⚠⚠ <b>诊断工具（ZF121 的临时探针）</b>：振金的**合金冶炼炉配方**。
 *
 * <p>用户原话（改口后的最终版）：「对不起刚才忘了合金炉的限制 这是新振金合金冶炼炉配方；
 * 1硬质钛合金+8热力金属+2高碳钢+3银锭+12金锭 粗振金+2下界合金碎片 14500Fe/t 产出1振金」。</p>
 *
 * <p>四段，缺一不可：</p>
 * <ol>
 *   <li><b>五个输入标签真的存在而且非空</b> —— 本轮最危险的一条：<b>硬质钛合金与热力金属
 *       本来都不在 {@code #c:ingots} 里</b>（ZF104 / ZF45 当年没给它们挂标签），而输入槽
 *       只收这个标签 ⇒ 不挂就<b>放都放不进去</b>、配方永远开不了工，且静态检查看不出来
 *       （表里写的只是个 TagKey，与 ZF111 踩的 {@code c:ingots/netherite} 同一类坑）：</li>
 *   <li><b>配方表第四条本身</b>：5 个输入（8 热力金属 / 12 金锭 …）、<b>2 个消耗品</b>
 *       （1 粗振金 + 2 下界合金碎片；用户改口后钻石与红石粉<b>不在里面</b>）、
 *       产物 1 振金锭、每 tick 14500 FE、一轮 600 tick（= 8,700,000 FE）；</li>
 *   <li><b>真机器跑一轮</b>（照 ZF62/ZF111 那套：程序搭出 4 层结构 + 自动成型 + 直接连调
 *       {@code craftTick()}）：缺消耗品 ⇒ 不开工、一度电都不许扣；齐了 ⇒ 跑满 600 tick
 *       正好扣 8,700,000 FE，五样输入与两样消耗品按数目扣干净、输出槽里正好 1 个振金锭；</li>
 *   <li><b>三条回归</b>：① 老配方仍是 800 FE/t、星璨钢那条仍是 12000（没被 14500 弄坏）；
 *       ② <b>防复制</b>：硬质钛合金 + 高碳钢 + 镍锭**不许**凑出"硬质钛合金 → 硬质钛合金"
 *       （那正是"别把硬质钛合金并进 {@code c:ingots/titanium_alloy}"的理由）；
 *       ③ 用户改口后的口径：钻石与红石粉**既不收进消耗槽、也不算消耗品**。</li>
 * </ol>
 *
 * <p>⚠ 期望值一律写<b>用户说的字面量</b>（1/8/2/3/12 / 2 / 600 / 14500 / 8700000），
 * 不从被测常量抄 —— 抄的话改坏常数探针也跟着变，等于没检查（§4.27）。</p>
 *
 * <p>挂载方式：`PotatoST` 构造器末尾加一行 `Zf121Check.register();`，跑完用
 * {@code _zf121_unprobe.py} 摘掉（**先抄进 `build/zftools/check/` 再删**）。</p>
 */
public final class Zf121Check {

    private static final String TAG = "[A121] ";
    private static final Direction FACING = Direction.SOUTH;
    private static final BlockPos C = new BlockPos(384, 260, 176);

    /** §4.50：runServer 的日志按 GBK 打，中文会变乱码 ⇒ 自己攒一份 UTF-8 报告，路径必须绝对。 */
    private static final StringBuilder REPORT = new StringBuilder();
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf121_probe_utf8.txt";

    private static boolean registered;
    private static int passed;
    private static int failed;

    private Zf121Check() {
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
            w.write("ZF121 探针报告（振金配方：标签 / 配方表 / 真机器跑一轮 / 三条回归）· UTF-8 · §4.50\n");
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
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf121Check.class);
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
    //  ① 五个输入标签 + 两处漂移补账
    // ============================================================
    private static void testTags() {
        say(TAG + "① item tags: c:ingots/{hard_titanium_alloy,thermal_metal,steel,silver,gold}");
        tagCase("hard_titanium_alloy", ModItems.HARD_TITANIUM_ALLOY.get());
        tagCase("thermal_metal", ModItems.THERMAL_METAL.get());
        tagCase("steel", ModItems.HIGH_CARBON_STEEL.get());
        tagCase("silver", ModItems.SILVER_INGOT.get());
        tagCase("gold", Items.GOLD_INGOT);

        say(TAG + "①b drift repair: vibranium back into the two parent tags");
        parentHas("ingots", ModItems.VIBRANIUM_INGOT.get(), 12);
        parentHas("raw_materials", ModItems.RAW_VIBRANIUM.get(), 10);
        check("c:ingots 里也有硬质钛合金与热力金属",
                new ItemStack(ModItems.HARD_TITANIUM_ALLOY.get()).is(parentTag("ingots"))
                        && new ItemStack(ModItems.THERMAL_METAL.get()).is(parentTag("ingots")));
    }

    private static TagKey<Item> parentTag(String path) {
        return TagKey.create(Registries.ITEM, ResourceLocation.fromNamespaceAndPath("c", path));
    }

    /**
     * 父标签里"至少要有我们这 N 件 + 认得到这一件"。
     *
     * <p>⚠ 这里**不能断言精确件数**：{@code c:ingots} / {@code c:raw_materials} 这两个父标签
     * NeoForge 自己也在往里塞（解包核过：{@code c:ingots} 收 {@code #c:ingots/copper|gold|iron|netherite}，
     * {@code c:raw_materials} 收三种原版粗矿；还各挂一个 optional 的 {@code #forge:...}）
     * ⇒ 运行时件数 = 我们的 + 原版那几件。断言精确值会在 NeoForge 更新时变成假红。</p>
     */
    private static void parentHas(String path, Item item, int ourCount) {
        TagKey<Item> tag = parentTag(path);
        List<Item> got = new ArrayList<>();
        BuiltInRegistries.ITEM.getTagOrEmpty(tag).forEach(h -> got.add(h.value()));
        say(TAG + "    c:" + path + " 运行时一共 " + got.size() + " 件");
        check("c:" + path + " 至少收下我们这 " + ourCount + " 件（实际 " + got.size() + "）",
                got.size() >= ourCount);
        check("c:" + path + " 里有 " + item, got.contains(item));
        check("ItemStack 判定认得它（c:" + path + "）", new ItemStack(item).is(tag));
    }

    private static void tagCase(String path, Item expected) {
        TagKey<Item> tag = TagKey.create(Registries.ITEM,
                ResourceLocation.fromNamespaceAndPath("c", "ingots/" + path));
        List<Item> got = new ArrayList<>();
        BuiltInRegistries.ITEM.getTagOrEmpty(tag).forEach(h -> got.add(h.value()));
        check("c:ingots/" + path + " 非空（" + got.size() + " 件）", !got.isEmpty());
        check("c:ingots/" + path + " 认得到 " + expected, got.contains(expected));
        check("ItemStack 判定认得它（" + path + "）", new ItemStack(expected).is(tag));
    }

    // ============================================================
    //  ② 配方表
    // ============================================================
    private static void testTable() {
        say(TAG + "② recipe table");
        List<AlloySmelterRecipes.Smelt> all = AlloySmelterRecipes.all();
        check("配方表一共 4 条（实际 " + all.size() + "）", all.size() == 4);
        if (all.size() < 4) {
            return;
        }
        AlloySmelterRecipes.Smelt vib = all.get(3);
        check("第四条是 5 种输入（实际 " + vib.needs().size() + "）", vib.needs().size() == 5);
        check("第四条：1 硬质钛合金", needIs(vib, "ingots/hard_titanium_alloy", 1));
        check("第四条：8 热力金属", needIs(vib, "ingots/thermal_metal", 8));
        check("第四条：2 高碳钢", needIs(vib, "ingots/steel", 2));
        check("第四条：3 银锭", needIs(vib, "ingots/silver", 3));
        check("第四条：12 金锭", needIs(vib, "ingots/gold", 12));

        check("第四条：2 个消耗品（实际 " + vib.consumes().size() + "）", vib.consumes().size() == 2);
        check("消耗品里有 1 个粗振金",
                consumeIs(vib, ModItems.RAW_VIBRANIUM.get(), 1));
        check("消耗品里有 2 个下界合金碎片",
                consumeIs(vib, Items.NETHERITE_SCRAP, 2));
        check("用户改口后**没有**钻石当消耗品", !consumeIs(vib, Items.DIAMOND, 1));
        check("用户改口后**没有**红石粉当消耗品", !consumeIs(vib, Items.REDSTONE, 1));

        check("产物是振金锭（实际 " + vib.result().getHoverName().getString() + "）",
                vib.result().is(ModItems.VIBRANIUM_INGOT.get()));
        check("产物 1 个（实际 " + vib.result().getCount() + "）", vib.result().getCount() == 1);
        check("每 tick 14500 FE（实际 " + vib.energyPerTick() + "）", vib.energyPerTick() == 14_500);
        check("一轮 600 tick（实际 " + vib.durationTicks() + "）", vib.durationTicks() == 600);
        check("一轮总耗电 8700000 FE（实际 " + vib.totalEnergy() + "）",
                vib.totalEnergy() == 8_700_000L);

        check("第①②③条仍是 800 / 800 / 12000 FE/t（没被 14500 弄坏）",
                all.get(0).energyPerTick() == 800
                        && all.get(1).energyPerTick() == 800
                        && all.get(2).energyPerTick() == 12_000);
        check("第①②条没有消耗品", all.get(0).consumes().isEmpty() && all.get(1).consumes().isEmpty());
        check("全表最贵 = 14500 且 ≤ 储能 32768（ZF42 守卫）",
                AlloySmelterRecipes.MAX_ENERGY_PER_TICK == 14_500
                        && AlloySmelterRecipes.MAX_ENERGY_PER_TICK
                        <= AlloySmelterBlockEntity.MAX_ENERGY);
    }

    private static boolean needIs(AlloySmelterRecipes.Smelt smelt, String path, int count) {
        for (AlloySmelterRecipes.Need need : smelt.needs()) {
            if (need.tag().location().getPath().equals(path) && need.count() == count) {
                return true;
            }
        }
        return false;
    }

    private static boolean consumeIs(AlloySmelterRecipes.Smelt smelt, Item item, int count) {
        for (AlloySmelterRecipes.Consume consume : smelt.consumes()) {
            if (consume.item() == item && consume.count() == count) {
                return true;
            }
        }
        return false;
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

        // ---------- ③a 门禁 ----------
        say(TAG + "③a slot gates");
        check("输入槽收硬质钛合金（ZF121 才挂上的标签）",
                be.getInventory().isItemValid(in, new ItemStack(ModItems.HARD_TITANIUM_ALLOY.get())));
        check("输入槽收热力金属（ZF121 才挂上的标签）",
                be.getInventory().isItemValid(in, new ItemStack(ModItems.THERMAL_METAL.get())));
        check("输入槽收金锭（原版）",
                be.getInventory().isItemValid(in, new ItemStack(Items.GOLD_INGOT)));
        check("输入槽不收钻石", !be.getInventory().isItemValid(in, new ItemStack(Items.DIAMOND)));
        check("输入槽不收粗振金",
                !be.getInventory().isItemValid(in, new ItemStack(ModItems.RAW_VIBRANIUM.get())));
        check("消耗槽收粗振金",
                be.getInventory().isItemValid(con, new ItemStack(ModItems.RAW_VIBRANIUM.get())));
        check("消耗槽收下界合金碎片",
                be.getInventory().isItemValid(con, new ItemStack(Items.NETHERITE_SCRAP)));
        check("消耗槽不收圆石（垃圾进不去）",
                !be.getInventory().isItemValid(con, new ItemStack(Items.COBBLESTONE)));
        check("消耗槽不收钻石（用户改口后它不再是消耗品）",
                !be.getInventory().isItemValid(con, new ItemStack(Items.DIAMOND)));
        check("消耗槽不收红石粉（同上）",
                !be.getInventory().isItemValid(con, new ItemStack(Items.REDSTONE)));

        // ---------- ③b 缺消耗品 ⇒ 不开工、不扣电 ----------
        say(TAG + "③b five inputs but NO consumables -> no craft, no draw");
        be.getInventory().setStackInSlot(in, new ItemStack(ModItems.HARD_TITANIUM_ALLOY.get(), 2));
        be.getInventory().setStackInSlot(in + 1, new ItemStack(ModItems.THERMAL_METAL.get(), 9));
        be.getInventory().setStackInSlot(in + 2, new ItemStack(ModItems.HIGH_CARBON_STEEL.get(), 3));
        be.getInventory().setStackInSlot(in + 3, new ItemStack(ModItems.SILVER_INGOT.get(), 4));
        be.getInventory().setStackInSlot(in + 4, new ItemStack(Items.GOLD_INGOT, 13));
        fill(be, 40_000L);
        int e0 = be.getEnergyStored();
        for (int i = 0; i < 10; i++) {
            be.craftTick();
        }
        check("缺消耗品：进度仍是 0（实际 " + be.getProgress() + "）", be.getProgress() == 0);
        check("缺消耗品：一度电都没扣（" + e0 + " → " + be.getEnergyStored() + "）",
                e0 == be.getEnergyStored());

        be.getInventory().setStackInSlot(con, new ItemStack(ModItems.RAW_VIBRANIUM.get(), 2));
        for (int i = 0; i < 5; i++) {
            be.craftTick();
        }
        check("只有粗振金、没有下界合金碎片：进度仍是 0（实际 " + be.getProgress() + "）",
                be.getProgress() == 0);

        // ---------- ③c 齐了 ⇒ 跑满一轮 ----------
        say(TAG + "③c everything present -> one full craft, exact accounting");
        be.getInventory().setStackInSlot(con + 1, new ItemStack(Items.NETHERITE_SCRAP, 3));
        long startBalance = be.getEnergyStored();
        long injected = 0;
        int ticks = 600;                                   // 用户没给时长 ⇒ 本机规格 30 秒（字面量）
        for (int i = 0; i < ticks; i++) {
            injected += fill(be, 14_500L);                 // 正好这一 tick 的耗电（字面量）
            be.craftTick();
        }
        long spent = startBalance + injected - be.getEnergyStored();
        say(TAG + "    ticks=" + ticks + " injected=" + injected + " spent=" + spent
                + " buffer=" + be.getEnergyStored());
        check("每 tick 正好 14500 FE（实扣 " + spent + "）", spent == (long) ticks * 14_500L);
        check("一轮 = 600 × 14500 = 8700000 FE", spent == 8_700_000L);
        check("进度归零（实际 " + be.getProgress() + "）", be.getProgress() == 0);

        ItemStack result = be.getInventory().getStackInSlot(out);
        check("输出槽 = 1 个振金锭（实际 " + result.getCount() + " × "
                        + result.getHoverName().getString() + "）",
                result.is(ModItems.VIBRANIUM_INGOT.get()) && result.getCount() == 1);
        check("硬质钛合金 2 → 1（实际 " + be.getInventory().getStackInSlot(in).getCount() + "）",
                be.getInventory().getStackInSlot(in).getCount() == 1);
        check("热力金属 9 → 1（实际 " + be.getInventory().getStackInSlot(in + 1).getCount() + "）",
                be.getInventory().getStackInSlot(in + 1).getCount() == 1);
        check("高碳钢 3 → 1（实际 " + be.getInventory().getStackInSlot(in + 2).getCount() + "）",
                be.getInventory().getStackInSlot(in + 2).getCount() == 1);
        check("银锭 4 → 1（实际 " + be.getInventory().getStackInSlot(in + 3).getCount() + "）",
                be.getInventory().getStackInSlot(in + 3).getCount() == 1);
        check("金锭 13 → 1（实际 " + be.getInventory().getStackInSlot(in + 4).getCount() + "）",
                be.getInventory().getStackInSlot(in + 4).getCount() == 1);
        check("粗振金 2 → 1（实际 " + be.getInventory().getStackInSlot(con).getCount() + "）",
                be.getInventory().getStackInSlot(con).getCount() == 1);
        check("下界合金碎片 3 → 1（实际 " + be.getInventory().getStackInSlot(con + 1).getCount() + "）",
                be.getInventory().getStackInSlot(con + 1).getCount() == 1);

        // ---------- ③d 防复制：硬质钛合金不许顶替轻质钛合金 ----------
        say(TAG + "③d anti-dupe: hard titanium alloy must NOT satisfy recipe 2");
        wipe(be);
        be.getInventory().setStackInSlot(in, new ItemStack(ModItems.HARD_TITANIUM_ALLOY.get(), 2));
        be.getInventory().setStackInSlot(in + 1, new ItemStack(ModItems.HIGH_CARBON_STEEL.get(), 2));
        be.getInventory().setStackInSlot(in + 2, new ItemStack(ModItems.NICKEL_INGOT.get(), 2));
        fill(be, 40_000L);
        int e3 = be.getEnergyStored();
        for (int i = 0; i < 10; i++) {
            be.craftTick();
        }
        check("硬质钛合金 + 高碳钢 + 镍锭**凑不出**配方（进度仍 " + be.getProgress() + "）",
                be.getProgress() == 0);
        check("也一度电都没扣（" + e3 + " → " + be.getEnergyStored() + "）",
                e3 == be.getEnergyStored());

        // ---------- ③e 老配方仍是 800 ----------
        say(TAG + "③e the older recipes still work (800 FE/t)");
        wipe(be);
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

        // ---------- ③f 星璨钢那条仍是 12000 ----------
        say(TAG + "③f the star-steel recipe still costs 12000 FE/t");
        wipe(be);
        be.getInventory().setStackInSlot(in, new ItemStack(Items.NETHERITE_INGOT, 2));
        be.getInventory().setStackInSlot(in + 1, new ItemStack(ModItems.HIGH_CARBON_STEEL.get(), 5));
        be.getInventory().setStackInSlot(in + 2, new ItemStack(ModItems.COBALT_INGOT.get(), 2));
        be.getInventory().setStackInSlot(in + 3, new ItemStack(ModItems.SILVER_INGOT.get(), 2));
        be.getInventory().setStackInSlot(in + 4, new ItemStack(Items.COPPER_INGOT, 2));
        be.getInventory().setStackInSlot(con, new ItemStack(
                PotatoSTOres.DEEPSLATE_COBALT_ORE.get().asItem(), 2));
        be.getInventory().setStackInSlot(con + 1, new ItemStack(Items.END_CRYSTAL, 2));
        long start4 = be.getEnergyStored();
        long injected4 = 0;
        for (int i = 0; i < 600; i++) {
            injected4 += fill(be, 12_000L);
            be.craftTick();
        }
        long spent4 = start4 + injected4 - be.getEnergyStored();
        check("星璨钢那条仍是每 tick 12000 FE（实扣 " + spent4 + "）", spent4 == 7_200_000L);
        ItemStack star = be.getInventory().getStackInSlot(out);
        check("星璨钢产物仍是 3 个",
                star.is(ModArmorItems.STAR_STEEL_INGOT.get()) && star.getCount() == 3);

        clear(level);
    }

    // ==================== 工具（照 ZF62/ZF111 那套） ====================

    private static void wipe(AlloySmelterBlockEntity be) {
        for (int slot = 0; slot < AlloySmelterBlockEntity.SLOT_COUNT; slot++) {
            be.getInventory().setStackInSlot(slot, ItemStack.EMPTY);
        }
    }

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
