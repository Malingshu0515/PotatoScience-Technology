# -*- coding: utf-8 -*-
u"""_zf86_docs.py —— ZF86 文档：档案 §5 ZF86 行 + §9 验收 + 贴图清单

（用户这一批是"又放了几张素材"：铜板被重存成了 JPEG、氯化钠、电容、碳酸锂。）
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


def read(p):
    if not os.path.exists(p):
        fails.append(u"缺文件：%s" % p)
        return u""
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t)


def insert_after(text, anchor, block, label):
    if text.count(anchor) != 1:
        fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (label, text.count(anchor)))
        return text
    at = text.find(anchor)
    eol = text.find(u"\n", at)
    return text[:eol + 1] + block + text[eol + 1:]


ROW = (u"| ZF86 | **新建 `zf86_pre`**（11 份改前件：4 张素材 / 3 个物品模型 / 2 份文档 / 旧成品 jar 与 `.sha1`；"
       u"逐份核哈希、失败 0。**先抄后动手**） | "
       u"0.11：**用户又放了四张素材，全部转档上线**。① ⚠ **`copper_plate.png` 的内容其实是 JPEG**"
       u"（用户重存铜板时存成了 jpg 却仍叫 .png）—— 游戏里会当坏图，门里那条「必须真 PNG」当场抓住；"
       u"解出来重写成**真 PNG**（16×16 / 8 位 / RGBA，保留用户的画）。"
       u"② **氯化钠** `氯化钠.jpg` → `sodium_chloride.png`（原先借原版**糖**的贴图）；"
       u"③ **电容** `电容.jpg` → `capacitor.png`（原先借原版**铁粒**）；"
       u"④ **碳酸锂** `碳酸锂.png` 是 **20×20** 自带 alpha 的图 ⇒ 取非透明包围盒（19×13）**最近邻**缩到 16×16"
       u"（像素画不重采样取平均，免得糊成一团）；三件物品的模型全部改成指向自己的贴图。"
       u"⑤ 四张原图按 §4.24 挪到 `build/用户素材/`（ASCII 名 + `_来源凭据.json` 记哈希），"
       u"**资源目录里不留中文名**。⑥ 转档规则仍用 §4.56 那套：从四边泛洪 + 只留最大连通域。 |\n")

VERIFY = u"""
### ZF86（0.11）四张素材转档 —— 待你实测

- [ ] **铜板**：图标应当还是你画的那张（我把那个"扩展名骗人的 JPEG"重存成了真 PNG）
- [ ] **氯化钠 / 电容 / 碳酸锂**：三件物品的图标应当换成你新给的三张（原先氯化钠借的是原版糖、
      电容借的是原版铁粒）
- [ ] 碳酸锂那张原来是 **20×20**，我按非透明范围**最近邻**缩到了 16×16 —— 如果你觉得糊了，
      给我一张 16×16 的就行
- [ ] 顺带上一轮（ZF85）：IDE 里 `ModFluids.java` 的 25 条警告/报错应当清干净了，
      且**八种流体的外观必须和以前完全一样**（那条是本轮唯一的回归风险）

**成品**：`release\\PotatoST-0.11.jar` = `__NEWSHA__`（__NEWSIZE__ B / __NEWENTRIES__ 条目），
**作废上一版 `c2aa30f92f532798f8c36f7ae48cb9c923ee79d9`**（ZF85）；0.10 成品 `84d09345…` 原样保留。
"""

TEX_SECTION = u"""
## ZF86（0.11）：四张素材转档（铜板 / 氯化钠 / 电容 / 碳酸锂）

| 文件 | 状态 | 来源 / 说明 |
|---|---|---|
| `textures/item/copper_plate.png` | ✅ **重存** | 内容其实是 JPEG（扩展名骗人）⇒ 解出来重写成真 PNG，保留用户的画 |
| `textures/item/sodium_chloride.png` | ✅ **新建** | 用户 `氯化钠.jpg`（原先借原版**糖**） |
| `textures/item/capacitor.png` | ✅ **新建** | 用户 `电容.jpg`（原先借原版**铁粒**） |
| `textures/item/lithium_carbonate.png` | ✅ **新建** | 用户给的 **20×20** 图 ⇒ 按非透明包围盒最近邻缩到 16×16 |
| `build/用户素材/{sodium_chloride,capacitor,lithium_carbonate}.jpg/.png` | 留档 | §4.24 原名件（不进 jar），哈希在 `_来源凭据.json` |
"""


def main():
    arch_p = os.path.join(DOCS, u"开发档案.md")
    arch = read(arch_p)
    if u"| ZF86 |" not in arch:
        arch = insert_after(arch, u"| ZF85 | **新建 `zf85_pre`**", ROW, u"档案 §5：ZF86 行")
    if u"### ZF86（0.11）四张素材转档" not in arch:
        if arch.count(u"\n## 10. 备份策略") != 1:
            fails.append(u"档案 §9：锚点命中 %d 次" % arch.count(u"\n## 10. 备份策略"))
        else:
            arch = arch.replace(u"\n## 10. 备份策略", u"\n" + VERIFY + u"\n## 10. 备份策略", 1)
    write(arch_p, arch)

    tex_p = os.path.join(DOCS, u"贴图清单.md")
    tex = read(tex_p)
    if u"## ZF86（0.11）" not in tex:
        write(tex_p, tex.rstrip(u"\n") + u"\n" + TEX_SECTION)
        print(u"贴图清单：追加 ZF86 一节")

    print(u"文档改完，失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
