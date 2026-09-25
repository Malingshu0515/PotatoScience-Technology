# -*- coding: utf-8 -*-
"""_zf54_docs.py —— §5 加 ZF54 行 + §9 补两条（模型已整体化 / 摆放图仍然有效）。"""
import io

DOC = r"E:\PotatoST\docs\开发档案.md"
ROW_ANCHOR = u"> ZF40~ZF44 全是**电力高炉的连续改动**"
NOTE_ANCHOR = u"## 10. 备份策略"

ROW = (
    u"| ZF54 | 复用 `zf49_pre`（同 ZF50~53） | 0.10：**合金冶炼炉改成「电力高炉那样的整体建模」**"
    u"（用户：「改成像电力高炉那样的建模 先用4*5*4的长方体」；并在两个选项里选了"
    u"「只是模型：结构还得逐格摆对」）。① 新增 `alloy_smelter_part` 部件格（INVISIBLE + 不掉落，"
    u"**不需要方块实体**）；② `build/zftools/_zf54_obj.py` 生成 **4×5×4 长方体的 OBJ + MTL**"
    u"（四个朝向各烘一份；包围盒由 80 格算出，南向 = X[-3,1] Z[-4,1] Y[-1,3]）；③ 4 个 "
    u"`neoforge:obj` model JSON + blockstate 按 facing 挑那一份；④ **接线口改 INVISIBLE**"
    u"（否则和盒子的面 z-fighting）；⑤ 成型时把 **80 格原始方块状态**记进 NBT"
    u"（`cells`/`cellStates`，与电力高炉同款），77 格换部件格、2 格换接线口、控制器那格不动；"
    u"⑥ 拆解 `disassemble(skip)` 原样还原（ZF40 的 `skip` 教训）；⑦ 部件格 `onRemove` 掉回**原方块**。"
    u"探针 `AlloyModelCheck`：成型后 `part=77 port=2 controller=1 other=0`、挖一格掉原方块（且不掉部件格）、"
    u"整台失效、其余格还原、再成型后满拆解 **restored=58 / leftover=0** ⇒ **16 项全 [OK]**；"
    u"反证（让两处接线块也变部件格）⇒ **2 项 FAIL**。另写 `_zf54_verify.py`：**OBJ 包围盒必须正好罩住 "
    u"4×5×4**（四朝向逐个算）+ 模型/blockstate 接线 + **ZF52 摆放图回归**，全过。"
    u"⚠ 探针第一轮又有 1 条假 FAIL：我把「相邻格」挑成了图纸里本就是空气的格（§4.31 第 2 次） | 见 §9 |\n"
)

NOTE = (
    u"- [ ] **ZF54 起，合金冶炼炉激活后是一整块模型了**：结构格换成不渲染的部件格，控制器那格画"
    u"一个 **4×5×4 长方体**（贴图就是主控那张，UV 每面 0..1 ⇒ 会拉伸，这是占位）。以后换正式模型"
    u"只要替换 `models/block/alloy_smelter_{north,east,south,west}.obj` 并保持"
    u"**包围盒 = 4×5×4、原点在控制器角点**（`_zf54_verify.py` 会核对）。\n"
    u"      - [ ] 挖任意一格部件格 = 掉回**原来那个方块**，且整台失效（其余格立刻还原）\n"
    u"      - [ ] 拆解（扳手 Shift 右键控制器）会把 80 格**原样还原**、控制器那格变空气、掉回一个主控\n"
    u"- [ ] ⚠ **「激活不了」与建模无关**：判定逻辑一个字没改。ZF53 那几行报错（第几层/第几排/第几格 + "
    u"**实际是什么** + 坐标，一次列 4 处）仍是唯一能定位根因的东西。\n\n"
)

text = io.open(DOC, encoding="utf-8").read()
changed = []
if u"| ZF54 |" not in text:
    i = text.index(ROW_ANCHOR)
    text = text[:i] + ROW + u"\n" + text[i:]
    changed.append(u"§5 加了 ZF54 行")
if u"ZF54 起，合金冶炼炉激活后是一整块模型了" not in text:
    i = text.index(NOTE_ANCHOR)
    text = text[:i] + NOTE + text[i:]
    changed.append(u"§9 加了 ZF54 注意事项")
if changed:
    io.open(DOC, "w", encoding="utf-8", newline="").write(text)
    print(u"；".join(changed))
else:
    print(u"已经写过了")
