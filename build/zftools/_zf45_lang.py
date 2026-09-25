# -*- coding: utf-8 -*-
"""_zf45_lang.py —— ZF45 的四语言改动（一次改完，改完由 _zf45_verify.py 独立复核）

四件事：
  ① 新增 4 个物品的键（铁粉 / 磁铁 / 热力金属 / 光伏原件）；
  ② `carbon` 的显示名 碳 → **碳粉**（用户的粉碎配方点名要"碳粉"这个产物）；
  ③ 和 ② 配套：`toner` 的显示名 碳粉 → **墨粉** ——
     否则背包里会出现**两个都叫"碳粉"**的物品（toner 就是打印机墨粉，本来该叫墨粉）；
  ④ 两条已有说明**按锚点插入**新配方行：
     微型粉碎机（碳粉 / 铁粉）、电力高炉（两条双输入）。

**为什么说明行是"插入"而不是"整行重写"**：整行重写等于把 en/ja/ru 三份翻译
重新写一遍 —— 只要我抄漏一句，译文就静默缺内容，而 LangCheck 只查键集、查不出这个。
按锚点插进去，原文一个字都不动。

**只改文本行，不重新序列化 JSON**：`json.dump` 会把整个文件重排格式、还会把
`\\u0026` 这类转义统一掉，diff 会变成整个文件 —— 那样就没人能复核这次到底改了什么。
"""
import io
import json
import os
import sys

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
ALL_CODES = ("zh_cn", "en_us", "ja_jp", "ru_ru")
# 可以只跑某几个语言（`python _zf45_lang.py ru_ru`）—— 本脚本**幂等**：
# 锚点插入前先查"这段文字是不是已经在里面了"，重复跑不会插两遍。
CODES = tuple(sys.argv[1:]) or ALL_CODES

# ---------- ① 新键 ----------
NEW_KEYS = [
    ("item.potato_s_t.iron_powder", {
        "zh_cn": u"铁粉",
        "en_us": u"Iron Dust",
        "ja_jp": u"鉄粉",
        "ru_ru": u"Железная пыль",
    }),
    ("item.potato_s_t.magnet", {
        "zh_cn": u"磁铁",
        "en_us": u"Magnet",
        "ja_jp": u"磁石",
        "ru_ru": u"Магнит",
    }),
    ("item.potato_s_t.thermal_metal", {
        "zh_cn": u"热力金属",
        "en_us": u"Thermal Metal",
        "ja_jp": u"熱金属",
        "ru_ru": u"Термальный металл",
    }),
    ("item.potato_s_t.photovoltaic_component", {
        "zh_cn": u"光伏原件",
        "en_us": u"Photovoltaic Component",
        "ja_jp": u"太陽光発電素子",
        "ru_ru": u"Фотоэлектрический компонент",
    }),
    # JEI 高炉分类的两条说明（0.10 ZF45 给电力高炉补 JEI 时用）
    ("gui.potato_s_t.jei.energy_per_item", {
        "zh_cn": u"每件耗电 %s FE",
        "en_us": u"Costs %s FE per item",
        "ja_jp": u"1 個あたり %s FE",
        "ru_ru": u"Расход %s FE за предмет",
    }),
    ("gui.potato_s_t.jei.ebf_vanilla", {
        "zh_cn": u"原版高炉能烧的东西这里也能烧",
        "en_us": u"Also smelts everything a blast furnace can",
        "ja_jp": u"溶鉱炉で焼けるものもすべて扱えます",
        "ru_ru": u"Также плавит всё, что умеет доменная печь",
    }),
]

# ---------- ②③ 改名（整行替换，就这两条是"重写"） ----------
RENAME = [
    ("item.potato_s_t.carbon", {
        "zh_cn": u"碳粉", "en_us": u"Carbon Dust", "ja_jp": u"炭素粉末", "ru_ru": u"Угольная пыль",
    }),
    ("item.potato_s_t.toner", {
        "zh_cn": u"墨粉", "en_us": u"Toner", "ja_jp": u"トナー", "ru_ru": u"Тонер",
    }),
]

