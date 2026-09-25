# -*- coding: utf-8 -*-
"""_zf51_docs.py —— 往档案 §9 里插一段 ZF51 的待确认项（插在 "## 10. 备份策略" 之前）。

用文件而不是 `python -c`：那行锚点里带全角括号和反引号，在 PowerShell 里转义太容易出错
（本次已经因为同样的原因踩过一次）。
"""
import io

DOC = r"E:\PotatoST\docs\开发档案.md"
ANCHOR = u"## 10. 备份策略"

NOTE = u"""- [ ] **ZF51 已改成"匠魂式控制器"**：这个方块现在叫**合金炉主控**，放下时**不是**炉子 ——
      空手右键（带不带 Shift 都一样）= 试激活，结构不完整会告诉你哪一格不对；
      **激活之后**右键才开界面，界面标题才变成"合金冶炼炉"。
      未激活时：灌不进电、10 个槽位一个都不收、界面根本打不开。
      要改文案动这 3 个键：`block.potato_s_t.alloy_smelter`（主控名）/
      `gui.potato_s_t.alloy_smelter.name`（炉子名）/ `gui.potato_s_t.alloy_smelter.formed`
- [ ] 激活 / 未激活**外观完全一样**（你只给了一张贴图）。想要"激活后看得出区别"，
      我可以照你那张生成一张"点亮版"（炉火更亮）并给方块加一个 `active` 状态 —— 说一声
- [ ] 控制器自己**不再暴露能量能力**（ZF51 收紧）：电只从那两处接线口进，与 §9 一直写着的口径一致

"""

text = io.open(DOC, encoding="utf-8").read()
if u"ZF51 已改成" in text:
    print(u"已经插过了，跳过")
else:
    idx = text.index(ANCHOR)
    text = text[:idx] + NOTE + text[idx:]
    io.open(DOC, "w", encoding="utf-8", newline="").write(text)
    print(u"已插入 §9 的 ZF51 注意事项（%d 字符）" % len(NOTE))
