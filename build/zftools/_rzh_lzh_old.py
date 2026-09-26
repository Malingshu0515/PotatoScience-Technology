# -*- coding: utf-8 -*-
r"""_rzh_lzh_old.py —— 把 lzh 里指定成就的**现况值**导成 Python 转义字面量。

用途：写文言文改动稿时，旧值要逐字准确。**手抄长句 = 再打错一次**（这个坑
本会话踩了不止一次），所以机读出来，直接粘进改动脚本。

输出 `_rzh_lzh_old.txt`（ASCII，\uXXXX 转义 —— 不受控制台 GBK 影响）。
"""
from __future__ import print_function
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LZH = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t",
                   u"lang", u"lzh.json")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), u"_rzh_lzh_old.txt")

IDS = [
    u"acid", u"alloy_smelter", u"capacitor", u"clean_energy", u"combustion",
    u"crushing", u"diesel_generator", u"electrolyzer", u"first_power",
    u"fluid_logistics", u"fuel", u"gas_handling", u"light_alloy",
    u"lithium_battery", u"lithium_battery_plant", u"oil", u"oil_pump",
    u"pressing", u"salt", u"silver_wire", u"stable_block", u"star_chart_tome",
    u"star_steel", u"star_steel_armor", u"star_steel_slash", u"star_steel_tools",
    u"starfall", u"steel", u"stronger_power", u"titanium", u"titanium_armor",
    u"vibranium", u"vibranium_armor", u"wiring", u"distillation",
]


def main():
    d = json.load(io.open(LZH, encoding=u"utf-8"))
    out = []
    for i in IDS:
        k = u"advancements.potato_s_t.%s.description" % i
        out.append(u'    u"%s": %s,' % (i, json.dumps(d[k], ensure_ascii=True)))
    io.open(OUT, u"w", encoding=u"ascii", newline=u"\n").write(u"\n".join(out) + u"\n")
    print(u"wrote %s (%d 条)" % (OUT, len(IDS)))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
