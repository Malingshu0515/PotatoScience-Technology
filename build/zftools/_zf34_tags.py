# -*- coding: utf-8 -*-
"""ZF34 第 ④ 步（修正版）：往两个原版标签里加 6 个值。

⚠ 上一版 `_zf34_apply.py` 在这里栽了，原因值得记：
   我写的 `insert_lines` 是"从文件末尾往前找第一个 strip() 为 `]` 或 `}` 的行"。
   对 lang 文件（纯对象，收尾是 `}`）没问题；但标签文件是 `{ "values": [ ... ] }`，
   **末尾往前第一个收尾行是 `}`，不是 `]`** —— 于是逗号被加到了 `]` 后面，
   插进去的 6 个值落到了数组外面，`json.loads` 当场报
   `Expecting ':' delimiter: line 31 column 36`。
   （好在 `insert_lines` 是**先校验后写盘**，所以文件没被写坏。）

   教训：同一个"插行"函数用在两种结构的文件上时，必须把**收尾字符**当参数传进去。
"""
import io
import json
import os
import sys

DATA = r"E:\PotatoST\src\main\resources\data"
IDS = ["common_metal_block", "advanced_metal_block", "stable_metal_block",
       "heat_resistant_metal_block", "heater", "heat_sink"]

fail = []


def check(ok, msg):
    print(("  [OK]   " if ok else "  [FAIL] ") + msg)
    if not ok:
        fail.append(msg)


def insert_before_closer(path, new_lines, closer, expect_delta, what):
    with io.open(path, "r", encoding="utf-8") as f:
        text = f.read()
    before = json.loads(text)
    lines = text.split("\n")

    close_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == closer:      # ← 关键：按**指定的**收尾字符找
            close_idx = i
            break
    if close_idx is None:
        raise SystemExit("找不到收尾符号 %r: %s" % (closer, path))

    j = close_idx - 1
    while lines[j].strip() == "":
        j -= 1
    if not lines[j].rstrip().endswith(","):
        lines[j] = lines[j].rstrip() + ","

    lines[close_idx:close_idx] = new_lines
    out = "\n".join(lines)

    after = json.loads(out)                 # 先校验，通过了才写
    n0 = len(before["values"])
    n1 = len(after["values"])
    check(n1 - n0 == expect_delta, "%s 条目 %d → %d（应 +%d）" % (what, n0, n1, expect_delta))

    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    return after


print("=" * 72)
print("④ 原版标签：mineable/pickaxe + needs_stone_tool")
print("   （不加这两条的话，requiresCorrectToolForDrops 的方块空手挖下去什么都不掉）")
print("=" * 72)
for rel, label in ((r"minecraft\tags\block\mineable\pickaxe.json", "mineable/pickaxe"),
                   (r"minecraft\tags\block\needs_stone_tool.json", "needs_stone_tool")):
    path = os.path.join(DATA, rel)
    new_lines = [u'    "potato_s_t:%s"%s' % (bid, "," if k < len(IDS) - 1 else "")
                 for k, bid in enumerate(IDS)]
    with io.open(path, "r", encoding="utf-8") as f:
        orig = json.loads(f.read())["values"]
    after = insert_before_closer(path, new_lines, "]", len(IDS), label)
    vals = after["values"]
    for bid in IDS:
        check("potato_s_t:" + bid in vals, "%s 含 potato_s_t:%s" % (label, bid))
    # 反查：改动前已有的条目一个都不能丢
    lost = [v for v in orig if v not in vals]
    check(not lost, "%s 原有 %d 项全部保留（丢失 %d 项）" % (label, len(orig), len(lost)))
    print("     %s 现在共 %d 项" % (label, len(vals)))

print()
if fail:
    print("有 %d 项失败：" % len(fail))
    for m in fail:
        print("   - " + m)
    sys.exit(1)
print("④ 全部通过。")
