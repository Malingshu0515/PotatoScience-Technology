# -*- coding: utf-8 -*-
r"""_rzh_lzh_glyphcheck1.py —— 用原版取证的字形检查（不靠我手写黑名单）。

做法：把原版 `minecraft/lang/zh_cn.json` 与 `minecraft/lang/lzh.json` 按同键对齐，
取**等长**的键值对做逐字对齐，统计 (简体字 → 繁体字) 的出现次数；
出现次数够多且映射一致的，才算"这个字在繁体里该写成那样"。
然后拿这张**从盘上取证得来**的表去查译稿：译稿里若还留着简体的那个字，就是失手。

用法：`python build/zftools/_rzh_lzh_glyphcheck1.py [要检查的 json，默认 out1]`

⚠ 教训：报告**自己写 UTF-8 文件**，不要靠 print —— Windows 控制台是 GBK，
   正文里有「……」这类字符时 `print` 直接抛 UnicodeEncodeError，
   于是"检出问题"变成了"脚本崩了"，反而看不出问题是什么。
"""
from __future__ import print_function
import io
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
INDEX = r"E:\gradle-home\caches\minecraft\assets\indexes\asset-index.json"
STORE = r"E:\gradle-home\caches\minecraft\assets\objects"
TARGET = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, u"_rzh_lzh_out1.json")
MIN = 5          # 同一对字至少要出现这么多次才认
REPORT = os.path.join(HERE, u"_rzh_lzh_glyphcheck.txt")


def vanilla(name):
    with io.open(INDEX, encoding=u"utf-8") as f:
        idx = json.load(f)
    h = idx[u"objects"][u"minecraft/lang/" + name][u"hash"]
    p = os.path.join(STORE, h[:2], h)
    with io.open(p, encoding=u"utf-8") as f:
        return json.load(f)


def main():
    # 报告自己写 UTF-8 文件（见文件头那条教训）
    lines = []

    def say(s):
        lines.append(s)
        try:
            print(s)
        except UnicodeEncodeError:
            pass

    zh, lzh = vanilla(u"zh_cn.json"), vanilla(u"lzh.json")
    lzh_chars = set(u"".join(v for v in lzh.values() if v))
    pair = defaultdict(lambda: defaultdict(int))
    for k, zv in zh.items():
        lv = lzh.get(k)
        if not lv or len(zv) != len(lv):
            continue
        for a, b in zip(zv, lv):
            if a != b:
                pair[a][b] += 1
    m = {}
    for a, dst in pair.items():
        b, n = max(dst.items(), key=lambda t: t[1])
        # 三条都要：
        #   ① 映射够一致；
        #   ② 这个字**在原版繁体里从不出现**（挡掉 青→黛、流→紋 这类"用词不同"的噪声）；
        #   ③ **源字必须是汉字** —— 只靠 ①② 会把标点也算进来：原版 zh_cn 用「…」、
        #      原版 lzh 用「⋯」，于是「…→⋯」被当成字形对，把我们的「電生磁……
        #      莫問」误报成"残留简体"。标点是**风格**不是字形，不该进这张表。
        #      （这条是被一次真实误报逼出来的，不是预防性加的。）
        if (n >= MIN and n >= 0.9 * sum(dst.values()) and a not in lzh_chars
                and u"\u4e00" <= a <= u"\u9fff"):
            m[a] = b
    say(u"取证得到的简→繁字表：%d 对（每对至少出现 %d 次，且该字原版繁体从不使用）"
        % (len(m), MIN))

    with io.open(TARGET, encoding=u"utf-8") as f:
        doc = json.load(f)
    hits = []
    for k, v in doc.items():
        bad = sorted(set(c for c in v if c in m))
        if bad:
            hits.append((k, u"".join(bad), u"".join(m[c] for c in bad), v))
    say(u"检查 %s：%d 键" % (os.path.basename(TARGET), len(doc)))
    say(u"残留简体字形：%d 条" % len(hits))
    for k, bad, good, v in hits:
        say(u"   %-46s %s 应为 %s   | %s" % (k, bad, good, v[:90]))
    io.open(REPORT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(lines) + u"\n")
    return 1 if hits else 0


if __name__ == u"__main__":
    sys.exit(main())
