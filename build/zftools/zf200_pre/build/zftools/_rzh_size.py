import io, json, os
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
zh = json.load(io.open(os.path.join(LANG, "zh_cn.json"), encoding="utf-8"))
import sys
sys.path.insert(0, r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools")
import _rzh_guide_zh as GZ
guide = sorted(GZ.NEW)
cfg = sorted(k for k in zh if k.startswith("potato_s_t.configuration"))
sync = ["tooltip.potato_s_t.cola.1","tooltip.potato_s_t.cola.2",
        "tooltip.potato_s_t.gravity_device.one_shot.on","tooltip.potato_s_t.gravity_device.one_shot.off"]
allk = guide + cfg + sync
tot = sum(len(zh[k]) for k in allk)
print("keys=%d  zh total chars=%d" % (len(allk), tot))
print("guide=%d cfg=%d sync=%d" % (len(guide), len(cfg), len(sync)))
