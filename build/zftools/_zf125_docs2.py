# -*- coding: utf-8 -*-
u"""_zf125_docs2.py —— 把控制器贴图那一行从「待画」挪到「已经有自己贴图的」

**为什么**：`docs\贴图清单.md` 的「待画（N 个）」那张表的语义是
「**现在还借原版贴图**的方块/物品」（`TextureCheck.py --plan` 按"模型里指向 minecraft: 的贴图"生成），
而 ZF125 的控制器贴图是**我们自己的**（`_zf125_assets.py` 程序化画的 16×16 占位图），
模型指向 `potato_s_t:block/diesel_generator_controller` ⇒ 它**不属于**这张表。
我第一版把它塞进了「待画」并顺手把表头 13 改成 14 ⇒ `_zf90_verify.py` 两条当场红
（那条门交叉核 `_zf71_verify.py` 的 `n_draw == 13` 与这张表的表头，两个数必须一致）。

正确落点：**「已经有自己贴图的」**那张表，并注明"这是占位图、待美术替换"。

跑法：
    python build\\zftools\\_zf125_docs2.py
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = r"E:\PotatoST\docs\贴图清单.md"
BAD_ROW_MARK = u"| `textures/block/` | `diesel_generator_controller.png` | 柴油发电机控制器 |"
ANCHOR_ROW = u"| `textures/block/` | `acidic_reaction_chamber_side.png`"

notes, fails = [], []


def main():
    text = io.open(P, encoding="utf-8", newline=u"").read()
    nl = u"\r\n" if u"\r\n" in text else u"\n"

    # ① 表头 14 → 13
    if u"## 待画（14 个" in text:
        text = text.replace(u"## 待画（14 个", u"## 待画（13 个", 1)
        notes.append(u"① 表头改回 13 个")
    elif u"## 待画（13 个" in text:
        notes.append(u"① 表头本来就是 13 个")
    else:
        fails.append(u"找不到「待画（N 个」那行表头")

    # ② 把那一行从「待画」里摘掉
    lines = text.split(nl)
    kept, dropped = [], []
    for l in lines:
        if l.startswith(BAD_ROW_MARK):
            dropped.append(l)
            continue
        kept.append(l)
    if len(dropped) != 1:
        fails.append(u"「待画」里那一行命中 %d 次（要 1 次）" % len(dropped))
    else:
        notes.append(u"② 从「待画」里摘掉 1 行")
    text = nl.join(kept)

    # ③ 插到「已经有自己贴图的」那张表（只认 **第 36 行那个小节** 里那一行，别撞上后面两张同名表）
    head = u"## 已经有自己贴图的（列出来是方便你替换）"
    if head not in text:
        fails.append(u"找不到「已经有自己贴图的」小节标题")
        new_row = None
    else:
        seg_start = text.index(head)
        seg_end = text.find(u"\n## ", seg_start + 1)
        if seg_end < 0:
            seg_end = len(text)
        seg = text[seg_start:seg_end]
        anchor_in_seg = ANCHOR_ROW + u", `acidic_reaction_chamber_top.png` | acidic_reaction_chamber |"
        if seg.count(anchor_in_seg) != 1:
            fails.append(u"小节内锚点命中 %d 次（要 1 次）" % seg.count(anchor_in_seg))
            new_row = None
        else:
            new_row = (u"| `textures/block/` | `diesel_generator_controller.png` | "
                       u"柴油发电机控制器 —— ⚠ **程序化占位图**（`_zf125_assets.py` 画的 16×16："
                       u"金属面板 + 四角铆钉 + 一扇能看到柴油液位的观察窗），待美术替换 |")
            text = text[:seg_start] + seg.replace(anchor_in_seg, anchor_in_seg + nl + new_row, 1) \
                + text[seg_end:]
            notes.append(u"③ 在「已经有自己贴图的」小节里插了 1 行（注明「占位图、待美术替换」）")

    io.open(P, "w", encoding="utf-8", newline=u"").write(text)
    back = io.open(P, encoding="utf-8", newline=u"").read()
    if u"## 待画（13 个" not in back:
        fails.append(u"回读：表头不是 13")
    if back.count(u"diesel_generator_controller.png") != 1:
        fails.append(u"回读：控制器贴图出现 %d 次（要 1 次）"
                     % back.count(u"diesel_generator_controller.png"))
    if not fails:
        notes.append(u"回读通过（表头 13、控制器贴图恰 1 行）")

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
