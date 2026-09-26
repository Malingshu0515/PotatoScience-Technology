# -*- coding: utf-8 -*-
"""_zf134_verfix2.py —— 补强 B24：反证 K-A1 抓出的**判据漏洞**

K-A1 注入的是"把法线清零"（`perpX = 0; perpZ = 0;`）⇒ 采样退回"只有主轴前进、横向不铺"，
**但 B24 照样全绿** —— 因为它是**源码字符串**判据，只检查"那几行字在不在"，
不管它们在**循环体里到底算出了什么**。

判据要盯"**循环体里真的用到了法线**"：
  · 不能再出现 `perpX = 0` / `perpZ = 0` 这种把法线抹掉的赋值；
  · `Math.floor(frontX + perpX * lat)` 与 `Math.floor(frontZ + perpZ * lat)`
    必须**落在采样循环体内**（用 `for (int lateral` 到 `if (state.isAir())` 之间切出循环体再查）。

⇒ 这条本身的教训也值得记：**源码字符串判据能防"删掉"，防不住"改坏"**；
   能"改坏"的地方（数值、算式、赋值）要尽量用**运行时**判据（探针那 21° 场景就是），
   源码判据只能当第二道。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\build\zftools\_zf133_verify.py"

OLD = '''    ok("B24 采样点 = 前缘 + 法线 × 横向偏移（任意角度的核心算式）",
       "double perpX = -wave.dirZ;" in shock and "double perpZ = wave.dirX;" in shock
       and "Math.floor(frontX + perpX * lat)" in shock
       and "Math.floor(frontZ + perpZ * lat)" in shock)'''

NEW = '''    # B24：**采样循环体内部**必须真的用上法线（反证 K-A1 教出来的：
    #      只查"那几行字在不在"挡不住"把法线清零"这种改坏 ⇒ 这里切出循环体再查）。
    i_loop = shock.find("for (int lateral = 0; lateral < WIDTH; lateral++) {")
    i_after = shock.find("if (state.isAir()) {", i_loop)
    body = shock[i_loop:i_after] if (i_loop > 0 and i_after > i_loop) else ""
    ok("B24 采样点 = 前缘 + 法线 × 横向偏移（算式落在**循环体内**）",
       "double perpX = -wave.dirZ;" in shock and "double perpZ = wave.dirX;" in shock
       and "Math.floor(frontX + perpX * lat)" in body
       and "Math.floor(frontZ + perpZ * lat)" in body)
    ok("B24b 法线没有被抹掉（不许出现 perpX = 0 / perpZ = 0 这类赋值）",
       not re.search(r"perp[XYZ]\\s*=\\s*0\\s*;", shock))'''

s = io.open(P, encoding="utf-8").read()
n = s.count(OLD)
assert n == 1, "B24 锚点 %d 次" % n
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(OLD, NEW, 1))
print("[OK] B24 已补强（循环体内查 + 禁止抹掉法线）")
