#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""证明 ZF165 对两份文档的改动是**纯插入**：原文件每一行都还在、顺序不变、格式口径没变。

跑法：python build/zftools/_zf165_doc_check.py
基准：build/tmp/zf165/*.before-zf165（改前整份留底）
"""

import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PAIRS = [
    (r"E:\PotatoST\docs\开发档案.md",
     r"E:\PotatoST\build\tmp\zf165\开发档案.md.before-zf165",
     [("§5 的 ZF165 行", "| ZF165 |"),
      ("§4.173", "### 4.173 【兼容雷】"),
      ("§4.174", "### 4.174 【数据雷】"),
      ("§9 的 ZF165 待实测段", "### ZF165（0.13）")]),
    (r"E:\PotatoST\docs\多会话协作交接.md",
     r"E:\PotatoST\build\tmp\zf165\多会话协作交接.md.before-zf165",
     [("§5.3.3", "### 5.3.3 ZF165"),
      ("§6 第 37 条", "37. **ZF165 的账"),
      ("§1 活体数字行", "| ZF165 新增")]),
]

fails = []
oks = []


def ok(label):
    oks.append(label)


def bad(label, detail=""):
    fails.append(label + ("  —— " + detail if detail else ""))


for after_path, before_path, checks in PAIRS:
    name = os.path.basename(after_path)
    if not os.path.exists(before_path):
        bad("%s 没有改前留底" % name, before_path)
        continue
    before = io.open(before_path, "r", encoding="utf-8", newline="").read()
    after = io.open(after_path, "r", encoding="utf-8", newline="").read()
    b = before.split("\n")
    a = after.split("\n")

    # ① 改前每一行按原顺序仍是改后的子序列
    k = 0
    for line in a:
        if k < len(b) and line == b[k]:
            k += 1
    if k != len(b):
        bad("%s：改前 %d 行里有 %d 行没能按顺序对上" % (name, len(b), len(b) - k),
            "第一处对不上：改前第 %d 行 = %r" % (k + 1, b[k] if k < len(b) else None))
    else:
        ok("%s：改前 %d 行全部按原顺序保留（纯插入）" % (name, len(b)))

    # ② 行数只增不减
    if len(a) < len(b):
        bad("%s 行数变少：%d -> %d" % (name, len(b), len(a)))
    else:
        ok("%s：行数 %d -> %d（+%d）" % (name, len(b), len(a), len(a) - len(b)))

    # ③ heading 数不许减少
    for mark in ("## ", "### "):
        hb = sum(1 for l in b if l.startswith(mark))
        ha = sum(1 for l in a if l.startswith(mark))
        if ha < hb:
            bad("%s 的 `%s` 标题变少：%d -> %d" % (name, mark.strip(), hb, ha))
        else:
            ok("%s：`%s` 标题 %d -> %d" % (name, mark.strip(), hb, ha))

    # ④ 新增内容在位且恰好一次
    for label, needle in checks:
        n = after.count(needle)
        if n == 1:
            ok("%s：新增内容在位且唯一 —— %s" % (name, label))
        else:
            bad("%s：%s 出现 %d 次（必须恰好 1 次）" % (name, label, n))

    # ⑤ 格式：纯 LF、无 BOM
    raw = open(after_path, "rb").read()
    if raw[:3] == b"\xef\xbb\xbf":
        bad("%s 有 BOM" % name)
    elif b"\r\n" in raw:
        bad("%s 是 CRLF" % name)
    else:
        ok("%s：纯 LF、无 BOM" % name)

print("doc check: passed=%d failed=%d" % (len(oks), len(fails)))
for f in fails:
    print("  [FAIL] " + f)
sys.exit(1 if fails else 0)
