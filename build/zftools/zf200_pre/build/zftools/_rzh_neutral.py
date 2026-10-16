# 只把 ru 补丁交给合并门：临时把 en 补丁换成"与盘上一致"的空补丁，避免再动 en
import io, json, os, sys
HERE = r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools"
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
en = json.load(io.open(os.path.join(LANG, "en_us.json"), encoding="utf-8"))
sys.path.insert(0, HERE)
import _rzh_guide_zh as GZ
keys = sorted(GZ.NEW) + sorted(k for k in en if k.startswith("potato_s_t.configuration")) + [
    "tooltip.potato_s_t.cola.1","tooltip.potato_s_t.cola.2",
    "tooltip.potato_s_t.gravity_device.one_shot.on","tooltip.potato_s_t.gravity_device.one_shot.off"]
io.open(os.path.join(HERE, "_rzh_patch_A_en_us.json"), "w", encoding="utf-8", newline="\n").write(
    json.dumps({k: en[k] for k in keys}, ensure_ascii=False, indent=2) + "\n")
print("en patch neutralised (%d keys = 盘上现值)" % len(keys))
