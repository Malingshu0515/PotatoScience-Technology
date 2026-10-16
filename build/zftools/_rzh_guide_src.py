# -*- coding: utf-8 -*-
"""Dump the final Chinese source text for (a) the 42 rewritten guide keys and
(b) the 9 keys the user just changed -- the authoritative source for the four
target languages."""
import io
import json
import os
import sys

sys.path.insert(0, r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools")
import _rzh_guide_zh as GZ                                  # noqa: E402

ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")
OUT = os.path.join(ROOT, "build", "zftools", "_rzh_guide_src.txt")

zh = json.load(io.open(os.path.join(LANG, "zh_cn.json"), encoding="utf-8"))

L = []
L.append("# 帕秋莉手册：中文定稿（四语翻译的权威源）")
L.append("# 风格口径：无感叹号、无破折号、无省略号、无解释性括号、无口语备注、")
L.append("#           不用「可以/能够/就能/即可」、句子短、主谓宾清晰、数字与限定词一字不动。")
L.append("#           $(br2) 是帕秋莉换行宏，保留。")
L.append("")
for k in sorted(GZ.NEW):
    L.append("### %s" % k)
    L.append(zh[k])
    L.append("")

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("keys=%d -> %s" % (len(GZ.NEW), OUT))
