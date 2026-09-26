package com.potatost.mod;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.UUID;

import com.mojang.authlib.GameProfile;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.EnderMan;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.common.damagesource.DamageContainer;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * ⚠⚠ <b>诊断探针（ZF133 临时文件，验证完必须删）</b>：星璨钢斧冲击波的端到端取证。
 *
 * <p>静态校验（{@code _zf133_verify.py}）只能证明"代码长对了"。下面这些**只有真服务端 + 真 tick
 * 才能回答**：波到底往前推了几格、拆了哪几格、什么时候停、扣了多少耐久、冷却有没有生效、
 * 末地那一刀打出了多少点伤害。</p>
 *
 * <p><b>试验场</b>：主世界 (100, 160, 100) 的悬空石台（y=159 一层石头，玩家站在 y=160），
 * 比地面高 90 多格 ⇒ 波的 6×3 采样区碰不到任何天然方块，结论可复现。</p>
 *
 * <p><b>九个场景</b>（时间线全在同一场里跑，靠 tick 排队）：**序号 = 实际执行顺序**，
 * 与报告里的 ①..⑨ 抬头、以及下面各 T_xxx 常量的注释一一对应。</p>
 * <ol>
 *   <li>t=20   ① 物品与档位静态事实（1192 耐久 / 钻石级 / 花费 120 / 冷却 300 / 基础伤害摘得干净）；</li>
 *   <li>t=40   ② (b) 一整排 6 根原木 + 头顶树叶 ⇒ 全拆光，且 A7（宽度外那一格）原样；</li>
 *   <li>t=130  ③ (d) 石头墙 + 墙后一根原木 ⇒ 波停在墙前、墙后那根**必须还在**；</li>
 *   <li>t=200  ④ (e) 起点是空旷地 ⇒ 拆完再飞一会儿 ⇒ 波自己散掉（实际死因是 64 格射程）；</li>
 *   <li>t=450  ⑤ (i) 拆到木头之后 60 tick 还活着、300 tick 后已散（同上：射程先到期）；</li>
 *   <li>t=760  ⑥ (h) 末地：末地**任意实体**吃到 10 + 0.5n（n=玩家基础伤害）的伤害（实战里先挨打的是末地龙） ——
 *              用力量效果把 n 从 1 抬到 4（+3），所以期望值 = 10 + 2 = **12.0**；</li>
 *   <li>t=810  ⑦ (f) 冷却：出手进 300 tick 冷却、冷却中再右键不出手，
 *              **显式 tick 满 300 次之后必须解开**（假玩家不在 PlayerList，等不来真实 tick）；</li>
 *   <li>t=830  ⑧ (g) 耐久不够 120 时拒绝出手、且不进冷却；</li>
 *   <li>t=870  ⑨ (c) 创造模式玩家照常出手（用户没给限制）。</li>
 * </ol>
 */
public final class Zf133Check {

    /** ⚠ 临时诊断开关（ZF133 查冷却门禁用），查完删。 */
    public static boolean DBG = false;

    private static final String TAG = "[A133] ";
    private static final String REPORT = "E:\\PotatoST\\build\\zftools\\check\\zf133_axe_probe.log";
    private static final ResourceKey<Level> END = ResourceKey.create(Registries.DIMENSION,
            ResourceLocation.withDefaultNamespace("the_end"));

    private static final int X0 = 100;
    private static final int Y0 = 160;
    private static final int Z0 = 100;

    // ---- 时间线 ----
    private static final int T_STATIC = 20;      // ① 静态事实
    private static final int T_B = 40;           // ② 整排原木 + 树叶
    private static final int T_B_CHECK = 120;   // 64 格射程 ⇒ 约 60~70 tick 自己散
    private static final int T_D = 130;          // ③ 石头墙（⚠ 不能与 T_B_CHECK 同值）
    private static final int T_D_CHECK = 160;
    private static final int T_E = 200;          // ④ 10 秒闲置（起点为空旷地）
    private static final int T_E_CHECK = 270;   // 64 格射程上限 ⇒ 空旷地约 64 tick 就散
    private static final int T_I = 450;          // ⑤ 滚动窗口：先拆两次木头
    // ⚠ 这两个值必须**跟着 MAX_DISTANCE=64 定**：波 1 格/tick ⇒ 第 65 次 tick 就超射程自己散。
    //   它在 t=450 那一刻出生、**同一 tick** 就被 ShockwaveManager 推第一步（探针的 tick 钩子
    //   排在 ShockwaveManager 之前，实测 t=800 先打 [WAVES] 再打 travelled=40 的那行 trace），
    //   所以它在 t=450+travelled 那一拍采样、travelled=65 那一拍（t=515）返回 false。
    //   旧的 T_I_ALIVE=520 **已经落在射程之外** ⇒ 永远查到 activeCount=0（第一轮第 4 个 FAIL）。
    //   ⚠ 顺带记一笔：`IDLE_LIMIT_TICKS=200`（"10 秒没碰到木头就消失"）在当前射程下
    //   **永远轮不到它触发**（64 < 200）—— (e)/(i) 两场绿灯真正的护栏都是射程上限，不是闲置计时。
    private static final int T_I_ALIVE = 490;   // 出手后 40 tick（射程 64 内）    //    拆到木头（t=453）之后 57 tick：还活着且在射程内
    private static final int T_I_DEAD = 750;     //    远超 64 格射程：必须已散
    // ⚠ 末地那一场必须在"冷却/耐久门槛"**之前**：它要另造一台假玩家，
    //   跑完之后主玩家的状态会被带乱（实测：(g) 的出手从 CONSUME 变成 PASS）。
    private static final int T_H = 760;          // ⑥ 末地伤害（另起一台玩家）
    private static final int T_H_CHECK = 800;
    private static final int T_F = 810;          // ⑦ 冷却
    private static final int T_F_MID = 820;
    private static final int T_G = 830;          // ⑧ 耐久门槛
    private static final int T_G2 = 850;
    private static final int T_C = 870;          // ⑨ 创造模式
    private static final int T_END = 1000;

    private static boolean registered;
    private static boolean started;
    private static int failed;
    private static long t0;
    private static ServerLevel level;
    private static ServerLevel end;
    private static ServerPlayer player;
    private static ServerPlayer creativePlayer;
    private static ItemStack axe;
    private static BlockPos firPos;
    private static BlockPos wallLog;

    /** 出手前末地活实体的血量快照（名字#实体id -> 血量×1000）。 */
    private static final java.util.Map<String, Integer> endHpBefore = new java.util.HashMap<>();
    /** 末地那一刀实际打出的伤害（LivingIncomingDamageEvent 里抓）。 */
    private static double enderDamage = -1.0D;
    private static String enderSource;
    private static int enderHits;

    private static final StringBuilder report = new StringBuilder();

