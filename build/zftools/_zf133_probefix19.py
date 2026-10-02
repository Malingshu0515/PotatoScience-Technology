# -*- coding: utf-8 -*-
"""_zf133_probefix19.py —— 给探针加一条"时间线不许撞车"的自检（防复发）

§4.30 的老规矩：**这次踩到的坑要变成一条会自己红的检查**，不能只写在档案里。
`T_B_CHECK = T_D = 120` 那次是同值 ⇒ 后者被静默跳过 ⇒ 整场在 t=150 NPE ⇒
后面九个场景一个没跑。这条自检在开场就把所有 T_xxx 常量数一遍，撞车就当场 FAIL
（而且打印出是哪两个），下次不可能再靠眼睛发现。

跑法：python build\\zftools\\_zf133_probefix19.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

ANCHOR = """            failed += check("假玩家朝向是东（视线 x > 0.9，实际 "
                    + String.format("%.3f", player.getLookAngle().x) + "）",
                    player.getLookAngle().x > 0.9D);"""

INSERT = ANCHOR + """

            // ⚠ 时间线自检（ZF133 踩过一次）：所有 T_xxx 常量**两两不能同值**。
            //   同值 = 后面那一拍被 `else if` 静默跳过，症状是"后面整段场景都没跑"，
            //   而报告上看着像一堆互不相关的失败。
            int[] timeline = {T_STATIC, T_B, T_B_CHECK, T_D, T_D_CHECK, T_E, T_E_CHECK,
                    T_I, T_I_ALIVE, T_I_DEAD, T_H, T_H_CHECK, T_F, T_F_MID, T_G, T_G2,
                    T_C, T_END};
            String[] names = {"T_STATIC", "T_B", "T_B_CHECK", "T_D", "T_D_CHECK", "T_E",
                    "T_E_CHECK", "T_I", "T_I_ALIVE", "T_I_DEAD", "T_H", "T_H_CHECK", "T_F",
                    "T_F_MID", "T_G", "T_G2", "T_C", "T_END"};
            String clash = "";
            for (int i = 0; i < timeline.length; i++) {
                for (int j = i + 1; j < timeline.length; j++) {
                    if (timeline[i] == timeline[j]) {
                        clash += names[i] + "==" + names[j] + " ";
                    }
                }
            }
            failed += check("时间线常量两两不同（" + timeline.length + " 个" +
                    (clash.isEmpty() ? "" : "，撞车：" + clash) + "）", clash.isEmpty());"""

s = io.open(CHK, encoding="utf-8").read()
n = s.count(ANCHOR)
assert n == 1, "锚点 %d 次" % n
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s.replace(ANCHOR, INSERT, 1))
print("[OK] 已加时间线自检")
