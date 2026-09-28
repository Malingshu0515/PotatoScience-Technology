# -*- coding: utf-8 -*-
u"""看一眼 lang 的键序与 lzh 的文体（只读，ZF153 加键前先看清）。"""
import io
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"

for code in (u"zh_cn", u"lzh"):
    p = LANG + u"\\" + code + u".json"
    d = json.loads(io.open(p, encoding="utf-8").read())
    keys = list(d.keys())
    print(u"\n==== %s：%d 键 ====" % (code, len(keys)))
    print(u"键序是否字典序递增：%s" % (keys == sorted(keys)))
    # 找出 star_steel_sword 与 vibranium_ingot 附近的邻居（看新键该插哪）
    for probe in (u"item.potato_s_t.vibranium_ingot", u"tooltip.potato_s_t.star_steel_sword.1",
                  u"item.potato_s_t.star_steel_sword"):
        if probe in keys:
            i = keys.index(probe)
            lo = max(0, i - 2)
            hi = min(len(keys), i + 3)
            print(u"  %s 在第 %d 位；邻居：%s" % (probe, i, keys[lo:hi]))
    print(u"  最后 5 个键：%s" % keys[-5:])
    # 6 个带 sword / vibranium 的写法
    for k in sorted(d):
        if u"star_steel_sword" in k or u"vibranium_sword" in k:
            print(u"    %-52s %s" % (k, d[k]))

# lzh 的文体样本
d = json.loads(io.open(LANG + u"\\lzh.json", encoding="utf-8").read())
print(u"\n==== lzh 文体样本（剑的三行 + 振金套） ====")
for k in (u"tooltip.potato_s_t.star_steel_sword.1", u"tooltip.potato_s_t.star_steel_sword.2",
          u"tooltip.potato_s_t.star_steel_sword.3", u"item.potato_s_t.star_steel_sword",
          u"item.potato_s_t.vibranium_ingot", u"tooltip.potato_s_t.hold_shift"):
    print(u"  %-46s %s" % (k, d.get(k)))
