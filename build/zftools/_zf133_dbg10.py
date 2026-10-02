# -*- coding: utf-8 -*-
"""_zf133_dbg10.py —— 在 onServerTick 里打一行"这一 tick 有几道波 + 各自推到哪了"

trace 显示 (b) 场景那 20 tick 里**一条都没有** —— 说明那道波压根没进 tick（不是"进去了没拆"）。
这一刀把 tick 循环本身的行为打出来：每 tick 波的数量与各自的 travelled。

跑法：python build\\zftools\\_zf133_dbg10.py  /  --off
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

OLD = """    public static void onServerTick(ServerTickEvent.Post event) {
        if (WAVES.isEmpty()) {
            return;
        }"""
NEW = """    public static void onServerTick(ServerTickEvent.Post event) {
        if (TRACE && !WAVES.isEmpty()) {
            StringBuilder sb = new StringBuilder("[TRLOOP] tick 波数=" + WAVES.size());
            for (Wave w : WAVES) {
                sb.append(" [" + w.owner.toString().substring(0, 8)
                        + " travelled=" + w.travelled + " total=" + w.totalTicks
                        + " dim=" + w.level.dimension().location() + "]");
            }
            System.out.println(sb);
        }
        if (WAVES.isEmpty()) {
            return;
        }"""


def main():
    off = "--off" in sys.argv
    s = io.open(SHOCK, encoding="utf-8").read()
    a, b = (NEW, OLD) if off else (OLD, NEW)
    n = s.count(a)
    assert n == 1, "锚点 %d 次" % n
    io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(s.replace(a, b, 1))
    print("[OK] %s" % ("撤销" if off else "插入"))


main()
