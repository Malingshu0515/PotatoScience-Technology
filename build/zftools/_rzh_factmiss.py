import io, json, os
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
d = json.load(io.open(os.path.join(LANG, "en_us.json"), encoding="utf-8"))
print("=== en_us: Oil Pump / Oil Extractor ===")
for k, v in d.items():
    if "Oil Pump" in v or "Oil Extractor" in v:
        print("  %-52s %s" % (k, v[:90]))
print()
print("=== 中文 guide 里这些事实还在不在 ===")
zh = json.load(io.open(os.path.join(LANG, "zh_cn.json"), encoding="utf-8"))
CHECKS = [("四条配方", "bl_cast_alloy"), ("阳光/太阳", "salt"), ("32x32", "distillation"),
          ("4 点耐久", "starfall_pendant"), ("爆炸伤害减半", "vibranium"), ("抬头", "sky_and_star")]
for needle in ["四条配方", "阳光", "32×32", "耐久 4", "爆炸伤害减半", "抬头", "半速"]:
    hits = [k for k, v in zh.items() if needle in v and k.startswith("potato_s_t.guide")]
    print("  %-10s -> %s" % (needle, hits or "（guide 里没有）"))
