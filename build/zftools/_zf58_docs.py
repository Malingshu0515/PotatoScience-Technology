# -*- coding: utf-8 -*-
"""_zf58_docs.py —— ZF58 档案落笔

三处动：① §5 加 ZF58 行；② §9 把"第4层第5排待确认"那条结掉 + 新待办；③ §12.16 补一段
（OBJ 的包围盒也是按旧列号烘的 ⇒ 模型偏 3 格，与"读反一个数字"同一类错）。
"""
import io
import sys

DOC = r"E:\PotatoST\docs\开发档案.md"

ROW = u'''| ZF58 | **新建 `zf58_pre`**（13 个改前件：`AlloySmelterStructure` + 4 份 `.obj` + 4 个 lang + `_zf54_obj.py` / `_zf54_verify.py` / `_zf57_verify.py` / `_zf57_lang.py`） | 0.10：**用户截图报了三件事**。① **模型在左边、机器方块在右边** ⇒ ZF57 把主控从最左列挪到最右列时，**OBJ 的包围盒还是按旧的列号烘的**（`_zf54_obj.py` 里写死 `i * u`，等于 CTRL_I=0）⇒ 整台模型偏了 3 格。改法：**生成脚本与校验脚本都改成现读 Java 里的 `CTRL_Y/J/I` 与 `HEIGHT`**（不再自己假设列号），重新烘四份 OBJ ⇒ 南向 `X[0,4] Z[-4,1] Y[-1,3]`；② **第 4 层是 5 排**【空·耐热·耐热·空】（ZF57 时用户只写了 4 排、我按空补了第 5 排）⇒ `LAYERS` 与四语言介绍图的最后一行 `0000` 改成 `0110`；③ **Jade 显示的是 id**（`block.potato_s_t.alloy_smelter_part`）⇒ 部件格缺 lang 条目，四语言补上（照电力高炉的做法，用**整台机器**的名字：合金冶炼炉 / Alloy Smelter / 合金精錬炉 / Плавильня сплавов），lang 200 → **201** 键。探针 `AlloyLayoutCheck` 复跑 **24 项全 [OK]**（新数：部件格 55 / 接线口 2 / 顶面空格 10）。反证：把**旧的** `alloy_smelter_south.obj` 放回去 ⇒ `_zf54_verify.py` 当场报 `south：X 范围 (-3.0, 1.0) == 预期 (0, 4.0)` —— 这条检查就是为"模型跟机器对不上"准备的 | 见 §9 |
'''

OLD9 = u'''- [ ] **ZF57：等用户确认两件事**（成品 `812f2142…`）。
      ① **第 4 层用户只写了 4 排**（都是【】【1】【1】【】），第 5 排（最前排）我按「空」补进图里 ⇒
         如果那一排也要耐热金属块，说一声就改（顶面不参与判定，只影响介绍图与吸收范围）。
      ② 现在照图纸一层层搭的话，**第 4 层通常是"成型之后"才摆上去的** —— 那几块会在**一秒内被机器吸收**
         （变成机器的一部分、看不见了，拆解时原样还给你，挖掉掉回耐热金属块）。
         要是不想要这个"吸收"，或者想让它**等第 4 层摆完再成型**，也可以改。
'''

NEW9 = u'''- [x] ~~ZF57 待确认①：第 4 层第 5 排~~ → **ZF58 用户答复：5 排都要**【】【1】【1】【】。
- [ ] ZF57 待确认②（**仍然挂着**）：照图纸一层层搭的话，**第 4 层通常是"成型之后"才摆上去的** ——
      那几块会在**一秒内被机器吸收**（变成机器的一部分、看不见了，拆解时原样还给你，挖掉掉回耐热金属块）。
      要是不想要这个"吸收"、或者想让它**等第 4 层摆完再成型**，说一声就改。
'''

TAIL = u'''
**ZF58 补记（同一类错的第二个受害者）**：ZF57 把 `CTRL_I` 从 0 改成 3（主控挪到最右列）时，
**OBJ 的包围盒没有跟着翻** —— `_zf54_obj.py` 里把"控制器在最前排最左格"写死在 `i * u` 里，
于是模型整体偏了 3 格（用户截图：**模型在左边、机器方块在右边**）。
更糟的是 `_zf54_verify.py` 的 `expected_box()` 也用了同一套写死的列号 ⇒ **代码和检查一起错、门全绿**。
修法与 §12.16 同一条：**两边都改成现读 Java 里的 `CTRL_Y/J/I`**，并加一条"旧 OBJ 放回去必须报错"的反证
（旧件当场报 `south：X 范围 (-3.0, 1.0) == 预期 (0, 4.0)`）。
'''

SEC9 = u'''- [ ] **ZF58：等用户再看一眼模型位置**（成品 `9c917dad…`）。现在四份 OBJ 的包围盒是**按当前
      `CTRL_Y/J/I` 现算**的，南向应当是 `X[0,4] Z[-4,1] Y[-1,3]`（控制器那一格在盒子的一角）。
      要看的：成型后**盒子正好罩住机器方块**（不再偏左/偏右）；Jade 指着机器时显示「合金冶炼炉」而不是 id。
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
        if line.startswith(u"| ZF57 |") and not added:
            out.append(ROW.rstrip(u"\n"))
            added = True
    if not added:
        problems.append(u"没找到 ZF57 行")
    text = u"\n".join(out)

    anchor9 = u"## 9. 待办与已知限制\n\n"
    if text.count(anchor9) != 1:
        problems.append(u"§9 标题不唯一")
    else:
        text = text.replace(anchor9, anchor9 + SEC9, 1)
    if text.count(OLD9) != 1:
        problems.append(u"§9 里 ZF57 那条待确认没找到（可能已被改过）")
    else:
        text = text.replace(OLD9, NEW9, 1)

    tail = u"  否则读反一个数字，代码和测试会一起错。\n"
    if text.count(tail) != 1:
        problems.append(u"§12.16 尾巴锚点不唯一（%d）" % text.count(tail))
    else:
        text = text.replace(tail, tail + TAIL, 1)

    if problems:
        print(u"有失败项，**不落盘**：")
        for p in problems:
            print(u"  !! " + p)
        return 1

    io.open(DOC, "w", encoding="utf-8", newline="\n").write(text)
    print(u"字数 %d -> %d（+%d）" % (before, len(text), len(text) - before))
    print(u"§5 ZF58 行 / §9（结掉一条 + 新待办）/ §12.16 补记 全部写入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
