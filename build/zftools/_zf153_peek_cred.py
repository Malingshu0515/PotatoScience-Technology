# -*- coding: utf-8 -*-
u"""看一眼 _来源凭据.json 的条目形状（只读）。"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = r"E:\PotatoST\build\用户素材\_来源凭据.json"
raw = io.open(P, encoding="utf-8").read()
d = json.loads(raw)
print(u"条目数 = %d；顶层键里最后 6 个 = %s" % (len(d), sorted(d)[-6:]))
for k in (u"星璨钢剑.png", u"星璨铲子.png"):
    if k in d:
        print(u"\n---- %s ----" % k)
        print(json.dumps(d[k], ensure_ascii=False, indent=2))
print(u"\n---- 文件头 60 字符 ----")
print(repr(raw[:60]))
print(u"---- 文件尾 120 字符 ----")
print(repr(raw[-120:]))
print(u"---- 顶层条目的键签名（去重）----")
sigs = {}
for k, v in d.items():
    sigs.setdefault(tuple(sorted(v.keys())), []).append(k)
for sig, keys in sigs.items():
    print(u"  %s  ×%d   例：%s" % (u", ".join(sig), len(keys), keys[:3]))
print(u"\n目标文件在不在：", os.path.exists(os.path.join(os.path.dirname(P), u"振金剑_001.png")))
