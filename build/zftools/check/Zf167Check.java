package com.potatost.mod;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;
import java.util.UUID;

import com.mojang.authlib.GameProfile;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.SingleRecipeInput;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;

/**
 * ⚠⚠ <b>诊断探针（ZF167 临时文件，验证完必须删）</b>：空铝罐 + 可乐 + 饮料罐装机的端到端取证。
 *
 * <p><b>用户原话</b>：「先加个空铝罐配方；【】【铝粒】【】，【】【铝板】【】，【】【】【】
 * 合成2个空铝罐 熔炉/高炉烧制一个空铝罐产出5个铝粒；再加一个饮料罐装机…一个碳酸储罐（100MB）
 * 一个水储罐（1000mb）一个乙醇储罐（100mb 目前本mod没有乙醇 做个兼容别的mod的乙醇）
 * 三个输入槽 一个输出槽 耗电600fe/t 先做一个配方试试水 1.10mb碳酸+500mb水+2糖+1可可豆
 * +1空铝罐 5s产出1罐可乐 可乐是食物 但是食用音效用蜂蜜瓶的 食用后给予120s的急迫
 * 3s的生命恢复1 恢复3点饥饿值 9点饱和度 （食用后返还一个空铝罐）」。</p>
 *
 * <h2>判据只吃"外面看得见的行为"</h2>
 * <ul>
 *   <li><b>配方在不在</b>：从**真的配方管理器**里按产物找（{@code RecipeManager} 的 shaped /
 *       smelting / blasting），不看源码文本；</li>
 *   <li><b>机器跑一轮</b>：放一台真机器、真喂流体、真给料、**让它自己 tick 100 次**，
 *       然后看四个槽、三只罐、电量各差多少 —— 不看内部状态；</li>
 *   <li><b>可乐</b>：真调 {@code finishUsingItem}（原版吃的那条路），看饥饿/饱和/效果/背包；</li>
 *   <li><b>乙醇兼容</b>：那只罐的校验器认的是 {@code c:ethanol} 标签 ⇒ 负向对照（水/碳酸进不去）
 *       + 正向（装了沉浸工程时 IE 的乙醇进得去；这台机器上没装 IE，所以正向那条会打印"不在场"）。</li>
 * </ul>
 *
 * <p>跑法：{@code python build\zftools\_zf167_probe.py run}（挂载 → 起服 → 收报告 → 摘除）。</p>
 */
public final class Zf167Check {

    private static final String TAG = "[A167] ";
    private static final String DIR = "E:\\PotatoST\\build\\zftools\\check\\";
    private static final String REPORT = DIR + "zf167_罐装机取证.log";

    private static final int PX = 320;
    private static final int PY = 120;
    private static final int PZ = 320;

    private static boolean started;
    private static boolean finished;
    private static int failed;
    private static net.minecraft.server.MinecraftServer server;
    private static ServerLevel level;
    private static ServerPlayer player;
    private static BlockPos machinePos;
    private static long t0 = -1L;
    private static int phase;

    private static final StringBuilder report = new StringBuilder();

    /** 喂进去的电（mB 那种账：这一轮一共给了多少 FE）。 */
    private static long fedEnergy;
    /** 开跑那一刻的电量与罐里的液面。 */
    private static int energyAtStart;
    private static final int[] tankAtStart = new int[3];

    private Zf167Check() {
    }

    public static void register() {
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf167Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    // ============================================================
    //  开场：静态事实 + 配方存在性 + 搭台
    // ============================================================
    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        if (started) {
            return;
        }
        started = true;
        try {
            server = event.getServer();
            level = event.getServer().overworld();
            buildArena();

            GameProfile profile = new GameProfile(
                    UUID.nameUUIDFromBytes("zf167probe".getBytes(StandardCharsets.UTF_8)), "zf167probe");
            player = new ServerPlayer(event.getServer(), level, profile, ClientInformation.createDefault());
            net.minecraft.network.Connection conn = new net.minecraft.network.Connection(
                    net.minecraft.network.protocol.PacketFlow.SERVERBOUND);
            try {
                java.lang.reflect.Field channelField =
                        net.minecraft.network.Connection.class.getDeclaredField("channel");
                channelField.setAccessible(true);
                channelField.set(conn, new io.netty.channel.embedded.EmbeddedChannel());
            } catch (Throwable t) {
                say(TAG + "EmbeddedChannel 注入失败：" + t);
            }
            player.connection = new net.minecraft.server.network.ServerGamePacketListenerImpl(
                    event.getServer(), conn, player,
                    net.minecraft.server.network.CommonListenerCookie.createInitial(profile, false));
            player.moveTo(PX + 0.5D, PY + 1, PZ + 0.5D, 0.0F, 0.0F);

            sectionA();
            sectionBRecipes();
            sectionDStatic();

            // 放机器
            machinePos = new BlockPos(PX, PY + 1, PZ);
            level.setBlockAndUpdate(machinePos, ModBlocks.BEVERAGE_CANNING_MACHINE.get().defaultBlockState());
            failed += check("机器放得下、方块实体建起来了",
                    level.getBlockEntity(machinePos) instanceof BeverageCanningMachineBlockEntity);

            sectionCFluids();
            t0 = level.getGameTime();
            say(TAG + "① 试验场就绪，世界时间 = " + t0 + "（接下来 +20 装料 / +160 收账 / +200 负向对照）");
        } catch (Throwable t) {
            fail(t);
        }
    }

