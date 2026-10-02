# -*- coding: utf-8 -*-
"""_zf133_final2.py —— ModTiers 那两处（注释文本与盘上差一个空行/措辞，按实际文本改）"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TIERS = r"E:\PotatoST\src\main\java\com\potatost\mod\ModTiers.java"
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

pairs_tiers = [
    ("    public static final float STAR_STEEL_DAMAGE = 0.0F;",
     "    public static final float STAR_STEEL_DAMAGE = 8.0F;"),
    ("""     * 它们都**不是**显示伤害。本档位取 <b>0.0F</b>：
     * 修饰符 = 0 + 档位加成 8 = 8 ⇒ 显示总伤害 = 基础值 1 + 8 = <b>9.0</b>。</p>""",
     """     * 它们都**不是**显示伤害。本档位取 <b>8.0F</b>：
     * 修饰符 = 8 + 档位加成 8 = 16 ⇒ 显示总伤害 = 属性基础值 1 + 16 = <b>17.0</b>
     * （全模组最高一档；对照：下界合金斧 10、钻石剑 7）。
     * ⚠ 这个数是**探针打印出来的**，不是我推的 —— 探针会打出
     * `[ATTR] ... 显示的总伤害 = 1 + 16.0 = 17.0`，`_zf133_verify.py` 也盯着它。</p>"""),
]

s = io.open(TIERS, encoding="utf-8").read()
for a, b in pairs_tiers:
    n = s.count(a)
    assert n == 1, "ModTiers 锚点 %d：%r" % (n, a[:50])
    s = s.replace(a, b, 1)
io.open(TIERS, "w", encoding="utf-8", newline="\n").write(s)
print("[OK] ModTiers：伤害参数 8.0F + 注释")

pairs_chk = [
    ("    private static final int T_B_CHECK = 60;",
     "    private static final int T_B_CHECK = 120;   // 64 格射程 ⇒ 约 60~70 tick 自己散"),
    ("    private static final int T_I_ALIVE = 600;",
     "    private static final int T_I_ALIVE = 520;"),
]
s = io.open(CHK, encoding="utf-8").read()
for a, b in pairs_chk:
    n = s.count(a)
    assert n == 1, "探针锚点 %d：%r" % (n, a[:40])
    s = s.replace(a, b, 1)
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
print("[OK] 探针时间线")
