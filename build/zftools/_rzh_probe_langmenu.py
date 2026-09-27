# -*- coding: utf-8 -*-
r"""_rzh_probe_langmenu.py —— 取证：语言菜单里的"文言"是哪来的。

问题背景：模组加了 `assets/potato_s_t/lang/lzh.json`，玩家切到「文言」后
**本模组仍然显示英文**。可能的原因有两类：

  A. **资源没进 jar**（构建产物老旧）—— 那就与代码无关，重建即可；
  B. **代码不认这个 locale** —— 原版 ClientLanguage/LanguageManager 若有一张
     "已知语言"的硬编码清单，清单里没有的代码即便有 lang 文件也不出现在菜单里，
     或者出现在菜单里但资源管理器不把它当有效语言去查。

这个脚本查 B 类：client.jar 是混淆过的，不指望类名，改为**全量搜索常量池**，
看 `lzh` 与一组"已知语言代码"是否出现在同一个 class 里（那大概率就是那张清单）。

用法：`python build/zftools/_rzh_probe_langmenu.py` → `_rzh_probe_langmenu.txt`
"""
from __future__ import print_function
import io
import json
import os
import re
import sys
import zipfile

JAR = r"E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar"
INDEX = r"E:\gradle-home\caches\minecraft\assets\indexes\asset-index.json"
OBJ = r"E:\gradle-home\caches\minecraft\assets\objects"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), u"_rzh_probe_langmenu.txt")

# 一组"确定存在的冷门语言代码"当路标：它们只可能出现在那张语言清单里
MARKS = [b"lol_us", b"en_ud", b"tok", b"isv", b"got_de", b"qya_aa", b"lzh"]


def main():
    L = []
    if not os.path.exists(JAR):
        L.append(u"找不到 %s" % JAR)
    else:
        z = zipfile.ZipFile(JAR)
        hit_classes = []
        for name in z.namelist():
            if not name.endswith(u".class"):
                continue
            raw = z.read(name)
            if b"lol_us" in raw or b"en_ud" in raw:
                found = [m.decode(u"ascii") for m in MARKS if m in raw]
                hit_classes.append((name, len(raw), found))
        L.append(u"== 含冷门语言代码的 class：%d 个 ==" % len(hit_classes))
        for name, size, found in hit_classes:
            L.append(u"   %-52s %7d  %s" % (name, size, u", ".join(found)))

        # zh_cn / en_us 与 lzh 是否同处一个 class
        L.append(u"")
        L.append(u"== lzh 是否与其它语言代码同处一个 class ==")
        for name, size, found in hit_classes:
            raw = z.read(name)
            L.append(u"   %-52s lzh=%s zh_cn=%s" % (name, b"lzh" in raw, b"zh_cn" in raw))
        z.close()

    # 原版 lzh.json 里的元数据（语言菜单显示名就是读这里，但**能不能出现**另说）
    L.append(u"")
    L.append(u"== 原版 minecraft/lang/lzh.json 的元数据 ==")
    with io.open(INDEX, encoding=u"utf-8") as f:
        idx = json.load(f)[u"objects"]
    ent = idx.get(u"minecraft/lang/lzh.json")
    if ent:
        p = os.path.join(OBJ, ent[u"hash"][:2], ent[u"hash"])
        with io.open(p, encoding=u"utf-8") as f:
            lang = json.load(f)
        for k in (u"language.name", u"language.region", u"language.code"):
            L.append(u"   %-18s %s" % (k, lang.get(k, u"<没有>")))
        L.append(u"   总键数 %d" % len(lang))
    else:
        L.append(u"   索引里没有 lzh.json")

    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
    print(u"wrote %s" % OUT)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
