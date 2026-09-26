# -*- coding: utf-8 -*-
r"""_rzh_probe_lzh_meta.py —— 取证：1.21.1 客户端认不认 `lzh` 这个语言代码。

`lzh.json` 光放进去还不够 —— 原版有一个"已知语言"元数据表（代码 -> 显示名、
地区、双向文字），游戏据此决定语言列表里出不出现这一项。如果 `lzh` 不在表里，
语言菜单就不会显示「文言文」，玩家也就选不到。

所以这个脚本去翻 client.jar 里每一处出现 `lzh` 的常量池，把**同一个小段里的
可读字符串**打出来 —— 如果能看到 "Literary Chinese" 之类的显示名，就说明
元数据里有它。（class 是混淆过的，不指望按类名找。）

用法：`python build/zftools/_rzh_probe_lzh_meta.py`  → `_rzh_probe_lzh_meta.txt`
"""
from __future__ import print_function
import io
import os
import re
import sys
import zipfile

JAR = r"E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), u"_rzh_probe_lzh_meta.txt")


def main():
    if not os.path.exists(JAR):
        print(u"找不到 %s" % JAR)
        return 1
    z = zipfile.ZipFile(JAR)
    lines = []
    hits = 0

    # 语言元数据表通常和这一堆代码常量待在同一个 class 的常量池里。
    # 拿这些"邻居"当路标：zh_cn / en_ud / lol_us / tok 都是原版真实存在的语言代码。
    marks = [b"zh_cn", b"lol_us", b"en_ud", b"tok", b"isv", b"got_de"]

    for name in z.namelist():
        if not name.endswith(u".class"):
            continue
        raw = z.read(name)
        if b"lzh" not in raw:
            continue
        hits += 1
        lines.append(u"")
        lines.append(u"########## %s（%d 字节）" % (name, len(raw)))
        # 常量池里的 ASCII 串
        strs = [m.group(0).decode(u"ascii") for m in re.finditer(rb"[\x20-\x7e]{2,48}", raw)]
        # 打印 lzh 附近的窗口
        for i, s in enumerate(strs):
            if s == u"lzh" or u"lzh" in s:
                lo, hi = max(0, i - 12), min(len(strs), i + 13)
                lines.append(u"   ... %s ..." % u" | ".join(strs[lo:hi]))
        # 有没有语言元数据的路标
        near = [m.decode(u"ascii") for m in marks if m in raw]
        lines.append(u"   同段路标: %s" % (u", ".join(near) if near else u"（无）"))
        # 有没有 "Literary Chinese" 之类
        for m in re.finditer(rb"(Literary|Classical|Chinese|Wenyan)[\x20-\x7e]{0,30}", raw):
            lines.append(u"   显示名候选: %s" % m.group(0).decode(u"ascii"))

    lines.insert(0, u"client.jar 里含 'lzh' 的 class：%d 个" % hits)

    # 官方资源索引里 lzh 的显示名在 minecraft/lang 之外还可能在
    # assets/minecraft/lang/ 的 meta 里 —— 顺手把 en_us 的 lzh 显示名找出来
    IDX = r"E:\gradle-home\caches\minecraft\assets\indexes\asset-index.json"
    OBJ = r"E:\gradle-home\caches\minecraft\assets\objects"
    if os.path.exists(IDX):
        import json
        with io.open(IDX, encoding=u"utf-8") as f:
            idx = json.load(f)[u"objects"]
        ent = idx.get(u"minecraft/lang/lzh.json")
        if ent:
            p = os.path.join(OBJ, ent[u"hash"][:2], ent[u"hash"])
            with io.open(p, encoding=u"utf-8") as f:
                lang = json.load(f)
            for k in (u"language.name", u"language.region", u"language.code",
                      u"block.minecraft.iron_ore", u"item.minecraft.raw_iron",
                      u"item.minecraft.iron_ingot", u"block.minecraft.deepslate_iron_ore",
                      u"item.minecraft.diamond_sword", u"item.minecraft.iron_helmet"):
                lines.append(u"原版 lzh.json: %-34s %s" % (k, lang.get(k, u"<没有>")))

    z.close()
    with io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n") as f:
        f.write(u"\n".join(lines) + u"\n")
    print(u"wrote %s" % OUT)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
