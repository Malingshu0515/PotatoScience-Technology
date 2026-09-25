# -*- coding: utf-8 -*-
"""_zf59_docs.py —— ZF59 档案落笔（等第四层摆完再成型）

三处动：① §5 加 ZF59 行；② §9 把"要不要等第四层"那条**结掉**；③ §4.34 补一段收尾。
"""
import io
import sys

DOC = r"E:\PotatoST\docs\开发档案.md"

ROW = u'''| ZF59 | **新建 `zf59_pre`**（8 个改前件：`AlloySmelterStructure` + 4 个 lang + `_zf57_lang.py` + `_zf55_verify.py` + `_zf57_verify.py`） | 0.10：**「等第四层摆完再成型」**（用户原话）。① `isRequired()` 的顶面分支从"整层不查"改成"**图纸画了方块的格才查**"（{@code kindAt != AIR}，读图纸，不写死坐标）⇒ 要查的格 48 → **58**（底面 20 + 三层墙 28 + 顶面那两列 10）；② 于是"成型"＝"图纸 4 层全摆完"，正常流程不再出现"顶层晚摆、被吸收"；`absorbNewHullBlocks()` 保留，只管"成型后又往表面空格补机器方块"这种少数情况；③ 四语言介绍文案改成"照图纸把 4 层摆完（要查 58 格…）"；④ `_zf55_verify.py` / `_zf57_verify.py` 的"要查的格"推导同步改成 58，并新增"顶面 10 格进判定且都是图纸画了方块的"两条断言。探针 `AlloyLayoutCheck` **26 项全 [OK]**，其中新增的是 **ZF59 的核心三条**：只搭前三层 ⇒ 缺 10 格、判定不成立、**连心跳那条路也不许成型**；摆完第四层 ⇒ 才成型。反证：把顶面分支改回 `return false` ⇒ **4 FAIL**（`holes=0` / 提前成型 / blockstate 已 true / 部件格只剩 45） | 见 §9 |
'''

OLD9 = u'''- [ ] ZF57 待确认②（**仍然挂着**）：照图纸一层层搭的话，**第 4 层通常是"成型之后"才摆上去的** ——
      那几块会在**一秒内被机器吸收**（变成机器的一部分、看不见了，拆解时原样还给你，挖掉掉回耐热金属块）。
      要是不想要这个"吸收"、或者想让它**等第 4 层摆完再成型**，说一声就改。
'''

NEW9 = u'''- [x] ~~ZF57 待确认②：要不要"吸收"晚摆的顶层方块~~ → **ZF59 用户拍板：「等第四层摆完再成型」**。
      判定把顶面图纸画了方块的那 10 格也纳入（要查 48 → **58**）⇒ 图纸 4 层全摆完才成型，
      正常流程不再有晚摆的方块；`absorbNewHullBlocks()` 留给"成型后又往表面空格补方块"这种情况。
'''

TAIL = u'''
**ZF59 收尾**：用户选了"等第四层摆完再成型"，于是判定多查顶面那 10 格（48 → 58），
"成型"与"图纸摆完"从此是同一件事 —— 这比"先成型、再吸收晚摆的方块"干净：
**让判定符合玩家的操作顺序，比事后修补玩家的操作顺序要好**。
'''

SEC9 = u'''- [ ] **ZF59：等用户实测"摆完第四层才成型"**（成品 `10016a23…`）。现在要查 58 格：
      底面 + 三格高的墙 + 顶面那两列耐热金属块。要看的：① 搭完前三层**不该**有任何动静；
      ② 顶面那两列补完的那一下才成型（可能慢半秒 —— 心跳每 0.5 秒一次）。
'''


def main():
    text = io.open(DOC, encoding="utf-8").read()
    before = len(text)
    problems = []

    lines = text.split(u"\n")
    out = []
    added = False
    for line in lines:
        out.append(line)
        if line.startswith(u"| ZF58 |") and not added:
            out.append(ROW.rstrip(u"\n"))
            added = True
    if not added:
        problems.append(u"没找到 ZF58 行")
    text = u"\n".join(out)

    anchor9 = u"## 9. 待办与已知限制\n\n"
    if text.count(anchor9) != 1:
        problems.append(u"§9 标题不唯一")
    else:
        text = text.replace(anchor9, anchor9 + SEC9, 1)
    if text.count(OLD9) != 1:
        problems.append(u"§9 里 ZF57 待确认② 那条没找到（可能已被改过）")
    else:
        text = text.replace(OLD9, NEW9, 1)

    tail = u"> 这次不改数字，直接换成**结构断言**（空格只许出现在内部与顶面、内部 12 格全空）。\n"
    if text.count(tail) != 1:
        problems.append(u"§4.34 尾巴锚点不唯一（%d）" % text.count(tail))
    else:
        text = text.replace(tail, tail + TAIL, 1)

    if problems:
        print(u"有失败项，**不落盘**：")
        for p in problems:
            print(u"  !! " + p)
        return 1

    io.open(DOC, "w", encoding="utf-8", newline="\n").write(text)
    print(u"字数 %d -> %d（+%d）" % (before, len(text), len(text) - before))
    print(u"§5 ZF59 行 / §9（结掉待确认② + 新待办）/ §4.34 收尾 全部写入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
