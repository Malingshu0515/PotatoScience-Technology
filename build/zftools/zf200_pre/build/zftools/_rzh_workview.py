# -*- coding: utf-8 -*-
"""Emit a per-locale work view: ZH source + current value, grouped, so the three missing
patches can be written by hand against exact source text."""
import io
import json
import os
import sys

sys.path.insert(0, r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools")
import _rzh_guide_zh as GZ                                  # noqa: E402

ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")
zh = json.load(io.open(os.path.join(LANG, "zh_cn.json"), encoding="utf-8"))

guide = sorted(GZ.NEW)
cfg = sorted(k for k in zh if k.startswith("potato_s_t.configuration"))
sync = ["tooltip.potato_s_t.cola.1", "tooltip.potato_s_t.cola.2",
        "tooltip.potato_s_t.gravity_device.one_shot.on",
        "tooltip.potato_s_t.gravity_device.one_shot.off"]

for loc in ("en_us", "ru_ru", "lzh"):
    d = json.load(io.open(os.path.join(LANG, loc + ".json"), encoding="utf-8"))
    L = []
    L.append("# %s 待翻（中文为权威源；下面是当前值）" % loc)
    for title, keys in (("A 手册正文", guide), ("B 配置说明", cfg), ("C 其余", sync)):
        L.append("")
        L.append("======== %s（%d 键）========" % (title, len(keys)))
        for k in keys:
            L.append("")
            L.append("### %s" % k)
            L.append("ZH:  %s" % zh[k])
            L.append("CUR: %s" % d.get(k, "<MISSING>"))
    io.open(os.path.join(ROOT, r"build\zftools\_rzh_work_%s.txt" % loc), "w",
            encoding="utf-8", newline="\n").write("\n".join(L) + "\n")

print("wrote _rzh_work_en_us.txt / _rzh_work_ru_ru.txt / _rzh_work_lzh.txt")
