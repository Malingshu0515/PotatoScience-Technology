# -*- coding: utf-8 -*-
u"""_zf103_show.py —— 只读：把合金炉介绍图那几行从四份语言里打出来（临时文件）"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
KEY = u"tooltip.potato_s_t.alloy_smelter"
for f in (u"zh_cn.json", u"en_us.json"):
    text = json.loads(io.open(os.path.join(LANG, f), encoding="utf-8").read())[KEY]
    print(u"=== %s（共 %d 行）===" % (f, len(text.split(u"\n"))))
    for i, l in enumerate(text.split(u"\n")):
        mark = u"  <<<" if i in (5, 12, 13, 14) else u""
        print(u"%2d| %s%s" % (i + 1, l, mark))
