package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.common.Tags;
import net.neoforged.neoforge.items.IItemHandler;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.energy.IEnergyStorage;

/**
 * 矿物探测器（0.14 ZF169）：右键花 600 FE，报出**最近的一处矿物**并标注。
 *
 * <p><b>用户原话</b>：「加一个【矿物探测器】……本身有能量条（黄色）（1200FE）
 * 右键识别最近的（xz3x3区块y45格内寻找 没有则提示附近没有任何矿物）矿物并标注出来
 * （这个你自由发挥 是做成矿透那样的直接穿过别的方块显示矿物 或者 title/聊天栏告诉玩家矿物的方位都可以）
 * 右键一次消耗600FE」。</p>
 *
 * <h2>我替用户拍板的三处（都写在这里，改起来都是一处）</h2>
 * <ol>
 *   <li><b>「y45格内」按 <em>y ≤ 45</em> 读</b>（"45 层以下才有矿"的常规读法），
 *       不是"以玩家为中心上下 45 格"。要改就是 {@link #MAX_Y} 一个数。</li>
 *   <li><b>标注方式选「聊天栏 + 标题 + 方位/距离/坐标 + 目标处粒子柱」</b>：
 *       矿透式的<b>穿墙高亮</b>要自己写一层渲染（{@code LevelRenderer} 事件 +
 *       自定义 {@code VertexConsumer} 或每帧发方块轮廓包），本轮的探针验不到画面、
 *       只能验"报了什么"，所以先给**能验、也一定看得见**的这一种。
 *       粒子柱会被地形挡住 —— 但聊天栏/标题那三行永远看得见。</li>
 *   <li><b>能量存在物品自己的组件里</b>（{@code CustomData} 的 {@code potatost:energy}），
 *       不是另起一个 DataComponent 注册项：本工程还没有"带储能的物品"，
 *       用 CustomData 就<b>不用动注册表</b>，也不会和以后真加组件的轮次撞车。</li>
 * </ol>
 *
 * <p>能量条走原版那三个方法（{@code isBarVisible/getBarWidth/getBarColor}）——
 * 用户要的"黄色"就是本工程状态灯那支黄（{@code 0xFFE0C040}）。</p>
 */
public class OreDetectorItem extends Item {

    /** 储量（用户给的 1200 FE）。 */
    public static final int CAPACITY = 1200;
    /** 一次扫描的价（用户给的 600 FE）⇒ 满电正好两次。 */
    public static final int COST = 600;

    /** 横向：以玩家所在区块为中心的 3×3 区块 ⇒ ±1 区块 = ±16 格。 */
    public static final int CHUNK_RADIUS = 1;
    /** 纵向：y ≤ 45（见类注释第 1 条）。 */
    public static final int MAX_Y = 45;
    /** 聊天栏最多报几处（按距离排）。 */
    public static final int REPORT_LIMIT = 3;

    private static final String ENERGY_KEY = "potatost:energy";

    public OreDetectorItem(Properties properties) {
        super(properties);
    }

    // ============================================================
    //  能量（存在物品自己身上）
    // ============================================================
    public static int getEnergy(ItemStack stack) {
        CompoundTag tag = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        return tag.getInt(ENERGY_KEY);
    }

    public static void setEnergy(ItemStack stack, int value) {
        int clamped = Math.max(0, Math.min(CAPACITY, value));
        CompoundTag tag = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        tag.putInt(ENERGY_KEY, clamped);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
    }

    /** 给物品挂上 NeoForge 的能量能力（在 {@code RegisterCapabilitiesEvent} 里调一次）。 */
    public static IEnergyStorage energyStorage(ItemStack stack) {
        return new IEnergyStorage() {
            @Override
            public int receiveEnergy(int toReceive, boolean simulate) {
                int now = getEnergy(stack);
                int taken = Math.min(CAPACITY - now, Math.max(0, toReceive));
                if (!simulate && taken > 0) {
                    setEnergy(stack, now + taken);
                }
                return taken;
            }

            @Override
            public int extractEnergy(int toExtract, boolean simulate) {
                int now = getEnergy(stack);
                int given = Math.min(now, Math.max(0, toExtract));
                if (!simulate && given > 0) {
                    setEnergy(stack, now - given);
                }
                return given;
            }

            @Override
            public int getEnergyStored() {
                return getEnergy(stack);
            }

            @Override
            public int getMaxEnergyStored() {
                return CAPACITY;
            }

            @Override
            public boolean canExtract() {
                return true;
            }

            @Override
            public boolean canReceive() {
                return true;
            }
        };
    }

