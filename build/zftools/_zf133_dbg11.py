# -*- coding: utf-8 -*-
"""_zf133_dbg11.py —— 在 tick() 的**第一句**就打印（回答"到底进没进来、owner 是不是 null"）

已排除的：TRACE 没打开（TRLOOP 打出来了，同一个字段）、wave 没进循环（TRLOOP 里波数=1）。
剩下的唯一可能：`tick()` 在第一句 `owner == null || !owner.isAlive()` 就 false 了。
这一刀把那两个值直接打出来，顺带打玩家实体是否被移除。

跑法：python build\\zftools\\_zf133_dbg11.py  /  --off
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

OLD = """        ServerPlayer owner = wave.level.getServer().getPlayerList().getPlayer(wave.owner);
        if (owner == null || !owner.isAlive()) {
            return false;
        }"""
NEW = """        ServerPlayer owner = wave.level.getServer().getPlayerList().getPlayer(wave.owner);
        if (TRACE) {
            System.out.println("[TRENTRY] tick 进入 owner=" + (owner == null ? "null" : owner.getName().getString())
                    + " alive=" + (owner != null && owner.isAlive())
                    + " removed=" + (owner != null && owner.isRemoved())
                    + " serverPlayers=" + wave.level.getServer().getPlayerList().getPlayers().size()
                    + " travelled=" + wave.travelled);
        }
        if (owner == null || !owner.isAlive()) {
            if (TRACE) {
                System.out.println("[TRENTRY] -> 就地散掉（owner null 或已死）");
            }
            return false;
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