    // ============================================================
    //  A 三件东西注册了没
    // ============================================================
    private static void sectionA() {
        say(TAG + "======== A 注册与名字 ========");
        failed += check("A1 空铝罐注册名 = potato_s_t:empty_aluminum_can",
                idOf(ModItems.EMPTY_ALUMINUM_CAN.get()).equals("potato_s_t:empty_aluminum_can"),
                idOf(ModItems.EMPTY_ALUMINUM_CAN.get()));
        failed += check("A2 可乐注册名 = potato_s_t:cola",
                idOf(ModItems.COLA.get()).equals("potato_s_t:cola"), idOf(ModItems.COLA.get()));
        failed += check("A3 饮料罐装机注册名 = potato_s_t:beverage_canning_machine",
                idOf(ModBlocks.BEVERAGE_CANNING_MACHINE_ITEM.get())
                        .equals("potato_s_t:beverage_canning_machine"),
                idOf(ModBlocks.BEVERAGE_CANNING_MACHINE_ITEM.get()));
        String n1 = nameOf(ModItems.EMPTY_ALUMINUM_CAN.get());
        String n2 = nameOf(ModItems.COLA.get());
        failed += check("A4 两个名字在语言表里念得出", !n1.startsWith("item.") && !n2.startsWith("item."),
                n1 + " / " + n2);
        failed += check("A5 可乐的食用音效 = 蜂蜜瓶那一支（HONEY_DRINK）",
                ModItems.COLA.get().getEatingSound() == net.minecraft.sounds.SoundEvents.HONEY_DRINK
                        && ModItems.COLA.get().getDrinkingSound()
                        == net.minecraft.sounds.SoundEvents.HONEY_DRINK);
        // 食物数值：营养 3、饱和度修饰 1.5 ⇒ 9 点
        var food = new ItemStack(ModItems.COLA.get())
                .get(net.minecraft.core.component.DataComponents.FOOD);
        failed += check("A6 可乐是食物（FOOD 组件在）", food != null);
        if (food != null) {
            // ⚠ 这里比的是 **9.0**，不是注册时写的 1.5：
            //   `FoodProperties.Builder.build()` 会用 FoodConstants.saturationByModifier 把
            //   "修饰值"换算成**绝对点数**（= 饥饿 × 修饰 × 2 = 3 × 1.5 × 2 = 9）再存进 record，
            //   所以 `saturation()` 读出来就是 9.0（第一版拿 1.5 比 ⇒ 假红）。
            failed += check("A7 饥饿值 3 / 饱和度点数 9（注册时写的修饰值是 1.5）",
                    food.nutrition() == 3 && Math.abs(food.saturation() - 9.0F) < 1.0E-4F,
                    food.nutrition() + " / " + food.saturation());
            failed += check("A8 食物自带两条效果（急迫 2400t / 生命恢复 60t）",
                    food.effects().size() == 2, String.valueOf(food.effects().size()));
        }
    }

    // ============================================================
    //  B 配方（从真的配方管理器里找）
    // ============================================================
    private static void sectionBRecipes() {
        say(TAG + "======== B 四张配方 ========");
        var rm = level.getRecipeManager();

        // 空铝罐：shaped，产物 2 个
        var canId = ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "empty_aluminum_can");
        var canRecipe = rm.byKey(canId);
        failed += check("B1 空铝罐的合成配方在（" + canId + "）", canRecipe.isPresent());
        if (canRecipe.isPresent()) {
            ItemStack result = canRecipe.get().value().getResultItem(level.registryAccess());
            failed += check("B2 空铝罐配方产物 = 2 个空铝罐",
                    result.is(ModItems.EMPTY_ALUMINUM_CAN.get()) && result.getCount() == 2,
                    result.getCount() + " x " + idOf(result.getItem()));
        }

