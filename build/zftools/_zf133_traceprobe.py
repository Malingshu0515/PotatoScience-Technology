# -*- coding: utf-8 -*-
"""_zf133_traceprobe.py —— 打开 trace + 在检查点打印玩家位置

为什么要打玩家位置：上一次被误导，就是因为**玩家会掉下去**（波把他脚下那格拆了，
重力把他拉到下一层），而波的采样原点 `oy` 是**每 tick 现读玩家 Y** ⇒
波跟着人一起"下沉"，于是采到石台、被自己的地板挡住。
把玩家坐标打出来，这条才看得见。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

A1 = "    private static void buildB() {"
B1 = A1 + "\n        ShockwaveManager.TRACE = true;"

A2 = "            } else if (t == T_B_CHECK) {"
B2 = (A2 + "\n                say(TAG + \"      [TR] 检查时玩家在哪：\"\n"
      "                        + player.blockPosition().toShortString()\n"
      "                        + \" 站在 \" + level.getBlockState(player.blockPosition().below())\n"
      "                                .getBlock().getName().getString());")

A3 = "            } else if (t == T_E_CHECK) {"
B3 = (A3 + "\n                say(TAG + \"      [TR] (e) 检查时玩家在哪：\"\n"
      "                        + player.blockPosition().toShortString());")


def main():
    s = io.open(P, encoding="utf-8").read()
    for i, (a, b) in enumerate([(A1, B1), (A2, B2), (A3, B3)]):
        n = s.count(a)
        assert n == 1, "第 %d 段锚点 %d 次" % (i + 1, n)
        s = s.replace(a, b, 1)
        print("[OK] 第 %d 段" % (i + 1))
    io.open(P, "w", encoding="utf-8", newline="\n").write(s)
    print("已打开 trace + 位置打印")


main()
