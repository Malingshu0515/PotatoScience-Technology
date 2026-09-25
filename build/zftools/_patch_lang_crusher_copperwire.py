# -*- coding: utf-8 -*-
"""ZF33 补丁：把"铜锭 → 4 铜线"那行插进微型粉碎机的 tooltip（四种语言）。

上一版锚点写错了（凭空写了 `| · 粗锂 -> ...`，而实际文本是 `· 粗锂 -> ...` 且不含行首的 `| `），
脚本自己报 SKIP 拦住了 —— 这里改成**按现有行尾定位**：
每种语言里"粗锂那一行"的唯一尾部（如 zh 的 `（12s，20 FE/t）`），
在它后面接上新行，前缀沿用**上一行自己的 `| `**，不靠我再手写一遍格式。

数值（4 个 / 3s / 90 FE/t）从 Java 源码解析，避免文案与代码各写一份。
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
LANG_DIR = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
JAVA = r"E:\PotatoST\src\main\java\com\potatost\mod\MicroCrusherRecipes.java"

src = io.open(JAVA, encoding="utf-8").read()
m = re.search(
    r"Crush copperWire = new Crush\(ModItems\.COPPER_WIRE\.get\(\),\s*(\d+),\s*(\d+),\s*(\d+)\s*\*\s*SEC,\s*(\d+)\)",
    src)
assert m, "在 MicroCrusherRecipes.java 里找不到铜线配方定义"
count_min, count_max, secs, fe = (int(g) for g in m.groups())
assert count_min == count_max, "铜线产物数量是随机的？本脚本按固定数量写文案"
print("从源码解析到：铜锭 → %d 铜线，%ds，%d FE/t" % (count_min, secs, fe))

# 每种语言：粗锂那一行的**唯一尾部**（用来定位） + 新行正文（不含前导 "| "）
CASES = {
    "zh_cn": ("粗锂 -> 2~4 锂矿精粉（12s，20 FE/t）",
              "铜锭 -> %d 铜线（%ds，%d FE/t）" % (count_min, secs, fe)),
    "en_us": ("Raw Lithium -> 2~4 Lithium Concentrate (12s, 20 FE/t)",
              "Copper Ingot -> %d Copper Wire (%ds, %d FE/t)" % (count_min, secs, fe)),
    "ja_jp": ("粗リチウム -> リチウム精鉱 2~4 個（12秒、20 FE/t）",
              "銅インゴット -> 銅線 %d 本（%d 秒、%d FE/t）" % (count_min, secs, fe)),
    "ru_ru": ("Необработанный литий -> 2~4 литиевого концентрата (12 с, 20 FE/t)",
              "Медный слиток -> %d медного провода (%d с, %d FE/т)" % (count_min, secs, fe)),
}

KEY = "tooltip.potato_s_t.micro_crusher"
for lang, (tail, body) in CASES.items():
    path = os.path.join(LANG_DIR, lang + ".json")
    text = io.open(path, encoding="utf-8").read()
    before = json.loads(text)
    value = before[KEY]
    lines = value.split("\n")
    hits = [i for i, l in enumerate(lines) if tail in l]
    assert len(hits) == 1, "%s：尾部锚点命中 %d 行（应为 1）" % (lang, len(hits))
    i = hits[0]
    prev = lines[i]
    prefix = "| " if prev.startswith("| ") else ""
    assert body not in value, "%s 已经有这一行了" % lang
    lines.insert(i + 1, prefix + body)
    new_value = "\n".join(lines)

    # 整行替换（保住行尾逗号 —— ZF30 的教训）
    raw = text.splitlines(keepends=True)
    key_hits = [k for k, l in enumerate(raw) if '"%s"' % KEY in l]
    assert len(key_hits) == 1, "%s 键行命中 %d 行" % (lang, len(key_hits))
    comma = "," if raw[key_hits[0]].rstrip().endswith(",") else ""
    raw[key_hits[0]] = '    "%s":  "%s"%s\n' % (
        KEY, json.dumps(new_value, ensure_ascii=False)[1:-1], comma)
    out = "".join(raw)
    parsed = json.loads(out)
    assert parsed[KEY] == new_value, "%s 落盘不符" % lang
    assert len(parsed) == len(before), "%s 键数变了" % lang
    io.open(path, "w", encoding="utf-8", newline="").write(out)
    print("OK  %-8s 已插入：%s%s" % (lang, prefix, body))
