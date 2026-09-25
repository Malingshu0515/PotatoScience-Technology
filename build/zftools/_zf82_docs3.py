# -*- coding: utf-8 -*-
u"""_zf82_docs3.py —— 补一笔：用户新放进 textures/item 的三张素材按 §4.24 挪走留档

（这件事是门炸出来的，不是本轮任务；照实记进贴图清单与档案 §9，并说明**没有**动任何在用贴图。）
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOCS = r"E:\PotatoST\docs"
fails = []

TEX_NOTE = u"""
### 顺带一件（门炸出来的）：用户新放进 `textures/item` 的三张素材

`钢板.jpg` / `铁板.jpg` / `铜板.jpg`（09-23、09-24 放进来的）被 ZF66 那条
「textures/item 下不许有中文文件名」检查逮住。处理：**原样挪出资源目录**、逐字节留档到
`build/用户素材/`（ASCII 名 `steel_plate.jpg` / `iron_plate.jpg` / `copper_plate.jpg`
+ `_来源凭据.json` 记哈希）。

⚠ **没有动任何在用的贴图**：铜板/钢板早就有 ASCII PNG（`copper_plate.png` / `steel_plate.png`，
09-19），铁板目前仍借原版贴图。**要不要把这三张 jpg 转成 16×16 RGBA 用上去（尤其铁板）**——
说一声就做，属一个生成器 + 三个模型的事。
"""

ARCH_NOTE = u"""- [ ] **三张板材素材**：`build/用户素材/{steel,iron,copper}_plate.jpg` 是你在 ZF82 前后放进
      `textures/item` 的原图，已按 §4.24 挪出资源目录留档；**在用的贴图一张没动**。
      要不要把它们转成 16×16 用上（铁板目前还借原版贴图）—— 说一声
"""


def main():
    tex_p = os.path.join(DOCS, u"贴图清单.md")
    tex = io.open(tex_p, encoding="utf-8").read()
    if u"用户新放进 `textures/item` 的三张素材" not in tex:
        io.open(tex_p, "w", encoding="utf-8", newline=u"\n").write(tex.rstrip(u"\n") + u"\n" + TEX_NOTE)
        print(u"贴图清单：补上三张素材那一节")

    arch_p = os.path.join(DOCS, u"开发档案.md")
    arch = io.open(arch_p, encoding="utf-8").read()
    anchor = u"### ZF82（0.11）柴油桶/汽油桶 + 容器换流器 —— 待你实测"
    if u"build/用户素材/{steel,iron,copper}_plate.jpg" not in arch:
        if arch.count(anchor) != 1:
            fails.append(u"§9 ZF82 锚点命中 %d 次" % arch.count(anchor))
        else:
            arch = arch.replace(anchor, anchor + u"\n\n" + ARCH_NOTE, 1)
            io.open(arch_p, "w", encoding="utf-8", newline=u"\n").write(arch)
            print(u"档案 §9：补上三张素材那条待办")

    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
