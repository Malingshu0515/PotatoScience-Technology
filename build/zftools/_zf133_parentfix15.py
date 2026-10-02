# -*- coding: utf-8 -*-
"""_zf133_parentfix15.py —— 按盘上实际文本补上"直接结算"那一发的调用"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

A = """        failed += check("末影人已就位（血量 " + ender.getHealth() + "）", ender.isAlive());"""
B = A + """
        // 末地龙会先挨打（它在采样带上盘旋），所以这一发**直接结算**拿末影人当靶子
        directDamageProbe(endPlayer, ender, new BlockPos(0, 100, 12));"""

# 快照那两条断言换成"记录"（说明不了问题：末地龙会再生）
C = """        failed += check("末地有实体被这一刀打到（掉血实体 " + hits + " 个）", hits > 0);
        failed += check("其中有一个**正好掉 12.0** = 10 + 0.5 × 4（实际 "
                + (exact < 0 ? "没有" : exact) + "）", exact > 0.0D);"""
D = """        // 快照法说明不了问题：末地龙每 tick 回 1 血，隔 40 tick 早回满（实测 0 个掉血）。
        // 真正的判据在 directDamageProbe() 里（反射造波 + 当场量血）。
        say(TAG + "      [HP1-记录] 快照法看到掉血实体 " + hits + " 个（末地龙会再生 ⇒ 不可靠）");"""

s = io.open(CHK, encoding="utf-8").read()
for i, (a, b) in enumerate([(A, B), (C, D)]):
    n = s.count(a)
    assert n == 1, "第 %d 段锚点 %d 次" % (i + 1, n)
    s = s.replace(a, b, 1)
    print("[OK] 第 %d 段" % (i + 1))
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
print("完成")
