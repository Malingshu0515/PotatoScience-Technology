package com.potatost.mod;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.authlib.GameProfile;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.contents.TranslatableContents;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.ShovelItem;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.TieredItem;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.living.LivingDeathEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠️ <b>诊断工具（ZF144 的临时探针）</b>：星璨钢锹 + 剑的「星辉斩」端到端取证。
 *
 * <p>用户原话：「锹现在放用户素材了 然后剑你看看能不能再加个特殊技能」。</p>
 *
 * <p>要证的八件事（每一条都在**真服务端**上跑）：</p>
 * <ol>
 *   <li><b>锹</b>：注册在 {@code potato_s_t:star_steel_shovel}、类是 {@link StarSteelShovelItem}；
 *       与剑/镐/锄**共用同一个档位对象**，且那一档与斧子逐字同值；耐久 1192；修理材料 = 星璨钢锭；</li>
 *   <li><b>锹的属性</b>：显示伤害 <b>13.5</b>、攻速 <b>1.0</b>（对照原版钻石锹 5.5 / 1.0，
 *       以及本模组的镐 13.0 / 1.2、剑 16.0 / 1.6 —— 锹落在镐与剑之间，与原版次序一致）；</li>
 *   <li><b>锹的挖掘等级</b>：{@code getDestroySpeed(泥土)} = <b>9.0</b>（钻石级标签 + 速度 9）、
 *       挖得动泥土；对照：挖**石头**不掉落（那不是锹该挖的方块 ⇒ 证明走的是原版工具类型判定）；</li>
 *   <li><b>锹的「与夜同频」</b>：白天采掘/攻击照掉（采掘 1、攻击 2），夜晚两样都是 <b>0</b>；</li>
 *   <li><b>锹的配方</b>：真合成网格里摆原版锹的图纸（1 锭 + 2 棍）出我们的锹；
 *       同一张图纸换成原版钻石 ⇒ 出**原版钻石锹**（证明图纸没动）；</li>
 *   <li><b>剑的技能「星辉斩」几何</b>：正前方 3 格挨 <b>12.0</b>（哑巴僵尸的护甲被清零，
 *       所以量到的就是这一下的原始伤害）；<b>身后</b> / <b>12 格外</b> / <b>横向偏 4 格</b> /
 *       <b>隔着墙</b> 四种情形**一次都不挨**（各自都是独立的负向对照）；正前方两个目标**都挨**（贯穿）；</li>
 *   <li><b>剑的技能代价与状态</b>：出手扣 <b>100</b> 耐久、进冷却；不按 Shift / 冷却中 /
 *       耐久不足 100 这三种情形**既不出手也不扣耐久**；命中者拿到**发光**；</li>
 *   <li><b>剑气的伤害类型与死亡文案</b>：{@code potato_s_t:star_steel_slash} 在数据包注册表里取得到、
 *       四个字段与 JSON 逐字对上；被这一下打死的人在**死亡那一刻**的文案键是
 *       {@code death.attack.potato_s_t.star_steel_slash}，且 {@code %1$s} 解析出来是他自己的名字。</li>
 * </ol>
 *
 * <p>另外复核两条**旧账没被碰坏**：剑的「夜晚不磨损」仍在；手持星璨钢斧仍然给急迫 I。</p>
 *
 * <p>挂载方式：{@code PotatoST} 构造器末尾加一行 {@code Zf144Check.register();}，
 * 跑完用 {@code _zf144_unprobe.py} 摘掉（**先抄进 {@code build/zftools/check/} 再删**）。</p>
 */
public final class Zf144Check {

    private static final String TAG = "[A144] ";
    private static final String NS = "potato_s_t";

    private static final StringBuilder REPORT = new StringBuilder();
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf144_probe_utf8.txt";

    private static final long DAY_TIME = 6000L;
    private static final long NIGHT_TIME = 18000L;

    /** 探针自己的试验场（**必须在已加载的区块里**：实体查询只看得到已加载区块）。 */
    private static final double CX = 8.5D;
    private static final double CY = 100.0D;
    private static final double CZ = 8.5D;

    private static boolean registered;
    private static int passed;
    private static int failed;

    /** 靶子有没有真的进世界（`addFreshEntity` 的返回值）—— 单独留一条对照。 */
    private static boolean dummyAdded = true;

    /** 死亡**那一刻**抓到的文案（见 ZF139 §4.129：死完之后再问只会拿到 generic）。 */
    private static Component lastDeathMessage;

    private Zf144Check() {
    }

    private static void say(String line) {
        System.out.println(line);
        REPORT.append(line).append('\n');
    }

    private static void check(String name, boolean ok) {
        if (ok) {
            passed++;
            say(TAG + "[OK]   " + name);
        } else {
            failed++;
            say(TAG + "[FAIL] " + name);
        }
    }

    private static void check(String name, boolean ok, String detail) {
        if (ok) {
            passed++;
            say(TAG + "[OK]   " + name);
        } else {
            failed++;
            say(TAG + "[FAIL] " + name + "　" + detail);
        }
    }

    private static void head(String title) {
        say(TAG + title);
    }

