import io, json, os, re, sys
sys.path.insert(0, r"E:\PotatoST\build\zftools")
import _rzh_fix_batch as fb
for loc, old, new, need in fb.SUBSTITUTIONS:
    d = json.load(io.open(os.path.join(fb.LANGDIR, loc + ".json"), encoding="utf-8"))
    hits = sum(v.count(old) for v in d.values())
    if hits and hits < need:
        print("SHORT", loc, "hits=%d need=%d" % (hits, need), repr(old))
    elif hits == 0:
        print("gone ", loc, "need=%d" % need, repr(old[:40]))
