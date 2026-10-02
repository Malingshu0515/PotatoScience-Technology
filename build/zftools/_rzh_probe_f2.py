import io, json, os, sys
sys.path.insert(0, r"E:\PotatoST\build\zftools")
import _rzh_zverify as V
L = []
for loc, key, needle in V.GONE:
    v = V.load(loc)[2].get(key)
    if v is not None and needle in v:
        i = v.find(needle)
        L.append("MISS  loc=%s key=%s" % (loc, key))
        L.append("   needle=%r  (len=%d)" % (needle, len(needle)))
        L.append("   ctx=%r" % v[max(0,i-30):i+len(needle)+30])
L.append("total misses=%d" % (sum(1 for loc,k,n in V.GONE if n in (V.load(loc)[2].get(k) or ""))))
io.open(r"E:\PotatoST\build\zftools\_rzh_zfail2.txt","w",encoding="utf-8",newline="\n").write("\n".join(L))
print("ok")
