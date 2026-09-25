# -*- coding: utf-8 -*-
"""_zf47_inject.py —— 反证用：把耐热金属块配方的 result.count 从 1 改成 2。

**为什么单独写个文件**：`python -c "...t.replace('\"count\": 1', ...)..."` 在 PowerShell 里
被 here-string 吃掉转义，Python 直接报 SyntaxError —— **注入没发生**，那一轮跑出来的
"17 项全 OK" 是**没注入的结果**（差点被我当成"探针抓不到"）。写成文件就没这问题。
"""
import io
import sys

P = r"E:\PotatoST\src\main\resources\data\potato_s_t\recipe\heat_resistant_metal_block.json"

mode = sys.argv[1] if len(sys.argv) > 1 else "--inject"
text = io.open(P, encoding="utf-8").read()

if mode == "--inject":
    new = text.replace(u'"count": 1', u'"count": 2')
    if new == text:
        raise SystemExit(u"注入失败：文件里没有 '\"count\": 1'")
    io.open(P, "w", encoding="utf-8", newline="\n").write(new)
    print(u"已注入：result.count 1 -> 2")
else:
    print(u"（--restore 请改用 _zf45_recipes.py --write 重新生成）")
