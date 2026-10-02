# -*- coding: utf-8 -*-
r"""_rzh_lzh_check1.py —— 第一份译稿的自检（键集 / 漏译 / 长度 / 字节）。"""
from __future__ import print_function
import io
import json

IN1 = r"E:\PotatoST\build\zftools\_rzh_lzh_in1.json"
OUT1 = r"E:\PotatoST\build\zftools\_rzh_lzh_out1.json"

a = json.load(io.open(IN1, encoding="utf-8"))
b = json.load(io.open(OUT1, encoding="utf-8"))
print("keys equal:", list(a) == list(b), len(a), len(b))
print("untranslated (still identical to zh):", [k for k in a if a[k] == b[k]])
print("too long (>9 chars):", [(k, b[k]) for k in b if len(b[k]) > 9])

raw = io.open(OUT1, "rb").read()
print("BOM:", raw.startswith(b"\xef\xbb\xbf"), "| CR:", b"\r" in raw,
      "| bytes:", len(raw), "| ends with LF:", raw.endswith(b"\n"))
print("longer than input+1:", [(k, b[k], a[k]) for k in a if len(b[k]) > len(a[k]) + 1])
print("len(out) > len(in) count:", sum(1 for k in a if len(b[k]) > len(a[k])))
print("max length:", max(len(v) for v in b.values()))
