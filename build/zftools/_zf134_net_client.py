# -*- coding: utf-8 -*-
"""_zf134_net_client.py —— 数据包与客户端光墙也跟着换成"方向向量"

## ① ShockwaveNetworking：包里原来带 `alongX + sign`，现在带 `dirX + dirZ`（两个 double）
`StreamCodec.composite` 的参数是"编解码器 + getter"交替，`ByteBufCodecs.DOUBLE` 直接可用。

## ② client/ShockwaveClientState：Wave 记录改成 dirX/dirZ（前端位置按前缘 + 法线算）

## ③ client/ShockwaveRenderer：光墙不再"沿 x 或沿 z 的一面平板"，
    改成按法线算两个端点 ⇒ **斜着放也能正对朝向**
      左端 = 前缘 - 法线 × 半宽     右端 = 前缘 + 法线 × 半宽
    （朝向 +X 时法线 = (0,+1) ⇒ 端点落在 z ∓ half，与旧版逐字一致）

跑法：python build\\zftools\\_zf134_net_client.py
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
NET = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveNetworking.java"
STATE = r"E:\PotatoST\src\main\java\com\potatost\mod\client\ShockwaveClientState.java"
REND = r"E:\PotatoST\src\main\java\com\potatost\mod\client\ShockwaveRenderer.java"


def splice(s, start, end, new, label):
    assert s.count(start) == 1, "%s 起点 %d 次" % (label, s.count(start))
    assert s.count(end) == 1, "%s 终点 %d 次" % (label, s.count(end))
    i = s.index(start)
    j = s.index(end) + len(end)
    assert j > i, "%s 终点在起点前" % label
    print("[OK ] %-22s %d -> %d 字符" % (label, (j - i), len(new)))
    return s[:i] + new + s[j:]


# ---------------- ① 数据包 ----------------
NET_RECORD_OLD = """    public record ShockwavePayload(int x, int y, int z, boolean alongX, int sign, long startTick)
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
                ShockwavePayload::new);"""

NET_RECORD_NEW = """    /**
     * ⚠ 方向用**单位向量**（ZF134 起）：旧版带的是"主轴 + 正负号"两个字段，
     * 只能表达正东南西北；现在带 {@code dirX / dirZ}，任意角度都行。
     */
    public record ShockwavePayload(int x, int y, int z, double dirX, double dirZ, long startTick)
            implements CustomPacketPayload {

        public static final CustomPacketPayload.Type<ShockwavePayload> TYPE =
                new CustomPacketPayload.Type<>(ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "shockwave"));

        public static final StreamCodec<RegistryFriendlyByteBuf, ShockwavePayload> CODEC = StreamCodec.composite(
                ByteBufCodecs.VAR_INT, ShockwavePayload::x,
                ByteBufCodecs.VAR_INT, ShockwavePayload::y,
                ByteBufCodecs.VAR_INT, ShockwavePayload::z,
                ByteBufCodecs.DOUBLE, ShockwavePayload::dirX,
                ByteBufCodecs.DOUBLE, ShockwavePayload::dirZ,
                ByteBufCodecs.VAR_LONG, ShockwavePayload::startTick,
                ShockwavePayload::new);"""

NET_BROADCAST_OLD = "    public static void broadcastWave(ServerPlayer player, int x, int y, int z, boolean alongX, int sign) {"
NET_BROADCAST_NEW = "    public static void broadcastWave(ServerPlayer player, int x, int y, int z, double dirX, double dirZ) {"

NET_BODY_OLD = """        ShockwavePayload payload = new ShockwavePayload(x, y, z, alongX, sign,
                player.serverLevel().getGameTime());"""
NET_BODY_NEW = """        ShockwavePayload payload = new ShockwavePayload(x, y, z, dirX, dirZ,
                player.serverLevel().getGameTime());"""

# ---------------- ② 客户端状态 ----------------
ST_WAVE_OLD = """    /** 一波的起点与方向。 */
    public static final class Wave {
        public final double x;
        public final double y;
        public final double z;
        public final boolean alongX;
        public final int sign;
        public final long startTick;

        Wave(double x, double y, double z, boolean alongX, int sign, long startTick) {
            this.x = x;
            this.y = y;
            this.z = z;
            this.alongX = alongX;
            this.sign = sign;
            this.startTick = startTick;
        }
    }"""

ST_WAVE_NEW = """    /**
     * 一波的起点与方向。
     *
     * <p>方向是**单位向量**（ZF134 起）：旧版存"主轴 + 正负号"，只能画四个正方向的墙。</p>
     */
    public static final class Wave {
        public final double x;
        public final double y;
        public final double z;
        public final double dirX;
        public final double dirZ;
        public final long startTick;

        Wave(double x, double y, double z, double dirX, double dirZ, long startTick) {
            this.x = x;
            this.y = y;
            this.z = z;
            this.dirX = dirX;
            this.dirZ = dirZ;
            this.startTick = startTick;
        }
    }"""

ST_ACCEPT_OLD = """        WAVES.add(new Wave(payload.x(), payload.y(), payload.z(),
                payload.alongX(), payload.sign(), payload.startTick()));"""
ST_ACCEPT_NEW = """        WAVES.add(new Wave(payload.x(), payload.y(), payload.z(),
                payload.dirX(), payload.dirZ(), payload.startTick()));"""

# ---------------- ③ 渲染器 ----------------
R_CALL_OLD = """        for (ShockwaveClientState.Wave wave : waves) {
            float age = (float) (now - wave.startTick) + partial;
            if (age < 0.0F) {
                continue;
            }
            double main = (wave.alongX ? wave.x : wave.z) + wave.sign * age;
            double lateral = wave.alongX ? wave.z : wave.x;
            // 芯在方块中心
            double mainCenter = main + 0.5D;
            double lateralCenter = lateral + 0.5D;
            double baseY = wave.y + 1.0D;
            float fade = Math.max(0.0F, 1.0F - age / ShockwaveClientState.MAX_SHOW_TICKS);

            drawWall(holder, wave.alongX, mainCenter, lateralCenter, baseY,
                    ShockwaveManager.HEIGHT, fade);
        }"""
R_CALL_NEW = """        for (ShockwaveClientState.Wave wave : waves) {
            float age = (float) (now - wave.startTick) + partial;
            if (age < 0.0F) {
                continue;
            }
            // 前缘中心：起点 + 单位方向 × 已经过的时间（服务端 1 格/tick，客户端同拍推算）
            double frontX = wave.x + 0.5D + wave.dirX * age;
            double frontZ = wave.z + 0.5D + wave.dirZ * age;
            // 阵面方向 = 左手法线（把朝向转 90°）：朝向 +X 时它是 (0,+1)，与旧版一致
            double perpX = -wave.dirZ;
            double perpZ = wave.dirX;
            double baseY = wave.y + 1.0D;
            float fade = Math.max(0.0F, 1.0F - age / ShockwaveClientState.MAX_SHOW_TICKS);

            drawWall(holder, frontX, frontZ, perpX, perpZ, baseY,
                    ShockwaveManager.HEIGHT, fade);
        }"""

R_DRAW_OLD_START = "    private static void drawWall(Matrix4fHolder holder, boolean alongX, double main, double lateral,"
R_DRAW_END = "    /** 一个竖直的四边形：底边两个点 alpha 高、顶边两个点 alpha 低（底亮顶淡）。 */"

R_DRAW_NEW = '''    /**
     * 一道波的全部四边形（每层一个正面 + 顶上的余晖）。
     *
     * <p><b>阵面由「前缘中心 + 法线」直接给出两个端点</b>（ZF134：任意角度）：
     * {@code 端点 = 前缘 ± 法线 × 半宽} —— 这样斜着放时光墙也正对朝向。
     * 朝向为 +X 时法线是 (0, +1)，端点于是落在 z ∓ 半宽，与旧版逐字一致。</p>
     *
     * <p>⚠⚠ <b>必须先算「要不要画」，再碰 `Tesselator`</b>（ZF133 用户实机抓出的崩溃）：
     * 原版 `BufferBuilder.buildOrThrow()` 对**空** builder 是**直接抛**
     * （名字里的 orThrow 就是这个意思），根本没有「清空它」这种用法。
     * 我第一版写成「没东西就 `else { buffer.buildOrThrow(); }` 收个尾」，
     * 于是**波淡出的最后两帧**（三层 alpha 都被 `<= 2` 挡掉）必炸：
     * `IllegalStateException: BufferBuilder was empty`。</p>
     */
    private static void drawWall(Matrix4fHolder holder, double frontX, double frontZ,
                                 double perpX, double perpZ, double baseY, int height, float fade) {
        // ⚠ 门槛与下面循环里**同一份算法**（否则「过了门槛却没画」又会欠一次收尾）
        int coreAlpha = (int) Math.round(255.0D * LAYERS[0][2] * fade * 0.75D);
        if (coreAlpha <= 2) {
            return;   // 整道波都淡到看不见了：**不开始** builder
        }
        BufferBuilder buffer = Tesselator.getInstance()
                .begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION_COLOR);
        for (double[] layer : LAYERS) {
            double half = ShockwaveManager.HALF_WIDTH + layer[0];
            double vx = perpX * half;
            double vz = perpZ * half;
            double top = baseY + height + layer[1];
            int alpha = (int) Math.round(255.0D * layer[2] * fade * 0.75D);
            if (alpha <= 2) {
                continue;
            }
            // 内层更白、外层更青（星璨那点意思）
            float[] rgb = layer[2] > 0.5D ? CORE_RGB : OUTER_RGB;
            int ta = alpha;
            int ba = Math.min(255, alpha + 60);
            quad(buffer, holder, frontX - vx, frontZ - vz, frontX + vx, frontZ + vz,
                    top, baseY, rgb, ta, ba);
        }
        // 顶上的余晖（只往上一小块，朝上淡出）
        int glowAlpha = (int) Math.round(255.0D * GLOW_ALPHA * fade);
        if (glowAlpha > 2) {
            double half = ShockwaveManager.HALF_WIDTH + 0.3D;
            double vx = perpX * half;
            double vz = perpZ * half;
            double top = baseY + ShockwaveManager.HEIGHT + GLOW_HEIGHT;
            quad(buffer, holder, frontX - vx, frontZ - vz, frontX + vx, frontZ + vz, top,
                    baseY + ShockwaveManager.HEIGHT, CORE_RGB, 0, glowAlpha);
        }
        // 到这里一定至少有一个四边形（门槛已在函数开头判过）
        BufferUploader.drawWithShader(buffer.buildOrThrow());
    }

'''

R_QUAD_START = "    /** 一个竖直的四边形：底边两个点 alpha 高、顶边两个点 alpha 低（底亮顶淡）。 */"
R_QUAD_END = "    /** 只是为了让 {@code org.joml.Matrix4f} 的 import 收在一处（渲染热路径里取矩阵）。 */"

R_QUAD_NEW = '''    /**
     * 一个竖直的四边形。
     *
     * <p>两个底端点、两个顶端点由调用方按法线算好传进来 ⇒ **斜着也能正对朝向**。
     * 底边 alpha 高、顶边 alpha 低（底亮顶淡）。</p>
     */
    private static void quad(BufferBuilder buffer, Matrix4fHolder holder,
                             double x0, double z0, double x1, double z1,
                             double topY, double bottomY, float[] rgb, int bottomAlpha, int topAlpha) {
        buffer.addVertex(holder.matrix(), (float) x0, (float) bottomY, (float) z0)
                .setColor(rgb[0], rgb[1], rgb[2], bottomAlpha / 255.0F);
        buffer.addVertex(holder.matrix(), (float) x1, (float) bottomY, (float) z1)
                .setColor(rgb[0], rgb[1], rgb[2], bottomAlpha / 255.0F);
        buffer.addVertex(holder.matrix(), (float) x1, (float) topY, (float) z1)
                .setColor(rgb[0], rgb[1], rgb[2], topAlpha / 255.0F);
        buffer.addVertex(holder.matrix(), (float) x0, (float) topY, (float) z0)
                .setColor(rgb[0], rgb[1], rgb[2], topAlpha / 255.0F);
    }

'''


def main():
    # ① 网络
    s = io.open(NET, encoding="utf-8").read()
    s = splice(s, NET_RECORD_OLD, "ShockwavePayload::new);", NET_RECORD_NEW, "包结构")
    assert s.count(NET_BROADCAST_OLD) == 1, "broadcastWave 签名 %d 次" % s.count(NET_BROADCAST_OLD)
    s = s.replace(NET_BROADCAST_OLD, NET_BROADCAST_NEW, 1)
    assert s.count(NET_BODY_OLD) == 1, "broadcastWave 体 %d 次" % s.count(NET_BODY_OLD)
    s = s.replace(NET_BODY_OLD, NET_BODY_NEW, 1)
    assert "alongX" not in s and "payload.sign()" not in s
    io.open(NET, "w", encoding="utf-8", newline="\n").write(s)
    print("[OK ] ShockwaveNetworking：dirX/dirZ")
    print("     签名：%s" % NET_BROADCAST_NEW.strip()[:90])

    # ② 客户端状态
    s = io.open(STATE, encoding="utf-8").read()
    assert s.count(ST_WAVE_OLD) == 1, "Wave 记录 %d 次" % s.count(ST_WAVE_OLD)
    s = s.replace(ST_WAVE_OLD, ST_WAVE_NEW, 1)
    assert s.count(ST_ACCEPT_OLD) == 1, "accept %d 次" % s.count(ST_ACCEPT_OLD)
    s = s.replace(ST_ACCEPT_OLD, ST_ACCEPT_NEW, 1)
    assert "alongX" not in s
    io.open(STATE, "w", encoding="utf-8", newline="\n").write(s)
    print("[OK ] ShockwaveClientState：dirX/dirZ")

    # ③ 渲染器
    s = io.open(REND, encoding="utf-8").read()
    assert s.count(R_CALL_OLD) == 1, "调用段 %d 次" % s.count(R_CALL_OLD)
    s = s.replace(R_CALL_OLD, R_CALL_NEW, 1)
    s = splice(s, R_DRAW_OLD_START, R_DRAW_END, R_DRAW_NEW + R_DRAW_END, "drawWall 整段")
    # quad 整段（从 quad 的注释到 Matrix4fHolder 的注释）
    s = splice(s, R_QUAD_START, R_QUAD_END, R_QUAD_NEW + R_QUAD_END, "quad 整段") \
        if s.count(R_QUAD_START) == 1 else s
    code = re.sub(r"/\*[\s\S]*?\*/", "", s)
    code = re.sub(r"//[^\n]*", "", code)
    assert "alongX" not in code, "渲染器代码里还有 alongX"
    assert code.count("buildOrThrow()") == 1, "buildOrThrow 数量 %d" % code.count("buildOrThrow()")
    io.open(REND, "w", encoding="utf-8", newline="\n").write(s)
    print("[OK ] ShockwaveRenderer：按法线算端点；buildOrThrow 仍只有 1 处")


main()
