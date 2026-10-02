# -*- coding: utf-8 -*-
import io, json
p = r"E:\PotatoST\build\zftools\_rzh_lzh_in2.json"
a = json.load(io.open(p, encoding="utf-8"))
out = io.open(r"E:\PotatoST\build\zftools\_rzh_t2_dump.txt", "w", encoding="utf-8", newline="\n")
for i, k in enumerate(a):
    v = a[k]
    out.write(u"[%d] %s  (nl=%d)\n" % (i, k, v.count("\n")))
    out.write(u"    " + v.replace(u"\n", u"\\n\u21b5\n    ") + u"\n")
out.close()
print("done")
