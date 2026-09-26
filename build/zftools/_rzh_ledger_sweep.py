# -*- coding: utf-8 -*-
r"""_rzh_ledger_sweep.py —— 全库"流水账"体检（只读，不改任何东西）。

口径（前几轮和用户一起定下来的那一条）：
  **流水账 = 玩家不需要在游戏里读第二遍的东西**
    · JEI 里能查到的配方表（材料清单 + 数量 + 耗时 + FE/t）
    · 同一句话里出现两遍的数值
    · 只在 tooltip 里出现一次、读者也记不住的规格（缓冲容量、罐容、每 tick 精确值）

所以这个脚本不判"好不好看"，只**把候选挑出来**给人过目。它扫三类信号：

  S1 配方味：一行里出现 ≥3 个「数字+单位」或「A + B + C → D」这种箭头式配方
  S2 重复味：同一段文本里同一个数字出现 ≥2 次
  S3 超长行：单行超过阈值（成就说明 >90 字、tooltip 行 >60 字）

输出 `_rzh_ledger_sweep.txt`。
用法：`python build/zftools/_rzh_ledger_sweep.py`
"""
from __future__ import print_function
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), u"_rzh_ledger_sweep.txt")

NUM = re.compile(u"\\d+(?:\\.\\d+)?")
UNIT = re.compile(u"\\d+(?:\\.\\d+)?\\s*(?:mB|FE|FE/t|FE/т|mB/t|mB/s|mB/с|秒|s\\b|с\\b|tick|塊|块|個|个|格|層|层)")
ARROW = re.compile(u"[^。\\n]{0,30}[→⇒>][^。\\n]{0,30}")

# 只扫玩家真的会读的类别；键名类（item./block.）跳过
SKIP_PREFIX = (u"item.", u"block.", u"biome.", u"jukebox_song.", u"sky.", u"itemGroup.",
               u"fluid.", u"fluid_type.", u"mode.")


def main():
    with io.open(os.path.join(LANGDIR, u"zh_cn.json"), encoding=u"utf-8") as f:
        zh = json.load(f)

    s1, s2, s3 = [], [], []
    for k in sorted(zh):
        if k.startswith(SKIP_PREFIX):
            continue
        v = zh[k]
        for line in v.split(u"\n"):
            n_units = len(UNIT.findall(line))
            if n_units >= 3:
                s1.append((k, n_units, line))
            nums = NUM.findall(line)
            rep = sorted(set(n for n in nums if nums.count(n) >= 2))
            if len(line) >= 12 and rep:
                s2.append((k, u",".join(rep), line))
            limit = 90 if k.startswith(u"advancements.") else 60
            if len(line) > limit:
                s3.append((k, len(line), line))

    L = []
    L.append(u"== S1 配方味（一行里 ≥3 个「数字+单位」）：%d 行 ==" % len(s1))
    for k, n, line in s1:
        L.append(u"  [%d] %-46s %s" % (n, k, line[:96]))
    L.append(u"")
    L.append(u"== S2 重复味（同一行里同一个数字出现 ≥2 次）：%d 行 ==" % len(s2))
    for k, rep, line in s2:
        L.append(u"  [%s] %-46s %s" % (rep, k, line[:96]))
    L.append(u"")
    L.append(u"== S3 超长行（成就 >90 字 / 其它 >60 字）：%d 行 ==" % len(s3))
    for k, n, line in s3:
        L.append(u"  [%d] %-46s %s" % (n, k, line[:96]))

    # ---- S4：说明里重复了标题本身 ----
    # 这是"流水账"最典型的一种：标题已经说了"三元聚合物锂电池"，
    # 说明开头又写一遍。玩家读了两遍同一个词，信息量为零。
    L.append(u"")
    s4 = []
    for k in sorted(zh):
        if not k.startswith(u"advancements.") or not k.endswith(u".title"):
            continue
        t = zh[k]
        dk = k[:-len(u".title")] + u".description"
        d = zh.get(dk, u"")
        if len(t) >= 2 and t in d:
            s4.append((k, t, d))
    L.append(u"== S4 说明里重复了标题（标题 %d 条）==" % len(s4))
    for k, t, d in s4:
        L.append(u"  %-46s 标题「%s」" % (k.split(u".")[-2], t))
        L.append(u"        说明 %s" % d[:96])

    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
    print(u"wrote %s  (S1 %d / S2 %d / S3 %d / S4 %d)"
          % (OUT, len(s1), len(s2), len(s3), len(s4)))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
