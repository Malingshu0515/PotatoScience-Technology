# -*- coding: utf-8 -*-
"""_zf52_docs.py —— 往 §5 表尾加 ZF52 行、往 §9 补一条。

⚠ 本文件踩了两次 Python 语法错：中文里混了**直角双引号**当引号用，把 Python 字符串截断了。
   现在所有引号一律用「」。
"""
import io

DOC = r"E:\PotatoST\docs\开发档案.md"
ROW_ANCHOR = u"> ZF40~ZF44 全是**电力高炉的连续改动**"
NOTE_ANCHOR = u"## 10. 备份策略"

ROW = (
    u"| ZF52 | 复用 `zf49_pre`（同 ZF50/51：只改 ZF49 起那批文件） | 0.10："
    u"**把合金炉主控的介绍改成「摆放方式」**（用户：「合金冶炼炉控制器介绍改成合金炉摆放方式」）。"
    u"工具提示从散文改成**数字摆放图**：`0` 空 / `1` 一般金属块 / `2` 加热装置 / `3` 耐热金属块 / "
    u"`4` 接线块 / `5` 高炉 / `6` 主控 / `7` 漏斗 / `8` 炼药锅 / `9` 散热装置；四层**两列并排**、"
    u"`|` 当列分隔（不并排就是 20 行，工具提示会糊满屏幕）⇒ 四语言各 16 行。**关键**：新写 "
    u"`_zf52_verify.py` 把工具提示里的数字图**解析回 4×5×4 网格**，与 `AlloySmelterStructure.java` "
    u"里的图案**逐格比对**（工具提示画错一格 = 骗玩家）⇒ 四语言全一致；反证（把中文第二层前排的 "
    u"`6337` 改成 `6339`）⇒ **1 项 FAIL**，报「图里 CRRS / 代码 CRRP」 | 见 §9 |\n"
)

NOTE = (
    u"- [ ] **ZF52 起，主控的介绍就是摆放图了**（按 Shift 看）：数字图 + 图例 + 一行说明，四语言各 16 行。"
    u"改结构时**必须同时改四语言的图** —— `_zf52_verify.py` 会把图与 `AlloySmelterStructure.LAYERS` "
    u"逐格比对，画错一格就报错（这轮的反证实测过）。想换记法（比如把 `0` 换成 `·`）改脚本里的 "
    u"`DIGIT` 表即可。\n"
    u"- [ ] 摆放图目前**只印在物品介绍里**（按 Shift）。嫌太长或不好看的话，也可以做成界面里的一页、"
    u"或 JEI 的一张信息页 —— 说一声。\n\n"
)

text = io.open(DOC, encoding="utf-8").read()
changed = []
if u"| ZF52 |" not in text:
    idx = text.index(ROW_ANCHOR)
    text = text[:idx] + ROW + u"\n" + text[idx:]
    changed.append(u"§5 加了 ZF52 行")
if u"ZF52 起，主控的介绍就是摆放图了" not in text:
    idx = text.index(NOTE_ANCHOR)
    text = text[:idx] + NOTE + text[idx:]
    changed.append(u"§9 加了 ZF52 注意事项")
if changed:
    io.open(DOC, "w", encoding="utf-8", newline="").write(text)
    print(u"；".join(changed))
else:
    print(u"已经写过了，跳过")
