# -*- coding: utf-8 -*-
r"""_rzh_probe_locales.py —— 从原版资源取证：1.21.1 到底支持哪些语言。

要回答的问题（文言文语言包能不能被游戏直接选到）：
  1. client.jar 里 assets/minecraft/lang/ 有几个语言文件
  2. launcher 的资源索引 assets/indexes/asset-index.json 里列了哪些
     minecraft/lang/<locale>.json —— 这一份才是权威的"支持语言"清单
     （游戏里每个语言都对应一个真实存在的 lang 文件）
  3. 有没有文言文候选：lzh（ISO 639-3 文言文）或 zh_classical

⚠ 只读，不改任何东西。
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


REPORT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      u"_rzh_probe_locales.txt")
_BUF = []


def out(s):
    _BUF.append(s)


def main():
    # ⚠ 教训：PowerShell 的 `python x.py > y.txt` **不管 python 怎么设 stdout**，
    #   落盘都是 UTF-16LE + BOM，read 工具直接当二进制拒读。
    #   ⇒ 结论自己写文件，绝不依赖 shell 重定向。
    _main()
    with io.open(REPORT, u"w", encoding=u"utf-8", newline=u"\n") as f:
        f.write(u"\n".join(_BUF) + u"\n")
    sys.stdout.write(u"wrote %s (%d bytes)\n" % (REPORT, os.path.getsize(REPORT)))


def _main():

    out(u"=== 索引: %s ===" % INDEX)
    with io.open(INDEX, encoding=u"utf-8") as f:
        idx = json.load(f)
    objs = idx.get(u"objects", {})
    out(u"索引共 %d 个对象" % len(objs))

    langs = {}
    for k, v in objs.items():
        if k.startswith(u"minecraft/lang/") and k.endswith(u".json"):
            langs[k[len(u"minecraft/lang/"):-len(u".json")]] = v
    out(u"\n=== 索引里的语言文件: %d 个 ===" % len(langs))
    for loc in sorted(langs):
        h = langs[loc][u"hash"]
        p = os.path.join(OBJ, h[:2], h)
        out(u"   %-16s %s  (%s)" % (loc, u"在盘" if os.path.exists(p) else u"缺失", h[:12]))

    out(u"\n=== 文言文候选（lzh / classical / wenyan / ancient）===")
    hit = [l for l in sorted(langs) if re.search(u"lzh|classical|wenyan|ancient", l, re.I)]
    out(u"   " + (u", ".join(hit) if hit else u"（无）"))

    out(u"\n=== client.jar 里 assets/minecraft/lang/ ===")
    if os.path.exists(JAR):
        z = zipfile.ZipFile(JAR)
        inJar = sorted(n for n in z.namelist() if n.startswith(u"assets/minecraft/lang/"))
        out(u"   %d 个: %s" % (len(inJar), u", ".join(inJar)))
        cls = [n for n in z.namelist() if u"LanguageManager" in n or u"/language/" in n]
        out(u"   language 相关类: %s" % (u", ".join(cls) if cls else u"（无，混淆过）"))
        z.close()
    else:
        out(u"   找不到 %s" % JAR)

    out(u"\n=== 结论 ===")
    out(u"   索引里有 lzh/文言文: %s" % (u"有" if hit else u"没有"))
    out(u"   1.21.1 支持的完整语言数: %d" % len(langs))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
