# -*- coding: utf-8 -*-
u"""看几份门里"键数变量"的**用法**（只读）——决定它是"活体数字断言"还是"历史快照"。"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOOLS = r"E:\PotatoST\build\zftools"

WANT = {
    u"_zf150_verify.py": [u"KEYS4", u"KEYS5"],
    u"_zf148_verify.py": [u"KEYS"],
    u"_zf139_verify.py": [u"KEYS_BEFORE", u"KEYS_AFTER", u"stale"],
    u"_zf117_verify.py": [u"KEY_OLD", u"KEY_NEW"],
    u"_zf119_verify.py": [u"KEY_OLD", u"KEY_NEW"],
    u"_zf145_verify.py": [u"KEYS_ALL", u"N_NEW"],
    u"_zf125_verify.py": [u"tables", u"F1", u"F2", u"E12"],
    u"_zf126_verify.py": [u"583"],
    u"_zf127_verify.py": [u"583"],
    u"_zf128_verify.py": [u"583"],
    u"_zf141_verify.py": [u"KEYS"],
    u"_zf103_verify.py": [u"len(table)"],
    u"_zf71_verify.py": [u"keys"],
    u"_zf109_verify.py": [u"ann"],
    u"_zf112_verify.py": [u"ann", u"EXPECT_KEYS"],
}

for fn, names in sorted(WANT.items()):
    p = os.path.join(TOOLS, fn)
    if not os.path.exists(p):
        print(u"\n== %s 不存在 ==" % fn)
        continue
    print(u"\n================ %s ================" % fn)
    lines = io.open(p, encoding="utf-8").read().split(u"\n")
    for i, line in enumerate(lines, 1):
        if any(re.search(r"\b%s\b" % re.escape(n), line) for n in names):
            print(u"  %5d | %s" % (i, line.rstrip()[:190]))