# ---------- ④ 插入（锚点 = 文件里**已经存在**的原句；插入内容拼在锚点前面） ----------
# 微型粉碎机：插在"铜锭 -> 铜线"那一行之前
CRUSHER_ANCHOR = {
    "zh_cn": u"\\n铜锭 -> 4 铜线",
    "en_us": u"\\nCopper Ingot -> 4 Copper Wire",
    "ja_jp": u"\\n銅インゴット -> 銅線 4 本",
    "ru_ru": u"\\nМедный слиток -> 4 медного провода",
}
CRUSHER_INSERT = {
    "zh_cn": u"\\n· 煤炭 / 木炭 -> 1 碳粉（3s，10 FE/t）\\n· 铁锭 -> 1 铁粉（20s，70 FE/t）",
    "en_us": u"\\n· Coal / Charcoal -> 1 Carbon Dust (3s, 10 FE/t)\\n· Iron Ingot -> 1 Iron Dust (20s, 70 FE/t)",
    "ja_jp": u"\\n· 石炭 / 木炭 -> 炭素粉末 1 個（3秒、10 FE/t）\\n· 鉄インゴット -> 鉄粉 1 個（20秒、70 FE/t）",
    "ru_ru": u"\\n· Уголь / древесный уголь -> 1 угольная пыль (3 с, 10 FE/т)\\n· Железный слиток -> 1 железная пыль (20 с, 70 FE/т)",
}

# 电力高炉：插在最后一句之前
BLAST_ANCHOR = {
    "zh_cn": u"\\n除本模组的矿物处理外",
    "en_us": u"\\nIt also handles everything",
    "ja_jp": u"\\n溶鉱炉で焼けるものはすべて",
    "ru_ru": u"\\nОбрабатывает всё",
}
BLAST_INSERT = {
    "zh_cn": u"\\n铁粉 + 碳粉 -> 高碳钢；铁粉 + 沙砾 -> 磁铁（放进任意两个输入槽即自动配对）。",
    "en_us": u"\\nIron Dust + Carbon Dust -> High Carbon Steel; Iron Dust + Gravel -> Magnet (any two input slots pair up automatically).",
    "ja_jp": u"\\n鉄粉 + 炭素粉末 -> 高炭素鋼、鉄粉 + 砂利 -> 磁石（任意の入力 2 スロットで自動的に組みになります）。",
    "ru_ru": u"\\nЖелезная пыль + угольная пыль -> высокоуглеродистая сталь; железная пыль + гравий -> магнит (любые два входных слота).",
}


def replace_line(lines, key, value):
    hit = 0
    for i, l in enumerate(lines):
        if ('"' + key + '"') in l:
            lines[i] = u'    "%s":  "%s"%s' % (key, value, "," if l.rstrip().endswith(",") else "")
            hit += 1
    if hit != 1:
        raise SystemExit(u"%s: 找到 %d 处（应为 1）" % (key, hit))


for code in CODES:
    path = os.path.join(LANG, code + ".json")
    with io.open(path, "r", encoding="utf-8") as f:
        text = f.read()
    before = json.loads(text)

    lines = text.split("\n")
    for key, table in RENAME:
        replace_line(lines, key, table[code])
    text = "\n".join(lines)

    for key, anchor, insert in (
            ("tooltip.potato_s_t.micro_crusher", CRUSHER_ANCHOR[code], CRUSHER_INSERT[code]),
            ("tooltip.potato_s_t.electric_blast_furnace", BLAST_ANCHOR[code], BLAST_INSERT[code])):
        if key not in text:
            raise SystemExit(u"%s: 找不到 %s" % (code, key))
        if insert in text:
            print(u"  [跳过] %s 的新增行已经在里面了" % key)
            continue
        if text.count(anchor) != 1:
            raise SystemExit(u"%s: 锚点 %r 出现 %d 次（应为 1）" % (code, anchor, text.count(anchor)))
        text = text.replace(anchor, insert + anchor, 1)

    # 追加 4 个新键：给最后一个键行补逗号，再插到收尾的 "}" 之前
    lines = text.split("\n")
    last = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith('"'):
            last = i
            break
    if last is None:
        raise SystemExit(u"%s: 找不到最后一个键行" % code)
    # 新键**除最后一个以外**都要带逗号（最后一个后面直接跟收尾的 "}"）
    todo = [(k, t) for k, t in NEW_KEYS if ('"' + k + '"') not in text]
    if todo:
        if not lines[last].rstrip().endswith(","):
            lines[last] = lines[last].rstrip() + ","
        add = [u'    "%s":  "%s",' % (key, table[code]) for key, table in todo]
        add[-1] = add[-1][:-1]
        lines[last + 1:last + 1] = add
    text = "\n".join(lines)

    after = json.loads(text)
    if len(after) != len(before) + len(todo):
        raise SystemExit(u"%s: 键数 %d -> %d（应有 %d 个新键）" % (code, len(before), len(after), len(todo)))
    for key, table in NEW_KEYS:
        if after[key] != table[code]:
            raise SystemExit(u"%s: %s = %r" % (code, key, after[key]))
    if u"10 FE" not in after["tooltip.potato_s_t.micro_crusher"]:
        raise SystemExit(u"%s: 粉碎机说明里没有新配方" % code)
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print(u"[OK] %s: %d -> %d 键" % (code, len(before), len(after)))

print(u"改完，跑 _zf45_verify.py 复核。")
