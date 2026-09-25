# -*- coding: utf-8 -*-
"""把"反向重建结果"与 zf24_pre 备份（ZF24 定稿，逐字节权威）对差，
逐行打印差异，好看出我到底漏了/多改了什么。"""
import difflib
import io
import os
import sys

sys.path.insert(0, r"E:\PotatoST\build\zftools")
src = io.open(r"E:\PotatoST\src\main\java\com\potatost\mod\SolarPanelBlockEntity.java",
              encoding="utf-8").read()

SP_EDITS = [
    (" * 太阳能板（0.10 ZF22 加入；ZF24 改为<b>共享储能</b>；ZF29 发电量 ×3）。",
     " * 太阳能板（0.10 ZF22 加入；ZF24 改为<b>共享储能</b>）。"),
    ("""
 *
 * <p><b>ZF29：发电量变成原来的 300%</b>（用户："太阳能板发电量变成原来300%"）。
 * 三档 <b>20/45/60 → 60/135/180 FE/t</b>。⚠ 注意 <b>{@value #MAX_ENERGY} FE 的储能没动</b> ——
 * 于是"攒满"从约 26 tick（1.3 秒）变成约 9 tick（0.4 秒），
 * 也就是说<b>它现在几乎总是满的，真正的瓶颈变成了下方设备能抽多快</b>。
 * 这是用户只要"发电量"三个字时**有意不动储能**的结果，写在档案 §9 里而不是自作主张改容量。</p>
 *""", ""),
    ("""    /** 晴天三档（FE/t）。ZF29 起 = 原值 × 3（用户："太阳能板发电量变成原来300%"） */
    public static final int RATE_DAWN_DUSK = 60;
    public static final int RATE_MORNING = 135;
    public static final int RATE_NOON = 180;""",
     """    /** 晴天三档（FE/t） */
    public static final int RATE_DAWN_DUSK = 20;
    public static final int RATE_MORNING = 45;
    public static final int RATE_NOON = 60;"""),
    ("""     *   0 ~  2000 日出      60      ← ZF29 起是原来的 3 倍
     *   2000 ~  5000 上午     135
     *   5000 ~  7000 正午     180
     *   7000 ~ 10000 下午     135
     *   10000 ~ 12000 傍晚     60
     *   12000 ~ 24000 夜间      0""",
     """     *   0 ~  2000 日出      20
     *   2000 ~  5000 上午      45
     *   5000 ~  7000 正午      60
     *   7000 ~ 10000 下午      45
     *   10000 ~ 12000 傍晚     20
     *   12000 ~ 24000 夜间      0"""),
    ("            // 正确语义：组的输出 = 速率和 ÷ 块数 = 每块的额定值（ZF29 起是 60/135/180，**每块**的）。",
     "            // 正确语义：组的输出 = 速率和 ÷ 块数 = 每块的额定值（用户给的 20/45/60 是**每块**的）。"),
]
for new, old in SP_EDITS:
    assert src.count(new) == 1, new[:60]
    src = src.replace(new, old)

ref = io.open(r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf24_pre\SolarPanelBlockEntity.java",
              encoding="utf-8").read()

a = ref.splitlines()
b = src.splitlines()
print("zf24_pre 行数 = %d   反向重建 行数 = %d" % (len(a), len(b)))
print("=" * 70)
n = 0
for line in difflib.unified_diff(a, b, "zf24_pre(权威)", "反向重建", lineterm="", n=1):
    print(line)
    n += 1
    if n > 120:
        print("…（差异过多，截断）")
        break
if n == 0:
    print("两者完全相同 ⇒ 反向重建 = ZF24 定稿，说明 478dec40… 这个哈希本身是可疑的")
