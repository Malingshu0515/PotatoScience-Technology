# -*- coding: utf-8 -*-
"""_zf133_trace2.py —— 把 trace 开关做成**全程打开**（放在 verify 里，不是临时插）

前两次诊断失败的原因是"我读错了日志窗口"。这次让 trace 常开，并用**汇总**来读：
把每个场景窗口里的 TR 行归到最近的 `[A133]` 标记之下，一眼能看出波在哪一格停的。

跑法：python build\\zftools\\_zf133_trace2.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

# 在 onServerStarted 里就打开（而不是 buildB 里）
OLD = """            say(TAG + "试验场就绪：玩家 " + player.blockPosition()"""
NEW = """            ShockwaveManager.TRACE = true;   // 全程 trace（诊断用，修好前不关）
            say(TAG + "试验场就绪：玩家 " + player.blockPosition()"""

# 末地那台玩家也要断言活着（上一次 (h) 全军覆没很可能就是它死了）
OLD2 = """        endPlayer.moveTo(0.5D, 100.0D, 0.5D, -90.0F, 0.0F);
        end.addFreshEntity(endPlayer);"""
NEW2 = """        endPlayer.moveTo(0.5D, 100.0D, 0.5D, -90.0F, 0.0F);
        end.addFreshEntity(endPlayer);
        failed += check("末地那台假玩家活着（hp=" + endPlayer.getHealth() + "/"
                + endPlayer.getMaxHealth() + " alive=" + endPlayer.isAlive() + "）",
                endPlayer.isAlive() && endPlayer.getHealth() > 0.0F);"""

# 检查点加"波进到哪一格了"（用 travelled 反推当前主轴坐标）
OLD3 = """            long t = level.getGameTime() - t0;
            if (t == T_STATIC || t == T_B || t == T_B_CHECK) {"""
NEW3 = """            long t = level.getGameTime() - t0;
            if (t == T_B_CHECK || t == T_E_CHECK || t == T_I_ALIVE || t == T_H_CHECK) {
                say(TAG + "      [WAVES] t=" + t + " activeCount=" + ShockwaveManager.activeCount());
            }
            if (t == T_STATIC || t == T_B || t == T_B_CHECK) {"""


def main():
    s = io.open(CHK, encoding="utf-8").read()
    for i, (a, b) in enumerate([(OLD, NEW), (OLD2, NEW2), (OLD3, NEW3)]):
        n = s.count(a)
        assert n == 1, "第 %d 段锚点 %d 次" % (i + 1, n)
        s = s.replace(a, b, 1)
        print("[OK] 第 %d 段" % (i + 1))
    io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
    print("trace 常开 + 末地玩家存活断言 + 波数打印")


main()