        // 熔炉 / 高炉：1 罐 → 5 铝粒
        for (String kind : List.of("smelting", "blasting")) {
            var rid = ResourceLocation.fromNamespaceAndPath(PotatoST.MODID,
                    "empty_aluminum_can_from_" + kind);
            var holder = rm.byKey(rid);
            failed += check("B3 " + kind + " 配方在（" + rid + "）", holder.isPresent());
            if (holder.isPresent()) {
                var recipe = holder.get().value();
                ItemStack out = recipe.getResultItem(level.registryAccess());
                failed += check("B4 " + kind + " 产物 = 5 个铝粒",
                        out.is(ModItems.ALUMINUM_NUGGET.get()) && out.getCount() == 5,
                        out.getCount() + " x " + idOf(out.getItem()));
                // ⚠ 别用 `recipe.matches(new SingleRecipeInput(...), level)`：`Recipe<?>` 的
                //   `matches` 参数是**捕获类型**（CAP#1），直接传会编译不过（第一版就栽在这）。
                //   判"输入是不是空铝罐"用原料表那张 Ingredient 自己 test，语义一样、还更直白。
                boolean ok = !recipe.getIngredients().isEmpty()
                        && recipe.getIngredients().get(0)
                                .test(new ItemStack(ModItems.EMPTY_ALUMINUM_CAN.get()));
                failed += check("B5 " + kind + " 的输入真的是空铝罐", ok);
            }
        }

