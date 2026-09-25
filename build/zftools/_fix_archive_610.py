# -*- coding: utf-8 -*-
"""修文档结构：上一轮编辑把 §6.10 的 **⑩** 标题吃掉了（只留下它的正文首句）。

现象：`⑪` 段落后面拖着一句孤零零的
      「用户原话：**「哎呀shift介绍...」**。 / 我写液压机那次塞了一堆...」
      —— 那是 ⑩ 的开头，标题没了，而且位置跑到 ⑪ 后面去了。

做法：把 ⑪ 整段（从它的标题行到「…"红条 + 绿进度"同时出现是正常的。」那一行）**上移**
到那句孤句之前，并给它补回 `**⑩ tooltip 是给玩家看的，别写成"给开发者的解释"**（用户当场点出）：` 标题。
用行号区间搬移，搬完校验"⑩ 在 ⑪ 之前"且两段都在。
"""
import io
import re

PATH = r"E:\PotatoST\docs\开发档案.md"
lines = io.open(PATH, encoding="utf-8").read().splitlines(keepends=True)

# 定位 ⑪ 段落的起止
start = None
for i, l in enumerate(lines):
    if l.startswith("**⑪ 复用 GUI 部件时"):
        start = i
        break
assert start is not None, "找不到 ⑪ 标题行"
end = None
for j in range(start, len(lines)):
    if "红条 + 绿进度" in lines[j]:
        end = j
        break
assert end is not None, "找不到 ⑪ 段落的结尾行"

# ⑪ 后面应当紧跟一个空行
assert lines[end + 1].strip() == "", "⑪ 结尾后面不是空行：%r" % lines[end + 1]

# 定位那句"孤句"（⑩ 的正文首句）
orphan = None
for i, l in enumerate(lines):
    if l.startswith("用户原话：**「哎呀shift介绍"):
        orphan = i
        break
assert orphan is not None, "找不到 ⑩ 的孤句"
assert orphan > end, "孤句应该在 ⑪ 之后（这正是要修的结构问题）"

block = lines[start:end + 2]          # 含结尾空行
rest = lines[:start] + lines[end + 2:]

# 在孤句前插入 ⑩ 的标题 + 搬过来的 ⑪
title = '**⑩ tooltip 是给玩家看的，别写成"给开发者的解释"**（0.10 ZF30 用户当场点出）：\n'
idx = rest.index(lines[orphan])
out = rest[:idx] + [title, "\n"] + block + rest[idx:]

text = "".join(out)
# 校验：⑩ 必须出现在 ⑪ 之前，且两段都在
p10 = text.find("**⑩ tooltip 是给玩家看的")
p11 = text.find("**⑪ 复用 GUI 部件时")
assert p10 != -1 and p11 != -1, "搬移后有两段丢失"
assert p10 < p11, "⑩ 仍然在 ⑪ 之后"
assert text.count("**⑩ tooltip 是给玩家看的") == 1
assert text.count("**⑪ 复用 GUI 部件时") == 1

io.open(PATH, "w", encoding="utf-8", newline="").write(text)
print("OK  §6.10 结构已修：⑩ 标题补回，⑪ 移到它后面")
print("    ⑩ 位置 = 第 %d 行" % (text[:p10].count("\n") + 1))
print("    ⑪ 位置 = 第 %d 行" % (text[:p11].count("\n") + 1))
