# -*- coding: utf-8 -*-
"""_zf133_trace.py —— 常驻到修好为止的紧凑 trace（按格打印：采样 / 销毁 / 挡住）

上一次把 trace 撤得太早，导致后两轮只能靠推演。这次保留到全绿：
每格一行 `[TR] pos block choppable -> destroy=… / BLOCKED`。

跑法：python build\\zftools\\_zf133_trace.py   /  --off
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

OLD = """                BlockState state = wave.level.getBlockState(pos);
                if (state.isAir()) {
                    continue;
                }"""
NEW = """                BlockState state = wave.level.getBlockState(pos);
                boolean tr = TRACE;
                if (state.isAir()) {
                    if (tr) {
                        System.out.println("[TR] t" + wave.totalTicks + " " + pos.toShortString()
                                + " air");
                    }
                    continue;
                }"""

OLD2 = """                if (!isChoppable(state)) {
                    // 原木/树叶**以外**的方块：斧子挖不动它 ⇒ 波被挡住（用户那条规则）。"""
NEW2 = """                if (tr) {
                    System.out.println("[TR] t" + wave.totalTicks + " " + pos.toShortString()
                            + " " + state.getBlock().getName().getString()
                            + " chop=" + isChoppable(state)
                            + " tool=" + owner.getMainHandItem().isCorrectToolForDrops(state));
                }
                if (!isChoppable(state)) {
                    // 原木/树叶**以外**的方块：斧子挖不动它 ⇒ 波被挡住（用户那条规则）。"""

OLD3 = """                boolean destroyed = wave.level.destroyBlock(pos, true, owner);"""
NEW3 = """                boolean destroyed = wave.level.destroyBlock(pos, true, owner);
                if (tr) {
                    System.out.println("[TR] t" + wave.totalTicks + " " + pos.toShortString()
                            + " DESTROY=" + destroyed);
                }"""

OLD4 = """    /** 还在推进的冲击波。只在服务端主线程上增删（ServerTickEvent 与右键都是主线程）。 */
    private static final List<Wave> WAVES = new ArrayList<>();"""
NEW4 = """    /** 还在推进的冲击波。只在服务端主线程上增删（ServerTickEvent 与右键都是主线程）。 */
    private static final List<Wave> WAVES = new ArrayList<>();

    /** ⚠ 临时 trace 开关（ZF133 查"波为什么停"，修好前一直留着）。 */
    public static boolean TRACE = false;"""

EDITS = [(OLD, NEW), (OLD2, NEW2), (OLD3, NEW3), (OLD4, NEW4)]


def main():
    off = "--off" in sys.argv
    pairs = [(b, a) for a, b in EDITS] if off else EDITS
    s = io.open(SHOCK, encoding="utf-8").read()
    for i, (a, b) in enumerate(pairs):
        n = s.count(a)
        if n != 1:
            print("[FAIL] 第 %d 段锚点 %d 次：%r" % (i + 1, n, a.strip().split("\n")[0][:60]))
            sys.exit(1)
        s = s.replace(a, b, 1)
    io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(s)
    print("[OK] %s 完成" % ("撤销" if off else "插入"))


main()
