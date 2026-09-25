# -*- coding: utf-8 -*-
u"""_zf84_docs.py —— ZF84 文档：贴图清单更新 + 档案 §5 ZF84 行 + §9 验收

`__NEWSHA__` / `__NEWSIZE__` / `__NEWENTRIES__` 由 `_zf84_publish.py` 填真值。
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


ROW = (u"| ZF84 | **新建 `zf84_pre`**（6 份改前件：`gasoline_still.png` / `gasoline_flow.png` / "
       u"2 份文档 / 旧成品 jar 与 `.sha1`；逐份核哈希、失败 0。**这次是先抄后动手**） | "
       u"0.11：**汽油流体贴图换新**（用户原话：「**汽油的新贴图**」+ 一张 16×16 JPEG）。"
       u"① 新图转档成 `textures/block/gasoline_still.png` **与** `gasoline_flow.png`"
       u"（16×16 / 8 位 / RGBA / 全不透明；ZF78 起这两张一直是**同一张图**兼作 still/flow，本轮保持该约定）；"
       u"平均 RGB (187,174,106)、12 种颜色 —— 就是用户发来的那张（写回逐像素核对 256/256）。"
       u"② 旧图 sha1 `30b5e42d…` → 新图 `35cee09b…`（校验里断言「必须与旧图不同」，防「改了没生效」）。"
       u"③ 原图按 §4.24 存 `build/用户素材/gasoline_new.jpg` 并记进 `_来源凭据.json`。"
       u"④ 校验 `_zf84_verify.py` 顺带钉住「**流体类型确实指向这两个文件**」"
       u"（`ModFluids` 里的 `block/gasoline_still|_flow`）—— 否则换了图但没人用。 |\n")

VERIFY = u"""
### ZF84（0.11）汽油流体贴图换新 —— 待你实测

- [ ] 世界里的**汽油**（液体方块 / 桶倒出来的那格）颜色应当是这张新图：偏黄绿的金色
- [ ] 分馏塔操作器的汽油罐、JEI 里的汽油图标也应当同步变（同一个贴图文件）
- [ ] 顺带：桶里的汽油**流动**时用的也是同一张图（ZF78 起 still/flow 同图，本轮保持）
- [ ] ⚠ 上一轮那两条还没在启动器实例里复核：**三张板子贴图**、**柴油桶/汽油桶 + 容器换流器**

**成品**：`release\\PotatoST-0.11.jar` = `__NEWSHA__`（__NEWSIZE__ B / __NEWENTRIES__ 条目），
**作废上一版 `9e2a9e25882dd0f27ecc2392c63ccea1cfc2b015`**（ZF83）；0.10 成品 `84d09345…` 原样保留。
"""

TEX_SECTION = u"""
## ZF84（0.11）：汽油流体贴图换新

| 文件 | 状态 | 说明 |
|---|---|---|
| `textures/block/gasoline_still.png` | ✅ **换新** | 用户 2026-09-24 发来的「汽油的新贴图」（16×16 JPEG）转档：16×16 / 8 位 / RGBA / 全不透明，平均 RGB (187,174,106) |
| `textures/block/gasoline_flow.png` | ✅ **换新** | 同上（ZF78 起的约定：still 与 flow 用**同一张**图） |
| `build/用户素材/gasoline_new.jpg` | 留档 | §4.24 原名件（不进 jar），哈希在 `_来源凭据.json` |
"""


def main():
    arch_p = os.path.join(DOCS, u"开发档案.md")
    arch = read(arch_p)
    if u"| ZF84 |" not in arch:
        arch = insert_after(arch, u"| ZF83 | **补建 `zf83_pre`**", ROW, u"档案 §5：ZF84 行")
    if u"### ZF84（0.11）汽油流体贴图换新" not in arch:
        if arch.count(u"\n## 10. 备份策略") != 1:
            fails.append(u"档案 §9：锚点命中 %d 次" % arch.count(u"\n## 10. 备份策略"))
        else:
            arch = arch.replace(u"\n## 10. 备份策略", u"\n" + VERIFY + u"\n## 10. 备份策略", 1)
    write(arch_p, arch)

    tex_p = os.path.join(DOCS, u"贴图清单.md")
    tex = read(tex_p)
    if u"## ZF84（0.11）" not in tex:
        write(tex_p, tex.rstrip(u"\n") + u"\n" + TEX_SECTION)
        print(u"贴图清单：追加 ZF84 一节")

    print(u"文档改完，失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
