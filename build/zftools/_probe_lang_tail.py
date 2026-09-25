# -*- coding: utf-8 -*-
import io
import os
import re

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
fname = "zh_cn.json"
text = io.open(os.path.join(LANG, fname), encoding="utf-8").read()
lines = text.splitlines(keepends=True)
last = None
for i, l in enumerate(lines):
    if re.match(r'^\s*"[^"]+"\s*:', l):
        last = i
print("总行数 =", len(lines), " 最后键行 =", last + 1)
print("该行   =", repr(lines[last]))
if last + 1 < len(lines):
    print("下一行 =", repr(lines[last + 1]))
print("---- 末尾 4 行 ----")
for l in lines[-4:]:
    print(repr(l))
