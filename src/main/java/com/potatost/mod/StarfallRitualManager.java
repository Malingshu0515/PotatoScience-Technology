package com.potatost.mod;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderSet;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.TagKey;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * 星轨坠的"仪式"状态机（0.11 ZF114）：倒计时 → 取消窗口 → 通报 → 落陨石 → 引爆 + 喷矿。
 *
 * <p><b>时间线</b>（用户原话逐条落点）：</p>
 * <pre>
 *   t=0        右键起手：扣 1 点耐久，锁定"那一刻所站的位置"（用户拍板），开始 600 tick 倒计时
 *   t=0~200    可取消窗口（前 10 秒）：再右键一次 ⇒ 取消，不扣耐久、不通报
 *   t=200 起   不可取消；在剩余 20/15/10/5/3/2 秒各向全服通报一条
 *   剩余 1 秒  通报「使用者 + 坐标」（最后一条警告，给别人跑路的时间）
 *   剩余 0     在 y=200 生成陨石（roll 7~20 威力），开始自由下坠
 *   落地       爆炸（带火）+ 粒子 + 喷射粗矿（档位看威力）
 * </pre>
 *
 * <p><b>为什么状态放在服务端的一张表里</b>：本工程**没有**玩家持久化数据（0 attachments），
 * 而倒计时要跨维度、跨死亡、跨掉线继续走（陨石已经"叫来了"，人不该能靠退出游戏赖掉）。
 * 所以用一个 {@code Map<UUID, Ritual>}，由服务器 tick 驱动；玩家重新登录时补发一次同步包
 * （见 {@link #onPlayerLogin}）让 HUD 恢复。</p>
 *
 * <p><b>威力 7~20 一个数两用</b>：既是原版爆炸的 power（TNT 是 4 ⇒ 这是 TNT 的 1.75~5 倍），
 * 也是掉落档位（用户原话「7-12只有铁铜 12以上所有粗矿标签都有 15以上固定产出3个粗振金」）。</p>
 *
 * <p><b>喷射的物品在爆炸之后才生成</b>：物品实体会被爆炸清掉 —— 先炸后撒，一滴不丢。</p>
 */
public final class StarfallRitualManager {

    /** 倒计时总长（30 秒）。 */
    public static final int TOTAL_TICKS = 20 * 30;
    /** 可取消窗口（前 10 秒）。 */
    public static final int CANCEL_TICKS = 20 * 10;
    /** 威力下限 / 上限（含）。 */
    public static final int MIN_POWER = 7;
    public static final int MAX_POWER = 20;
    /** 超过这个威力：从"全部粗矿"标签里抽（用户原话「12以上」）。 */
    public static final int TAG_POWER = 12;
    /** 达到这个威力：额外固定产出粗振金（用户原话「15以上」）。 */
    public static final int VIBRANIUM_POWER = 15;
    public static final int VIBRANIUM_COUNT = 3;
    /** 喷射的基础件数（威力每高 2 点 +1，7→6 件、20→12 件）。 */
    private static final int BASE_DROPS = 6;
    private static final int MAX_BONUS_DROPS = 6;

    /** 通报节点（剩余秒数）。 */
    private static final int[] ANNOUNCE_SECONDS = {20, 15, 10, 5, 3, 2};

    /** 全部粗矿的通用标签（粗振金也会挂进去 ⇒ 高威力档位能抽到它）。 */
    private static final TagKey<Item> RAW_MATERIALS =
            TagKey.create(Registries.ITEM, ResourceLocation.fromNamespaceAndPath("c", "raw_materials"));

    /** 起手/取消/拒绝三种结果，由物品类拿去决定要不要扣耐久。 */
    public enum Outcome { STARTED, CANCELLED, LOCKED }

    /** 正在进行的仪式（一个玩家最多一个）。 */
    private static final Map<UUID, Ritual> ACTIVE = new HashMap<>();

    /** 探针计数：通报一共发了几条（只读，不参与任何逻辑）。 */
    static int debugAnnouncements;

    private StarfallRitualManager() {
    }

    private static final class Ritual {
        private final UUID owner;
        private final String name;
        private final ServerLevel level;
        private final double x;
        private final double y;
        private final double z;
        private final long endTick;
        private int nextAnnounce;
        private boolean finalWarned;

        private Ritual(ServerPlayer player, long endTick) {
            this.owner = player.getUUID();
            this.name = player.getName().getString();
            this.level = player.serverLevel();
            this.x = player.getX();
            this.y = player.getY();
            this.z = player.getZ();
            this.endTick = endTick;
        }
    }

    // ------------------------------------------------------------------
    // ① 右键：起手 / 取消 / 拒绝
    // ------------------------------------------------------------------

    public static Outcome use(ServerPlayer player, ItemStack stack) {
        ServerLevel level = player.serverLevel();
        long now = level.getGameTime();
        Ritual current = ACTIVE.get(player.getUUID());

        if (current != null) {
            boolean cancelable = current.endTick - now > TOTAL_TICKS - CANCEL_TICKS;
            if (!cancelable) {
                player.displayClientMessage(Component.translatable("message.potato_s_t.starfall.locked")
                        .withStyle(ChatFormatting.RED), true);
                return Outcome.LOCKED;
            }
            ACTIVE.remove(player.getUUID());
            player.displayClientMessage(Component.translatable("message.potato_s_t.starfall.cancelled")
                    .withStyle(ChatFormatting.GRAY), true);
            level.playSound(null, player.getX(), player.getY(), player.getZ(),
                    SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 0.6F, 0.5F);
            StarfallNetworking.sendTo(player, StarfallNetworking.PHASE_CLEAR, 0L,
                    player.getX(), player.getY(), player.getZ());
            return Outcome.CANCELLED;
        }

        Ritual ritual = new Ritual(player, now + TOTAL_TICKS);
        ACTIVE.put(player.getUUID(), ritual);
        player.displayClientMessage(Component.translatable("message.potato_s_t.starfall.started",
                StarfallPendantItem.DURABILITY - 1).withStyle(ChatFormatting.GOLD), false);
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                SoundEvents.RESPAWN_ANCHOR_CHARGE, SoundSource.PLAYERS, 1.0F, 0.7F);
        StarfallNetworking.sendTo(player, StarfallNetworking.PHASE_START, ritual.endTick,
                ritual.x, ritual.y, ritual.z);
        return Outcome.STARTED;
    }

    // ------------------------------------------------------------------
    // ② 每 tick 推进（game 总线的 ServerTickEvent.Post，见档案 §4.20 的总线判据）
    // ------------------------------------------------------------------

    public static void onServerTick(ServerTickEvent.Post event) {
        tick(event.getServer());
    }

    /** 拆出来是为了让探针能自己喂时间（不必真等 30 秒）。 */
    static void tick(MinecraftServer server) {
        if (ACTIVE.isEmpty()) {
            return;
        }
        Iterator<Map.Entry<UUID, Ritual>> it = ACTIVE.entrySet().iterator();
        while (it.hasNext()) {
            Ritual ritual = it.next().getValue();
            long remain = ritual.endTick - ritual.level.getGameTime();

            while (ritual.nextAnnounce < ANNOUNCE_SECONDS.length
                    && remain <= ANNOUNCE_SECONDS[ritual.nextAnnounce] * 20L) {
                broadcast(server, Component.translatable("message.potato_s_t.starfall.countdown",
                        ritual.name, ANNOUNCE_SECONDS[ritual.nextAnnounce]).withStyle(ChatFormatting.RED));
                ritual.nextAnnounce++;
            }

            if (!ritual.finalWarned && remain <= 20L) {
                ritual.finalWarned = true;
                broadcast(server, Component.translatable("message.potato_s_t.starfall.warning",
                        ritual.name, floor(ritual.x), floor(ritual.y), floor(ritual.z))
                        .withStyle(ChatFormatting.RED, ChatFormatting.BOLD));
            }

            if (remain <= 0L) {
                summonMeteor(server, ritual);
                it.remove();
            }
        }
    }

    /** 玩家重新登录：如果他手上那场仪式还在，补发一次同步包（HUD 才画得出来）。 */
    public static void onPlayerLogin(PlayerEvent.PlayerLoggedInEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }
        Ritual ritual = ACTIVE.get(player.getUUID());
        if (ritual != null) {
            StarfallNetworking.sendTo(player, StarfallNetworking.PHASE_START, ritual.endTick,
                    ritual.x, ritual.y, ritual.z);
        }
    }

    private static void summonMeteor(MinecraftServer server, Ritual ritual) {
        ServerLevel level = ritual.level;
        int power = MIN_POWER + level.random.nextInt(MAX_POWER - MIN_POWER + 1);
        StarfallMeteorEntity meteor = ModEntities.STARFALL_METEOR.get().create(level);
        if (meteor == null) {
            return;                     // 理论上不会发生；真发生了就静默放弃，不要留下半个空指针
        }
        BlockPos spawn = BlockPos.containing(ritual.x, StarfallMeteorEntity.SPAWN_Y, ritual.z);
        level.getChunkAt(spawn);        // 先把落点那根区块加载出来，免得陨石掉进未生成的地形
        meteor.setPos(ritual.x, StarfallMeteorEntity.SPAWN_Y, ritual.z);
        meteor.setPower(power);
        meteor.setOwnerId(ritual.owner);
        level.addFreshEntity(meteor);
        level.playSound(null, ritual.x, ritual.y, ritual.z,
                SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.WEATHER, 2.0F, 1.3F);
        broadcast(server, Component.translatable("message.potato_s_t.starfall.incoming",
                floor(ritual.x), floor(ritual.z)).withStyle(ChatFormatting.GOLD));
        ServerPlayer owner = server.getPlayerList().getPlayer(ritual.owner);
        if (owner != null) {
            StarfallNetworking.sendTo(owner, StarfallNetworking.PHASE_FALLING, 0L,
                    ritual.x, ritual.y, ritual.z);
        }
    }

    // ------------------------------------------------------------------
    // ③ 落地：爆炸 + 粒子 + 喷射粗矿
    // ------------------------------------------------------------------

    static void impact(ServerLevel level, Vec3 pos, int power, Entity source, UUID ownerId) {
        // ① 爆炸（带火、破坏地形 —— 用户原话「7~20power的爆炸 带火」）。
        //    用原版实现：它自带性能控制与伤害结算，比自己遍历方块可靠得多。
        level.explode(source, pos.x, pos.y, pos.z, power, true, Level.ExplosionInteraction.BLOCK);

        // ② 粒子（服务端广播，原版自带距离裁剪；档案 §4.67）
        level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, pos.x, pos.y + 0.6D, pos.z, 1, 0.0D, 0.0D, 0.0D, 0.0D);
        level.sendParticles(ParticleTypes.FLASH, pos.x, pos.y + 1.0D, pos.z, 2, 0.4D, 0.4D, 0.4D, 0.0D);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, pos.x, pos.y + 1.0D, pos.z, 40, 3.0D, 2.0D, 3.0D, 0.05D);
        level.sendParticles(ParticleTypes.LAVA, pos.x, pos.y + 1.0D, pos.z, 30, 2.5D, 1.5D, 2.5D, 0.0D);
        level.sendParticles(ParticleTypes.FLAME, pos.x, pos.y + 1.0D, pos.z, 60, 3.0D, 1.5D, 3.0D, 0.08D);
        level.sendParticles(ParticleTypes.END_ROD, pos.x, pos.y + 1.0D, pos.z, 24, 2.0D, 1.5D, 2.0D, 0.12D);
        level.playSound(null, pos.x, pos.y, pos.z,
                SoundEvents.ENDER_DRAGON_GROWL, SoundSource.HOSTILE, 1.2F, 0.8F);

        // ③ 喷射粗矿 —— **必须在爆炸之后**：物品实体会被爆炸清掉，先炸后撒才一件不丢。
        RandomSource random = level.random;
        double bx = pos.x;
        double by = pos.y + 1.2D;
        double bz = pos.z;
        for (ItemStack stack : rollLoot(power, random)) {
            ItemEntity drop = new ItemEntity(level, bx, by, bz, stack);
            drop.setDeltaMovement(random.nextDouble() - 0.5D,
                    0.5D + random.nextDouble() * 0.7D,
                    random.nextDouble() - 0.5D);
            drop.setPickUpDelay(20);
            level.addFreshEntity(drop);
        }

        // ④ 通知施法者收尾（HUD 清空）
        if (ownerId != null && level.getServer() != null) {
            ServerPlayer owner = level.getServer().getPlayerList().getPlayer(ownerId);
            if (owner != null) {
                StarfallNetworking.sendTo(owner, StarfallNetworking.PHASE_CLEAR, 0L, pos.x, pos.y, pos.z);
            }
        }
    }

    /**
     * 落点掉落（纯函数，探针直接喂威力就能验档位）。
     *
     * <p>档位照用户原话：<b>7~12 只有铁/铜</b>（原版粗铁 + 粗铜）；
     * <b>13 以上</b>从 {@code #c:raw_materials} 全部粗矿里抽；<b>15 以上</b>再额外固定 3 个粗振金。</p>
     */
    static List<ItemStack> rollLoot(int power, RandomSource random) {
        List<ItemStack> drops = new ArrayList<>();
        int count = BASE_DROPS + Math.min(MAX_BONUS_DROPS, Math.max(0, power - MIN_POWER) / 2);
        for (int i = 0; i < count; i++) {
            if (power <= TAG_POWER) {
                drops.add(new ItemStack(random.nextBoolean() ? Items.RAW_IRON : Items.RAW_COPPER));
            } else {
                Item picked = pickRawOre(random);
                if (picked != null) {
                    drops.add(new ItemStack(picked));
                }
            }
        }
        if (power >= VIBRANIUM_POWER) {
            for (int i = 0; i < VIBRANIUM_COUNT; i++) {
                drops.add(new ItemStack(ModItems.RAW_VIBRANIUM.get()));
            }
        }
        return drops;
    }

    private static Item pickRawOre(RandomSource random) {
        Optional<HolderSet.Named<Item>> tag = BuiltInRegistries.ITEM.getTag(RAW_MATERIALS);
        if (tag.isEmpty() || tag.get().size() <= 0) {
            return null;                // 标签被别的整合包清空了也不能崩，只是这一档抽不出东西
        }
        return tag.get().get(random.nextInt(tag.get().size())).value();
    }

    private static void broadcast(MinecraftServer server, Component message) {
        debugAnnouncements++;
        server.getPlayerList().broadcastSystemMessage(message, false);
    }

    private static int floor(double value) {
        return (int) Math.floor(value);
    }

    // ------------------------------------------------------------------
    // ④ 探针接口（只读；不影响任何行为）
    // ------------------------------------------------------------------

    public static boolean isActive(UUID playerId) {
        return ACTIVE.containsKey(playerId);
    }

    public static long endTickOf(UUID playerId) {
        Ritual ritual = ACTIVE.get(playerId);
        return ritual == null ? Long.MIN_VALUE : ritual.endTick;
    }

    public static void resetForTest() {
        ACTIVE.clear();
        debugAnnouncements = 0;
    }
}
