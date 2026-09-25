# -*- coding: utf-8 -*-
u"""_zf109_docs2.py —— ZF109 补文档：§4.82（创造页漏挂）+ §9 那节的实测反馈

用户实测原话：「创造模式物品栏没看见采油机  jei也搜不到 但是 jei有配方」。
锚点要求**正好命中 1 次**，找不到/找到多处就报错退出，不猜。
⚠ 中文里一律用「」，不许 ASCII 双引号。
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = r"E:\PotatoST\docs\开发档案.md"
ANCHOR_TABLE = u"| 版本 | 内容 |"
ANCHOR_TRY = u"**要你实测的**（进游戏）："
OLD_KNIFE = u"- [x] 反证刀 **K99~K121（23 把，23 把全咬住、还原后回到全绿）**"

SEC482 = u"""### 4.82 【流程雷】新机器漏进**创造页** = 物品栏看不见 + JEI 搜不到，但**配方还在**（0.11 ZF109）

用户实测一句话点名：「创造模式物品栏没看见采油机  jei也搜不到 但是 jei有配方」。
这三件事其实是**同一件事**：原版创造菜单只显示"被某个页 `output.accept()` 过的物品"，
JEI 的物品搜索索引也是照**创造页**建的 ⇒ 两边一起看不见；而合成配方是 datapack 数据，
JEI 照旧解析 ⇒ **配方在、物品不在**，看上去像"图标丢了"。

档案 §6.14「加一个机器方块要动哪些文件」那张清单的**第 3 条**就是它
（`ModItems.java` 创造页里一行 `output.accept(...)`）—— 我照着清单做的时候**漏了这一步**。
根因不是"不知道"，而是**没把它做成检查项**（§4.17：没有检查项，就必然漏第二次）。

**三个可执行动作（已落地）**：

1. `build\\zftools\\_zf109_tabaudit.py`（只读账目）：拿 `ModBlocks` 里注册的每个方块物品，
   去 `ModItems` 的创造页里找 `output.accept(ModBlocks.<常量>.get())`，列出"没进创造页的"。
   修之前正好 **1 个**（采油机），修之后 **35/35**；
2. `_zf109_verify.py` 里成了常驻检查，并且**钉住"方块物品一共 35 个"这个基准**
   —— 以后加新机器忘了进创造页会当场红；
3. 反证刀 **K122**（把那行删掉 ⇒ 校验器必须 FAIL）盯着它。

**通用教训**：用户说"看不见某个东西"时先分三问 —— **注册了吗**（registry）→
**进了创造页吗**（tab）→ **名字/图标/模型对吗**（lang / model / texture）。
本轮三问里**第二问**漏了：注册、贴图、配方、JEI 都齐，独独少一行 accept。

"""


def main():
    fails = []
    text = io.open(DOC, encoding="utf-8", newline="").read()
    if u"### 4.82 " in text:
        fails.append(u"§4.82 已经写过了")
    lines = text.split(u"\n")

    def uniq(anchor):
        idx = [i for i, l in enumerate(lines) if anchor in l]
        if len(idx) != 1:
            fails.append(u"锚点 %r 命中 %d 次" % (anchor[:24], len(idx)))
            return None
        return idx[0]

    it = uniq(ANCHOR_TABLE)
    itry = uniq(ANCHOR_TRY)
    if fails:
        for f in fails:
            print(u"  !! " + f)
        return 1

    # ① §4.82 插在 §4 块尾（本轮表头之前）
    block = SEC482.split(u"\n")
    if block and block[-1] == u"":
        block = block[:-1]
    lines = lines[:it] + block + [u""] + lines[it:]

    # ② §9：把刀的编号改到 K122，并在"要你实测的"之前插一段实测反馈
    out = u"\n".join(lines)
    out, n1 = re.subn(re.escape(OLD_KNIFE),
                      u"- [x] 反证刀 **K99~K122（24 把，24 把全咬住、还原后回到全绿）**", out)
    if n1 != 1:
        fails.append(u"刀编号那行命中 %d 次" % n1)
    feedback = (u"**用户实测反馈（当天补）**：「创造模式物品栏没看见采油机  jei也搜不到 "
                u"但是 jei有配方」—— **创造页漏挂**，根因与三问见 §4.82。\n"
                u"补的东西：`ModItems` 加一行 accept（补账进 `zf109_pre`）、新账目脚本 "
                u"`_zf109_tabaudit.py`（修前 35 个方块物品里差 1 个，修后 35/35）、"
                u"`_zf109_verify.py` 增 3 条常驻检查、反证刀 **K122**、档案 §4.82。\n\n")
    anchor = u"\n" + ANCHOR_TRY
    if out.count(anchor) != 1:
        fails.append(u"「要你实测的」锚点命中 %d 次" % out.count(anchor))
    else:
        out = out.replace(anchor, u"\n" + feedback + ANCHOR_TRY)

    # ③ 核对
    for h in (u"### 4.82 【流程雷】", u"创造页漏挂", u"K99~K122"):
        if out.count(h) != 1:
            fails.append(u"核对：%r 出现 %d 次" % (h, out.count(h)))
    if fails:
        print(u"失败项 = %d（**没落盘**）" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    io.open(DOC, "w", encoding="utf-8", newline=u"\n").write(out)
    print(u"档案：%d 行 → %d 行" % (len(text.split(u"\n")), len(out.split(u"\n"))))
    print(u"失败项 = 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
