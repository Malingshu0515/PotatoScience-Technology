package com.potatost.mod;

import com.potatost.mod.client.StarfallClientState;

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
 * 星轨坠的网络同步（0.11 ZF114）—— 本工程**第一个自定义数据包**。
 *
 * <p>要同步的东西只有一样：<b>倒计时还剩多久</b>（客户端要在快捷栏上方画那行红字）。
 * 做法是"发一次截止时刻"，不是"每 tick 发一次剩余秒数"：</p>
 * <ul>
 *   <li>服务端在起手 / 取消 / 进入下落 / 落地这四个时刻各发一包，带的是
 *       <b>{@code endTick}（服务器世界时间戳）</b>；</li>
 *   <li>客户端自己拿 {@code level.getGameTime()} 去减 —— 客户端世界时间与服务器同步推进，
 *       所以本地算出来的剩余秒数与服务端一致，而<b>整场倒计时只用了 4 个包</b>。</li>
 * </ul>
 *
 * <p>每 tick 发一次也能做，但那意味着 30 秒里 600 个包 × 每个施法者 ——
 * 用户明确说了「不要太卡」，这条是从源头省的。</p>
 *
 * <p><b>为什么处理器里能引用客户端类</b>：{@code playToClient} 注册的处理器**只在客户端执行**，
 * 专用服务端永远走不到那一行；Java 的 lambda 目标类是在**首次执行**时才解析的
 * （{@code invokedynamic} 的链接时机），所以服务端不会因为缺 {@code StarfallClientState}
 * 而 {@code NoClassDefFoundError}。这是 NeoForge 官方推荐写法。</p>
 */
public final class StarfallNetworking {

    /** 客户端收到后清空倒计时（取消或落地收尾）。 */
    public static final int PHASE_CLEAR = 0;
    /** 倒计时开始（带 {@code endTick}）。 */
    public static final int PHASE_START = 1;
    /** 陨石已经离手、正在下落（HUD 换成"下落中"）。 */
    public static final int PHASE_FALLING = 2;

    public record StarfallPayload(int phase, long endTick, int x, int y, int z) implements CustomPacketPayload {

        public static final CustomPacketPayload.Type<StarfallPayload> TYPE =
                new CustomPacketPayload.Type<>(ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "starfall"));

        public static final StreamCodec<RegistryFriendlyByteBuf, StarfallPayload> CODEC = StreamCodec.composite(
                ByteBufCodecs.VAR_INT, StarfallPayload::phase,
                ByteBufCodecs.VAR_LONG, StarfallPayload::endTick,
                ByteBufCodecs.VAR_INT, StarfallPayload::x,
                ByteBufCodecs.VAR_INT, StarfallPayload::y,
                ByteBufCodecs.VAR_INT, StarfallPayload::z,
                StarfallPayload::new);

        @Override
        public CustomPacketPayload.Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /** 模组总线（在 {@code PotatoST} 构造器里 addListener）。 */
    public static void register(RegisterPayloadHandlersEvent event) {
        event.registrar("1").playToClient(StarfallPayload.TYPE, StarfallPayload.CODEC, StarfallNetworking::handle);
    }

    private static void handle(StarfallPayload payload, IPayloadContext context) {
        context.enqueueWork(() -> StarfallClientState.accept(payload));
    }

    /** 发给某一个玩家（星轨坠的倒计时只有施法者自己要画）。 */
    public static void sendTo(ServerPlayer player, int phase, long endTick, double x, double y, double z) {
        try {
            PacketDistributor.sendToPlayer(player, new StarfallPayload(phase, endTick,
                    (int) Math.floor(x), (int) Math.floor(y), (int) Math.floor(z)));
        } catch (Throwable t) {
            // ⚠ ZF114 探针实测：客户端**没登记过这条通道**时，NeoForge 的
            //   NetworkRegistry.checkPacket 会抛 UnsupportedOperationException
            //   （"Payload potato_s_t:starfall may not be sent to the client!"）。
            //   触发场景：无头服务端里的假玩家、原版客户端、客户端与服务端模组版本对不上。
            //   这时**不该让整个右键失败** —— 倒计时归服务端管，HUD 只是装饰：
            //   仪式照常推进、耐久照常扣，只是那个人看不到那行红字。
            //   日志用英文（Audit 的 E 项只认 lang 里的中文，见档案 §4.29），且只报一次免得刷屏。
            if (!deliveryWarned) {
                deliveryWarned = true;
                System.err.println("[potato_s_t] starfall payload could not be delivered "
                        + "(client has not registered the channel): " + t);
            }
        }
    }

    /** 投递失败只报一次（静态标志；不参与任何玩法逻辑）。 */
    private static boolean deliveryWarned;

    private StarfallNetworking() {
    }
}
