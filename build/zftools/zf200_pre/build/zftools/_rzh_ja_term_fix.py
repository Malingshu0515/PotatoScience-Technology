import io, json, os
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
p = os.path.join(LANG, "ja_jp.json")
d = json.load(io.open(p, encoding="utf-8"))
KEYS = ["potato_s_t.configuration.black_hole.one_shot.tooltip",
        "potato_s_t.configuration.gravity_device.capacity_fe.tooltip"]
n = 0
for k in KEYS:
    if "引力装置" in d[k]:
        d[k] = d[k].replace("引力装置", "重力装置")
        n += 1
print("replaced in %d keys" % n)
# 只在两处文本上做，不动文件结构：用精确文本改写
import io as _io
raw = _io.open(p, encoding="utf-8", newline="").read()
for k in KEYS:
    old = None
# 安全做法：整份重写（同样是 UTF-8 + LF），但先核键数
assert len(d) == 689, len(d)
_io.open(p, "w", encoding="utf-8", newline="\n").write(
    json.dumps(d, ensure_ascii=False, indent=2) + "\n")
d2 = json.load(_io.open(p, encoding="utf-8"))
print("keys after =", len(d2))
print("引力装置 left:", sum(1 for v in d2.values() if "引力装置" in v))
print("重力装置 now :", sum(1 for v in d2.values() if "重力装置" in v))
