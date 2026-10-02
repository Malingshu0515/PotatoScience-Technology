# -*- coding: utf-8 -*-
import io, json, re
a = json.load(io.open(r"E:\PotatoST\build\zftools\_rzh_lzh_in2.json", encoding="utf-8"))
b = json.load(io.open(r"E:\PotatoST\build\zftools\_rzh_lzh_out2.json", encoding="utf-8"))
print("keys equal:", list(a) == list(b), len(a), len(b))
for k in a:
    pa = re.findall(r"%[sd]|%%", a[k]); pb = re.findall(r"%[sd]|%%", b.get(k, ""))
    if pa != pb:
        print("PLACEHOLDER", k, pa, pb)
    if a[k].count("\\n") != b.get(k, "").count("\\n"):
        print("NEWLINE", k, a[k].count("\\n"), b.get(k, "").count("\\n"))
for tok in ["FE", "mB", "tick", "JEI", "Shift", "Y=", "c:"]:
    na = sum(a[k].count(tok) for k in a); nb = sum(b.get(k, "").count(tok) for k in b)
    if na != nb:
        print("TOKEN", tok, na, nb)
print("done")
