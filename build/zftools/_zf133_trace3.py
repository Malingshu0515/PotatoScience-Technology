# -*- coding: utf-8 -*-
"""_zf133_trace3.py —— 修正锚点后再打补丁（第 2 段锚点文本对不上，先看盘上是什么）"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

s = io.open(CHK, encoding="utf-8").read()

# 段 1：TRACE 常开（buildB 里那行改成在 onServerStarted 里，并去掉 buildB 里那次）
OLD1 = "        ShockwaveManager.TRACE = true;\n"
assert s.count(OLD1) == 1, "TRACE 行 %d 次" % s.count(OLD1)
s = s.replace(OLD1, "", 1)
OLD1B = '            say(TAG + "试验场就绪：玩家 " + player.blockPosition()'
assert s.count(OLD1B) == 1
s = s.replace(OLD1B,
              "            ShockwaveManager.TRACE = true;   // 全程 trace（诊断用，修好前不关）\n"
              + OLD1B, 1)
print("[OK] 段1 TRACE 改成常开")

# 段 2：末地玩家的存活断言（锚点用"它后面那行"）
i = s.find("endPlayer.moveTo(0.5D, 100.0D, 0.5D, -90.0F, 0.0F);")
assert i > 0, "找不到 endPlayer.moveTo"
line_end = s.index("\n", i) + 1
# 下一行应该就是 end.addFreshEntity(endPlayer);（如果不在一行内，往后找）
j = s.find("end.addFreshEntity(endPlayer);", line_end)
assert j > 0, "找不到 end.addFreshEntity(endPlayer)"
j_end = s.index("\n", j) + 1
INSERT2 = ('        failed += check("末地那台假玩家活着（hp=" + endPlayer.getHealth() + "/"\n'
           '                + endPlayer.getMaxHealth() + " alive=" + endPlayer.isAlive() + "）",\n'
           '                endPlayer.isAlive() && endPlayer.getHealth() > 0.0F);\n')
s = s[:j_end] + INSERT2 + s[j_end:]
print("[OK] 段2 末地玩家存活断言")

# 段 3：波数打印
OLD3 = "            long t = level.getGameTime() - t0;"
assert s.count(OLD3) == 1
NEW3 = (OLD3 + "\n            if (t == T_B_CHECK || t == T_E_CHECK || t == T_I_ALIVE"
        " || t == T_H_CHECK) {\n"
        "                say(TAG + \"      [WAVES] t=\" + t + \" activeCount=\""
        " + ShockwaveManager.activeCount());\n"
        "            }")
s = s.replace(OLD3, NEW3, 1)
print("[OK] 段3 波数打印")

io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
print("完成")
