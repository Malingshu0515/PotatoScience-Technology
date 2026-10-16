# -*- coding: utf-8 -*-
"""Check that the shared editing entries still expose what my translation pass needs."""
import io
import re

F = r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools\_rzh_fix_batch.py"
L = r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools\_rzh_lzh_set.py"

t = io.open(F, encoding="utf-8").read()
out = []
for name in ("EDITS", "SUBSTITUTIONS", "REGEX_SUBST", "FORBIDDEN_AFTER"):
    out.append("has %-16s : %s" % (name, bool(re.search(r"(?m)^%s\s*=" % name, t))))
out.append("has main()        : %s" % ("def main(" in t))
out.append("LANGDIR defined   : %s" % ("LANGDIR" in t))
out.append("EDITS entries     : %d" % len(re.findall(r'(?m)^\s{4}\(u"', t.split("EDITS = [")[1].split("]")[0])))

t2 = io.open(L, encoding="utf-8").read()
out.append("")
out.append("lzh_set apply()   : %s" % ("def apply(" in t2))
out.append("lzh_set LZH path  : %s" % ("lzh.json" in t2))

io.open(r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools\_rzh_iface.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("ok")