    // ============================================================
    //  物品条（黄色）
    // ============================================================
    @Override
    public boolean isBarVisible(ItemStack stack) {
        return true;
    }

    @Override
    public int getBarWidth(ItemStack stack) {
        return Math.round(13.0F * getEnergy(stack) / CAPACITY);
    }

    @Override
    public int getBarColor(ItemStack stack) {
        // 与状态灯/能量柱那支黄同色（0.13 ZF167 起全工程共用）
        return 0xFFE0C040;
    }

    // ============================================================
    //  右键扫描
    // ============================================================
    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) {
            // 客户端只做"手挥一下"，账在服务端算（否则两端各扣一次）
            return InteractionResultHolder.sidedSuccess(stack, true);
        }
        if (!(level instanceof ServerLevel serverLevel) || !(player instanceof ServerPlayer serverPlayer)) {
            return InteractionResultHolder.pass(stack);
        }
        int now = getEnergy(stack);
        if (now < COST) {
            serverPlayer.displayClientMessage(Component.translatable(
                    "message.potato_s_t.ore_detector.no_power", now, COST), true);
            serverLevel.playSound(null, player.getX(), player.getY(), player.getZ(),
                    SoundEvents.NOTE_BLOCK_BASS.value(), SoundSource.PLAYERS, 0.8F, 0.6F);
            return InteractionResultHolder.fail(stack);
        }
        setEnergy(stack, now - COST);

        List<OreHit> hits = scan(serverLevel, player);
        serverLevel.playSound(null, player.getX(), player.getY(), player.getZ(),
                SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 0.7F, 1.4F);
        if (hits.isEmpty()) {
            // 用户点名要的那一句，一个字不改
            serverPlayer.displayClientMessage(
                    Component.translatable("message.potato_s_t.ore_detector.none"), true);
            serverPlayer.sendSystemMessage(Component.translatable(
                    "message.potato_s_t.ore_detector.none.chat")
                    .withStyle(ChatFormatting.GRAY));
            return InteractionResultHolder.success(stack);
        }

        OreHit best = hits.get(0);
        int dx = best.pos().getX() - player.blockPosition().getX();
        int dz = best.pos().getZ() - player.blockPosition().getZ();
        int dy = best.pos().getY() - player.blockPosition().getY();
        String dir = direction(dx, dz);
        int dist = (int) Math.round(Math.sqrt((double) (dx * dx + dy * dy + dz * dz)));

        Component line = Component.translatable("message.potato_s_t.ore_detector.found",
                best.state().getBlock().getName(), arrow(dx, dz),
                dist, best.pos().getX(), best.pos().getY(), best.pos().getZ());
        serverPlayer.displayClientMessage(line, true);
        serverPlayer.sendSystemMessage(line.copy().withStyle(ChatFormatting.AQUA));
        serverPlayer.sendSystemMessage(Component.translatable(
                        "message.potato_s_t.ore_detector.arrow", arrow(dx, dz))
                .withStyle(ChatFormatting.YELLOW));
        if (hits.size() > 1) {
            StringBuilder more = new StringBuilder();
            for (int i = 1; i < Math.min(REPORT_LIMIT, hits.size()); i++) {
                OreHit h = hits.get(i);
                more.append(h.state().getBlock().getName().getString())
                        .append(" ").append(h.pos().toShortString()).append("　");
            }
            serverPlayer.sendSystemMessage(Component.translatable(
                            "message.potato_s_t.ore_detector.more", more.toString().trim())
                    .withStyle(ChatFormatting.DARK_GRAY));
        }
        marker(serverLevel, best.pos());
        return InteractionResultHolder.success(stack);
    }

    /** 扫描一次：3×3 区块、y ≤ 45、按距离排序。 */
    public static List<OreHit> scan(ServerLevel level, Player player) {
        BlockPos center = player.blockPosition();
        int cx = center.getX() >> 4;
        int cz = center.getZ() >> 4;
        List<OreHit> out = new ArrayList<>();
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();
        for (int chunkX = cx - CHUNK_RADIUS; chunkX <= cx + CHUNK_RADIUS; chunkX++) {
            for (int chunkZ = cz - CHUNK_RADIUS; chunkZ <= cz + CHUNK_RADIUS; chunkZ++) {
                int baseX = chunkX << 4;
                int baseZ = chunkZ << 4;
                for (int x = baseX; x < baseX + 16; x++) {
                    for (int z = baseZ; z < baseZ + 16; z++) {
                        for (int y = level.getMinBuildHeight(); y <= MAX_Y; y++) {
                            cursor.set(x, y, z);
                            BlockState state = level.getBlockState(cursor);
                            if (!isOre(state)) {
                                continue;
                            }
                            double d = center.distSqr(cursor);
                            out.add(new OreHit(cursor.immutable(), state, d));
                        }
                    }
                }
            }
        }
        out.sort((a, b) -> Double.compare(a.distSqr(), b.distSqr()));
        return out;
    }

    /**
     * 什么算"矿物"：NeoForge 的 {@code c:ores} 标签。
     *
     * <p>用标签而不是写死一张方块表 ⇒ 别的模组（以及本 mod 自己以后加的原矿）只要挂了
     * 这个标签就自动能被探到（与 ZF167 那只乙醇罐认 {@code c:ethanol} 同一个思路）。</p>
     */
    public static boolean isOre(BlockState state) {
        return state.is(Tags.Blocks.ORES);
    }

    /** 目标处的粒子柱：从矿物那一格往上冒一串符文（会被地形挡住 —— 见类注释第 2 条）。 */
    private static void marker(ServerLevel level, BlockPos pos) {
        for (int i = 0; i < 24; i++) {
            level.sendParticles(net.minecraft.core.particles.ParticleTypes.END_ROD,
                    pos.getX() + 0.5D, pos.getY() + 0.5D + i * 0.45D, pos.getZ() + 0.5D,
                    2, 0.08D, 0.0D, 0.08D, 0.01D);
        }
        level.sendParticles(net.minecraft.core.particles.ParticleTypes.GLOW,
                pos.getX() + 0.5D, pos.getY() + 0.5D, pos.getZ() + 0.5D, 20, 0.4D, 0.4D, 0.4D, 0.0D);
    }

    /** 八方位（聊天栏里的"它在哪边"）。 */
    public static String direction(int dx, int dz) {
        if (Math.abs(dx) <= 8 && Math.abs(dz) <= 8) {
            return "here";
        }
        if (Math.abs(dx) > 2 * Math.abs(dz)) {
            return dx > 0 ? "east" : "west";
        }
        if (Math.abs(dz) > 2 * Math.abs(dx)) {
            return dz > 0 ? "south" : "north";
        }
        if (dx > 0) {
            return dz > 0 ? "southeast" : "northeast";
        }
        return dz > 0 ? "southwest" : "northwest";
    }

    /** 指北针式的一行字（聊天栏第二行，不用资源包也看得懂）。 */
    public static String arrow(int dx, int dz) {
        StringBuilder sb = new StringBuilder();
        if (Math.abs(dx) > 8 || Math.abs(dz) > 8) {
            sb.append(dz < -8 ? "↑" : "");
            sb.append(dz > 8 ? "↓" : "");
            sb.append(dx < -8 ? "←" : "");
            sb.append(dx > 8 ? "→" : "");
        }
        sb.append(" ").append(dx >= 0 ? "+" : "").append(dx)
                .append(" / ").append(dz >= 0 ? "+" : "").append(dz);
        return sb.toString();
    }

    /** 一处命中。 */
    public record OreHit(BlockPos pos, BlockState state, double distSqr) {
    }
}
