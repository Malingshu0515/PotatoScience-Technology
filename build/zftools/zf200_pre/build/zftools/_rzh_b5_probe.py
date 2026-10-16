# -*- coding: utf-8 -*-
"""Mechanically decide whether the 2 B5-flagged keys really have 'no character to change':
every character must be absent from the simplified->traditional variant table."""
import io
import json
import os
import sys

sys.path.insert(0, r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools")
from _rzh_lzh_sameok import S2T                             # noqa: E402

LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
KEYS = ["potato_s_t.guide.category.materials", "message.potato_s_t.gravity.charging"]

zh = json.load(io.open(os.path.join(LANG, "zh_cn.json"), encoding="utf-8"))
lzh = json.load(io.open(os.path.join(LANG, "lzh.json"), encoding="utf-8"))

out = []
for k in KEYS:
    v = lzh[k]
    hit = sorted(set(c for c in v if c in S2T))
    out.append("%s" % k)
    out.append("   value : %r  (len %d)" % (v, len(v)))
    out.append("   zh==lzh? %s" % (zh[k] == v))
    out.append("   异形字命中: %s" % (u"".join(hit) if hit else u"（无）"))
    out.append("   → 可入白名单: %s" % (not hit))
    out.append("")

# also: how many OTHER keys are currently zh==lzh but NOT whitelisted? (scope check)
import importlib
T = importlib.import_module("_rzh_touched")
whitelist = T.LZH_SAME_OK
extra = []
for k in zh:
    if k in lzh and zh[k] == lzh[k] and k not in whitelist:
        hit = sorted(set(c for c in lzh[k] if c in S2T))
        extra.append((k, lzh[k], hit))
out.append("=== 当前 zh==lzh 但**不在**白名单里的键：%d 条 ===" % len(extra))
for k, v, hit in extra:
    out.append("   %-52s %-28s 异形字:%s" % (k, v[:28], u"".join(hit) or u"无"))
io.open(r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools\_rzh_b5_probe.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("ok")
