# -*- coding: utf-8 -*-
"""_zf133_verfix.py —— B10 的锚点要跟着"拆/挡分成两支"那次重构一起改

旧判据盯的是 `if (!isChoppable(state)) { ... isCorrectToolForDrops ... }` 这个顺序，
而 `_zf133_parentfix3.py` 已经把结构改成"**先判拆、再判挡**"（那次重构本身是对的，
只是判据没跟上）。新判据要盯**语义**：原木/树叶那一支里**必须出现 destroyBlock**，
而 `isCorrectToolForDrops` 必须出现在它**之后**（即只作用于"原木/树叶以外"）。

跑法：python build\\zftools\\_zf133_verfix.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\build\zftools\_zf133_verify.py"

OLD = """    ok("B10 工具判据只用于「非原木/树叶」那一支（树叶必须能拆）",
       "树叶的正确工具是锄/剪刀" in shock
       and re.search(r"if \\(!isChoppable\\(state\\)\\) \\{[\\s\\S]*?isCorrectToolForDrops", shock) is not None)"""
NEW = """    # B10：拆与挡必须是两支（第一版写成一个 continue 套一个 continue，
    # 结果"同一排里有挡路方块 ⇒ 这一排的原木也跟着不拆" —— 探针抓出来的）。
    # 判据盯**顺序**：isChoppable 那一支里必须先出现 destroyBlock，
    # 而 isCorrectToolForDrops 必须排在它后面（只作用于"原木/树叶以外"）。
    i_chop = shock.find("if (isChoppable(state)) {")
    i_destroy = shock.find("destroyBlock(pos, true, owner)")
    i_tool = shock.find("if (!owner.getMainHandItem().isCorrectToolForDrops(state))")
    ok("B10 拆与挡分成两支：isChoppable 支里先 destroyBlock，工具判据排在其后",
       i_chop > 0 and i_destroy > i_chop and i_tool > i_destroy,
       "idx chop=%d destroy=%d tool=%d" % (i_chop, i_destroy, i_tool))
    ok("B10b isAir 早退还在（删了它波会被空气挡死 —— 我踩过，代价四轮）",
       shock.count("if (state.isAir()) {") == 1)"""

s = io.open(P, encoding="utf-8").read()
n = s.count(OLD)
assert n == 1, "锚点 %d 次" % n
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(OLD, NEW, 1))
print("[OK] B10 判据已更新")
