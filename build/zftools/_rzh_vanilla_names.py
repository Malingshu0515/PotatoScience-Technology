# -*- coding: utf-8 -*-
r"""_rzh_vanilla_names.py —— 直接从**原版自己的语言文件**里取某个词条的官方译名。

为什么不信 wiki 传闻：ja/ru 审校报告给的"原版写法"彼此矛盾（一个说粗矿是
「粗製鉄」、另一个说是「鉄の原石」）。这类事只有一个权威 —— 盘上那份
`minecraft/lang/ja_jp.json`。本脚本按哈希路径去 assets/objects 里读它。

用法：`python build/zftools/_rzh_vanilla_names.py`
结论写 `_rzh_vanilla_names.txt`（UTF-8，不用 shell 重定向）。
"""
from __future__ import print_function
import io
import json
import os
import sys

IDX = r"E:\gradle-home\caches\minecraft\assets\indexes\asset-index.json"
OBJ = r"E:\gradle-home\caches\minecraft\assets\objects"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), u"_rzh_vanilla_names.txt")

WANT = {
    u"ja_jp": [u"block.minecraft.iron_ore", u"block.minecraft.deepslate_iron_ore",
               u"block.minecraft.gold_ore", u"block.minecraft.deepslate_gold_ore",
               u"block.minecraft.diamond_ore", u"block.minecraft.deepslate_diamond_ore",
               u"item.minecraft.raw_iron", u"item.minecraft.raw_copper", u"item.minecraft.raw_gold",
               u"block.minecraft.raw_iron_block",
               u"item.minecraft.iron_ingot", u"item.minecraft.iron_bucket",
               u"item.minecraft.iron_helmet", u"item.minecraft.netherite_scrap"],
    u"ru_ru": [u"block.minecraft.iron_ore", u"block.minecraft.deepslate_iron_ore",
               u"block.minecraft.gold_ore", u"block.minecraft.deepslate_gold_ore",
               u"block.minecraft.diamond_ore", u"block.minecraft.deepslate_diamond_ore",
               u"item.minecraft.raw_iron", u"item.minecraft.raw_copper", u"item.minecraft.raw_gold",
               u"block.minecraft.raw_iron_block",
               u"item.minecraft.iron_ingot", u"item.minecraft.iron_bucket",
               u"item.minecraft.netherite_scrap"],
    u"zh_cn": [u"block.minecraft.iron_ore", u"block.minecraft.deepslate_iron_ore",
               u"item.minecraft.raw_iron", u"item.minecraft.iron_ingot"],
    u"lzh": [u"block.minecraft.iron_ore", u"block.minecraft.deepslate_iron_ore",
             u"item.minecraft.raw_iron", u"item.minecraft.iron_ingot",
             u"item.minecraft.iron_bucket", u"item.minecraft.iron_helmet"],
}


def obj_path(sha):
    return os.path.join(OBJ, sha[:2], sha)


def main():
    with io.open(IDX, encoding=u"utf-8") as f:
        idx = json.load(f)[u"objects"]
    lines = []
    for loc, keys in sorted(WANT.items()):
        rel = u"minecraft/lang/%s.json" % loc
        ent = idx.get(rel)
        if ent is None:
            lines.append(u"%-6s 索引里没有 %s" % (loc, rel))
            continue
        p = obj_path(ent[u"hash"])
        with io.open(p, encoding=u"utf-8") as f:
            lang = json.load(f)
        lines.append(u"")
        lines.append(u"########## %s（%d 条总键数）" % (loc, len(lang)))
        for k in keys:
            lines.append(u"   %-42s %s" % (k, lang.get(k, u"<没有>")))
    with io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n") as f:
        f.write(u"\n".join(lines) + u"\n")
    print(u"wrote %s" % OUT)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
