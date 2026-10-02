# -*- coding: utf-8 -*-
"""_zf134_fixcomment.py —— 把脚本里那句注释的措辞换掉

原因：我在新 javadoc 里写了「旧版存的是 `alongX + sign`」——**那个词本身就是旧字段名**，
于是最后的"旧字段不许残留"断言把它自己数了出来（`alongX（1 次）`）⇒ 断言失败 ⇒ 不写盘。
这个断言是对的（它证明自己会咬），错的是我的注释用了要禁止的字面量。

⇒ 顺带一条规矩：**"禁止某标识符"的检查，注释里也不能出现那个标识符**（否则判据自己撞自己）。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\build\zftools\_zf134_manager5.py"

OLD = "旧版存的是 `alongX + sign`（主轴 + 正负），采样点只能落在 8 个方格方向上。"
NEW = "旧版只存了「主轴 + 正负号」两个字段，采样点只能落在 8 个方格方向上。"

s = io.open(P, encoding="utf-8").read()
n = s.count(OLD)
assert n == 1, "锚点 %d 次" % n
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(OLD, NEW, 1))
print("[OK] 注释已换措辞（不再含被禁的标识符）")
print("脚本里还有那个词吗：", "alongX" in io.open(P, encoding="utf-8").read().replace("alongX =", "").replace('"alongX"', ""))
