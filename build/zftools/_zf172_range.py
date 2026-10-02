# -*- coding: utf-8 -*-
u"""_zf172_range.py —— 黑洞吸方块的范围改成 **5×5×5 区块的正方体**（用户 ZF172）

用户原话：「黑洞范围改一下 5x5x5区块的正方体范围」。

    5×5 区块 = 80×80 格（水平），5 区块高 = 80 格（竖直）⇒ 以黑洞为中心 **±40 格**，
    即 81×81×81 ≈ **531,441** 个位置。

⚠⚠ 性能：每 tick 全扫 53 万个位置 = 服务器当场跪（旧版是 ±40 水平 × −8..+12 竖直，
   靠"由近到远一圈圈扫、每 tick 只搬 24 个"侥幸没炸）。新版必须**两把预算**：
   ① **检查预算** {@code EXAMINE_PER_TICK}（每 tick 最多看多少个位置，带**游标**续扫 ⇒
      一次完整扫完约 130 tick ≈ 6.5 秒）；
   ② **搬运预算** {@code BLOCKS_PER_TICK}（每 tick 最多搬几块）。
   两把都写进常量，别藏在循环里。
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\BlackHoleManager.java"
t = io.open(P, encoding="utf-8").read()

NEW = u'''    private static void pullBlocks(Hole hole) {
        // ⚠⚠ 0.14 ZF170b：上限判据原来只看 `placed` ⇒ 模式 2 那条路 `placed` 永远不涨，
        //   上限**彻底失效**（用户实测一次吸了 **16992** 块，世界被啃掉一大片）。
        //   现在改成看 **pulled**（搬走的都算），1500 一到立刻停手。
        if (hole.pulled >= MAX_BLOCKS) {
            return;
        }
        ServerLevel level = hole.level;
        BlockPos centerPos = BlockPos.containing(hole.center);
        // ── 0.14 ZF172：范围 = 5×5×5 区块的正方体（±40 格，81³ 个位置）──
        //    用**线性游标**扫：每 tick 只看 EXAMINE_PER_TICK 个位置，扫完一轮从头再来。
        //    这样"处处没有目标方块"时也只花固定的那点开销（否则 53 万个位置每 tick 全扫 = 服务器跪）。
        int budget = BLOCKS_PER_TICK;
        int examined = 0;
        while (examined < EXAMINE_PER_TICK && budget > 0) {
            int idx = hole.cursor;
            hole.cursor = (hole.cursor + 1) % SCAN_VOLUME;
            examined++;
            // 线性下标 → (dx, dy, dz)，每个轴都是 -HALF..+HALF
            int dx = idx % SCAN_SIDE - HALF;
            int dz = (idx / SCAN_SIDE) % SCAN_SIDE - HALF;
            int dy = idx / (SCAN_SIDE * SCAN_SIDE) - HALF;
            // 黑洞脚下那一圈是"禁采区"：不许把它自己码好的方块又吸一遍
            // （否则数字狂涨、地上什么都看不到 —— ZF170c 用户实测抓到的）
            if (Math.abs(dx) <= PILE_GUARD && Math.abs(dz) <= PILE_GUARD
                    && dy >= -8 && dy <= 30) {
                continue;
            }
            BlockPos p = centerPos.offset(dx, dy, dz);
            if (!level.isLoaded(p)) {
                continue;
            }
            BlockState state = level.getBlockState(p);
            if (!state.is(hole.block)) {
                continue;
            }
            // ① **先放后拆**（放不下就绝不拆）—— 修"吸走就消失"；
            // ② 落点也不够时 ⇒ **掉成掉落物**（用户点名要的兜底），仍然不消失。
            if (placeAt(hole, p)) {
                level.removeBlock(p, false);
                hole.pulled++;
            } else {
                level.removeBlock(p, false);
                Block.popResource(level, centerPos, new ItemStack(hole.block));
                hole.pulled++;
                hole.dropped++;
            }
            // 路上撒一串粒子，让"它被拽走了"看得见
            Vec3 from = Vec3.atCenterOf(p);
            for (int s = 0; s < 8; s++) {
                double k = s / 8.0D;
                level.sendParticles(ParticleTypes.REVERSE_PORTAL,
                        Mth.lerp(k, from.x, hole.center.x),
                        Mth.lerp(k, from.y, hole.center.y),
                        Mth.lerp(k, from.z, hole.center.z), 1, 0.05D, 0.05D, 0.05D, 0.02D);
            }
            budget--;
        }
    }'''

# 用花括号配平把整个方法抠出来（比按行猜安全）
start = t.index(u"    private static void pullBlocks(Hole hole) {")
i = t.index(u"{", start)
depth = 0
end = i
while end < len(t):
    if t[end] == u"{":
        depth += 1
    elif t[end] == u"}":
        depth -= 1
        if depth == 0:
            break
    end += 1
old = t[start:end + 1]
print(u"旧方法 %d 行 → 新方法 %d 行" % (old.count(u"\n") + 1, NEW.count(u"\n") + 1))
t = t[:start] + NEW + t[end + 1:]

# 常量：加扫描范围与两把预算 + Hole 里的游标
t = t.replace(
    u"    /** 单次最多搬多少方块（用户 ZF170b 把上限从 1200 提到 **1500**）。 */\n    public static final int MAX_BLOCKS = 1500;",
    u"    /** 单次最多搬多少方块（用户 ZF170b 把上限从 1200 提到 **1500**）。 */\n"
    u"    public static final int MAX_BLOCKS = 1500;\n"
    u"    /** 0.14 ZF172：吸方块的范围 = **5×5×5 区块的正方体** ⇒ 每轴 ±40 格（用户在「3x3区块」基础上改的）。 */\n"
    u"    public static final int HALF = 40;\n"
    u"    /** 每轴位置数（81）。 */\n"
    u"    public static final int SCAN_SIDE = HALF * 2 + 1;\n"
    u"    /** 正方体里的位置总数（81³ = 531,441）。 */\n"
    u"    public static final int SCAN_VOLUME = SCAN_SIDE * SCAN_SIDE * SCAN_SIDE;\n"
    u"    /** 每 tick 最多**检查**多少个位置（带游标续扫；一轮 ≈ 130 tick ≈ 6.5 秒扫完 53 万）。 */\n"
    u"    public static final int EXAMINE_PER_TICK = 4096;")
t = t.replace(u"        double spin;", u"        double spin;\n        /** 0.14 ZF172：这一轮扫到 81³ 里的第几个（每 tick 续着扫，不许每 tick 从头全扫）。 */\n        int cursor;")

io.open(P, "w", encoding="utf-8", newline=u"\n").write(t)
print(u"已写入；HALF=40 / SCAN_VOLUME=531441 / EXAMINE_PER_TICK=4096")
sys.exit(0)
