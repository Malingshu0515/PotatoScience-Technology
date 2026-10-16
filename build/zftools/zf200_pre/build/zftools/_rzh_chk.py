import io, json, sys
sys.path.insert(0, r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools")
import _rzh_ztrans2 as Z
K = "message.potato_s_t.gravity.charging"
print("table en_us:", repr(Z.T[K]["en_us"]))
d = json.load(io.open(r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang\en_us.json", encoding="utf-8"))
print("disk  en_us:", repr(d[K]))
print("equal? ", Z.T[K]["en_us"] == d[K])