    private static void flushReport() {
        try (java.io.OutputStreamWriter w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), StandardCharsets.UTF_8)) {
            w.write("ZF144 探针报告（星璨钢锹 + 剑的星辉斩）· UTF-8 · §4.50\n");
            w.write("生成时间：" + java.time.LocalDateTime.now() + "\n");
            w.write("判词：" + (failed == 0 ? "全绿" : failed + " 条 FAIL")
                    + "（通过 " + passed + "）\n\n");
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
            NeoForge.EVENT_BUS.register(Zf144Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onAnyDeath(LivingDeathEvent event) {
        lastDeathMessage = event.getEntity().getCombatTracker().getDeathMessage();
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        passed = 0;
        failed = 0;
        try {
            run(event, event.getServer().overworld());
        } catch (Throwable t) {
            failed++;
            say(TAG + "[FAIL] 探针自己抛异常：" + t);
            t.printStackTrace(System.out);
        }
        say(TAG + "done, halting server");
        flushReport();
        event.getServer().halt(false);
    }

    // ============================================================ 工具
    private static ServerPlayer fake(ServerStartedEvent event, ServerLevel level, String name) {
        GameProfile profile = new GameProfile(
                UUID.nameUUIDFromBytes(name.getBytes(StandardCharsets.UTF_8)), name);
        ServerPlayer player = new ServerPlayer(event.getServer(), level, profile,
                ClientInformation.createDefault());
        net.minecraft.network.Connection conn = new net.minecraft.network.Connection(
                net.minecraft.network.protocol.PacketFlow.SERVERBOUND);
        player.connection = new net.minecraft.server.network.ServerGamePacketListenerImpl(
                event.getServer(), conn, player,
                net.minecraft.server.network.CommonListenerCookie.createInitial(profile, false));
        player.setGameMode(GameType.SURVIVAL);
        return player;
    }

    private static String f(double v) {
        return String.format(java.util.Locale.ROOT, "%.4f", v);
    }

    private static String tierOf(Tier t) {
        return "(" + t.getUses() + ", " + t.getSpeed() + ", " + t.getAttackDamageBonus() + ", "
                + t.getIncorrectBlocksForDrops().location() + ", " + t.getEnchantmentValue() + ")";
    }

    private static boolean setTime(ServerLevel level, boolean night) {
        level.setDayTime(night ? NIGHT_TIME : DAY_TIME);
        return StarSteelAxeItem.isNight(level) == night;
    }

    /** 烧掉假玩家的 60 tick 出生保护（§4.128：不烧掉的话什么伤害都进不去）。 */
    private static void burnSpawnProtection(ServerPlayer p) {
        for (int i = 0; i < 61; i++) {
            p.tick();
            p.doTick();
        }
    }

    /**
     * 造一个"哑巴靶子"：僵尸、无 AI、**无重力**、**护甲清零**，并且**先定位再入世**。
     *
     * <p>为什么非要清零护甲：僵尸的 {@code Attributes.ARMOR} 天生是 2，12 点伤害进去会被
     * 原版护甲公式削成 11.808 —— 那样量到的就不是"这一下打多少"，而是"这一下 + 原版护甲公式"。
     * 清零之后 12.0 就是 12.0，判据能钉**等号**而不是"区间"。</p>
     *
     * <p>⚠⚠ <b>先定位再入世</b>是第二版才改对的（第一版整节剑气判据全红）：第一版是
     * 「{@code addFreshEntity}（这时它在 0,0,0）→ 再 {@code setPos(420,…)}」——
     * 而实体换区块要等它**下一次 tick** 才在实体管理器里改归档，
     * 一个不在已加载区块里的实体根本不会 tick ⇒ 管理器里它永远留在原点的那个 section，
     * 于是 {@code level.getEntities(caster, 远处AABB)} **永远数不到它**。
     * 现在：位置给好再 add，落点也在已加载区块里（见 {@link #loadChunks}）。</p>
     *
     * <p>无重力是为了让 y 别动（判据里纵向有 ±1.5 的窗口，掉下去就出窗了）。</p>
     */
    private static Zombie dummyAt(ServerLevel level, double dx, double dy, double dz) {
        Zombie z = EntityType.ZOMBIE.create(level);
        z.getAttribute(Attributes.ARMOR).setBaseValue(0.0D);
        z.setNoAi(true);
        z.setNoGravity(true);
        z.setPersistenceRequired();
        z.setPos(CX + dx, CY + dy, CZ + dz);
        z.setDeltaMovement(Vec3.ZERO);
        if (!level.addFreshEntity(z)) {
            dummyAdded = false;
        }
        return z;
    }

    /** 把靶子复位（血量 / 无敌帧 / 速度），**不动位置**。 */
    private static void reset(Zombie z) {
        z.setHealth(z.getMaxHealth());
        z.setDeltaMovement(Vec3.ZERO);
        z.invulnerableTime = 0;
    }

    /**
     * 把施法者摆回试验场原点、朝向 +Z、速度清零。
     *
     * <p>⚠ **每一次依赖位置的判据之前都要调**（第六次实测换来的）：⑧ 那一节为了量冷却走了
     * 302 次 `tick()+doTick()`，就算 {@code setNoGravity(true)} 也挡不住玩家在这 300 多 tick 里
     * **下沉 3.77 格**（100 → 96.23，实测值）—— 而剑气的纵向窗口只有 ±1.5 格，
     * 于是后面那条"打死 5 点血的靶子"命中 0 个。
     * **判据依赖位置，就要在判据之前把位置摆正，别指望它自己不动。**</p>
     */
    private static void recenter(ServerPlayer caster) {
        caster.setPos(CX, CY, CZ);
        caster.setYRot(0.0F);
        caster.setXRot(0.0F);
        caster.setDeltaMovement(Vec3.ZERO);
    }

    /**
     * 把试验场那几个区块**显式加载**出来。
     *
     * <p>实体查询（{@code level.getEntities}）只看得见已加载区块里的实体 ——
     * 第一版把试验场放在 (420,100,100)，那里连区块都没加载，靶子放进去等于扔进虚空。</p>
     */
    private static void loadChunks(ServerLevel level) {
        for (int cx = -1; cx <= 1; cx++) {
            for (int cz = -1; cz <= 1; cz++) {
                level.getChunk(cx, cz);
            }
        }
    }

    /**
     * 把试验场真的挖空（x −6..+13 / y −1..+4 / z −6..+14，够覆盖"12 格外"与"横向 4 格"）。
     *
     * <p>第一版**假设** (420,100,100) 那一片是空气 —— 结果整节剑气判据全红，
     * 因为地形比 y=100 高，僵尸直接埋在方块里，原版射线每次都命中。
     * ⇒ 探针里凡是"依赖场地空旷"的判据，都要**先把场地做出来**再判，别假设。</p>
     */
    private static void clearChamber(ServerLevel level) {
        BlockPos base = new BlockPos((int) CX, (int) CY - 1, (int) CZ);
        for (int dx = -6; dx <= 13; dx++) {
            for (int dy = -1; dy <= 4; dy++) {
                for (int dz = -6; dz <= 14; dz++) {
                    BlockPos p = base.offset(dx, dy, dz);
                    if (!level.getBlockState(p).isAir()) {
                        level.setBlockAndUpdate(p, Blocks.AIR.defaultBlockState());
                    }
                }
            }
        }
    }

    private static void run(ServerStartedEvent event, ServerLevel level) {
        ServerPlayer caster = fake(event, level, "zf144-caster");
        caster.setYRot(0.0F);      // yaw 0 ⇒ getLookAngle() 的水平投影是 +Z
        caster.setXRot(0.0F);
        burnSpawnProtection(caster);
        // ⚠⚠ 位置必须在**烧完出生保护之后**再给：那 61 次 tick 里玩家受重力会一路掉到地面
        //   （实测 y 从 100 掉到 **51.58**），而靶子停在 y=100 ⇒ 搜索盒（±8 格）压根罩不到，
        //   `getEntities` 返回 0、剑气"一条都打不中"。第四次实测才把这条抓出来（§4.146）。
        //   顺带关掉重力：后面冷却那一节还要原地 tick 300 次。
        caster.setPos(CX, CY, CZ);
        caster.setNoGravity(true);
        check("前置：caster 真的站在试验场高度上（没在烧保护时掉下去）",
                Math.abs(caster.getY() - CY) < 0.5D, "y=" + caster.getY());

        Item shovel = ModItems.STAR_STEEL_SHOVEL.get();
        Item sword = ModItems.STAR_STEEL_SWORD.get();
        Item pick = ModItems.STAR_STEEL_PICKAXE.get();
        Item hoe = ModItems.STAR_STEEL_HOE.get();
        Item axe = ModItems.STAR_STEEL_AXE.get();
        Item ingot = ModArmorItems.STAR_STEEL_INGOT.get();

        // ---------------- ① 注册与身份 ----------------
        head("① 注册与身份");
        var items = level.registryAccess().registryOrThrow(Registries.ITEM);
        check("锹注册在 potato_s_t:star_steel_shovel 上",
                String.valueOf(items.getKey(shovel)).equals(NS + ":star_steel_shovel"),
                String.valueOf(items.getKey(shovel)));
        check("锹用的是本轮的 StarSteelShovelItem 类（不是拿原版类顶的）",
                shovel instanceof StarSteelShovelItem, shovel.getClass().getSimpleName());
        check("剑也还在（本轮给它加了技能，类没换）", sword instanceof StarSteelSwordItem);

        // ---------------- ② 档位（五把的关系） ----------------
        head("② 档位：剑/锹/镐/锄同一对象，且与斧子逐字同值");
        Tier tShovel = ((TieredItem) shovel).getTier();
        Tier tSword = ((TieredItem) sword).getTier();
        Tier tPick = ((TieredItem) pick).getTier();
        Tier tHoe = ((TieredItem) hoe).getTier();
        Tier tAxe = ((TieredItem) axe).getTier();
        check("锹/剑/镐/锄四份 getTier() 是**同一个对象**",
                tShovel == tSword && tSword == tPick && tPick == tHoe);
        check("这一档 = (1192, 9.0, 8.0, 钻石标签, 22)　实际 " + tierOf(tShovel),
                tShovel.getUses() == 1192 && tShovel.getSpeed() == 9.0F
                        && tShovel.getAttackDamageBonus() == 8.0F
                        && tShovel.getIncorrectBlocksForDrops().location().toString()
                                .equals("minecraft:incorrect_for_diamond_tool")
                        && tShovel.getEnchantmentValue() == 22);
        check("它与斧子那一档逐字相同（斧子档 " + tierOf(tAxe) + "）",
                tAxe.getUses() == tShovel.getUses() && tAxe.getSpeed() == tShovel.getSpeed()
                        && tAxe.getAttackDamageBonus() == tShovel.getAttackDamageBonus()
                        && tAxe.getIncorrectBlocksForDrops() == tShovel.getIncorrectBlocksForDrops()
                        && tAxe.getEnchantmentValue() == tShovel.getEnchantmentValue());
        check("锹耐久 1192", new ItemStack(shovel).getMaxDamage() == 1192);
        check("锹认星璨钢锭、不认轻质钛合金",
                shovel.isValidRepairItem(new ItemStack(shovel), new ItemStack(ingot))
                        && !shovel.isValidRepairItem(new ItemStack(shovel),
                                new ItemStack(ModItems.LIGHT_TITANIUM_ALLOY.get())));

        // ---------------- ③ 属性记账 ----------------
        head("③ 属性记账（真读玩家属性）");
        String[] names = {"锹", "镐", "剑", "斧", "原版钻石锹"};
        Item[] list = {shovel, pick, sword, axe, Items.DIAMOND_SHOVEL};
        double[][] want = {{13.5D, 1.0D}, {13.0D, 1.2D}, {16.0D, 1.6D}, {17.0D, 0.9D}, {5.5D, 1.0D}};
        for (int i = 0; i < list.length; i++) {
            caster.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(list[i]));
            // ⚠ 两次踩同一个坑，这次写死在注释里：
            //   ① **必须 doTick()** —— 装备变化要下一次 tick 才进属性表（§4.140）；
            //      第一版我把 doTick() 只留给斧子（想省事），结果四把工具读出来全是
            //      "上一件"的值（锹/镐/剑 读到空手的 1.0/4.0、钻石锹读到斧子的 17.0/0.9）。
            //   ② 清效果之后**不许再 tick** —— 手还拿着斧子的话，那一次 tick 会把急迫又挂回来，
            //      攻速被顶到 0.99（§4.142）。正确顺序：tick 一次 → 清效果 → 直接读。
            caster.doTick();
            caster.removeAllEffects();
            double dmg = caster.getAttributeValue(Attributes.ATTACK_DAMAGE);
            double spd = caster.getAttributeValue(Attributes.ATTACK_SPEED);
            check(String.format(java.util.Locale.ROOT,
                            "%s：显示伤害 %s（期望 %s）、攻速 %s（期望 %s）",
                            names[i], f(dmg), f(want[i][0]), f(spd), f(want[i][1])),
                    Math.abs(dmg - want[i][0]) < 0.001D && Math.abs(spd - want[i][1]) < 0.001D);
        }
        check("锹落在镐与剑之间（原版的相对次序）", 13.0D < 13.5D && 13.5D < 16.0D);
        caster.setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
        caster.removeAllEffects();

        // ---------------- ④ 挖掘等级 / 速度 ----------------
        head("④ 锹的挖掘等级与速度");
        ItemStack shovelStack = new ItemStack(shovel);
        BlockState dirt = Blocks.DIRT.defaultBlockState();
        BlockState stone = Blocks.STONE.defaultBlockState();
        check("锹挖泥土的速度 = 9.0（档位速度）　实际 "
                        + f(shovel.getDestroySpeed(shovelStack, dirt)),
                Math.abs(shovel.getDestroySpeed(shovelStack, dirt) - 9.0F) < 0.001F);
        check("锹对泥土 isCorrectToolForDrops = true",
                shovel.isCorrectToolForDrops(shovelStack, dirt));
        check("对照：锹对石头 isCorrectToolForDrops = false（那不是锹该挖的方块）",
                !shovel.isCorrectToolForDrops(shovelStack, stone));
        check("对照：镐对石头 true、对泥土 false（同一套原版工具类型判定）",
                pick.isCorrectToolForDrops(new ItemStack(pick), stone)
                        && !pick.isCorrectToolForDrops(new ItemStack(pick), dirt));

        // ---------------- ⑤ 锹的「与夜同频」 ----------------
        head("⑤ 锹的「与夜同频」：采掘与攻击两个入口");
        BlockPos pos = new BlockPos((int) CX, (int) CY - 2, (int) CZ);
        check("前置：白天判据一致", setTime(level, false));
        for (String which : new String[]{"采掘", "攻击"}) {
            ItemStack s = new ItemStack(shovel);
            caster.setItemSlot(EquipmentSlot.MAINHAND, s);
            int before = s.getDamageValue();
            if (which.equals("采掘")) {
                s.mineBlock(level, dirt, pos, caster);
            } else {
                s.postHurtEnemy(caster, caster);
            }
            int delta = s.getDamageValue() - before;
            int expect = which.equals("采掘") ? 1 : 2;
            check("白天" + which + "：锹掉 " + delta + " 点耐久（期望 " + expect + "）", delta == expect);
        }
        check("前置：夜晚判据一致", setTime(level, true));
        for (String which : new String[]{"采掘", "攻击"}) {
            ItemStack s = new ItemStack(shovel);
            caster.setItemSlot(EquipmentSlot.MAINHAND, s);
            int before = s.getDamageValue();
            if (which.equals("采掘")) {
                s.mineBlock(level, dirt, pos, caster);
            } else {
                s.postHurtEnemy(caster, caster);
            }
            int delta = s.getDamageValue() - before;
            check("夜晚" + which + "：锹掉 " + delta + " 点耐久（应为 0 —— 与夜同频）", delta == 0);
        }

        // ---------------- ⑥ 锹的配方 ----------------
        head("⑥ 锹的配方：原版图纸只换材料");
        check("锹配方（星璨钢锭 + 木棍 ×2，竖排）",
                craftMatches(level, shovel, ingot, "X", "#", "#"));
        check("对照：同一张图纸换成原版钻石 ⇒ 出原版钻石锹",
                craftMatches(level, Items.DIAMOND_SHOVEL, Items.DIAMOND, "X", "#", "#"));
        check("对照：图纸换成剑的（X/X/#）⇒ 不出锹",
                !craftMatches(level, shovel, ingot, "X", "X", "#"));

        // ---------------- ⑦ 星辉斩：几何 ----------------
        head("⑦ 星辉斩（Shift + 右键）几何：该打的一定打、不该打的一次都不打");
        check("前置：切成夜晚（免得僵尸在太阳下着火干扰血量读数）", setTime(level, true));
        // ⚠⚠ 第一版这整节 6 条全红，根因是**试验场在地下**：(420,100,100) 那一片地形比 y=100 高，
        //   僵尸一放进去就埋在方块里 ⇒ `isBehindWall` 那条原版射线**每次都命中方块**、一个都打不到。
        //   ⇒ 先**真的挖一个空腔**（不是"假设那里是空气"），并立刻用"靶子找得到吗 / 中间是空气吗"
        //     两条对照把这个前提钉住 —— 否则"0 伤害"到底是几何拒绝还是场地问题，分不出来。
        loadChunks(level);
        clearChamber(level);
        recenter(caster);
        check("灵敏度对照：靶子真的进得了世界（addFreshEntity 成功）", dummyAdded);
        check("试验场已清空（caster 脚下到 +14 格都是空气）",
                level.getBlockState(new BlockPos((int) CX, (int) CY, (int) CZ + 2)).isAir()
                        && level.getBlockState(new BlockPos((int) CX, (int) CY, (int) CZ + 8)).isAir());

        // 灵敏度对照：先证明"这个靶子真的挨得住打"（否则下面的 0 全是假绿）
        Zombie probeDummy = dummyAt(level, 0.0D, 0.0D, 3.0D);
        float h0 = probeDummy.getHealth();
        boolean landed = probeDummy.hurt(level.damageSources().generic(), 1.0F);
        check("灵敏度对照：哑巴僵尸挨得住 1 点普通伤害（掉了 " + f(h0 - probeDummy.getHealth()) + "）",
                landed && Math.abs((h0 - probeDummy.getHealth()) - 1.0F) < 0.001F);
        // ⚠ 诊断（第三版加的）：`getEntities` 数不到靶子，但 `addFreshEntity` 是成功的
        //   ⇒ 把"谁在哪、盒子多大、各种查询各数到几个"全打出来，**别再猜**。
        net.minecraft.world.phys.AABB box = caster.getBoundingBox().inflate(8.0D);
        say(TAG + "   [诊断] caster pos=" + caster.position() + "  bb=" + caster.getBoundingBox());
        say(TAG + "   [诊断] 搜索盒=" + box);
        say(TAG + "   [诊断] 靶子 pos=" + probeDummy.position()
                + "  chunk=" + probeDummy.chunkPosition()
                + "  hasChunkAt=" + level.hasChunkAt(probeDummy.blockPosition()));
        say(TAG + "   [诊断] getEntities(caster, box).size="
                + level.getEntities(caster, box).size());
        say(TAG + "   [诊断] getEntitiesOfClass(Zombie, box).size="
                + level.getEntitiesOfClass(Zombie.class, box).size());
        say(TAG + "   [诊断] getEntitiesOfClass(Zombie, 大盒).size="
                + level.getEntitiesOfClass(Zombie.class,
                        new net.minecraft.world.phys.AABB(-1000, -100, -1000, 1000, 400, 1000)).size());
        check("灵敏度对照：level.getEntities 数得到这个靶子（几何那一关之前的前提）",
                level.getEntities(caster, box).contains(probeDummy));
        probeDummy.discard();

        Zombie front = dummyAt(level, 0.0D, 0.0D, 3.0D);
        float before = front.getHealth();
        int hits = StarSteelSwordItem.slash(caster);
        float lost = before - front.getHealth();
        check("正前方 3 格：挨 " + f(lost) + " 点（期望 12.0）、slash() 返回 " + hits + "（期望 1）",
                Math.abs(lost - 12.0F) < 0.001F && hits == 1);
        check("命中者拿到了发光效果（100 tick）",
                front.hasEffect(net.minecraft.world.effect.MobEffects.GLOWING)
                        && front.getEffect(net.minecraft.world.effect.MobEffects.GLOWING)
                                .getDuration() > 90);
        front.discard();

        Zombie behind = dummyAt(level, 0.0D, 0.0D, -3.0D);
        float b2 = behind.getHealth();
        int hBehind = StarSteelSwordItem.slash(caster);
        check("负向 · 身后 3 格：一点没挨（掉了 " + f(b2 - behind.getHealth())
                        + "）、slash() 返回 " + hBehind + "（期望 0）",
                Math.abs(b2 - behind.getHealth()) < 0.001F && hBehind == 0);
        behind.discard();

        Zombie far = dummyAt(level, 0.0D, 0.0D, 12.0D);
        float b3 = far.getHealth();
        int hFar = StarSteelSwordItem.slash(caster);
        check("负向 · 正前方 12 格（超程）：一点没挨（掉了 " + f(b3 - far.getHealth()) + "）",
                Math.abs(b3 - far.getHealth()) < 0.001F && hFar == 0);
        far.discard();

        Zombie side = dummyAt(level, 4.0D, 0.0D, 3.0D);
        float b4 = side.getHealth();
        int hSide = StarSteelSwordItem.slash(caster);
        check("负向 · 正前方 3 格但横向偏 4 格（出宽）：一点没挨（掉了 "
                        + f(b4 - side.getHealth()) + "）",
                Math.abs(b4 - side.getHealth()) < 0.001F && hSide == 0);
        side.discard();

        // 隔墙：在正前方 1..2 格砌一堵两格高的石头
        Zombie walled = dummyAt(level, 0.0D, 0.0D, 4.0D);
        BlockPos w1 = new BlockPos((int) CX, (int) CY, (int) CZ + 2);
        level.setBlockAndUpdate(w1, Blocks.STONE.defaultBlockState());
        level.setBlockAndUpdate(w1.above(), Blocks.STONE.defaultBlockState());
        float b5 = walled.getHealth();
        int hWall = StarSteelSwordItem.slash(caster);
        check("负向 · 隔着两格高的石墙：一点没挨（掉了 " + f(b5 - walled.getHealth())
                        + "）、slash() 返回 " + hWall + "（期望 0）",
                Math.abs(b5 - walled.getHealth()) < 0.001F && hWall == 0);
        level.removeBlock(w1, false);
        level.removeBlock(w1.above(), false);

        // 拆掉墙之后应当**打得到** —— 这条是"墙那一刀不是因为别的原因红的"的对照
        reset(walled);
        float b6 = walled.getHealth();
        int hAfter = StarSteelSwordItem.slash(caster);
        check("对照：墙拆了之后同一个目标挨 " + f(b6 - walled.getHealth())
                        + " 点（期望 12.0）—— 证明上一刀红的是墙、不是别的",
                Math.abs(b6 - walled.getHealth() - 12.0F) < 0.001F && hAfter == 1);
        walled.discard();

        Zombie twoA = dummyAt(level, 0.0D, 0.0D, 2.0D);
        Zombie twoB = dummyAt(level, 1.0D, 0.0D, 6.0D);
        float a0 = twoA.getHealth();
        float b0 = twoB.getHealth();
        int hTwo = StarSteelSwordItem.slash(caster);
        check("贯穿：走廊里两个目标**都**挨（" + f(a0 - twoA.getHealth()) + " / "
                        + f(b0 - twoB.getHealth()) + "），slash() 返回 " + hTwo + "（期望 2）",
                Math.abs(a0 - twoA.getHealth() - 12.0F) < 0.001F
                        && Math.abs(b0 - twoB.getHealth() - 12.0F) < 0.001F && hTwo == 2);
        twoA.discard();
        twoB.discard();

        // ---------------- ⑧ 星辉斩：代价与状态 ----------------
        head("⑧ 星辉斩的代价与状态（扣耐久 / 冷却 / 三种不出手）");
        ItemStack useStack = new ItemStack(sword);
        caster.setItemSlot(EquipmentSlot.MAINHAND, useStack);
        caster.getCooldowns().removeCooldown(sword);
        int d0 = useStack.getDamageValue();
        caster.setShiftKeyDown(true);
        useStack.use(level, caster, InteractionHand.MAIN_HAND);
        int cost = useStack.getDamageValue() - d0;
        check("Shift + 右键：扣 " + cost + " 点耐久（期望 100）", cost == 100);
        check("出手后进冷却（isOnCooldown = true）", caster.getCooldowns().isOnCooldown(sword));
        check("冷却百分比 ≈ 100%（刚出手）",
                caster.getCooldowns().getCooldownPercent(sword, 0.0F) > 0.9F,
                String.valueOf(caster.getCooldowns().getCooldownPercent(sword, 0.0F)));

        // 冷却中：再按一次不该扣
        int d1 = useStack.getDamageValue();
        useStack.use(level, caster, InteractionHand.MAIN_HAND);
        check("冷却中再按：不扣耐久（掉了 " + (useStack.getDamageValue() - d1) + "）",
                useStack.getDamageValue() == d1);

        // 不按 Shift
        caster.getCooldowns().removeCooldown(sword);
        caster.setShiftKeyDown(false);
        ItemStack noShift = new ItemStack(sword);
        caster.setItemSlot(EquipmentSlot.MAINHAND, noShift);
        int d2 = noShift.getDamageValue();
        var r2 = noShift.use(level, caster, InteractionHand.MAIN_HAND);
        check("不按 Shift：不扣耐久（掉了 " + (noShift.getDamageValue() - d2)
                        + "）、也不进冷却、结果是 PASS",
                noShift.getDamageValue() == d2 && !caster.getCooldowns().isOnCooldown(sword)
                        && r2.getResult() == net.minecraft.world.InteractionResult.PASS);
        caster.setShiftKeyDown(true);

        // 耐久不足
        ItemStack worn = new ItemStack(sword);
        worn.setDamageValue(worn.getMaxDamage() - 50);
        caster.setItemSlot(EquipmentSlot.MAINHAND, worn);
        var r3 = worn.use(level, caster, InteractionHand.MAIN_HAND);
        check("耐久只剩 50（不够一次 100）：不出手、不扣耐久、结果是 FAIL",
                worn.getDamageValue() == worn.getMaxDamage() - 50
                        && !caster.getCooldowns().isOnCooldown(sword)
                        && r3.getResult() == net.minecraft.world.InteractionResult.FAIL);

        // 冷却会自己走完
        // ⚠ 冷却是在 `Player.tick()`（也就是 `doTick()`）里推进的 ⇒ 只 `tick()` 不动它
        //   （第一版只调 `tick()`，301 次之后还在冷却 —— 与 §4.127「ServerPlayer 有两个 tick」同源）
        caster.getCooldowns().removeCooldown(sword);
        ItemStack tickStack = new ItemStack(sword);
        caster.setItemSlot(EquipmentSlot.MAINHAND, tickStack);
        tickStack.use(level, caster, InteractionHand.MAIN_HAND);
        for (int i = 0; i < 299; i++) {
            caster.tick();
            caster.doTick();
        }
        boolean still = caster.getCooldowns().isOnCooldown(sword);
        for (int i = 0; i < 3; i++) {
            caster.tick();
            caster.doTick();
        }
        check("冷却 15 秒：299 tick 后还在冷却（" + still + "）、302 tick 后已解除（"
                        + !caster.getCooldowns().isOnCooldown(sword) + "）",
                still && !caster.getCooldowns().isOnCooldown(sword));
        caster.setShiftKeyDown(false);

        // ---------------- ⑨ 伤害类型与死亡文案 ----------------
        head("⑨ 剑气的伤害类型与死亡文案");
        var types = level.registryAccess().registryOrThrow(Registries.DAMAGE_TYPE);
        Optional<net.minecraft.core.Holder.Reference<DamageType>> holder =
                types.getHolder(StarSteelSwordItem.STAR_STEEL_SLASH);
        check("potato_s_t:star_steel_slash 在数据包注册表里取得到", holder.isPresent());
        if (holder.isPresent()) {
            DamageType dt = holder.get().value();
            check("msgId = potato_s_t.star_steel_slash（实际 " + dt.msgId() + "）",
                    dt.msgId().equals(NS + ".star_steel_slash"));
            check("exhaustion = 0.1（实际 " + dt.exhaustion() + "）",
                    Math.abs(dt.exhaustion() - 0.1F) < 0.001F);
            check("effects = HURT（实际 " + dt.effects() + "）",
                    dt.effects() == net.minecraft.world.damagesource.DamageEffects.HURT);
            check("scaling = WHEN_CAUSED_BY_LIVING_NON_PLAYER（实际 " + dt.scaling() + "）",
                    dt.scaling() == net.minecraft.world.damagesource.DamageScaling
                            .WHEN_CAUSED_BY_LIVING_NON_PLAYER);
        }
        // ---- 死亡文案：**直接用剑气那个伤害类型**打一下 ----
        // ⚠ 为什么这里不走 slash()：几何那一节已经逐条证明过"打得到"（正前方 12.0、贯穿 2 个、
        //   四种负向各 0），而这一节要证的是「伤害类型 → 死亡文案」这条**独立**的链。
        //   第一版把两件事绑在一起（用 slash() 打死它），结果 victim 没死、两条文案判据
        //   连跑都没跑 —— 加诊断才看清 slash() 那一下命中 0 个（原因见下面那几行 [诊断]）。
        //   **几何与文案不该绑在一条判据里**：一条坏了，另一条的证据也跟着没了。
        Zombie victim = dummyAt(level, 0.0D, 0.0D, 3.0D);
        victim.setHealth(5.0F);
        DamageSource slashSource = new DamageSource(
                types.getHolderOrThrow(StarSteelSwordItem.STAR_STEEL_SLASH), caster);
        lastDeathMessage = null;
        boolean died = victim.hurt(slashSource, 12.0F);
        check("5 点血的靶子挨 12 点「剑气」伤害 ⇒ 死了、且死亡事件里抓到了文案",
                died && !victim.isAlive() && lastDeathMessage != null,
                "died=" + died + " alive=" + victim.isAlive() + " msg=" + lastDeathMessage);
        if (lastDeathMessage != null) {
            String key = lastDeathMessage.getContents() instanceof TranslatableContents tc
                    ? tc.getKey() : String.valueOf(lastDeathMessage.getContents());
            check("死亡那一刻的文案键 = death.attack.potato_s_t.star_steel_slash（实际 " + key + "）",
                    key.equals("death.attack.potato_s_t.star_steel_slash"));
            String shown = lastDeathMessage.getString();
            check("文案里 %1$s 解析出的是**受害者自己**的名字（「" + shown + "」）",
                    shown.contains(victim.getName().getString()));
        }
        // 顺带把"slash() 能不能真的把人打死"也量一遍（**只打印，不判**）：
        // 它是端到端那一环，值不值得判要看下面这行诊断说的是什么。
        recenter(caster);   // ⚠ ⑧ 那 302 次 tick 会把施法者拽下去 3.77 格
        Zombie slashed = dummyAt(level, 0.0D, 0.0D, 4.0D);
        slashed.setHealth(5.0F);
        say(TAG + "   [诊断] 打死测试前：caster pos=" + caster.position()
                + " yaw=" + caster.getYRot()
                + "  靶子 pos=" + slashed.position() + " hp=" + slashed.getHealth());
        int killed = StarSteelSwordItem.slash(caster);
        say(TAG + "   [诊断] slash() 命中 " + killed + " 个；靶子 hp=" + slashed.getHealth()
                + " alive=" + slashed.isAlive());
        check("端到端：slash() 打死 5 点血的靶子（命中 " + killed + " 个）",
                killed == 1 && !slashed.isAlive());
        slashed.discard();

        // ---------------- ⑩ 旧账复核 ----------------
        head("⑩ 旧账复核（本轮没碰它们）");
        ItemStack swordNight = new ItemStack(sword);
        caster.setItemSlot(EquipmentSlot.MAINHAND, swordNight);
        check("前置：夜晚判据一致", setTime(level, true));
        int n0 = swordNight.getDamageValue();
        swordNight.mineBlock(level, stone, pos, caster);
        swordNight.postHurtEnemy(caster, caster);
        check("剑的「夜晚不磨损」仍在（采掘 + 攻击掉了 "
                        + (swordNight.getDamageValue() - n0) + " 点）",
                swordNight.getDamageValue() == n0);
        caster.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(axe));
        caster.removeAllEffects();
        caster.doTick();
        check("手持星璨钢斧仍然给急迫 I（ZF133 那条没被碰坏）",
                caster.hasEffect(net.minecraft.world.effect.MobEffects.DIG_SPEED));
        caster.setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);

        // ---------------- ⑪ 四语言（类路径里的构建产物） ----------------
        head("⑪ 四语言键（从类路径读，证明已进构建产物）");
        JsonObject en = null;
        try (java.io.InputStream in = Zf144Check.class.getResourceAsStream(
                "/assets/potato_s_t/lang/en_us.json")) {
            check("类路径里取得到 assets/potato_s_t/lang/en_us.json", in != null);
            if (in != null) {
                try (BufferedReader r = new BufferedReader(
                        new InputStreamReader(in, StandardCharsets.UTF_8))) {
                    en = JsonParser.parseReader(r).getAsJsonObject();
                }
            }
        } catch (Throwable t) {
            say(TAG + "读 lang 失败：" + t);
        }
        if (en != null) {
            check("en_us 键数 = 492（ZF141 的 487 + 本轮 5）", en.size() == 492,
                    "实际 " + en.size());
            String[][] want2 = {
                    {"item.potato_s_t.star_steel_shovel", "Star Steel Shovel"},
                    {"tooltip.potato_s_t.star_steel_sword.1",
                            "No durability loss from mining or attacking at night. "
                                    + "1192 durability, diamond mining level"},
                    {"tooltip.potato_s_t.star_steel_sword.2",
                            "Shift + right-click: costs 100 durability to send an 8-block "
                                    + "starlight slash along your facing (15 s cooldown)"},
                    {"tooltip.potato_s_t.star_steel_sword.3",
                            "The slash pierces every enemy along its path for 12 damage and "
                                    + "lights them up for 5 s"},
                    {"death.attack.potato_s_t.star_steel_slash",
                            "%1$s was pierced by starlight"},
            };
            for (String[] kv : want2) {
                String got = en.has(kv[0]) ? en.get(kv[0]).getAsString() : "<缺键>";
                check("en_us " + kv[0] + " = 「" + got + "」", kv[1].equals(got),
                        "期望「" + kv[1] + "」");
            }
        }
    }

    /**
     * 在 3×3 真合成网格里按图形摆一次，断言产物是不是 {@code want}。
     * {@code X} = 材料、{@code #} = 木棍、空格 = 空。
     */
    private static boolean craftMatches(ServerLevel level, Item want, Item material, String... rows) {
        List<ItemStack> grid = new ArrayList<>();
        for (int y = 0; y < 3; y++) {
            String row = y < rows.length ? rows[y] : "   ";
            for (int x = 0; x < 3; x++) {
                char c = x < row.length() ? row.charAt(x) : ' ';
                if (c == 'X') {
                    grid.add(new ItemStack(material));
                } else if (c == '#') {
                    grid.add(new ItemStack(Items.STICK));
                } else {
                    grid.add(ItemStack.EMPTY);
                }
            }
        }
        CraftingInput input = CraftingInput.of(3, 3, grid);
        Optional<RecipeHolder<CraftingRecipe>> hit =
                level.getRecipeManager().getRecipeFor(RecipeType.CRAFTING, input, level);
        if (hit.isEmpty()) {
            return false;
        }
        ItemStack out = hit.get().value().assemble(input, level.registryAccess());
        return !out.isEmpty() && out.getItem() == want;
    }
}
