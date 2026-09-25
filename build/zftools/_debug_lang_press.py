# -*- coding: utf-8 -*-
"""调试：把 lang 追加结果打印出来（不写盘），定位 JSON 语法错在哪一行。"""
import importlib.util
import io
import json
import os
import re

spec = importlib.util.spec_from_file_location("p", r"E:\PotatoST\build\zftools\_patch_lang_press.py")
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)   # 会抛（因为 json.loads 失败），但我们只要模块级常量
except Exception as exc:
    print("（预期内的失败：%s）" % type(exc).__name__)

NEW_KEYS = mod.NEW_KEYS
LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
path = os.path.join(LANG, "zh_cn.json")
text = io.open(path, encoding="utf-8").read()
lines = text.splitlines(keepends=True)
last = None
for i, line in enumerate(lines):
    if re.match(r'^\s*"[^"]+"\s*:', line):
        last = i
if not lines[last].rstrip().endswith(","):
    lines[last] = lines[last].rstrip("\r\n") + ",\n"
add = ['    "%s":  "%s"\n' % (k, NEW_KEYS[k]["zh_cn"]) for k in NEW_KEYS]
lines[last + 1:last + 1] = add
out = "".join(lines)

print("---- 生成结果的第 140~146 行 ----")
for i, l in enumerate(out.splitlines(), 1):
    if 140 <= i <= 146:
        print("%3d| %s" % (i, l[:150]))
try:
    json.loads(out)
    print("JSON OK")
except Exception as exc:
    print("JSON 失败：%s" % exc)
    # 单独试每一个新键，找出是哪一条写坏了
    for k in NEW_KEYS:
        probe = '{"%s": "%s"}' % (k, NEW_KEYS[k]["zh_cn"])
        try:
            json.loads(probe)
            print("  单独 OK : %s" % k)
        except Exception as e2:
            print("  单独失败: %s -> %s" % (k, e2))