        // 机器本体配方
        var rid = ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "beverage_canning_machine");
        failed += check("B6 机器本体的合成配方在", rm.byKey(rid).isPresent());

        // 机器内部那一条（Java 表）
        var found = CanningMachineRecipes.find(new ItemStack(Items.SUGAR, 2),
                new ItemStack(Items.COCOA_BEANS), new ItemStack(ModItems.EMPTY_ALUMINUM_CAN.get()));
        failed += check("B7 罐装机那一条配方命中（2 糖 + 1 可可豆 + 1 空铝罐）", found != null);
        if (found != null) {
            failed += check("B8 配方数值：10 碳酸 / 500 水 / 0 乙醇 / 100 tick / 600 FE/t",
                    found.carbonicMb() == 10 && found.waterMb() == 500 && found.ethanolMb() == 0
                            && found.durationTicks() == 100 && found.energyPerTick() == 600,
                    found.carbonicMb() + "/" + found.waterMb() + "/" + found.ethanolMb() + " "
                            + found.durationTicks() + "t " + found.energyPerTick() + "FE/t");
            failed += check("B9 一轮总共 60,000 FE", found.totalEnergy() == 60000,
                    String.valueOf(found.totalEnergy()));
        }
        // 反向：换掉一样料就不该命中
        failed += check("B10 负向：换成面包就命中不了",
                CanningMachineRecipes.find(new ItemStack(Items.BREAD, 2),
                        new ItemStack(Items.COCOA_BEANS),
                        new ItemStack(ModItems.EMPTY_ALUMINUM_CAN.get())) == null);
        failed += check("B11 负向：只有 1 个糖也不命中（要 2 个）",
                CanningMachineRecipes.find(new ItemStack(Items.SUGAR, 1),
                        new ItemStack(Items.COCOA_BEANS),
                        new ItemStack(ModItems.EMPTY_ALUMINUM_CAN.get())) == null);
    }

    // ============================================================
    //  D 乙醇兼容（静态 + 负向）
    // ============================================================
    private static void sectionDStatic() {
        say(TAG + "======== D 乙醇罐认的是 c:ethanol 标签 ========");
        failed += check("D1 标签名 = c:ethanol",
                BeverageCanningMachineBlockEntity.ETHANOL_TAG.location().toString().equals("c:ethanol"),
                BeverageCanningMachineBlockEntity.ETHANOL_TAG.location().toString());
        // 机器还没放，先建一台临时的来问校验器（放完再问一次，见 C 组）
        var probe = new BeverageCanningMachineBlockEntity(machinePos == null
                ? new BlockPos(PX, PY + 1, PZ) : machinePos,
                ModBlocks.BEVERAGE_CANNING_MACHINE.get().defaultBlockState());
        boolean ethTakesWater = probe.getTank(BeverageCanningMachineBlockEntity.TANK_ETHANOL)
                .isFluidValid(new FluidStack(Fluids.WATER, 1));
        boolean ethTakesCarbonic = probe.getTank(BeverageCanningMachineBlockEntity.TANK_ETHANOL)
                .isFluidValid(new FluidStack(ModFluids.CARBONIC_ACID.get(), 1));
        boolean waterTakesCarbonic = probe.getTank(BeverageCanningMachineBlockEntity.TANK_WATER)
                .isFluidValid(new FluidStack(ModFluids.CARBONIC_ACID.get(), 1));
        boolean carbonicTakesWater = probe.getTank(BeverageCanningMachineBlockEntity.TANK_CARBONIC)
                .isFluidValid(new FluidStack(Fluids.WATER, 1));
        failed += check("D2 乙醇罐**不收**水（负向）", !ethTakesWater);
        failed += check("D3 乙醇罐**不收**碳酸（负向）", !ethTakesCarbonic);
        failed += check("D4 水罐**不收**碳酸（负向）", !waterTakesCarbonic);
        failed += check("D5 碳酸罐**不收**水（负向）", !carbonicTakesWater);
        // 装了沉浸工程时，c:ethanol 标签里就有 IE 的乙醇 ⇒ 这只罐就该收
        var tagged = level.registryAccess().registryOrThrow(net.minecraft.core.registries.Registries.FLUID)
                .getTag(BeverageCanningMachineBlockEntity.ETHANOL_TAG);
        int n = tagged.map(t -> (int) t.size()).orElse(0);
        say(TAG + "      c:ethanol 标签里现在有 " + n + " 种流体"
                + (n == 0 ? "（本探针环境没装沉浸工程 ⇒ 正向那条只能静态看）" : ""));
        if (n > 0) {
            var first = tagged.get().iterator().next().value();
            failed += check("D6 乙醇罐**收**标签里的那种流体（" + idOf(first) + "）",
                    probe.getTank(BeverageCanningMachineBlockEntity.TANK_ETHANOL)
                            .isFluidValid(new FluidStack(first, 1)));
        }
    }

    // ============================================================
    //  C 三只罐：容量与互斥
    // ============================================================
    private static void sectionCFluids() {
        say(TAG + "======== C 三只罐的容量与灌入 ========");
        var be = machine();
        if (be == null) {
            return;
        }
        failed += check("C1 容量：碳酸 100 / 水 1000 / 乙醇 100 mB",
                be.getTank(0).getCapacity() == 100 && be.getTank(1).getCapacity() == 1000
                        && be.getTank(2).getCapacity() == 100,
                be.getTank(0).getCapacity() + "/" + be.getTank(1).getCapacity()
                        + "/" + be.getTank(2).getCapacity());
        failed += check("C2 储能 = 12,000 FE（20 tick 的钱）",
                BeverageCanningMachineBlockEntity.MAX_ENERGY == 12000,
                String.valueOf(BeverageCanningMachineBlockEntity.MAX_ENERGY));

        int c = be.getFluidHandler().fill(new FluidStack(ModFluids.CARBONIC_ACID.get(), 100), IFluidHandler.FluidAction.EXECUTE);
        int w = be.getFluidHandler().fill(new FluidStack(Fluids.WATER, 1000), IFluidHandler.FluidAction.EXECUTE);
        say(TAG + "      灌入结果：碳酸 +" + c + " mB，水 +" + w + " mB");
        failed += check("C3 碳酸灌满 100 mB", c == 100 && be.getTank(0).getFluidAmount() == 100);
        failed += check("C4 水灌满 1000 mB", w == 1000 && be.getTank(1).getFluidAmount() == 1000);
        // 多灌的部分应当被拒（容量到顶）
        int extra = be.getFluidHandler().fill(new FluidStack(Fluids.WATER, 500), IFluidHandler.FluidAction.EXECUTE);
        failed += check("C5 水罐满了之后不再收（多灌 500 只进 " + extra + "）", extra == 0);
        // 输入罐只进不出
        var drained = be.getFluidHandler().drain(100, IFluidHandler.FluidAction.EXECUTE);
        failed += check("C6 三只罐都是**只进不出**（drain 拿到 " + drained.getAmount() + " mB）",
                drained.isEmpty());

        say(TAG + "======== C 装料（2 糖 + 1 可可豆 + 1 空铝罐）=======");
        be.getInventory().setStackInSlot(BeverageCanningMachineBlockEntity.SLOT_SUGAR,
                new ItemStack(Items.SUGAR, 2));
        be.getInventory().setStackInSlot(BeverageCanningMachineBlockEntity.SLOT_COCOA,
                new ItemStack(Items.COCOA_BEANS, 1));
        be.getInventory().setStackInSlot(BeverageCanningMachineBlockEntity.SLOT_CAN,
                new ItemStack(ModItems.EMPTY_ALUMINUM_CAN.get(), 1));
        // 红石负向：旁边放个红石块 ⇒ 应当 DISABLED
        level.setBlockAndUpdate(machinePos.offset(1, 0, 0), Blocks.REDSTONE_BLOCK.defaultBlockState());
        // 先只记下起点，真正的跑在 tick 里
        energyAtStart = be.getEnergyStorage().getEnergyStored();
        for (int i = 0; i < 3; i++) {
            tankAtStart[i] = be.getTank(i).getFluidAmount();
        }
        say(TAG + "      起点：能量 " + energyAtStart + " FE，罐 " + tankAtStart[0] + "/"
                + tankAtStart[1] + "/" + tankAtStart[2] + " mB");
    }

    // ============================================================
    //  节拍
    // ============================================================
    @SubscribeEvent
    public static void onServerTick(ServerTickEvent.Post event) {
        if (!started || finished || t0 < 0L) {
            return;
        }
        long dt = level.getGameTime() - t0;
        try {
            var be = machine();
            if (be == null) {
                return;
            }
            // ① 红石阶段（+20 ~ +60）：应当停机、进度不动
            if (phase == 0 && dt >= 20L) {
                phase = 1;
                say(TAG + "======== C 红石信号 = 停机 ========");
                failed += check("C7 红石信号下状态 = DISABLED（0）",
                        be.getStatus() == BeverageCanningMachineBlockEntity.STATUS_DISABLED,
                        String.valueOf(be.getStatus()));
                level.removeBlock(machinePos.offset(1, 0, 0), false);
            } else if (phase == 1 && dt >= 30L) {
                phase = 2;
                failed += check("C8 撤掉红石后不再停机（状态 " + be.getStatus() + "）",
                        be.getStatus() != BeverageCanningMachineBlockEntity.STATUS_DISABLED);
            } else if (phase == 2) {
                // ② 供电阶段：每 tick 喂 600 FE（模拟发电机），刚好够这台机器吃
                int accepted = be.getEnergyStorage().receiveEnergy(600, false);
                fedEnergy += accepted;
                if (dt >= 160L) {
                    phase = 3;
                    sectionCResult(be);
                }
            } else if (phase == 3 && dt >= 180L) {
                // ③ 负向对照：把水抽干（换一台新机器太麻烦，直接把水罐的水抽掉是不可能的
                //    —— 输入罐只进不出 ⇒ 改放第三台，见 sectionENegatives）
                phase = 4;
                sectionENegatives();
            } else if (phase == 4 && dt >= 200L) {
                phase = 5;
                sectionECola();
            } else if (phase == 5 && dt >= 210L) {
                phase = 6;
                sectionENegativeStates();
            } else if (phase == 6 && dt >= 220L) {
                phase = 7;
                finish(event.getServer());
            }
        } catch (Throwable t) {
            fail(t);
        }
    }

    /** 一轮跑完的账。 */
    private static void sectionCResult(BeverageCanningMachineBlockEntity be) {
        say(TAG + "======== C 跑完一轮的账 ========");
        ItemStack out = be.getInventory().getStackInSlot(BeverageCanningMachineBlockEntity.SLOT_OUTPUT);
        failed += check("C9 产出 1 罐可乐（" + out.getCount() + " x " + idOf(out.getItem()) + "）",
                out.is(ModItems.COLA.get()) && out.getCount() == 1);
        failed += check("C10 三个输入槽都扣干净了（糖 "
                        + be.getInventory().getStackInSlot(0).getCount() + " / 可可豆 "
                        + be.getInventory().getStackInSlot(1).getCount() + " / 空铝罐 "
                        + be.getInventory().getStackInSlot(2).getCount() + "）",
                be.getInventory().getStackInSlot(0).isEmpty()
                        && be.getInventory().getStackInSlot(1).isEmpty()
                        && be.getInventory().getStackInSlot(2).isEmpty());
        int dc = tankAtStart[0] - be.getTank(0).getFluidAmount();
        int dw = tankAtStart[1] - be.getTank(1).getFluidAmount();
        int de = tankAtStart[2] - be.getTank(2).getFluidAmount();
        failed += check("C11 碳酸正好扣 10 mB（实扣 " + dc + "）", dc == 10);
        failed += check("C12 水正好扣 500 mB（实扣 " + dw + "）", dw == 500);
        failed += check("C13 乙醇一点没动（实扣 " + de + "）", de == 0);
        long expectFed = 100L * 600L;
        int stored = be.getEnergyStorage().getEnergyStored();
        say(TAG + "      喂进去的电 = " + fedEnergy + " FE（一轮应当正好 "
                + expectFed + "），机器里还剩 " + stored + " FE");
        failed += check("C14 喂进去的电 ≥ 一轮的钱（" + fedEnergy + " ≥ " + expectFed + "）",
                fedEnergy >= expectFed);
        // 账目：喂进去的总量只可能变成"被机器吃掉"或"还留在缓冲里"（没有别的去处）
        failed += check("C15 净耗电 = 60,000 FE（喂进去 " + fedEnergy + " − 缓冲里剩 " + stored + "）",
                fedEnergy - stored == expectFed,
                "实得 " + (fedEnergy - stored));
        failed += check("C16 进度回到 0（这一轮结束了）", be.getProgress() == 0,
                String.valueOf(be.getProgress()));
    }

    // ============================================================
    //  E 负向对照：缺流体 / 缺电 / 输出满
    // ============================================================
    private static void sectionENegatives() {
        say(TAG + "======== E 负向对照 ========");
        var be = machine();
        if (be == null) {
            return;
        }
        // 把它清空，重新装一批料，但**只给碳酸、不给水**
        be.getInventory().setStackInSlot(0, new ItemStack(Items.SUGAR, 2));
        be.getInventory().setStackInSlot(1, new ItemStack(Items.COCOA_BEANS, 1));
        be.getInventory().setStackInSlot(2, new ItemStack(ModItems.EMPTY_ALUMINUM_CAN.get(), 1));
        // 水罐里还剩 500 mB（上一轮没用完）⇒ 这一条改为"把水罐灌满到 1000 后再看"没意义，
        // 所以换个法子：把水抽走的接口不存在（只进不出）⇒ 直接看**碳酸不够**那一种
        // （碳酸罐上一轮只剩 90，这一轮要 10，够）… 于是这一组改成验"缺电"与"输出满"。
        int before = be.getTank(0).getFluidAmount();
        say(TAG + "      （输入罐只进不出 ⇒ 没法把水抽掉，所以'缺流体'改由缺电/输出满两条负向来验；"
                + "碳酸罐现有 " + before + " mB）");
        failed += check("E1 料齐 + 流体齐 ⇒ 状态不是'缺流体'（" + be.getStatus() + "）",
                be.getStatus() != BeverageCanningMachineBlockEntity.STATUS_NO_FLUID);
    }

    /** 可乐：真吃一罐。 */
    private static void sectionECola() {
        say(TAG + "======== E 可乐：吃一罐 ========");
        player.getInventory().clearContent();
        player.getFoodData().setFoodLevel(10);
        player.getFoodData().setSaturation(0.0F);
        player.removeAllEffects();
        ItemStack cola = new ItemStack(ModItems.COLA.get(), 1);
        player.getInventory().setItem(0, cola);
        player.getInventory().selected = 0;

        ItemStack result = cola.getItem().finishUsingItem(cola, level, player);
        int food = player.getFoodData().getFoodLevel();
        float sat = player.getFoodData().getSaturationLevel();
        var haste = player.getEffect(MobEffects.DIG_SPEED);
        var regen = player.getEffect(MobEffects.REGENERATION);
        say(TAG + "      饥饿 10 → " + food + "，饱和度 0 → " + sat
                + "，急迫 " + (haste == null ? "无" : haste.getDuration() + "t")
                + "，生命恢复 " + (regen == null ? "无" : regen.getDuration() + "t"));
        failed += check("E2 恢复 3 点饥饿值（10 → 13）", food == 13, String.valueOf(food));
        failed += check("E3 恢复 9 点饱和度（0 → 9）", Math.abs(sat - 9.0F) < 1.0E-4F,
                String.valueOf(sat));
        failed += check("E4 急迫 120 秒（2400 tick）", haste != null && haste.getDuration() == 2400,
                haste == null ? "没有" : String.valueOf(haste.getDuration()));
        failed += check("E5 生命恢复 I 3 秒（60 tick）", regen != null && regen.getDuration() == 60
                && regen.getAmplifier() == 0, regen == null ? "没有" : String.valueOf(regen.getDuration()));
        // ⚠ 返还的容器是**返回值**，不是自动塞进背包：原版 `Player.eat` 在
        //   `usingConvertsTo` 命中且手上那栈被吃空时，把容器**当返回值交回给调用者**
        //   （真正的使用循环会拿它替换手上那一格）。所以这里判"返回值就是空铝罐" ✓，
        //   顺便也认"背包里出现了空铝罐"（万一以后改成直接进背包）。
        boolean hasCan = result.is(ModItems.EMPTY_ALUMINUM_CAN.get());
        for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
            if (player.getInventory().getItem(i).is(ModItems.EMPTY_ALUMINUM_CAN.get())) {
                hasCan = true;
            }
        }
        failed += check("E6 吃完返还一个空铝罐（返回值就是它，走的原版 usingConvertsTo）",
                hasCan, "finishUsingItem 返回 " + (result.isEmpty() ? "空栈" : idOf(result.getItem())));
        failed += check("E7 可乐本身被消耗掉了（手上那格已空）",
                player.getInventory().getItem(0).isEmpty()
                        || player.getInventory().getItem(0).is(ModItems.EMPTY_ALUMINUM_CAN.get()));
    }

    /** 输出满 / 缺电 两条负向：另起一台机器来问状态码。 */
    private static void sectionENegativeStates() {
        say(TAG + "======== E 负向：输出满 / 缺电 ========");
        BlockPos p2 = machinePos.offset(3, 0, 0);
        level.setBlockAndUpdate(p2, ModBlocks.BEVERAGE_CANNING_MACHINE.get().defaultBlockState());
        if (!(level.getBlockEntity(p2) instanceof BeverageCanningMachineBlockEntity be2)) {
            failed += check("E8 第二台机器建起来了", false);
            return;
        }
        failed += check("E8 第二台机器建起来了", true);
        // 输出槽塞满石头 ⇒ 料齐、流体缺、电也缺，但先是"缺电"（顺序：电 → 流体 → 输出）
        be2.getInventory().setStackInSlot(BeverageCanningMachineBlockEntity.SLOT_OUTPUT,
                new ItemStack(Items.STONE, 64));
        be2.getInventory().setStackInSlot(0, new ItemStack(Items.SUGAR, 2));
        be2.getInventory().setStackInSlot(1, new ItemStack(Items.COCOA_BEANS, 1));
        be2.getInventory().setStackInSlot(2, new ItemStack(ModItems.EMPTY_ALUMINUM_CAN.get(), 1));
        be2.getFluidHandler().fill(new FluidStack(ModFluids.CARBONIC_ACID.get(), 100),
                IFluidHandler.FluidAction.EXECUTE);
        be2.getFluidHandler().fill(new FluidStack(Fluids.WATER, 1000),
                IFluidHandler.FluidAction.EXECUTE);
        be2.getEnergyStorage().receiveEnergy(12000, false);
        // 手动推进一次（不等 100 tick）：调一次 tick 就该在"输出满"停住
        BeverageCanningMachineBlockEntity.tick(level, p2, level.getBlockState(p2), be2);
        failed += check("E9 输出槽被石头占着 ⇒ 状态 = OUTPUT_FULL（4），实测 " + be2.getStatus(),
                be2.getStatus() == BeverageCanningMachineBlockEntity.STATUS_OUTPUT_FULL);
        // 把输出槽清空、料留着 ⇒ 这一 tick 应当开跑（RUNNING）
        be2.getInventory().setStackInSlot(BeverageCanningMachineBlockEntity.SLOT_OUTPUT, ItemStack.EMPTY);
        BeverageCanningMachineBlockEntity.tick(level, p2, level.getBlockState(p2), be2);
        failed += check("E10 输出腾空后立刻开跑（状态 " + be2.getStatus() + "）",
                be2.getStatus() == BeverageCanningMachineBlockEntity.STATUS_RUNNING);
        // 把电抽干（机器只收不出 ⇒ 用一台新的问"缺电"）：新机器、有料有流体、不给电
        BlockPos p3 = machinePos.offset(0, 0, 3);
        level.setBlockAndUpdate(p3, ModBlocks.BEVERAGE_CANNING_MACHINE.get().defaultBlockState());
        if (level.getBlockEntity(p3) instanceof BeverageCanningMachineBlockEntity be3) {
            be3.getInventory().setStackInSlot(0, new ItemStack(Items.SUGAR, 2));
            be3.getInventory().setStackInSlot(1, new ItemStack(Items.COCOA_BEANS, 1));
            be3.getInventory().setStackInSlot(2, new ItemStack(ModItems.EMPTY_ALUMINUM_CAN.get(), 1));
            be3.getFluidHandler().fill(new FluidStack(ModFluids.CARBONIC_ACID.get(), 100),
                    IFluidHandler.FluidAction.EXECUTE);
            be3.getFluidHandler().fill(new FluidStack(Fluids.WATER, 1000),
                    IFluidHandler.FluidAction.EXECUTE);
            BeverageCanningMachineBlockEntity.tick(level, p3, level.getBlockState(p3), be3);
            failed += check("E11 没电 ⇒ 状态 = NO_POWER（3），实测 " + be3.getStatus(),
                    be3.getStatus() == BeverageCanningMachineBlockEntity.STATUS_NO_POWER);
            // 给电但不给流体：新机器、有料有电、罐是空的
            BlockPos p4 = machinePos.offset(0, 0, -3);
            level.setBlockAndUpdate(p4, ModBlocks.BEVERAGE_CANNING_MACHINE.get().defaultBlockState());
            if (level.getBlockEntity(p4) instanceof BeverageCanningMachineBlockEntity be4) {
                be4.getInventory().setStackInSlot(0, new ItemStack(Items.SUGAR, 2));
                be4.getInventory().setStackInSlot(1, new ItemStack(Items.COCOA_BEANS, 1));
                be4.getInventory().setStackInSlot(2, new ItemStack(ModItems.EMPTY_ALUMINUM_CAN.get(), 1));
                be4.getEnergyStorage().receiveEnergy(12000, false);
                BeverageCanningMachineBlockEntity.tick(level, p4, level.getBlockState(p4), be4);
                failed += check("E12 有料有电但罐是空的 ⇒ 状态 = NO_FLUID（20），实测 " + be4.getStatus(),
                        be4.getStatus() == BeverageCanningMachineBlockEntity.STATUS_NO_FLUID);
                failed += check("E13 「缺流体」用的是新号 20（没蹭液压机的 6）",
                        BeverageCanningMachineBlockEntity.STATUS_NO_FLUID == 20);
            }
        }
    }

    // ============================================================
    //  工具
    // ============================================================
    private static BeverageCanningMachineBlockEntity machine() {
        return level.getBlockEntity(machinePos) instanceof BeverageCanningMachineBlockEntity be ? be : null;
    }

    private static String idOf(net.minecraft.world.item.Item item) {
        return BuiltInRegistries.ITEM.getKey(item).toString();
    }

    private static String idOf(net.minecraft.world.level.material.Fluid fluid) {
        return BuiltInRegistries.FLUID.getKey(fluid).toString();
    }

    private static String nameOf(net.minecraft.world.item.Item item) {
        String key = new ItemStack(item).getDescriptionId();
        return net.minecraft.locale.Language.getInstance().getOrDefault(key, key);
    }

    private static void buildArena() {
        level.getChunkAt(new BlockPos(PX, PY, PZ));
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                level.setChunkForced((PX >> 4) + dx, (PZ >> 4) + dz, true);
            }
        }
        for (int dx = -8; dx <= 8; dx++) {
            for (int dz = -8; dz <= 8; dz++) {
                level.setBlockAndUpdate(new BlockPos(PX + dx, PY, PZ + dz),
                        Blocks.OAK_PLANKS.defaultBlockState());
                for (int dy = 1; dy <= 4; dy++) {
                    level.setBlockAndUpdate(new BlockPos(PX + dx, PY + dy, PZ + dz),
                            Blocks.AIR.defaultBlockState());
                }
            }
        }
        say(TAG + "试验场：悬空木平台 " + new BlockPos(PX, PY, PZ) + "（17×17）");
    }

    private static void fail(Throwable t) {
        say(TAG + "exception: " + t);
        java.io.StringWriter sw = new java.io.StringWriter();
        t.printStackTrace(new java.io.PrintWriter(sw));
        for (String line : sw.toString().split("\n")) {
            say(TAG + "    " + line);
        }
        failed++;
        finish(server);
    }

    private static int check(String name, boolean ok) {
        return check(name, ok, "");
    }

    private static int check(String name, boolean ok, String detail) {
        say(TAG + (ok ? "  [OK]   " : "  [FAIL] ") + name + (detail.isEmpty() ? "" : "   实测：" + detail));
        return ok ? 0 : 1;
    }

    private static void say(String line) {
        System.out.println(line);
        report.append(line).append('\n');
    }

    private static void flush() {
        try {
            Files.write(Paths.get(REPORT), report.toString().getBytes(StandardCharsets.UTF_8));
        } catch (Throwable t) {
            System.out.println(TAG + "report write failed: " + t);
        }
    }

    private static void finish(net.minecraft.server.MinecraftServer server) {
        if (finished) {
            return;
        }
        finished = true;
        say(TAG + "verdict: " + (failed == 0 ? "ALL OK" : "**" + failed + " FAILED**"));
        flush();
        say(TAG + "report: " + REPORT);
        say(TAG + "done, halting server");
        if (server != null) {
            server.halt(false);
        }
    }
}
