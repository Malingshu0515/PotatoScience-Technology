# -*- coding: utf-8 -*-
u"""_zf78_hashfix.py —— 把文档里的成品哈希改成**最终**那个（本轮的第二次打包）

本轮同版本打了两次：
  ① `9fd7340f…` —— 第一次打包（沥青贴图还是原版那种 **4 位调色板** PNG，被 TextureCheck 拦下）
  ② `2bf27d2c…` —— 把贴图重编码成 8 位 RGBA 之后重打 ⇒ **最终成品**
两次作废：`27787d5e…`（ZF77 的成品）与 `9fd7340f…`（本轮第一次）。
0.10 成品 `84d09345…` 始终原样保留（两个版本并存）。

每条替换都断言**正好命中 1 次**。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = r"E:\PotatoST\docs\开发档案.md"
OLD = "9fd7340f0d776a540e1935b2536c08ea03474c75"
NEW = "2bf27d2cf68a51e2721901af8805c6a8cf1273ed"
fails = []


def patch(old, new, label):
    t = io.open(DOC, encoding="utf-8").read()
    hits = t.count(old)
    if hits != 1:
        fails.append(u"%s：命中 %d 次（必须 1 次）" % (label, hits))
        return
    io.open(DOC, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)


def main():
    patch(
        u"发布：成品 `release\\PotatoST-0.11.jar` = **`%s`**（2,274,783 B / 771 条目），"
        u"上一版 `27787d5e…` **作废**（0.10 成品 `84d09345…` 仍原样保留）" % OLD,
        u"发布：成品 `release\\PotatoST-0.11.jar` = **`%s`**（2,274,796 B / 771 条目）。"
        u"⚠ **本轮同版本打了两次**：第一次 `9fd7340f…` 的沥青贴图还是原版那种 **4 位调色板** PNG"
        u"（TextureCheck 第 6 道门当场拦下）⇒ 解成 8 位 RGBA 重写后**重打一次**；"
        u"两次都作废：`27787d5e…`（ZF77）与 `9fd7340f…`（本轮第一次）。"
        u"0.10 成品 `84d09345…` 仍原样保留" % NEW,
        u"§5 ZF78 行 → 最终哈希 + 两次打包说明")

    patch(
        u"（成品 `release\\PotatoST-0.11.jar` = `%s`，2,274,783 B / 771 条目；"
        u"**同版本重打包 ⇒ 上一版 `27787d5e…` 作废**，0.10 成品 `84d09345…` 仍原样保留）" % OLD,
        u"（成品 `release\\PotatoST-0.11.jar` = `%s`，2,274,796 B / 771 条目；"
        u"**同版本重打包 ⇒ 作废 `27787d5e…`（ZF77）与 `9fd7340f…`（本轮第一次）**，"
        u"0.10 成品 `84d09345…` 仍原样保留）" % NEW,
        u"§9 ZF78 条目 → 最终哈希")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