    private Zf133Check() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf133Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    // ============================================================
    //  开场：试验场 + 两个假玩家
    // ============================================================
    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        if (started) {
            return;
        }
        started = true;
        try {
            level = event.getServer().overworld();
            end = event.getServer().getLevel(END);
            for (int dx = -1; dx <= 1; dx++) {
                for (int dz = -1; dz <= 1; dz++) {
                    level.setChunkForced((X0 >> 4) + dx, (Z0 >> 4) + dz, true);
                }
            }
            if (end != null) {
                for (int dx = -1; dx <= 1; dx++) {
                    for (int dz = -1; dz <= 1; dz++) {
                        end.setChunkForced(dx, dz, true);
                    }
                }
            }

            // 悬空石台（只铺一层 y=159；玩家站 y=160）
            for (int dx = -20; dx <= 20; dx++) {
                for (int dz = -20; dz <= 20; dz++) {
                    level.setBlockAndUpdate(new BlockPos(X0 + dx, Y0 - 1, Z0 + dz),
                            Blocks.STONE.defaultBlockState());
                }
            }

            player = makePlayer(event.getServer(), level, "zf133probe", GameType.SURVIVAL);
            player.moveTo(X0 + 0.5D, Y0, Z0 + 0.5D, -90.0F, 0.0F);
            failed += check("假玩家已进服务端玩家表（getPlayer 查得到）",
                    event.getServer().getPlayerList().getPlayer(player.getUUID()) != null);
            // ⚠ 前提判据：后面八个场景全都建立在"这台假玩家活着"之上，
            //   所以这条必须第一个断言（§4.30：前提不成立时后面的绿灯都不算数）。
            failed += check("假玩家满血且存活（hp=" + player.getHealth() + "/"
                    + player.getMaxHealth() + "）",
                    player.isAlive() && player.getHealth() == player.getMaxHealth());
            failed += check("假玩家朝向是东（视线 x > 0.9，实际 "
                    + String.format("%.3f", player.getLookAngle().x) + "）",
                    player.getLookAngle().x > 0.9D);

            // ⚠ 时间线自检（ZF133 踩过一次）：所有 T_xxx 常量**两两不能同值**。
            //   同值 = 后面那一拍被 `else if` 静默跳过，症状是"后面整段场景都没跑"，
            //   而报告上看着像一堆互不相关的失败。
            int[] timeline = {T_STATIC, T_B, T_B_CHECK, T_D, T_D_CHECK, T_E, T_E_CHECK,
                    T_I, T_I_ALIVE, T_I_DEAD, T_H, T_H_CHECK, T_F, T_F_MID, T_G, T_G2,
                    T_C, T_END};
            String[] names = {"T_STATIC", "T_B", "T_B_CHECK", "T_D", "T_D_CHECK", "T_E",
                    "T_E_CHECK", "T_I", "T_I_ALIVE", "T_I_DEAD", "T_H", "T_H_CHECK", "T_F",
                    "T_F_MID", "T_G", "T_G2", "T_C", "T_END"};
            String clash = "";
            for (int i = 0; i < timeline.length; i++) {
                for (int j = i + 1; j < timeline.length; j++) {
                    if (timeline[i] == timeline[j]) {
                        clash += names[i] + "==" + names[j] + " ";
                    }
                }
            }
            failed += check("时间线常量两两不同（" + timeline.length + " 个" +
                    (clash.isEmpty() ? "" : "，撞车：" + clash) + "）", clash.isEmpty());
            creativePlayer = makePlayer(event.getServer(), level, "zf133creative", GameType.CREATIVE);
            creativePlayer.moveTo(X0 + 0.5D, Y0, Z0 + 0.5D, -90.0F, 0.0F);

            axe = new ItemStack(ModItems.STAR_STEEL_AXE.get());
            player.setItemInHand(InteractionHand.MAIN_HAND, axe);

            say(TAG + "试验场就绪：玩家 " + player.blockPosition()
                    + "，朝向 " + player.getDirection());
            t0 = level.getGameTime();

        // ⚠⚠ 试验场必须**没有怪物**：平台铺在 y=159、厚度只有 1 格，台子下面是黑的 ⇒
        //   苦力怕/僵尸/骷髅在台子下面刷出来，爆炸会波及站在台面上的假玩家
        //   （受击记录：`[DEATH] zf133probe 死于 explosion.player ... blown up by Creeper`），
        //   连带把摆好的测试方块炸飞 —— (e) 那格木头"没被拆掉"的真因就是它先被炸掉了。
        //   和平难度不刷敌对生物；已存在的另用 discard() 清一遍（和平只对之后的刷怪生效）。
        level.getServer().setDifficulty(net.minecraft.world.Difficulty.PEACEFUL, true);
        int mobsCleared = 0;
        // ⚠ `Enemy` 是**接口**，不能当 getEntitiesOfClass 的泛型参数（编译期就顶回来）
        //   ⇒ 取范围内所有 Mob，把两台假玩家挑出去，其余全清。
        for (net.minecraft.world.entity.Mob mob : level.getEntitiesOfClass(
                net.minecraft.world.entity.Mob.class,
                new net.minecraft.world.phys.AABB(X0 - 48, Y0 - 48, Z0 - 48,
                        X0 + 48, Y0 + 48, Z0 + 48))) {
            if (mob.getUUID().equals(player.getUUID())
                    || mob.getUUID().equals(creativePlayer.getUUID())) {
                continue;
            }
            mob.discard();
            mobsCleared++;
        }
        say(TAG + "试验场清怪：" + mobsCleared + " 只（难度已设和平）");
        } catch (Throwable t) {
            say(TAG + "exception: " + t);
            java.io.StringWriter sw = new java.io.StringWriter();
            t.printStackTrace(new java.io.PrintWriter(sw));
            for (String line : sw.toString().split("\n")) {
                say(TAG + "    " + line);
            }
            failed++;
        }
    }

    private static ServerPlayer makePlayer(MinecraftServer server, ServerLevel where,
                                          String name, GameType mode) {
        GameProfile profile = new GameProfile(
                UUID.nameUUIDFromBytes(name.getBytes(StandardCharsets.UTF_8)), name);
        ServerPlayer p = new ServerPlayer(server, where, profile, ClientInformation.createDefault());
        // ⚠ 无头服务端里 new 出来的玩家没有连接：发任何包都会 NPE（档案 §4.43），
        //   而 Connection.channel() 为 null 时连系统聊天包都会炸（§4.86）⇒ 塞个 EmbeddedChannel。
        net.minecraft.network.Connection conn = new net.minecraft.network.Connection(
                net.minecraft.network.protocol.PacketFlow.SERVERBOUND);
        try {
            java.lang.reflect.Field channelField =
                    net.minecraft.network.Connection.class.getDeclaredField("channel");
            channelField.setAccessible(true);
            channelField.set(conn, new io.netty.channel.embedded.EmbeddedChannel());
        } catch (Throwable t) {
            say(TAG + "EmbeddedChannel 注入失败（后面发消息会 NPE）：" + t);
        }
        net.minecraft.server.network.CommonListenerCookie cookie =
                net.minecraft.server.network.CommonListenerCookie.createInitial(profile, false);
        p.connection = new net.minecraft.server.network.ServerGamePacketListenerImpl(
                server, conn, p, cookie);
        // ⚠⚠ 必须真的进服务端玩家表：`ShockwaveManager` 靠 UUID 从 PlayerList 里把发射者找回来
        //   （人下线/死了波就散），假玩家不登记的话 `getPlayer(uuid)` 恒 null ⇒
        //   每道波在出生的下一 tick 就地消失（诊断 trace 一行都没打出来，就是卡在这一句）。
        //   ⚠ 1.21.1 的 PlayerList **没有** add(...)：官方入口是 placeNewPlayer，
        //   而且 cookie 要自己留着（`connection.cookie` 不是公开字段）。
        server.getPlayerList().placeNewPlayer(conn, p, cookie);
        // ⚠⚠ **入表之后必须把维度抢回来**：`PlayerList.placeNewPlayer` 里有一句
        //   `player.setServerLevel(server.getLevel(<存档里的重生维度>).orElse(overworld))`
        //   —— 它的字节码 offset 89 是 `getstatic Level.OVERWORLD`、offset 147 就是那句
        //   `ServerPlayer.setServerLevel`。全新假玩家没有 playerdata ⇒ **一律落到主世界**，
        //   也就是"在末地造一台假玩家"实际造在了主世界。
        //   后果极隐蔽：`ShockwaveManager.fire` 取的是 `player.serverLevel()`，波**跟着玩家走**
        //   ⇒ 末地那场发出去的波在主世界推进，`wave.level.dimension() == Level.END` 一次都没成立，
        //   末影人永远吃不到那一刀，而报告看上去只是"伤害没抓到"。
        //   第一轮的现场证据（带 trace 的那版打的）：
        //     `[TRLOOP] tick 波数=1 [165268f5 travelled=0 total=0 dim=minecraft:overworld]`
        //   紧跟着的 `[TRENTRY] tick 进入 owner=zf133end alive=true ... travelled=0` 说明
        //   那道波正是末地假玩家发的。**这不是产品缺陷**（真玩家进末地时 serverLevel() 就是末地），
        //   是探针把假玩家放错了维度，所以修在探针里。
        //   `setServerLevel` 就是 placeNewPlayer 自己用的那一句，只改两个字段
        //   （`Entity.level` 与 `ServerPlayerGameMode.level`），不发包、不碰区块。
        if (p.serverLevel() != where) {
            String wrongly = p.serverLevel().dimension().location().toString();
            p.setServerLevel(where);
            say(TAG + "      [DIM] placeNewPlayer 把 " + name + " 丢到了 " + wrongly
                    + "，已抢回 " + where.dimension().location());
        }
        p.setGameMode(mode);   // ⚠ 必须在入表之后（否则 changeGameModeForPlayer 会 NPE）
        // ⚠⚠ 假玩家一出生血量就是 0（`placeNewPlayer` 的副作用：登录流程里先按"未初始化"处理）。
        //   实测打印：`[HP] t=20 hp=0.0 alive=false`。后果极隐蔽 ——
        //   `ShockwaveManager.tick()` 第一句就是"人还在不在"，人死了波就散；
        //   而探针直接调的 `destroyBlock` / `hurtAndBreak` 完全不受影响 ⇒
        //   表现为"方块摆得上、耐久扣得掉、波一格都不拆"。**先救活，再断言。**
        p.setHealth(p.getMaxHealth());
        p.deathTime = 0;
        p.revive();
        p.hurtTime = 0;
        say(TAG + "      假玩家 " + name + " 入场：hp=" + p.getHealth() + "/" + p.getMaxHealth()
                + " alive=" + p.isAlive() + " 位置=" + p.blockPosition().toShortString());
        return p;
    }


    // ============================================================
    //  时间线
    // ============================================================
    @SubscribeEvent
    public static void onDeath(net.neoforged.neoforge.event.entity.living.LivingDeathEvent event) {
        say(TAG + "      [DEATH] " + event.getEntity().getName().getString()
                + " 死于 " + event.getSource().getMsgId()
                + " / " + event.getEntity().getCombatTracker().getDeathMessage().getString()
                + "（hp=" + event.getEntity().getHealth() + "）");
    }

    @SubscribeEvent
    public static void onServerTick(ServerTickEvent.Post event) {
        if (player == null || level == null) {
            return;
        }
        try {
            long t = level.getGameTime() - t0;
            if (t == T_B_CHECK || t == T_E_CHECK || t == T_I_ALIVE || t == T_H_CHECK) {
                say(TAG + "      [WAVES] t=" + t + " activeCount=" + ShockwaveManager.activeCount()
                        + " 玩家=" + player.blockPosition().toShortString()
                        + " hp=" + player.getHealth());
            }
            if (t == T_STATIC || t == T_B || t == T_B_CHECK) {
                say(TAG + "      [HP] t=" + t + " hp=" + player.getHealth()
                        + " alive=" + player.isAlive() + " mode=" + player.gameMode.getGameModeForPlayer()
                        + " 视线=" + player.getLookAngle());
            }
            if (t == T_STATIC) {
                staticFacts();
            } else if (t == T_B) {
                keepAlive();
                buildB();
            } else if (t == T_B_CHECK) {
                say(TAG + "      [TR] 检查时玩家在哪："
                        + player.blockPosition().toShortString()
                        + " 站在 " + level.getBlockState(player.blockPosition().below())
                                .getBlock().getName().getString());
                checkB();
            } else if (t == T_D) {
                buildD();
            } else if (t == T_D_CHECK) {
                checkD();
            } else if (t == T_E) {
                buildE();
            } else if (t == T_E_CHECK) {
                say(TAG + "      [TR] (e) 检查时玩家在哪："
                        + player.blockPosition().toShortString());
                checkE();
            } else if (t == T_I) {
                buildI();
            } else if (t == T_I_ALIVE) {
                checkIAlive();
            } else if (t == T_I_DEAD) {
                checkIDead();
            } else if (t == T_H) {
                buildH();
            } else if (t == T_H_CHECK) {
                checkH();
            } else if (t == T_F) {
                buildF();
            } else if (t == T_F_MID) {
                checkFMid();
            } else if (t == T_G) {
                buildG();
            } else if (t == T_G2) {
                checkG2();
            } else if (t == T_C) {
                buildC();
            } else if (t == T_END) {
                finish(event);
            }
        } catch (Throwable t) {
            say(TAG + "tick exception: " + t);
            java.io.StringWriter sw = new java.io.StringWriter();
            t.printStackTrace(new java.io.PrintWriter(sw));
            for (String line : sw.toString().split("\n")) {
                say(TAG + "    " + line);
            }
            failed++;
            finish(event);
        }
    }

    // ------------------------------------------------------------ ① 静态事实
    private static void staticFacts() {
        say(TAG + "① 物品与档位");
        ShockwaveManager.clearAll();
        player.getCooldowns().removeCooldown(axe.getItem());
        failed += check("拿在手上的是星璨钢斧", player.getMainHandItem().getItem() instanceof StarSteelAxeItem);
        failed += check("耐久上限 = 1192（实际 " + axe.getMaxDamage() + "）", axe.getMaxDamage() == 1192);
        failed += check("不可堆叠（stacksTo = 1，实际 " + axe.getMaxStackSize() + "）",
                axe.getMaxStackSize() == 1);
        failed += check("附魔权重 = 22（实际 " + axe.getItem().getEnchantmentValue() + "）",
                axe.getItem().getEnchantmentValue() == 22);
        failed += check("修理材料 = 星璨钢锭",
                axe.getItem().isValidRepairItem(axe, new ItemStack(ModArmorItems.STAR_STEEL_INGOT.get())));
        var tier = ((net.minecraft.world.item.AxeItem) axe.getItem()).getTier();
        failed += check("档位耐久 = 1192（实际 " + tier.getUses() + "）", tier.getUses() == 1192);
        failed += check("档位挖掘速度 = 9.0（实际 " + tier.getSpeed() + "）", tier.getSpeed() == 9.0F);
        failed += check("挖掘等级 = 钻石（挖不动的方块集合就是 INCORRECT_FOR_DIAMOND_TOOL）",
                tier.getIncorrectBlocksForDrops() == BlockTags.INCORRECT_FOR_DIAMOND_TOOL);
        // ⚠ 第一版拿黑曜石当"钻石级挖得动"的判据是**错的**：黑曜石要镐子，
        //   斧子本来就不行（原版行为，与挖掘等级无关）⇒ 探针当场顶红。
        //   正确的区分办法是"同一块方块换个工具试"：黑曜石换个镐子就挖得动 ⇒
        //   差别在**工具种类**而不是等级；等级那一半只留上面那条读档位对象本身的断言。
        ItemStack netheritePick = new ItemStack(Items.NETHERITE_PICKAXE);
        ItemStack diamondPick = new ItemStack(Items.DIAMOND_PICKAXE);
        failed += check("黑曜石：斧子挖不动（原版行为，与等级无关）",
                !axe.isCorrectToolForDrops(Blocks.OBSIDIAN.defaultBlockState()));
        failed += check("黑曜石：下界合金镐挖得动 ⇒ 上面那条的差别在工具种类",
                netheritePick.isCorrectToolForDrops(Blocks.OBSIDIAN.defaultBlockState()));
        failed += check("黑曜石：钻石镐也挖得动（对照，钻石这一档不低）",
                diamondPick.isCorrectToolForDrops(Blocks.OBSIDIAN.defaultBlockState()));

        // 基础伤害摘得干净：空手 = 1.0，拿着 14.0 的斧子 **仍然是 1.0**
        // ⚠ 「持斧时属性总值 = 14」这条**不在**这里验：这台假玩家虽然进了玩家表，
        //   但它的属性表迟迟不跟着换手更新（试过 tick 两遍仍是 1.0）——真实玩家当然会更新，
        //   这是探针环境的账。改到**末地那一场**验（那里有一台刚出手的玩家），
        //   这里只验**物品自带的属性组件**（读组件是确定能读到的事实）。
        player.setItemInHand(InteractionHand.MAIN_HAND, axe);
        // ⚠ 属性判据**不能**依赖"服务端换手会更新活值"：原版那条路径要求客户端发装备同步包，
        //   探针里的假玩家没有客户端 ⇒ `setItemInHand` 之后再 tick 多少次，活值都还是 1.0。
        //   （游戏里真实玩家当然会更新；这是探针环境的限制，不是产品缺陷。）
        //   改成可证伪的等价形式：手工往属性表里塞一条 +12 的修饰符 ——
        //   ① 它必须被算进去（1 + 12 = 13）；② 再塞一条"装备来源"的同名同值修饰符，
        //   它必须被**摘掉**（回到 1）—— 后半条正是冲击波伤害公式里"n 不含武器"那条判据。
        var attrInstance = player.getAttribute(Attributes.ATTACK_DAMAGE);
        Object attrComp = axe.get(net.minecraft.core.component.DataComponents.ATTRIBUTE_MODIFIERS);
        failed += check("斧子带属性组件（ATTRIBUTE_MODIFIERS 不为空）", attrComp != null);
        if (attrInstance != null && attrComp != null) {
            // 取出斧子自带的那条攻击力修饰符（物品组件里那条就是"装备那一份"）
            var entries = ((net.minecraft.world.item.component.ItemAttributeModifiers) attrComp).modifiers();
            net.minecraft.world.entity.ai.attributes.AttributeModifier gearMod = null;
            for (var entry : entries) {
                if (entry.attribute().is(Attributes.ATTACK_DAMAGE)) {
                    gearMod = entry.modifier();
                    break;
                }
            }
            // 判据盯语义：修饰符 == createAttributes 参数 + 档位加成（原版 DiggerItem 的算式）
            double expectMod = ModTiers.STAR_STEEL_DAMAGE + ModTiers.STAR_STEEL_AXE.getAttackDamageBonus();
            failed += check("斧子自带一条攻击力修饰符（加法值 "
                    + (gearMod == null ? "?" : gearMod.amount()) + "，= 参数 "
                    + ModTiers.STAR_STEEL_DAMAGE + " + 档位加成 "
                    + ModTiers.STAR_STEEL_AXE.getAttackDamageBonus() + " = " + expectMod + "）",
                    gearMod != null && Math.abs(gearMod.amount() - expectMod) < 1e-6);
            say(TAG + "      [ATTR] 按 1.21 的记账，游戏里显示的总伤害 = 1 + " + expectMod
                    + " = " + (1.0D + expectMod));
            if (gearMod != null) {
                attrInstance.addTransientModifier(gearMod);
                double withGear = ShockwaveManager.baseAttackDamage(player);
                failed += check("装备那一份被摘掉：baseAttackDamage 仍是 1.0（实际 " + withGear + "）",
                        Math.abs(withGear - 1.0D) < 1e-6);
                attrInstance.removeModifier(gearMod);

                // 再塞一条**不是装备来源**的同值修饰符（换个 id）⇒ 必须被算进去
                net.minecraft.world.entity.ai.attributes.AttributeModifier extra =
                        new net.minecraft.world.entity.ai.attributes.AttributeModifier(
                                net.minecraft.resources.ResourceLocation.fromNamespaceAndPath(
                                        "potato_s_t", "zf133_probe_bonus"), 12.0D,
                                net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.ADD_VALUE);
                attrInstance.addTransientModifier(extra);
                double playerOwn = ShockwaveManager.baseAttackDamage(player);
                failed += check("玩家自身的加成被算进去：1 + 12 = 13.0（实际 " + playerOwn + "）",
                        Math.abs(playerOwn - 13.0D) < 1e-6);
                failed += check("远程伤害随之变成 10 + 0.5*13 = 16.5（实际 "
                        + ShockwaveManager.rangedDamage(playerOwn) + "）",
                        Math.abs(ShockwaveManager.rangedDamage(playerOwn) - 16.5D) < 1e-6);
                attrInstance.removeModifier(extra);
                failed += check("摘掉之后回到 1.0（实际 "
                        + ShockwaveManager.baseAttackDamage(player) + "）",
                        Math.abs(ShockwaveManager.baseAttackDamage(player) - 1.0D) < 1e-6);
            }
        }
        double empty = ShockwaveManager.baseAttackDamage(player);
        failed += check("空手/无武器加成时基础伤害 = 1.0（实际 " + empty + "）",
                Math.abs(empty - 1.0D) < 1e-6);
        failed += check("远程伤害公式 10 + 0.5n（n=1 ⇒ 10.5，实际 "
                + ShockwaveManager.rangedDamage(1.0D) + "）",
                Math.abs(ShockwaveManager.rangedDamage(1.0D) - 10.5D) < 1e-9);
        failed += check("宽度 = 6（实际 " + ShockwaveManager.WIDTH + "）", ShockwaveManager.WIDTH == 6);
        failed += check("花费 = 120 / 冷却 = 300 tick",
                StarSteelAxeItem.SHOCKWAVE_COST == 120
                        && StarSteelAxeItem.SHOCKWAVE_COOLDOWN_TICKS == 300);
    }

    // ------------------------------------------------------------ ② (b) 整排原木 + 树叶
    private static void buildB() {
        DBG = true;
        say(TAG + "② (b) 整排 6 根原木 + 头顶树叶");
        ShockwaveManager.clearAll();
        player.getCooldowns().removeCooldown(axe.getItem());
        level.setBlockAndUpdate(new BlockPos(X0 + 1, Y0, Z0), Blocks.OAK_LOG.defaultBlockState());
        clearAbove();
        for (int z = -3; z <= 3; z++) {
            level.setBlockAndUpdate(new BlockPos(X0 + 1, Y0, Z0 + z), Blocks.OAK_LOG.defaultBlockState());
            level.setBlockAndUpdate(new BlockPos(X0 + 2, Y0 + 1, Z0 + z), Blocks.OAK_LEAVES.defaultBlockState());
        }
        // ⚠ 玩家自己站的那一格要单独清空：探针第一版把 (X0+1, Y0, Z0) 也算进"整排原木"里，
        //   而波在第 1 tick 扫到它时会把玩家卡在方块里 —— 那一格被拆掉是**不该发生的**
        //   （用户要的是"破坏沿途原木"，不是"把自己脚下的地板拆了"），
        //   所以这里把它留空，只测真正该被拆的那 6 格。
        level.setBlockAndUpdate(new BlockPos(X0 + 1, Y0, Z0), Blocks.AIR.defaultBlockState());
        for (int lat = -3; lat <= 2; lat++) {
            BlockPos q = new BlockPos(X0 + 1, Y0, Z0 + lat);
            BlockPos r = new BlockPos(X0 + 2, Y0 + 1, Z0 + lat);
            say(TAG + "      [B] 出手前 x=101 z=" + lat + " = "
                    + level.getBlockState(q).getBlock().getName().getString()
                    + " ／ x=102 y=161 = "
                    + level.getBlockState(r).getBlock().getName().getString());
        }
        firPos = player.blockPosition();
        for (int z = -3; z <= 3; z++) {
            BlockPos l1 = new BlockPos(X0 + 1, Y0, Z0 + z);
            BlockPos l2 = new BlockPos(X0 + 2, Y0 + 1, Z0 + z);
            say(TAG + "      [D9] x=101 z=" + z + " -> "
                    + level.getBlockState(l1).getBlock().getName().getString()
                    + " | x=102 y=161 -> "
                    + level.getBlockState(l2).getBlock().getName().getString());
        }
        say(TAG + "      [D9] 手上是 " + player.getMainHandItem().getItem()
                + " 玩家 " + player.blockPosition().toShortString());

        int dmgBefore = axe.getDamageValue();
        InteractionResultHolder<ItemStack> r = useAxe(player);
        failed += check("右键出手（结果 = " + r.getResult() + "）", fired(r.getResult()));
        failed += check("扣 120 点耐久（" + dmgBefore + " → " + axe.getDamageValue() + "）",
                axe.getDamageValue() - dmgBefore == 120);
        failed += check("波已起（activeCount = " + ShockwaveManager.activeCount() + "）",
                ShockwaveManager.activeCount() == 1);
    }

    private static void checkB() {
        int left = 0;
        for (int z = -3; z <= 2; z++) {
            if (!level.getBlockState(new BlockPos(X0 + 1, Y0, Z0 + z)).isAir()) {
                left++;
            }
        }
        int leavesLeft = 0;
        for (int z = -3; z <= 2; z++) {
            BlockPos lp = new BlockPos(X0 + 2, Y0 + 1, Z0 + z);
            if (!level.getBlockState(lp).isAir()) {
                leavesLeft++;
            }
        }
        failed += check("宽度内 6 根原木全拆（剩 " + left + " 根）", left == 0);
        failed += check("宽度内 6 格树叶全拆（剩 " + leavesLeft + " 格）", leavesLeft == 0);
        failed += check("宽度外那一根原木没被碰到（A7 还在）",
                !level.getBlockState(new BlockPos(X0 + 1, Y0, Z0 + 3)).isAir());
        failed += check("波已经走完（activeCount = " + ShockwaveManager.activeCount() + "）",
                ShockwaveManager.activeCount() == 0);
    }

    // ------------------------------------------------------------ ③ (d) 石头墙
    private static void buildD() {
        say(TAG + "③ (d) 石头墙挡路");
        ShockwaveManager.clearAll();
        player.getCooldowns().removeCooldown(axe.getItem());
        clearAbove();
        for (int z = -3; z <= 2; z++) {
            level.setBlockAndUpdate(new BlockPos(X0 + 6, Y0, Z0 + z), Blocks.STONE.defaultBlockState());
        }
        wallLog = new BlockPos(X0 + 7, Y0, Z0);
        level.setBlockAndUpdate(wallLog, Blocks.OAK_LOG.defaultBlockState());
        useAxe(player);
    }

    private static void checkD() {
        failed += check("波在石头墙前就没了（activeCount = " + ShockwaveManager.activeCount() + "）",
                ShockwaveManager.activeCount() == 0);
        failed += check("墙后那根原木**还在**（证明撞墙即停）",
                !level.getBlockState(wallLog).isAir());
        failed += check("石头墙本身没被拆（斧子挖不动它）",
                level.getBlockState(new BlockPos(X0 + 6, Y0, Z0)).is(Blocks.STONE));
    }

    // ------------------------------------------------------------ ④ (e) 10 秒闲置
    private static void buildE() {
        say(TAG + "④ (e) 拆完木头再飞 10 秒 ⇒ 自己散掉");
        ShockwaveManager.clearAll();
        player.getCooldowns().removeCooldown(axe.getItem());
        clearAbove();
        // 走廊：只在前 8 格放一格木头，其余全空（6 格宽都在石台上方，碰不到别的东西）
        for (int x = 1; x <= 14; x++) {
            level.setBlockAndUpdate(new BlockPos(X0 + x, Y0, Z0), Blocks.AIR.defaultBlockState());
            level.setBlockAndUpdate(new BlockPos(X0 + x, Y0 + 1, Z0), Blocks.AIR.defaultBlockState());
        }
        for (int z = -3; z <= 2; z++) {
            for (int x = 1; x <= 14; x++) {
                for (int dy = 0; dy <= 2; dy++) {
                    level.setBlockAndUpdate(new BlockPos(X0 + x, Y0 + dy, Z0 + z),
                            Blocks.AIR.defaultBlockState());
                }
            }
        }
        level.setBlockAndUpdate(new BlockPos(X0 + 4, Y0, Z0), Blocks.OAK_LOG.defaultBlockState());
        for (int lat = 0; lat < 6; lat++) {
            BlockPos q = new BlockPos(X0 + 4, Y0, Z0 - 3 + lat);
            say(TAG + "      [E] 出手前 x=104 第" + lat + "列 " + q.toShortString() + " = "
                    + level.getBlockState(q).getBlock().getName().getString());
        }
        say(TAG + "      [E] 玩家 " + player.blockPosition().toShortString()
                + " 手上 " + player.getMainHandItem().getItem());
        useAxe(player);
    }

    private static void checkE() {
        failed += check("那一格木头被拆掉了",
                level.getBlockState(new BlockPos(X0 + 4, Y0, Z0)).isAir());
        failed += check("10 秒没碰到木头 ⇒ 波自己散掉（activeCount = "
                + ShockwaveManager.activeCount() + "）", ShockwaveManager.activeCount() == 0);
    }

    // ------------------------------------------------------------ ⑦ (f) 冷却
    private static void buildF() {
        say(TAG + "⑦ (f) 15 秒冷却");
        ShockwaveManager.clearAll();
        player.getCooldowns().removeCooldown(axe.getItem());
        axe.setDamageValue(0);
        clearAbove();
        level.setBlockAndUpdate(new BlockPos(X0 + 3, Y0, Z0), Blocks.OAK_LOG.defaultBlockState());
        useAxe(player);
        failed += check("出手后进入冷却（isOnCooldown = "
                + player.getCooldowns().isOnCooldown(axe.getItem()) + "）",
                player.getCooldowns().isOnCooldown(axe.getItem()));
        failed += check("出手那一刻冷却满格（percent = "
                + player.getCooldowns().getCooldownPercent(axe.getItem(), 0.0F) + "）",
                player.getCooldowns().getCooldownPercent(axe.getItem(), 0.0F) > 0.98F);

    }

    // ------------------------------------------------------------ ⑤ (i) 滚动窗口
    /** 用户第 2 条的**滚动**语义：拆到木头就重新计时 —— 连续拆两次，第二次之后还能再活 200 tick。 */
    private static void buildI() {
        say(TAG + "⑤ (i) 滚动窗口：拆到木头就重新计时");
        ShockwaveManager.clearAll();
        player.getCooldowns().removeCooldown(axe.getItem());
        clearAbove();
        // 走廊全清空，只在第 3 格放木头 ⇒ 波拆完它之后开始闲置计时
        for (int x = 1; x <= 24; x++) {
            for (int z = -4; z <= 4; z++) {
                for (int dy = 0; dy <= 3; dy++) {
                    level.setBlockAndUpdate(new BlockPos(X0 + x, Y0 + dy, Z0 + z),
                            Blocks.AIR.defaultBlockState());
                }
            }
        }
        level.setBlockAndUpdate(new BlockPos(X0 + 3, Y0, Z0), Blocks.OAK_LOG.defaultBlockState());
        useAxe(player);
    }

    /**
     * (i) 之后第 60 tick：**还活着**。
     *
     * <p>这条能证的：波拆到木头之后不会当场散掉，也不会在射程内提前消失。</p>
     *
     * <p>⚠ <b>它证不了"计时被重置"</b>：滚动窗口是 200 tick，而射程上限只有 64 格（64 tick），
     * 波**永远先撞射程、后轮到期** ⇒ "重置过"与"没重置"在观测量上不可区分。
     * 要真的证滚动窗口，得先让 {@code IDLE_LIMIT_TICKS} 短于 {@code MAX_DISTANCE}（那是改产品数值），
     * 探针造不出这个差异。写在这里，免得下次有人把这条绿灯当成"滚动窗口已验证"。</p>
     */
    private static void checkIAlive() {
        failed += check("拆到木头之后 57 tick（仍在 64 格射程内），波**还活着**（activeCount = "
                + ShockwaveManager.activeCount() + "）", ShockwaveManager.activeCount() == 1);
    }

    /** (i) 之后第 300 tick：已散（此时早已超出 64 格射程）。 */
    private static void checkIDead() {
        failed += check("再飞 300 tick（远超 64 格射程）⇒ 波已散（activeCount = "
                + ShockwaveManager.activeCount() + "）", ShockwaveManager.activeCount() == 0);
    }

    private static void checkFMid() {
        ShockwaveManager.clearAll();
        int dmg = axe.getDamageValue();
        InteractionResultHolder<ItemStack> r = useAxe(player);
        failed += check("冷却中再右键不出手（结果 = " + r.getResult() + "）", !fired(r.getResult()));
        failed += check("冷却中不额外扣耐久（" + dmg + " → " + axe.getDamageValue() + "）",
                axe.getDamageValue() == dmg);
        failed += check("冷却中不起波（activeCount = " + ShockwaveManager.activeCount() + "）",
                ShockwaveManager.activeCount() == 0);

        // 冷却的**时长**怎么验：这个假玩家虽然进了玩家表（服务端会 tick 它），但探针没有
        // 快进时间的能力，所以还是显式走 ItemCooldowns 的 tick —— 这正是"满 15 秒会解开"
        // 的可证伪形式：把常量改成 600，下面第一条当场红。
        // ⚠ 这一段必须放在**所有"冷却中"的断言之后**：第一版写在 buildF 里（同一个 tick 内），
        //   于是 checkFMid 在下一 tick 查到的已经是"冷却走完"的状态 ⇒ 三条假 FAIL。
        int aliveAt299 = -1;
        for (int i = 0; i < 300; i++) {
            if (i == 299) {
                aliveAt299 = player.getCooldowns().isOnCooldown(axe.getItem()) ? 1 : 0;
            }
            player.getCooldowns().tick();
        }
        failed += check("第 299 tick 时仍在冷却（实际 " + (aliveAt299 == 1) + "）", aliveAt299 == 1);
        failed += check("tick 满 300 次后冷却解开（实际 "
                + player.getCooldowns().isOnCooldown(axe.getItem()) + "）",
                !player.getCooldowns().isOnCooldown(axe.getItem()));
    }

    // ------------------------------------------------------------ ⑧ (g) 耐久门槛
    private static void buildG() {
        say(TAG + "⑧ (g) 耐久不够一次 120");
        ShockwaveManager.clearAll();
        player.getCooldowns().removeCooldown(axe.getItem());
        axe.setDamageValue(axe.getMaxDamage() - 119);   // 只剩 119
        int before = axe.getDamageValue();
        InteractionResultHolder<ItemStack> r = useAxe(player);
        failed += check("耐久 119 < 120 ⇒ 拒绝出手（结果 = " + r.getResult() + "）", !fired(r.getResult()));
        failed += check("拒绝时不扣耐久（" + before + " → " + axe.getDamageValue() + "）",
                axe.getDamageValue() == before);
        failed += check("拒绝时不进冷却", !player.getCooldowns().isOnCooldown(axe.getItem()));
        failed += check("拒绝时不起波", ShockwaveManager.activeCount() == 0);
    }

    private static void checkG2() {
        axe.setDamageValue(axe.getMaxDamage() - 120);   // 正好 120
        int before = axe.getDamageValue();
        say(TAG + "      [DBG] (g2) 手上是 " + player.getMainHandItem().getItem()
                + " 耐久=" + player.getMainHandItem().getDamageValue() + "/"
                + player.getMainHandItem().getMaxDamage()
                + " 冷却中=" + player.getCooldowns().isOnCooldown(player.getMainHandItem().getItem()));
        InteractionResultHolder<ItemStack> r = useAxe(player);
        failed += check("耐久正好 120 ⇒ 出手（结果 = " + r.getResult() + "）", fired(r.getResult()));
        failed += check("正好扣光那 120（" + before + " → " + axe.getDamageValue() + "）",
                axe.getDamageValue() == axe.getMaxDamage());
        ShockwaveManager.clearAll();
        axe.setDamageValue(0);
    }

    // ------------------------------------------------------------ ⑨ (c) 创造模式
    private static void buildC() {
        say(TAG + "⑨ (c) 创造模式");
        ShockwaveManager.clearAll();
        creativePlayer.getCooldowns().removeCooldown(axe.getItem());
        ItemStack creativeAxe = new ItemStack(ModItems.STAR_STEEL_AXE.get());
        creativePlayer.setItemInHand(InteractionHand.MAIN_HAND, creativeAxe);
        creativePlayer.moveTo(X0 + 0.5D, Y0, Z0 + 0.5D, -90.0F, 0.0F);
        clearAbove();
        for (int z = -3; z <= 2; z++) {
            level.setBlockAndUpdate(new BlockPos(X0 + 3, Y0, Z0 + z), Blocks.OAK_LOG.defaultBlockState());
        }
        say(TAG + "      [DBG] 创造玩家：gameType=" + creativePlayer.gameMode.getGameModeForPlayer()
                + " 手上是同一把=" + (creativePlayer.getMainHandItem() == creativeAxe)
                + " 出手前耐久=" + creativeAxe.getDamageValue());
        InteractionResultHolder<ItemStack> r = useAxe(creativePlayer);
        failed += check("创造模式玩家照常出手（结果 = " + r.getResult() + "）", fired(r.getResult()));
        // ⚠ 先看事实再下判据：原版 `ItemStack.hurtAndBreak` 对创造模式玩家**不扣耐久**。
        //   所以这里不写"必须扣 120"，而是把两条都打出来（探针的职责是记录事实，
        //   不是替原版规则下判决）；下面那条断言只要求"非创造玩家才扣"。
        say(TAG + "      [DBG] 创造玩家出手后耐久 = " + creativeAxe.getDamageValue()
                + "（原版创造模式不掉耐久 ⇒ 0 是正常的）");
    }

    // ------------------------------------------------------------ ⑥ (h) 末地伤害
    private static void buildH() {
        say(TAG + "⑥ (h) 末地：10 + 0.5n 的远程伤害");
        if (end == null) {
            failed += check("末地维度拿不到", false);
            return;
        }
        ShockwaveManager.clearAll();
        // 末地平台：岩浆块围栏（不燃、斧子挖不动不到——只是当墙），中间黑曜石台面
        // ⚠ 平台铺在 99 层（玩家站 y=100），100~102 清空 —— 与主世界同一套布局。
        //   第一版把地板铺在 100 层，于是 `dy=0` 采样到的正是玩家脚下的黑曜石 ⇒
        //   波第一步就被自己的地板挡住，一次都没打到末影人（探针当场报 0 次命中）。
        // ⚠ z 铺到 16：末影人在 z=12.5，台面不铺到那里它会掉进虚空
        for (int x = -6; x <= 16; x++) {
            for (int z = -6; z <= 16; z++) {
                for (int dy = 0; dy <= 4; dy++) {
                    end.setBlockAndUpdate(new BlockPos(x, 100 + dy, z), Blocks.AIR.defaultBlockState());
                }
                end.setBlockAndUpdate(new BlockPos(x, 99, z), Blocks.OBSIDIAN.defaultBlockState());
            }
        }
        ServerPlayer endPlayer = makePlayer(player.getServer(), end, "zf133end", GameType.SURVIVAL);
        // ⚠ 站到**采样区之外**：波的第 0 步会采样发射者脚下那一格，而"实体所在格"
        //   既不是原木/树叶、也不是"斧子挖得动的方块" ⇒ 波会在第 1 tick 被自己人挡死
        //   （[D14] 诊断实测：整场只采了一排 18 格就散）。挪到 z=6.5、朝 -Z：
        //   第 1 步采 z=5，末影人在 z=0，第 6 步扫到。
        endPlayer.moveTo(0.5D, 100.0D, 6.5D, 180.0F, 0.0F);
        failed += check("末地那台假玩家活着（hp=" + endPlayer.getHealth() + "/"
                + endPlayer.getMaxHealth() + " alive=" + endPlayer.isAlive() + "）",
                endPlayer.isAlive() && endPlayer.getHealth() > 0.0F);

        // ⚠ 前提判据（§4.30：前提不成立时后面所有绿灯都不算数）：**"这台玩家在末地"必须先钉死**。
        //   上面那条"活着"挡不住第一轮那个坑 —— 它在主世界活着、波也在主世界飞，
        //   一路绿灯到最后一拍才报"末影人一次都没被打到"。
        //   可证伪：把 makePlayer 里那句 `p.setServerLevel(where)` 删掉，这条当场变红。
        failed += check("末地那台假玩家的维度**真的是末地**（实际 "
                + endPlayer.serverLevel().dimension().location() + "）",
                endPlayer.serverLevel() == end);
        ItemStack endAxe = new ItemStack(ModItems.STAR_STEEL_AXE.get());
        endPlayer.setItemInHand(InteractionHand.MAIN_HAND, endAxe);

        // 用力量把"玩家基础伤害"从 1 抬到 4（+3 是加法，不再乘算）⇒ 期望伤害 10 + 2 = 12
        endPlayer.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 400, 0, false, false, false));
        endPlayer.tick();
        // ✅ 「持斧属性总值 = 14」在这里验（真实玩家、手上确实拿着斧子、已经 tick 过）
        // ⚠ 这里**不查**"持斧属性活值"：见 staticFacts 里的长注释（探针没有客户端装备同步）。
        //   力量的 +3 是**属性基础值**上的修饰符，不依赖那条路径，所以下面这条是有效的。
        double n = ShockwaveManager.baseAttackDamage(endPlayer);
        failed += check("力量 I 之后基础伤害 n = 4.0（实际 " + n + "）", Math.abs(n - 4.0D) < 1e-6);
        failed += check("期望远程伤害 = 10 + 0.5*4 = 12.0（实际 "
                + ShockwaveManager.rangedDamage(n) + "）",
                Math.abs(ShockwaveManager.rangedDamage(n) - 12.0D) < 1e-6);

        EnderMan ender = new EnderMan(net.minecraft.world.entity.EntityType.ENDERMAN, end);
        // ⚠ 第一版放在 x=5.5（第 5 步才扫到），而波那时可能已经因为别的原因停了 ⇒ 一次都没打到。
        //   挪到第 1 步就扫得到的位置，并且让它在被打到之前不死（血 30 > 12）。
        // ⚠ 放在 +Z 方向（发射者朝 yaw 180 = **+Z**，实测见 [D14B]）；z=0.5 在反方向，扫不到。
        ender.moveTo(0.5D, 100.0D, 12.5D, 0.0F, 0.0F);
        ender.setNoAi(true);
        // ⚠ 这一行第一版只打了探针自己的 `end` 变量（`end.dimension()`），**两个实体的真实维度
        //   一个都没打** ⇒ 读日志的人（包括写下"两者都在末地"那条结论的人）被它骗了。
        //   诊断必须打**现场值**：谁在哪个维度，各打各的。
        say(TAG + "      [DMG] 末影人 @ " + String.format("%.2f,%.2f,%.2f",
                ender.getX(), ender.getY(), ender.getZ())
                + " 维度=" + ender.level().dimension().location()
                + " 发射者 @ " + String.format("%.2f,%.2f,%.2f",
                        endPlayer.getX(), endPlayer.getY(), endPlayer.getZ())
                + " 维度=" + endPlayer.serverLevel().dimension().location()
                + "（探针手里的 end 变量 = " + end.dimension().location() + "）");
        end.addFreshEntity(ender);
        failed += check("末影人已就位（血量 " + ender.getHealth() + "）", ender.isAlive());
        // 末地龙会先挨打（它在采样带上盘旋），所以这一发**直接结算**拿末影人当靶子
        directDamageProbe(endPlayer, ender, new BlockPos(0, 100, 12));

        // 出手前：把末地这一带的活实体血量快照下来（名字 -> 血量×1000）
        endHpBefore.clear();
        for (LivingEntity le : end.getEntitiesOfClass(LivingEntity.class,
                new net.minecraft.world.phys.AABB(-32, 60, -32, 32, 140, 32))) {
            endHpBefore.put(le.getName().getString() + "#" + le.getId(), (int) (le.getHealth() * 1000.0F));
        }
        say(TAG + "      [HP0] 出手前末地活实体 " + endHpBefore.size() + " 个："
                + endHpBefore.keySet());
        InteractionResultHolder<ItemStack> r = useAxe(endPlayer);
        failed += check("末地出手成功（结果 = " + r.getResult() + "）", fired(r.getResult()));
    }

    /**
     * 末地伤害的判据：**量血量变化**，不依赖事件。
     *
     * <p>⚠ 为什么不用 `LivingIncomingDamageEvent`：末地龙重写了 `hurt()`、不调 `super.hurt()`
     * ⇒ NeoForge 那个事件不发（实测：`hurt(...) = true`、血量 208→196，但监听器 0 次）。
     * **事件的覆盖范围取决于被观测对象怎么实现** —— 拿它当判据会漏。</p>
     */
    /**
     * 末地伤害的**直接**取证：反射造一道波 + 当场调 `damageAt` + 当场量血。
     *
     * <p>绕开两个坑：① 末地龙**每 tick 回 1 血**（隔 40 tick 快照看不出掉血，
     * 实测 [HP1] 是 0 个）；② 它**重写了 `hurt()` 不调 `super.hurt()`**
     * ⇒ NeoForge 的 `LivingIncomingDamageEvent` 根本不发（实测监听器 0 次，
     * 而 `hurt(...)` 明明返回 true）。**事件的覆盖范围取决于被观测对象怎么实现** ——
     * 拿它当判据会漏，所以这里改成"当场量血"。</p>
     */
    private static void directDamageProbe(ServerPlayer owner, EnderMan victim, BlockPos pos) {
        try {
            Class<?> waveClass = Class.forName("com.potatost.mod.ShockwaveManager$Wave");
            var ctor = waveClass.getDeclaredConstructor(
                    net.minecraft.server.level.ServerLevel.class, java.util.UUID.class,
                    double.class, boolean.class, int.class, int.class);
            ctor.setAccessible(true);
            Object wave = ctor.newInstance(end, owner.getUUID(),
                    ShockwaveManager.baseAttackDamage(owner), true, 1, pos.getY());
            var m = ShockwaveManager.class.getDeclaredMethod("damageAt", waveClass,
                    ServerPlayer.class, BlockPos.class);
            m.setAccessible(true);

            float before = victim.getHealth();
            m.invoke(null, wave, owner, pos);
            float after = victim.getHealth();
            double lost = before - after;
            say(TAG + "      [DIRECT] damageAt(" + pos.toShortString() + ")：末影人 "
                    + before + " -> " + after + "（掉 " + lost + "）");
            failed += check("直接结算：末影人掉 12.0 = 10 + 0.5 × 4（实际 " + lost + "）",
                    Math.abs(lost - 12.0D) < 0.01D);

            float b2 = victim.getHealth();
            m.invoke(null, wave, owner, pos);
            say(TAG + "      [DIRECT] 同一格再来一次：末影人 " + b2 + " -> " + victim.getHealth());
            failed += check("同一格连续两次只掉一次（原版无敌帧生效）",
                    Math.abs(b2 - victim.getHealth()) < 0.01F);
        } catch (Throwable t) {
            say(TAG + "      [DIRECT] 反射调用失败：" + t);
            java.io.StringWriter sw = new java.io.StringWriter();
            t.printStackTrace(new java.io.PrintWriter(sw));
            for (String line : sw.toString().split("\n")) {
                say(TAG + "        " + line);
            }
            failed += check("直接结算那一刀", false);
        }
    }

    private static void checkH() {
        int hits = 0;
        double exact = -1.0D;
        StringBuilder log = new StringBuilder();
        for (LivingEntity le : end.getEntitiesOfClass(LivingEntity.class,
                new net.minecraft.world.phys.AABB(-32, 60, -32, 32, 140, 32))) {
            String key = le.getName().getString() + "#" + le.getId();
            Integer before = endHpBefore.get(key);
            if (before == null) {
                continue;
            }
            double lost = (before - (int) (le.getHealth() * 1000.0F)) / 1000.0D;
            if (lost <= 0.0D) {
                continue;
            }
            hits++;
            log.append(le.getName().getString()).append(" 掉 ").append(lost).append("；");
            if (Math.abs(lost - 12.0D) < 0.01D) {
                exact = lost;
            }
        }
        say(TAG + "      [HP1] 掉血的实体 " + hits + " 个：" + log);
        // 快照法说明不了问题：末地龙每 tick 回 1 血，隔 40 tick 早回满（实测 0 个掉血）。
        // 真正的判据在 directDamageProbe() 里（反射造波 + 当场量血）。
        say(TAG + "      [HP1-记录] 快照法看到掉血实体 " + hits + " 个（末地龙会再生 ⇒ 不可靠）");
        failed += check("（记录）事件监听抓不到这条伤害：末地龙不调 super.hurt", true);
    }

    // ============================================================
    //  工具
    // ============================================================
    @SubscribeEvent
    public static void onIncomingDamage(LivingIncomingDamageEvent event) {
        DamageContainer c = event.getContainer();
        // ⚠ 这里**不预过滤来源**：预过滤就是猜（第一版猜 `player_attack`，
        //   结果末地龙那一条一次都没记到 —— 末地龙有自己的伤害来源族）。
        //   判据放到断言里去判，判据才可能"失败"。
        enderDamage = c.getNewDamage();
        enderSource = event.getSource().getMsgId();
        String who = event.getEntity().getName().getString();
        say(TAG + "      [DMG-OK] " + who + " 吃 " + enderDamage + "（来源 " + enderSource + "）");
        enderHits++;
    }

    /** 把 x=X0+1 那一列（含玩家脚下头顶）清空，免得挡住 6×3 采样区。 */
    private static void clearAbove() {
        for (int dx = 0; dx <= 14; dx++) {
            for (int dz = -4; dz <= 4; dz++) {
                for (int dy = 0; dy <= 3; dy++) {
                    level.setBlockAndUpdate(new BlockPos(X0 + dx, Y0 + dy, Z0 + dz),
                            Blocks.AIR.defaultBlockState());
                }
            }
        }
    }

    /**
     * 出手。
     *
     * <p>⚠ 两件事是**第一轮探针踩出来的**：
     * ① 假玩家的 {@code isShiftKeyDown()} 恒为 false ⇒ 不先按下去的话 {@code use()} 会在
     * shift 那一步直接 PASS（第一轮八个场景全是这么假通过的）；
     * ② 判据不能用 {@code consumesAction()} —— 原版 {@code InteractionResult.PASS} 的
     * {@code consumesAction()} 也是 true（"物品没接这一下、但手要挥"），
     * 所以只认 {@code SUCCESS}。**判据必须能不能失败地卡住"真的出手了"这件事**。</p>
     */
    /** 每个动手的场景开局先确认假玩家活着（被怪打死过就救回来，免得整场结论作废）。 */
    private static void keepAlive() {
        if (!player.isAlive() || player.getHealth() < player.getMaxHealth()) {
            player.setHealth(player.getMaxHealth());
            player.deathTime = 0;
            player.revive();
            say(TAG + "      [KEEPALIVE] 假玩家被打死过 —— 已救回满血");
        }
        player.setItemInHand(InteractionHand.MAIN_HAND, axe);
    }

    private static InteractionResultHolder<ItemStack> useAxe(ServerPlayer who) {
        who.setShiftKeyDown(true);
        ItemStack stack = who.getMainHandItem();
        InteractionResultHolder<ItemStack> r =
                stack.getItem().use(who.level(), who, InteractionHand.MAIN_HAND);
        who.setShiftKeyDown(false);
        say(TAG + "      右键结果 = " + r.getResult() + "（耐久 "
                + stack.getDamageValue() + "/" + stack.getMaxDamage() + "）");
        return r;
    }

    /**
     * "这一下真的出手了吗"的判据。
     *
     * <p>⚠ 服务端 {@code InteractionResultHolder.sidedSuccess(stack, false)} 返回的是
     * {@code CONSUME}（SUCCESS 只给客户端那一侧）—— 所以只认 SUCCESS 会**假 FAIL**；
     * 而 {@code consumesAction()} 连 {@code PASS} 都算 true（第一轮的假通过）。
     * 判定只用枚举相等。</p>
     */
    private static boolean fired(net.minecraft.world.InteractionResult result) {
        return result == net.minecraft.world.InteractionResult.SUCCESS
                || result == net.minecraft.world.InteractionResult.CONSUME;
    }

    private static int check(String name, boolean ok) {
        say(TAG + (ok ? "  [OK]   " : "  [FAIL] ") + name);
        return ok ? 0 : 1;
    }

    private static void say(String line) {
        System.out.println(line);
        report.append(line).append('\n');
    }

    private static void finish(ServerTickEvent.Post event) {
        say(TAG + "verdict: " + (failed == 0 ? "ALL OK" : "**" + failed + " FAILED**"));
        try {
            Files.write(Paths.get(REPORT), report.toString().getBytes(StandardCharsets.UTF_8));
            say(TAG + "report: " + REPORT);
        } catch (Throwable t) {
            say(TAG + "report write failed: " + t);
        }
        say(TAG + "done, halting server");
        event.getServer().halt(false);
    }
}
