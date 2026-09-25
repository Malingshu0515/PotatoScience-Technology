# -*- coding: utf-8 -*-
"""打印 lang 里那一行的**原始字节**，好写出精确的锚点。"""
import io
import os

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
KEY = "tooltip.potato_s_t.hydraulic_press"
for lang in ("zh_cn", "en_us"):
    text = io.open(os.path.join(LANG, lang + ".json"), encoding="utf-8").read()
    for line in text.splitlines():
        if KEY in line:
            print("== %s ==" % lang)
            print("原样      :", repr(line[:120]))
            print("行首字节  :", list(line.encode("utf-8")[:40]))
            print()
