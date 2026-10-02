# -*- coding: utf-8 -*-
"""_zf133_trace4.py —— 三处补丁（全部用 find + 行边界，不写长锚点）"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

s = io.open(CHK, encoding="utf-8").read()

# ---- 1) TRACE 常开：从 buildB 挪到 onServerStarted 末尾 ----
a = "        ShockwaveManager.TRACE = true;\n"
assert s.count(a) == 1, "TRACE 行 %d 次" % s.count(a)
s = s.replace(a, "", 1)
b = "        t0 = level.getGameTime();"
assert s.count(b) == 1
s = s.replace(b, b + "\n        ShockwaveManager.TRACE = true;   // 全程 trace（诊断用，修好前不关）", 1)
print("[OK] 1) TRACE 常开")

# ---- 2) 末地玩家存活断言 ----
c = "        endPlayer.moveTo(0.5D, 100.0D, 0.5D, -90.0F, 0.0F);"
assert s.count(c) == 1
s = s.replace(c, c + """
        failed += check("末地那台假玩家活着（hp=" + endPlayer.getHealth() + "/"
                + endPlayer.getMaxHealth() + " alive=" + endPlayer.isAlive() + "）",
                endPlayer.isAlive() && endPlayer.getHealth() > 0.0F);""", 1)
print("[OK] 2) 末地玩家存活断言")

# ---- 3) 波数打印 ----
d = "            long t = level.getGameTime() - t0;"
assert s.count(d) == 1
s = s.replace(d, d + """
            if (t == T_B_CHECK || t == T_E_CHECK || t == T_I_ALIVE || t == T_H_CHECK) {
                say(TAG + "      [WAVES] t=" + t + " activeCount=" + ShockwaveManager.activeCount()
                        + " 玩家=" + player.blockPosition().toShortString()
                        + " hp=" + player.getHealth());
            }""", 1)
print("[OK] 3) 波数打印")

io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
print("完成")
