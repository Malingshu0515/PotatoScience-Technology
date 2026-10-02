# -*- coding: utf-8 -*-
"""_zf133_dbgtrace.py —— 临时诊断：把冲击波每 tick 的账打出来（查完就撤）

现象：探针里波确实起了（activeCount=1、耐久扣了 120），但**一格原木都没拆掉**，
3 tick 就散了。纸上推演不出为什么 ⇒ 加临时 trace，回答三个问题：
  ① 波到底 tick 了几次？
  ② 每个采样格的 blockState 是什么？走的是 air / hardness<0 / notChoppable / notCorrect 哪条分支？
  ③ `destroyBlock` 返回了什么？

跑法：python build\\zftools\\_zf133_dbgtrace.py           （插）
      python build\\zftools\\_zf133_dbgtrace.py --off     （撤，并逐字节核对）
"""
import hashlib
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

OLD = """        boolean broke = false;
        boolean blocked = false;
        for (int lateral = 0; lateral < WIDTH; lateral++) {"""
NEW = """        boolean broke = false;
        boolean blocked = false;
        StringBuilder trace = DEBUG ? new StringBuilder("t" + wave.totalTicks + " main=")
                .append(wave.mainCoord(wave.alongX ? ox : oz)) : null;
        for (int lateral = 0; lateral < WIDTH; lateral++) {"""

OLD2 = """                BlockState state = wave.level.getBlockState(pos);
                if (state.isAir()) {
                    continue;
                }"""
NEW2 = """                BlockState state = wave.level.getBlockState(pos);
                if (DEBUG && (state.isAir() || isChoppable(state) || !owner.getMainHandItem().isCorrectToolForDrops(state))) {
                    trace.append(' ').append(pos.toShortString()).append('=')
                            .append(state.getBlock().getName().getString());
                }
                if (state.isAir()) {
                    continue;
                }"""

OLD3 = """                if (wave.level.destroyBlock(pos, true, owner)) {
                    broke = true;
                }"""
NEW3 = """                boolean destroyed = wave.level.destroyBlock(pos, true, owner);
                if (DEBUG) {
                    trace.append(" [destroy ").append(pos.toShortString()).append('=')
                            .append(destroyed).append(']');
                }
                if (destroyed) {
                    broke = true;
                }"""

OLD4 = """        if (blocked) {
            return false;
        }"""
NEW4 = """        if (DEBUG) {
            System.out.println("[A133DBG] " + trace + " broke=" + broke + " blocked=" + blocked);
        }
        if (blocked) {
            return false;
        }"""

OLD5 = """    /** 还在推进的冲击波。只在服务端主线程上增删（ServerTickEvent 与右键都是主线程）。 */
    private static final List<Wave> WAVES = new ArrayList<>();"""
NEW5 = """    /** 还在推进的冲击波。只在服务端主线程上增删（ServerTickEvent 与右键都是主线程）。 */
    private static final List<Wave> WAVES = new ArrayList<>();

    /** ⚠ 临时诊断开关（ZF133 查"波不拆方块"用，查完连同 trace 一起删）。 */
    public static boolean DEBUG = false;"""

EDITS = [(OLD, NEW), (OLD2, NEW2), (OLD3, NEW3), (OLD4, NEW4), (OLD5, NEW5)]
REVERSE = [(b, a) for a, b in EDITS]


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    s = io.open(P, encoding="utf-8").read()
    off = "--off" in sys.argv
    pairs = REVERSE if off else EDITS
    for i, (a, b) in enumerate(pairs):
        n = s.count(a)
        if n != 1:
            print("[FAIL] 第 %d 段锚点 %d 次" % (i + 1, n))
            sys.exit(1)
        s = s.replace(a, b, 1)
    io.open(P, "w", encoding="utf-8", newline="\n").write(s)
    print("[OK] %s 完成（5 段）" % ("撤销" if off else "插入"))
    if off:
        body = io.open(P, encoding="utf-8").read()
        for needle in ("A133DBG", "DEBUG", "trace"):
            print("  残留 %s = %s" % (needle, needle in body))


main()
