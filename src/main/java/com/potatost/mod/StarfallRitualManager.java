package com.potatost.mod;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.HolderSet;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
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
import net.minecraft.world.level.saveddata.SavedData;
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
 * <p><b>状态存在哪里（ZF146 改）</b>：存在<b>存档里</b> —— {@link RitualData}（一个
 * {@link SavedData}，落在 {@code <存档>/data/potato_s_t_starfall.dat}），
 * 而<b>不是</b>存在这个类的 {@code static} 字段上。本类里已经没有任何"能活过一次世界切换"的
 * 世界引用：每 tick 都从 {@link MinecraftServer} 现取存档数据、现查维度。</p>
 *
 * <p><b>ZF146 修的是什么</b>（别人反馈的原话：「星轨坠 中途退出游戏就不会落下 再次进入就不能使用了」）：
 * 改之前是 {@code private static final Map<UUID, Ritual> ACTIVE}，而 {@code Ritual} 还攥着一个
 * {@link ServerLevel} 引用。单机"退回标题界面再进同一个世界"时，类加载器与静态字段跟着 JVM 活着、
 * 世界却换了一茬，于是：</p>
 * <ul>
 *   <li><b>不会落下</b>：{@code tick()} 算的是 {@code remain = endTick - ritual.level.getGameTime()}，
 *       而那个 {@code level} 是<b>上一个服务器</b>的、退出那一刻就停摆的时钟 ⇒ {@code remain} 冻住，
 *       永远走不到 0 ⇒ 陨石永远不生成；</li>
 *   <li><b>不能使用</b>：{@code use()} 看的是<b>新世界</b>的时钟，过了取消窗口就恒判"已锁定"，
 *       而那条死记录又永远不会被清掉 ⇒ 星轨坠从此永久失效。</li>
 * </ul>
 * <p>现在倒计时跨"退出到标题 / 关掉游戏 / 专用服务端重启"继续走（剩余时间按存档里的世界时间接着算），
 * 玩家仍然赖不掉那颗已经叫来的陨石 —— 这正是 ZF114 定下的语义。</p>
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

    /** 存档数据名：{@code <存档>/data/potato_s_t_starfall.dat}（ZF146）。 */
    public static final String DATA_ID = "potato_s_t_starfall";

    /** 全部粗矿的通用标签（粗振金也会挂进去 ⇒ 高威力档位能抽到它）。 */
    private static final TagKey<Item> RAW_MATERIALS =
            TagKey.create(Registries.ITEM, ResourceLocation.fromNamespaceAndPath("c", "raw_materials"));

    /** 起手/取消/拒绝三种结果，由物品类拿去决定要不要扣耐久。 */
    public enum Outcome { STARTED, CANCELLED, LOCKED }

    /** 探针计数：通报一共发了几条（只读，不参与任何逻辑，也不是世界状态）。 */
    static int debugAnnouncements;

    private StarfallRitualManager() {
    }

    // ------------------------------------------------------------------
    // ⓪ 状态：一条仪式 + 它的持久化容器
    // ------------------------------------------------------------------

    /**
     * 正在进行的仪式（一个玩家最多一个）。
     *
     * <p>⚠ 这里存的是<b>维度的 key</b>（{@link ResourceKey}）而不是 {@link ServerLevel}：
     * 存 level 引用就是 ZF146 那个 bug 的形状 —— 存档一换，引用指向的世界已经停摆，
     * 拿它的时钟算倒计时会永远算不完。</p>
     */
    public static final class Ritual {
        private final UUID owner;
        private final String name;
        private final ResourceKey<Level> dimension;
        private final double x;
        private final double y;
        private final double z;
        private final long endTick;
        private int nextAnnounce;
        private boolean finalWarned;

        private Ritual(ServerPlayer player, long endTick) {
            this.owner = player.getUUID();
            this.name = player.getName().getString();
            this.dimension = player.level().dimension();
            this.x = player.getX();
            this.y = player.getY();
            this.z = player.getZ();
            this.endTick = endTick;
        }

        /** 读盘用（{@link RitualData#load}）：一切都来自 NBT，不碰任何活对象。 */
        private Ritual(UUID owner, String name, ResourceKey<Level> dimension,
                       double x, double y, double z, long endTick) {
            this.owner = owner;
            this.name = name;
            this.dimension = dimension;
            this.x = x;
            this.y = y;
            this.z = z;
            this.endTick = endTick;
        }
    }

    /**
     * 仪式状态的持久化容器（ZF146）：一张 {@code UUID → Ritual} 表，跟着存档走。
     *
     * <p>存进<b>主世界</b>的数据目录（{@code server.overworld().getDataStorage()}），
     * 也就是 {@code <存档>/data/potato_s_t_starfall.dat} —— 与 {@code raids.dat} 同一个地方。
     * 放主世界而不是各维度各存一份：一条仪式本来就要跨维度结算（落点所在维度记在记录里）。</p>
     *
     * <p>{@code nextAnnounce / finalWarned} 也要存：不然读盘时"剩余 12 秒"会被当成刚过 20 秒，
     * 一边倒计时一边补发 20 秒 / 15 秒两条早就过时的通报（假通报比不通报更难看）。</p>
     *
     * <p>改这张表的四个口子（put/remove/clear/推进通报）都会 {@code setDirty()}：
     * 原版只在标记为脏时才会把 {@code .dat} 写下去，漏一个就等于"改了没存"。</p>
     */
    public static final class RitualData extends SavedData {

        private static final String KEY_LIST = "Rituals";
        private static final String KEY_OWNER = "Owner";
        private static final String KEY_NAME = "Name";
        private static final String KEY_DIM = "Dim";
        private static final String KEY_X = "X";
        private static final String KEY_Y = "Y";
        private static final String KEY_Z = "Z";
        private static final String KEY_END = "End";
        private static final String KEY_NEXT = "Next";
        private static final String KEY_WARNED = "Warned";

        /** 原版要的工厂：新建走无参构造，读盘走 {@link #load}。 */
        private static final SavedData.Factory<RitualData> FACTORY =
                new SavedData.Factory<>(RitualData::new, RitualData::load);

        private final Map<UUID, Ritual> rituals = new HashMap<>();

        private static RitualData load(CompoundTag tag, HolderLookup.Provider registries) {
            RitualData data = new RitualData();
            ListTag list = tag.getList(KEY_LIST, Tag.TAG_COMPOUND);
            for (int i = 0; i < list.size(); i++) {
                CompoundTag entry = list.getCompound(i);
                if (!entry.hasUUID(KEY_OWNER)) {
                    continue;                   // 没有主人的记录通报不出名字，丢掉这一条
                }
                ResourceLocation dim = ResourceLocation.tryParse(entry.getString(KEY_DIM));
                if (dim == null) {
                    continue;                   // 维度名读不出来 ⇒ 宁可不落，也不落到错的地方去
                }
                Ritual ritual = new Ritual(entry.getUUID(KEY_OWNER), entry.getString(KEY_NAME),
                        ResourceKey.create(Registries.DIMENSION, dim),
                        entry.getDouble(KEY_X), entry.getDouble(KEY_Y), entry.getDouble(KEY_Z),
                        entry.getLong(KEY_END));
                ritual.nextAnnounce = entry.getInt(KEY_NEXT);
                ritual.finalWarned = entry.getBoolean(KEY_WARNED);
                data.rituals.put(ritual.owner, ritual);
            }
            return data;
        }

        @Override
        public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
            ListTag list = new ListTag();
            for (Ritual ritual : this.rituals.values()) {
                CompoundTag entry = new CompoundTag();
                entry.putUUID(KEY_OWNER, ritual.owner);
                entry.putString(KEY_NAME, ritual.name);
                entry.putString(KEY_DIM, ritual.dimension.location().toString());
                entry.putDouble(KEY_X, ritual.x);
                entry.putDouble(KEY_Y, ritual.y);
                entry.putDouble(KEY_Z, ritual.z);
                entry.putLong(KEY_END, ritual.endTick);
                entry.putInt(KEY_NEXT, ritual.nextAnnounce);
                entry.putBoolean(KEY_WARNED, ritual.finalWarned);
                list.add(entry);
            }
            tag.put(KEY_LIST, list);
            return tag;
        }

        Ritual get(UUID owner) {
            return this.rituals.get(owner);
        }

        void put(Ritual ritual) {
            this.rituals.put(ritual.owner, ritual);
            setDirty();
        }

        void remove(UUID owner) {
            if (this.rituals.remove(owner) != null) {
                setDirty();
            }
        }

        void clear() {
            if (!this.rituals.isEmpty()) {
                this.rituals.clear();
                setDirty();
            }
        }

        boolean isEmpty() {
            return this.rituals.isEmpty();
        }

        int size() {
            return this.rituals.size();
        }

        /** <b>活视图</b>：tick 循环拿它的迭代器把走完的那条删掉（删的是表里那一行）。 */
        Collection<Ritual> rituals() {
            return this.rituals.values();
        }
    }

    /**
     * 取本存档的仪式表。
     *
     * <p>⚠ <b>每次现取，绝不缓存到 static</b>：任何"活过一次世界切换"的引用都会变成死引用，
     * 那正是 ZF146 那个 bug 的形状。原版 {@code computeIfAbsent} 在缓存命中时只是一次查表
     * （不在缓存里才读盘），所以每 tick 调它不心疼；反过来，没人开过仪式时它也不会写出文件
     * （{@code DimensionDataStorage.set} 不标脏，只有 {@code setDirty()} 才落盘）。</p>
     */
    private static RitualData data(MinecraftServer server) {
        return server.overworld().getDataStorage().computeIfAbsent(RitualData.FACTORY, DATA_ID);
    }

    // ------------------------------------------------------------------
    // ① 右键：起手 / 取消 / 拒绝
    // ------------------------------------------------------------------

    public static Outcome use(ServerPlayer player, ItemStack stack) {
        ServerLevel level = player.serverLevel();
        MinecraftServer server = level.getServer();
        long now = level.getGameTime();
        RitualData data = data(server);
        Ritual current = data.get(player.getUUID());

        if (current != null) {
            boolean cancelable = current.endTick - now > TOTAL_TICKS - CANCEL_TICKS;
            if (!cancelable) {
                player.displayClientMessage(Component.translatable("message.potato_s_t.starfall.locked")
                        .withStyle(ChatFormatting.RED), true);
                return Outcome.LOCKED;
            }
            data.remove(player.getUUID());
            player.displayClientMessage(Component.translatable("message.potato_s_t.starfall.cancelled")
                    .withStyle(ChatFormatting.GRAY), true);
            level.playSound(null, player.getX(), player.getY(), player.getZ(),
                    SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 0.6F, 0.5F);
            StarfallNetworking.sendTo(player, StarfallNetworking.PHASE_CLEAR, 0L,
                    player.getX(), player.getY(), player.getZ());
            return Outcome.CANCELLED;
        }

        Ritual ritual = new Ritual(player, now + TOTAL_TICKS);
        data.put(ritual);
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
        RitualData data = data(server);
        if (data.isEmpty()) {
            return;
        }
        Iterator<Ritual> it = data.rituals().iterator();
        while (it.hasNext()) {
            Ritual ritual = it.next();
            // ⚠ 现查维度：记录里没有 level 引用，所以"这台服务器现在还有没有那个维度"每 tick 都是真的在问。
            ServerLevel level = server.getLevel(ritual.dimension);
            if (level == null) {
                // 维度没了（整合包被换过、存档从别的整合包搬来）：静默放弃这一条，
                // 但不许抛异常 —— 一条读不懂的数据不该把整台服务器拖垮。
                it.remove();
                data.setDirty();
                continue;
            }
            long remain = ritual.endTick - level.getGameTime();

            while (ritual.nextAnnounce < ANNOUNCE_SECONDS.length
                    && remain <= ANNOUNCE_SECONDS[ritual.nextAnnounce] * 20L) {
                broadcast(server, Component.translatable("message.potato_s_t.starfall.countdown",
                        ritual.name, ANNOUNCE_SECONDS[ritual.nextAnnounce]).withStyle(ChatFormatting.RED));
                ritual.nextAnnounce++;
                data.setDirty();
            }

            if (!ritual.finalWarned && remain <= 20L) {
                ritual.finalWarned = true;
                data.setDirty();
                broadcast(server, Component.translatable("message.potato_s_t.starfall.warning",
                        ritual.name, floor(ritual.x), floor(ritual.y), floor(ritual.z))
                        .withStyle(ChatFormatting.RED, ChatFormatting.BOLD));
            }

            if (remain <= 0L) {
                summonMeteor(server, level, ritual);
                it.remove();
                data.setDirty();
            }
        }
    }

    /** 玩家重新登录：如果他手上那场仪式还在（存档里），补发一次同步包（HUD 才画得出来）。 */
    public static void onPlayerLogin(PlayerEvent.PlayerLoggedInEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }
        Ritual ritual = data(player.serverLevel().getServer()).get(player.getUUID());
        if (ritual != null) {
            StarfallNetworking.sendTo(player, StarfallNetworking.PHASE_START, ritual.endTick,
                    ritual.x, ritual.y, ritual.z);
        }
    }

    private static void summonMeteor(MinecraftServer server, ServerLevel level, Ritual ritual) {
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
    // ④ 探针接口（只读；不影响任何行为。⚠ 全部要 server：状态在存档里，不在类里）
    // ------------------------------------------------------------------

    public static boolean isActive(MinecraftServer server, UUID playerId) {
        return data(server).get(playerId) != null;
    }

    public static long endTickOf(MinecraftServer server, UUID playerId) {
        Ritual ritual = data(server).get(playerId);
        return ritual == null ? Long.MIN_VALUE : ritual.endTick;
    }

    public static int activeCount(MinecraftServer server) {
        return data(server).size();
    }

    public static void resetForTest(MinecraftServer server) {
        data(server).clear();
        debugAnnouncements = 0;
    }
}
