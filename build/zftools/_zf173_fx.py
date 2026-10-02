# -*- coding: utf-8 -*-
u"""_zf173_fx.py —— ZF173：黑洞特效重写（用户「再炫亿点，就当你炫技了，当然还是要为性能着想的」）

## 思路：**不是加粒子，是换画法**

旧版每 tick 发 ~300 个**独立包**（每个点一次 `sendParticles`），而且点**不带速度** ⇒
既费又"死"。新版三条原则：

1. **硬上限**：所有发包都走 {@code fx(...)} 助手，每 tick 每个黑洞最多 {@code FX_BUDGET_PER_TICK}
   个包 —— 超了直接不发。上限是**代码里的常量**，不是"应该不会太多"。
2. **错峰**：不同层挂在不同的 tick 相位（偶/奇、每 4、每 5、每 12 tick），
   同一 tick 只画该画的那些 ⇒ 观感是**层次**，不是"一锅粥"，包数还降下来了。
3. **带速度**（关键）：粒子用 `speed` 参数给**切向**速度 ⇒ 真的在绕着转；
   内落流给**朝心**速度 ⇒ 真的往里掉。静态点阵和"流体"的差别全在这儿。

## 五幕（20 秒 = 400 tick，与 LIFETIME 对齐）

| 幕 | tick | 画什么 |
|---|---|---|
| ① 降临 | 0–40 | 音爆冲击环由小扩到大、`FLASH` 闪白、四周尘土被吸起来 |
| ② 稳定 | 40–330 | 光子环（自转）+ 事件视界暗盘 + 三层反向吸积盘 + 内落粒子雨 + 收缩透镜光弧 + 电弧 + 低频轰鸣 |
| ③ 前兆 | 330–400 | 环的**转向反过来**、光弧急速收缩、鼓点加密、颜色转冷 |
| ④ 坍缩 | 400 | 大爆炸 + 音爆环 + 视界闪白（原有 collapse） |
| ⑤ 遗迹 | 之后 | 码下的方块小丘留着（原有） |
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\BlackHoleManager.java"
t = io.open(P, encoding="utf-8").read()

# ---------- 1) 常量：预算 + 分幕刻度 + 配色 ----------
CONST_ANCHOR = u"    /** 每 tick 最多**检查**多少个位置（带游标续扫；一轮 ≈ 130 tick ≈ 6.5 秒扫完 53 万）。 */"
NEW_CONST = u'''    /**
     * 每 tick 每个黑洞最多发多少个**粒子包**（0.14 ZF173：炫技可以，TPS 不能换）。
     *
     * <p>所有特效都必须走 {@link #fx} 这个助手，它在超预算时**直接不发** ——
     * 于是"再炫"也有硬顶：一层层叠上去只会被裁掉最后几层，不会把服务器拖死。</p>
     */
    public static final int FX_BUDGET_PER_TICK = 320;
    /** 分幕：降临结束 / 前兆开始（总长 = {@link #LIFETIME}）。 */
    public static final int FX_ARRIVE = 40;
    public static final int FX_OMEN = 330;
'''
t = t.replace(CONST_ANCHOR, NEW_CONST + CONST_ANCHOR, 1)

# ---------- 2) 整个 fx() 换掉（连 ring/disk 一起，花括号配平抠出来） ----------
def cut(text, sig):
    start = text.index(sig)
    i = text.index(u"{", start)
    depth = 0
    end = i
    while end < len(text):
        if text[end] == u"{":
            depth += 1
        elif text[end] == u"}":
            depth -= 1
            if depth == 0:
                break
        end += 1
    return start, end + 1

FX = u'''    /** 一个黑洞当前这一 tick 已经发出去的包数（每 tick 开头清零，见 {@link #tick}）。 */
    private static int fxSpent;

    /**
     * 发一"包"粒子（唯一出口）：超预算直接丢。
     *
     * <p>{@code speed} 是**速度**不是"扩散" —— 给切向速度粒子就绕圈、给朝心速度就往里掉，
     * 这是"点阵"和"流体"的分界（旧版全靠 0 速度的静态点 ⇒ 看着像撒了一把亮片）。</p>
     */
    private static void fx(ServerLevel level, ParticleOptions type, double x, double y, double z,
                           int count, double dx, double dy, double dz, double speed) {
        if (fxSpent >= FX_BUDGET_PER_TICK) {
            return;
        }
        fxSpent++;
        level.sendParticles(type, x, y, z, count, dx, dy, dz, speed);
    }

    /** 一圈：给**切向**速度 ⇒ 粒子真的在转（不是一个个静止的点）。 */
    private static void ring(ServerLevel level, ParticleOptions type, double cx, double cy, double cz,
                             double radius, int count, double phase, double tilt, double spinSpeed) {
        for (int i = 0; i < count; i++) {
            double a = phase + i * (Math.PI * 2.0D / count);
            double x = cx + Math.cos(a) * radius;
            double z = cz + Math.sin(a) * radius;
            double y = cy + Math.sin(a) * radius * tilt;
            // 切向 = (-sin, 0, cos)；乘上 spinSpeed 就是"绕着奇点转"的速度
            fx(level, type, x, y, z, 1, -Math.sin(a) * spinSpeed, 0.0D, Math.cos(a) * spinSpeed,
                    spinSpeed);
        }
    }

    /** 一张盘：螺旋 + 倾角 + 切向速度（吸积盘就是靠这个"转"起来的）。 */
    private static void disk(ServerLevel level, ParticleOptions type, double cx, double cy, double cz,
                             double radius, int count, double phase, double tilt, double spinSpeed) {
        for (int i = 0; i < count; i++) {
            double a = phase + i * (Math.PI * 2.0D / count) + i * 0.12D;
            double r = radius * (0.75D + 0.25D * Math.sin(a * 3.0D + phase));
            double x = cx + Math.cos(a) * r;
            double z = cz + Math.sin(a) * r;
            double y = cy + Math.sin(a) * r * tilt;
            fx(level, type, x, y, z, 1, -Math.sin(a) * spinSpeed, 0.0D, Math.cos(a) * spinSpeed,
                    spinSpeed);
        }
    }

    /**
     * 特效主循环（0.14 ZF173 重写）：五幕、错峰、带速度、**有硬预算**。
     *
     * <p>跟旧版比：包数不一定更少，但**观感是流体**（切向速度）、层次分明（错峰），
     * 而且无论怎么叠都撞不破 {@link #FX_BUDGET_PER_TICK}。</p>
     */
    private static void fx(Hole hole) {
        ServerLevel level = hole.level;
        double cx = hole.center.x;
        double cy = hole.center.y + 0.6D;
        double cz = hole.center.z;
        int age = hole.age;
        boolean omen = age >= FX_OMEN;                      // 第③幕：前兆（转向反了）
        double dir = omen ? -1.0D : 1.0D;                    // 1 = 往里吸，-1 = 往外炸
        double spin = hole.spin * dir;

        // ── 第①幕：降临（0–40 tick）音爆环由小扩到大 + 闪白 + 尘土被吸起 ──
        if (age < FX_ARRIVE) {
            double k = age / (double) FX_ARRIVE;             // 0 → 1
            double shockR = 2.0D + 26.0D * k;
            ring(level, ParticleTypes.SONIC_BOOM, cx, cy, cz, shockR, 36, age * 0.4D, 0.0D, 0.0D);
            if (age % 6 == 0) {
                fx(level, ParticleTypes.FLASH, cx, cy, cz, 2, 0.4D, 0.4D, 0.4D, 0.0D);
            }
            for (int i = 0; i < 26; i++) {
                double a = i * (Math.PI * 2.0D / 26.0D) + age * 0.2D;
                double r = 1.0D + 22.0D * k;
                // 朝心速度 ⇒ 尘土"被吸起来"
                fx(level, ParticleTypes.CAMPFIRE_COSY_SMOKE, cx + Math.cos(a) * r, cy - 0.5D,
                        cz + Math.sin(a) * r, 1, -Math.cos(a) * 0.12D, 0.06D, -Math.sin(a) * 0.12D, 0.12D);
            }
        }

        // ── 光子环：贴着急速旋转的亮环（每 tick、24 点、切向速度）── 黑洞的"招牌" ──
        ring(level, ParticleTypes.END_ROD, cx, cy, cz, 2.35D, 24, spin * 2.2D, 0.0D, 0.22D);

        // ── 事件视界暗盘（奇 tick）：中间要真的黑，边缘才亮 ──
        if (age % 2 == 1) {
            for (int i = 0; i < 30; i++) {
                double a = spin * 0.5D + i * (Math.PI * 2.0D / 30.0D);
                double r = 3.2D + 1.4D * Math.sin(a * 2.0D + age * 0.05D);
                fx(level, ParticleTypes.SQUID_INK, cx + Math.cos(a) * r, cy, cz + Math.sin(a) * r,
                        1, -Math.sin(a) * 0.1D, 0.0D, Math.cos(a) * 0.1D, 0.1D);
            }
            for (int i = 0; i < 18; i++) {
                double a = -spin * 0.9D + i * (Math.PI * 2.0D / 18.0D);
                fx(level, ParticleTypes.SCULK_SOUL, cx + Math.cos(a) * 2.0D, cy,
                        cz + Math.sin(a) * 2.0D, 1, -Math.sin(a) * 0.14D, 0.0D,
                        Math.cos(a) * 0.14D, 0.14D);
            }
        }

        // ── 三层反向吸积盘（偶 tick）：蓝焰 / 端杆 / 电弧，倾角各不相同 ──
        if (age % 2 == 0) {
            disk(level, ParticleTypes.SOUL_FIRE_FLAME, cx, cy, cz, 4.5D, 26, spin * 0.8D, 0.22D, 0.18D);
            disk(level, ParticleTypes.END_ROD, cx, cy, cz, 6.5D, 30, -spin * 0.55D, -0.18D, 0.16D);
            disk(level, ParticleTypes.ELECTRIC_SPARK, cx, cy, cz, 8.5D, 32, spin * 0.35D, 0.30D, 0.12D);
        }

        // ── 内落粒子雨（每 tick，核心看点）：**朝心速度** ⇒ 真的往里掉 ──
        for (int i = 0; i < 12; i++) {
            double a = spin * 0.7D + i * (Math.PI * 2.0D / 12.0D);
            double r0 = 7.5D + (i % 4) * 1.5D;
            for (int s = 0; s < 4; s++) {
                double k = s / 4.0D;
                double r = r0 * (1.0D - 0.22D * k);
                double y = cy + Math.sin(a * 2.0D + k * 5.0D) * 1.6D * (1.0D - k);
                fx(level, ParticleTypes.PORTAL, cx + Math.cos(a) * r, y, cz + Math.sin(a) * r,
                        1, -Math.cos(a) * 0.5D, -0.05D, -Math.sin(a) * 0.5D, 0.5D);
            }
        }

        // ── 引力透镜光弧（每 4 tick）：随时间收缩；前兆期急速收拢 ──
        if (age % 4 == 0) {
            double squeeze = omen
                    ? Math.max(2.6D, 10.0D - (age - FX_OMEN) * 0.28D)
                    : 10.0D - 4.0D * Math.sin(age * 0.05D);
            ring(level, ParticleTypes.END_ROD, cx, cy + 0.15D, cz, Math.max(2.6D, squeeze), 26,
                    spin * 0.25D, 0.0D, 0.05D);
            ring(level, ParticleTypes.DRAGON_BREATH, cx, cy - 0.15D, cz,
                    Math.max(2.6D, squeeze) * 0.8D, 20, -spin * 0.3D, 0.0D, 0.05D);
        }

        // ── 电弧（每 5 tick）：从奇点朝随机方向劈出去 ──
        if (age % 5 == 0) {
            for (int i = 0; i < 8; i++) {
                double a = (age * 0.37D + i * 0.9D) % (Math.PI * 2.0D);
                double up = Math.sin(age * 0.21D + i) * 0.6D;
                fx(level, ParticleTypes.ELECTRIC_SPARK, cx + Math.cos(a) * 1.2D, cy + up * 0.5D,
                        cz + Math.sin(a) * 1.2D, 1, Math.cos(a) * 0.9D, up, Math.sin(a) * 0.9D, 0.9D);
            }
        }

        // ── 核心：闪白（每 12 tick）+ 一层暗雾把"黑"压住 ──
        if (age % 12 == 0) {
            fx(level, ParticleTypes.FLASH, cx, cy, cz, 2, 0.35D, 0.35D, 0.35D, 0.0D);
        }
        fx(level, ParticleTypes.LARGE_SMOKE, cx, cy, cz, 4, 0.7D, 0.5D, 0.7D, 0.01D);

        // ── 前兆期的额外一记：音爆环 + 反向喷射（"要炸了"）──
        if (omen && age % 3 == 0) {
            double k = (age - FX_OMEN) / (double) Math.max(1, LIFETIME - FX_OMEN);
            ring(level, ParticleTypes.SONIC_BOOM, cx, cy, cz, 2.0D + 10.0D * k, 24, age * 0.5D,
                    0.0D, 0.0D);
        }
    }'''

s, e = cut(t, u"    private static void fx(Hole hole) {")
t = t[:s] + FX + t[e:]
# 旧的 ring/disk 已被新版覆盖 ⇒ 把旧的删掉（新版的签名不同，直接找旧签名抠）
for sig in (u"    /** 一圈（水平环）。 */", u"    /** 一张盘（螺旋，倾角靠 tilt 把 y 随角度抬起来）。 */"):
    if sig in t:
        s2, e2 = cut(t, sig)
        t = t[:s2] + t[e2:]
        print(u"删掉旧方法：%s" % sig.strip()[:24])

# ---------- 3) tick 里每 tick 清账 + 音效分幕 ----------
t = t.replace(u"            hole.spin += 0.35D;",
              u"            hole.spin += 0.35D;\n            fxSpent = 0;   // 0.14 ZF173：每 tick 重新给特效记账")
t = t.replace(u'''                    hole.level.playSound(null, hole.center.x, hole.center.y, hole.center.z,
                            SoundEvents.WARDEN_HEARTBEAT, SoundSource.PLAYERS, 1.2F + t, 0.5F + t * 0.4F);''',
              u'''                    hole.level.playSound(null, hole.center.x, hole.center.y, hole.center.z,
                            SoundEvents.WARDEN_HEARTBEAT, SoundSource.PLAYERS, 1.2F + t, 0.5F + t * 0.4F);
                    // 低频"轰鸣"：拿爆炸声压低调当鼓点用（只出声、不伤方块）
                    hole.level.playSound(null, hole.center.x, hole.center.y, hole.center.z,
                            SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS,
                            0.6F + 2.4F * t, 0.4F + 0.3F * t);''')
t = t.replace(u'''                if (hole.age % 60 == 0) {
                    hole.level.playSound(null, hole.center.x, hole.center.y, hole.center.z,
                            SoundEvents.RESPAWN_ANCHOR_CHARGE, SoundSource.PLAYERS, 2.0F, 0.6F);
                }''',
              u'''                if (hole.age % 60 == 0) {
                    hole.level.playSound(null, hole.center.x, hole.center.y, hole.center.z,
                            SoundEvents.RESPAWN_ANCHOR_CHARGE, SoundSource.PLAYERS, 2.0F, 0.6F);
                }
                // 0.14 ZF173 前兆期：鼓点加密 + 音调发冷（"要坍缩了"）
                if (hole.age >= FX_OMEN && hole.age % 10 == 0) {
                    hole.level.playSound(null, hole.center.x, hole.center.y, hole.center.z,
                            SoundEvents.RESPAWN_ANCHOR_DEPLETE.value(), SoundSource.PLAYERS,
                            2.2F, 0.5F + (hole.age - FX_OMEN) * 0.004F);
                }''')

io.open(P, "w", encoding="utf-8", newline=u"\n").write(t)
print(u"fx 重写完成：预算 %d 包/tick、五幕、切向/朝心速度都在" % 320)
sys.exit(0)
