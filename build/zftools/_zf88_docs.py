# -*- coding: utf-8 -*-
u"""_zf88_docs.py + verify —— 用户又放两张流体贴图（石油 / 柴油）：文档 + 独立校验

（这个文件只写文档；校验在 `_zf88_verify.py`。）
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

ROW = (u"| ZF88 | **新建 `zf88_pre`**（10 份改前件：4 张流体贴图 + 2 张用户原图 + 2 份文档 + 旧成品 jar 与 "
       u"`.sha1`；**先抄后动手**） | 0.11：**原油与柴油的流体贴图换新**（用户又直接放了两张进 "
       u"`textures/block`：`石油.png`、`柴油.png`）。两张**本来就是合格的 16×16 / 8 位 / RGBA**，"
       u"所以**原样转写**（零重采样、零调色）到 `crude_oil_still/flow` 与 `diesel_still/flow`；"
       u"核了两件事：alpha 全不透明、且与旧图**不同**（防「改了没生效」）。原图按 §4.24 挪到 "
       u"`build/用户素材/{crude_oil,diesel}.png`。⚠ 注意：这类「用户随时往资源目录丢图」的节奏下，"
       u"门里那两条「**不许中文文件名**」（item 与 block 两个目录各一条）就是安全网。 |\n")

VERIFY = u"""
### ZF88（0.11）石油 / 柴油流体贴图 —— 待你实测

- [ ] 世界里**原油**的颜色偏深灰（平均 RGB 35,35,35）、**柴油**偏棕黄（平均 RGB 172,116,42）
- [ ] 分馏塔操作器里那两个罐、JEI 图标同步变；液体**流动**时用的是同一张（本工程惯例）
- [ ] 仍待复核的旧项：汽油那张（ZF84）、三张板子 + 氯化钠/电容/碳酸锂/油桶（ZF83/86/87）、
      以及 **ZF85 那轮"八种流体外观不许变"**（那是清警告时唯一的回归风险）

**成品**：`release\\PotatoST-0.11.jar` = `__NEWSHA__`（__NEWSIZE__ B / __NEWENTRIES__ 条目），
**作废上一版 `3659d7ce8937f8f80fbabdd7cb4e5f557f4e05fa`**（ZF87）；0.10 成品 `84d09345…` 原样保留。
"""

TEX_SECTION = u"""
## ZF88（0.11）：原油 / 柴油流体贴图

| 文件 | 状态 | 说明 |
|---|---|---|
| `textures/block/crude_oil_still.png` + `_flow.png` | ✅ **换新** | 用户 `石油.png`（16×16/8/RGBA，平均 RGB 35,35,35）原样转写 |
| `textures/block/diesel_still.png` + `_flow.png` | ✅ **换新** | 用户 `柴油.png`（平均 RGB 172,116,42）原样转写 |
| `build/用户素材/{crude_oil,diesel}.png` | 留档 | §4.24 原名件（不进 jar） |
"""


def patch(rel, old, new, label, expect=1):
    p = os.path.join(r"E:\PotatoST", rel)
    t = io.open(p, encoding="utf-8").read()
    n = t.count(old)
    if n != expect:
        fails.append(u"%s：锚点命中 %d 次（期望 %d）" % (label, n, expect))
        return
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, expect))
    print(u"  [OK]   %s" % label)


def insert_after(text, anchor, block, label):
    if text.count(anchor) != 1:
        fails.append(u"%s：锚点命中 %d 次" % (label, text.count(anchor)))
        return text
    at = text.find(anchor)
    eol = text.find(u"\n", at)
    return text[:eol + 1] + block + text[eol + 1:]


def main():
    arch_p = os.path.join(DOCS, u"开发档案.md")
    arch = io.open(arch_p, encoding="utf-8").read()
    if u"| ZF88 |" not in arch:
        arch = insert_after(arch, u"| ZF87 | **新建 `zf87_pre`**", ROW, u"档案 §5：ZF88 行")
    if u"### ZF88（0.11）石油 / 柴油流体贴图" not in arch:
        if arch.count(u"\n## 10. 备份策略") != 1:
            fails.append(u"档案 §9：锚点命中 %d 次" % arch.count(u"\n## 10. 备份策略"))
        else:
            arch = arch.replace(u"\n## 10. 备份策略", u"\n" + VERIFY + u"\n## 10. 备份策略", 1)
    io.open(arch_p, "w", encoding="utf-8", newline=u"\n").write(arch)

    tex_p = os.path.join(DOCS, u"贴图清单.md")
    tex = io.open(tex_p, encoding="utf-8").read()
    if u"## ZF88（0.11）" not in tex:
        io.open(tex_p, "w", encoding="utf-8", newline=u"\n").write(tex.rstrip(u"\n") + u"\n" + TEX_SECTION)
        print(u"贴图清单：追加 ZF88 一节")

    print(u"文档改完，失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
