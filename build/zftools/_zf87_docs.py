# -*- coding: utf-8 -*-
u"""_zf87_docs.py —— ZF87（油桶贴图）+ 活体数字（借原版贴图的模型 8 → 7）+ 把 ZF86 校验扩成 5 件

用户又放了一张：`油桶.jpg`（油桶物品图标一直借的是原版铁锭）。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
DOCS = os.path.join(ROOT, "docs")
fails = []

ROW = (u"| ZF87 | **新建 `zf87_pre`**（6 份改前件：`油桶.jpg` / `oil_bucket.json` / 2 份文档 / 旧成品 jar 与 "
       u"`.sha1`；**先抄后动手**） | 0.11：**油桶物品贴图换新**（用户直接放进来的 `油桶.jpg`，16×16）。"
       u"油桶图标此前一直**借原版铁锭**（`models/item/oil_bucket.json` 的 layer0）⇒ 本轮转档成"
       u" `textures/item/oil_bucket.png`（16×16 / 8 位 / RGBA，四边泛洪去背景）并让模型指向自己；"
       u"原图按 §4.24 挪到 `build/用户素材/oil_bucket.jpg`。活体数字跟着动：**借原版贴图的模型 8 → 7**"
       u"（英文公告与 `_zf71_verify.py` 同步）。 |\n")

VERIFY = u"""
### ZF87（0.11）油桶贴图 —— 待你实测

- [ ] **油桶**（`potato_s_t:oil_bucket`）的图标应当换成你给的那张（原先借的是原版铁锭）
- [ ] 顺带把 ZF85/ZF86 那两条也看一眼：IDE 里 `ModFluids.java` 应无警告；
      **八种流体的外观**（原油/柴油/石脑油/汽油/液化石油气/氧/氢/氯）必须和以前完全一样

**成品**：`release\\PotatoST-0.11.jar` = `__NEWSHA__`（__NEWSIZE__ B / __NEWENTRIES__ 条目），
**作废上一版 `ba7ecc97eff87461704849b35680d632295c8079`**（ZF86）；0.10 成品 `84d09345…` 原样保留。
"""

TEX_SECTION = u"""
## ZF87（0.11）：油桶贴图

| 文件 | 状态 | 说明 |
|---|---|---|
| `textures/item/oil_bucket.png` | ✅ **新建** | 用户给的 `油桶.jpg`（16×16）⇒ 转档（四边泛洪去背景）；油桶图标此前借**原版铁锭** |
| `build/用户素材/oil_bucket.jpg` | 留档 | §4.24 原名件（不进 jar） |
"""


def patch(rel, old, new, label, expect=1):
    p = os.path.join(ROOT, rel)
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
    # ① 活体数字：借原版贴图的模型 8 → 7（油桶不再借铁锭）
    patch(r"docs\UpdateAnnouncement_EN.md", u"8 models still do this", u"7 models still do this",
          u"公告 8 → 7")
    patch(r"build\zftools\_zf71_verify.py",
          u'check(n_draw == 8 and u"8 models still do this" in doc,',
          u'check(n_draw == 7 and u"7 models still do this" in doc,',
          u"活体校验 8 → 7")

    # ② ZF86 的校验扩成 5 件（把油桶也算进"真 PNG / 指向自己"那一组）
    patch(r"build\zftools\_zf86_verify.py",
          u'FOUR = [u"copper_plate", u"sodium_chloride", u"capacitor", u"lithium_carbonate"]',
          u'# ⚠ ZF87 追加 oil_bucket：同一批"用户放图 ⇒ 转档 ⇒ 模型指向自己"的活，同一套断言\n'
          u'FOUR = [u"copper_plate", u"sodium_chloride", u"capacitor", u"lithium_carbonate",\n'
          u'        u"oil_bucket"]',
          u"ZF86 校验扩成 5 件")

    # ③ 档案：§5 ZF87 行 + §9
    arch_p = os.path.join(DOCS, u"开发档案.md")
    arch = io.open(arch_p, encoding="utf-8").read()
    if u"| ZF87 |" not in arch:
        arch = insert_after(arch, u"| ZF86 | **新建 `zf86_pre`**", ROW, u"档案 §5：ZF87 行")
    if u"### ZF87（0.11）油桶贴图" not in arch:
        if arch.count(u"\n## 10. 备份策略") != 1:
            fails.append(u"档案 §9：锚点命中 %d 次" % arch.count(u"\n## 10. 备份策略"))
        else:
            arch = arch.replace(u"\n## 10. 备份策略", u"\n" + VERIFY + u"\n## 10. 备份策略", 1)
    io.open(arch_p, "w", encoding="utf-8", newline=u"\n").write(arch)

    tex_p = os.path.join(DOCS, u"贴图清单.md")
    tex = io.open(tex_p, encoding="utf-8").read()
    if u"## ZF87（0.11）" not in tex:
        io.open(tex_p, "w", encoding="utf-8", newline=u"\n").write(
            tex.rstrip(u"\n") + u"\n" + TEX_SECTION)
        print(u"贴图清单：追加 ZF87 一节")

    print(u"文档改完，失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
