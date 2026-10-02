import io, json, os, sys
sys.path.insert(0, r"E:\PotatoST\build\zftools")
import _rzh_fix_batch as fb
L = []
for loc, old, new, need in fb.SUBSTITUTIONS:
    d = json.load(io.open(os.path.join(fb.LANGDIR, loc + ".json"), encoding="utf-8"))
    hits = sum(v.count(old) for v in d.values())
    if hits and hits < need:
        L.append("%s hits=%d need=%d" % (loc, hits, need))
        L.append("   OLD: %s" % old)
        L.append("   NEW: %s" % new)
        for k, v in d.items():
            if old in v:
                L.append("   HIT KEY: %s" % k)
        L.append("")
io.open(r"E:\PotatoST\build\zftools\_rzh_subst_short.txt", "w", encoding="utf-8", newline="\n").write("\n".join(L))
print("ok")
