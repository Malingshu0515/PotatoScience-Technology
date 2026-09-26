package com.potatost.mod;

import com.potatost.mod.client.ShockwaveClientState;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.network.PacketDistributor;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.neoforged.neoforge.network.handling.IPayloadContext;

/**
 * 冲击波的网络同步（0.11 ZF133）—— 只为了**客户端那道光墙**。
 *
 * <p><b>为什么只发一个包</b>：波的推进完全由服务端说了算（破坏方块是服务端的事），
 * 客户端只是"画一条看得见的波"。所以这里在**发射那一刻**发一次
 * （起点 + 主轴 + 正负 + 服务器世界时间戳），之后客户端自己按
 * {@code level.getGameTime()} 往前推 —— 与 ZF114 那套"发截止时刻、不发剩余秒数"
 * 是同一个思路：整场 10 秒只需 1 个包（用户要求过「不要太卡」）。</p>
 *
 * <p>广播范围 {@link #RANGE} 格：看不见的人不必收。</p>
 *
 * <p><b>为什么处理器里能引用客户端类</b>：{@code playToClient} 注册的处理器**只在客户端执行**，
 * 专用服务端永远走不到那一行；lambda 的目标类在首次执行时才解析（invokedynamic），
 * 所以服务端不会因为缺 {@code ShockwaveClientState} 而 {@code NoClassDefFoundError}。
 * 这条与 ZF114 的 {@code StarfallNetworking} 同源（NeoForge 官方推荐写法）。</p>
 */
public final class ShockwaveNetworking {

    /** 只发给这个距离内的人（格）。 */
    public static final double RANGE = 64.0D;

    public record ShockwavePayload(int x, int y, int z, boolean alongX, int sign, long startTick)
            implements CustomPacketPayload {

        public static final CustomPacketPayload.Type<ShockwavePayload> TYPE =
                new CustomPacketPayload.Type<>(ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "shockwave"));

        public static final StreamCodec<RegistryFriendlyByteBuf, ShockwavePayload> CODEC = StreamCodec.composite(
                ByteBufCodecs.VAR_INT, ShockwavePayload::x,
                ByteBufCodecs.VAR_INT, ShockwavePayload::y,
                ByteBufCodecs.VAR_INT, ShockwavePayload::z,
                ByteBufCodecs.BOOL, ShockwavePayload::alongX,
                ByteBufCodecs.VAR_INT, ShockwavePayload::sign,
                ByteBufCodecs.VAR_LONG, ShockwavePayload::startTick,
                ShockwavePayload::new);

        @Override
        public CustomPacketPayload.Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /** 模组总线（在 {@code PotatoST} 构造器里 addListener）。 */
    public static void register(RegisterPayloadHandlersEvent event) {
        event.registrar("1").playToClient(ShockwavePayload.TYPE, ShockwavePayload.CODEC,
                ShockwaveNetworking::handle);
    }

    private static void handle(ShockwavePayload payload, IPayloadContext context) {
        context.enqueueWork(() -> ShockwaveClientState.accept(payload));
    }

    /**
     * 发射时广播一次（附近 {@link #RANGE} 格内的人，含发射者自己）。
     *
     * <p>⚠ 与 ZF114 那条同一个道理：客户端没登记过这条通道时（无头服务端里的假玩家、
     * 原版客户端、两端版本对不上），NeoForge 的 {@code NetworkRegistry.checkPacket}
     * 会抛 {@code UnsupportedOperationException}（"Payload potato_s_t:shockwave may not be
     * sent to the client!"）。这时**不该让这一下右键失败** —— 破坏是服务端的事、
     * 光墙只是装饰：波照常推、耐久照常扣，只是那个人看不到光墙。
     * 日志用英文（Audit 的 E 项只认 lang 里的中文，见档案 §4.29），且只报一次免得刷屏。</p>
     */
    public static void broadcastWave(ServerPlayer player, int x, int y, int z, boolean alongX, int sign) {
        ShockwavePayload payload = new ShockwavePayload(x, y, z, alongX, sign,
                player.serverLevel().getGameTime());
        try {
            PacketDistributor.sendToPlayersNear(player.serverLevel(), null,
                    x + 0.5D, y + 0.5D, z + 0.5D, RANGE, payload);
        } catch (Throwable t) {
            if (!deliveryWarned) {
                deliveryWarned = true;
                System.err.println("[potato_s_t] shockwave payload could not be delivered "
                        + "(client has not registered the channel): " + t);
            }
        }
    }

    /** 投递失败只报一次（静态标志；不参与任何玩法逻辑）。 */
    private static boolean deliveryWarned;

    private ShockwaveNetworking() {
    }
}
