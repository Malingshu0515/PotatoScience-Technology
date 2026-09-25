# -*- coding: utf-8 -*-
"""_zf70_lang.py —— 给 4 个语言文件加 6 个进度键（3 个进度 × 标题/描述）

用户只给了中文原文（新的开始！/ 简洁的电力来源 方便且够用 / 更强劲的电源 /
电生磁 磁生电...... 别问我为什么导线可以传递动力 / 入门清洁能源 / 量变产生质变），
en/ja/ru 是**我译的**（汇报里会标出来）。

⚠ 两个 App 风格的坑都在这里防住：
  · 插入点写死"最后一个 key 行 + `}`"，不允许模糊匹配（§4.36）；
  · 改完**回读并逐键比对**：原有 204 个键的值必须一个都没变（只许 +6）。
"""
import io
import json
import os
import sys

PROJ = r"E:\PotatoST"
LANG = os.path.join(PROJ, r"src\main\resources\assets\potato_s_t\lang")
EXPECT_OLD = 204
EXPECT_NEW = 210

# 键 -> 各语言的值（zh 是用户原文）
VALUES = {
    "advancements.potato_s_t.new_beginning.title": {
        "zh_cn": u"新的开始！",
        "en_us": u"A New Beginning!",
        "ja_jp": u"新たな始まり！",
        "ru_ru": u"Новое начало!",
    },
    "advancements.potato_s_t.new_beginning.description": {
        "zh_cn": u"简洁的电力来源 方便且够用",
        "en_us": u"A simple power source - handy and sufficient",
        "ja_jp": u"簡素な電力源 便利で十分",
        "ru_ru": u"Простой источник энергии - удобный и достаточный",
    },
    "advancements.potato_s_t.stronger_power.title": {
        "zh_cn": u"更强劲的电源",
        "en_us": u"A Stronger Power Source",
        "ja_jp": u"より強力な電源",
        "ru_ru": u"Более мощный источник питания",
    },
    "advancements.potato_s_t.stronger_power.description": {
        "zh_cn": u"电生磁 磁生电...... 别问我为什么导线可以传递动力",
        "en_us": u"Electricity makes magnetism, magnetism makes electricity... don't ask me why wires can carry power",
        "ja_jp": u"電気が磁気を生み 磁気が電気を生む……なぜ導線が動力を伝えられるのかは聞かないで",
        "ru_ru": u"Электричество рождает магнетизм, магнетизм рождает электричество… не спрашивай, почему провода передают энергию",
    },
    "advancements.potato_s_t.clean_energy.title": {
        "zh_cn": u"入门清洁能源",
        "en_us": u"Clean Energy 101",
        "ja_jp": u"クリーンエネルギー入門",
        "ru_ru": u"Введение в чистую энергию",
    },
    "advancements.potato_s_t.clean_energy.description": {
        "zh_cn": u"量变产生质变",
        "en_us": u"Quantitative change brings qualitative change",
        "ja_jp": u"量が質に転じる",
        "ru_ru": u"Количество переходит в качество",
    },
}

ORDER = [
    "advancements.potato_s_t.new_beginning.title",
    "advancements.potato_s_t.new_beginning.description",
    "advancements.potato_s_t.stronger_power.title",
    "advancements.potato_s_t.stronger_power.description",
    "advancements.potato_s_t.clean_energy.title",
    "advancements.potato_s_t.clean_energy.description",
]

fails = []


def main():
    for lang in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        path = os.path.join(LANG, lang + ".json")
        raw = io.open(path, "rb").read()
        text = raw.decode("utf-8")
        if raw[:3] == b"\xef\xbb\xbf":
            fails.append(u"%s 带 BOM" % lang)
        before = json.loads(text)
        if len(before) != EXPECT_OLD:
            fails.append(u"%s 改前 %d 键（预期 %d）—— 期望先怀疑" % (lang, len(before), EXPECT_OLD))
            continue

        trailing_nl = text.endswith("\n")
        lines = text.split("\n")
        # 找最后一个单独成行的 '}'
        idx = None
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == "}":
                idx = i
                break
        if idx is None or idx == 0:
            fails.append(u"%s 找不到结尾的 }" % lang)
            continue
        last_key = lines[idx - 1]
        if not last_key.rstrip().endswith('"'):
            fails.append(u"%s 最后一个键行不是以引号结尾：%r" % (lang, last_key))
            continue
        lines[idx - 1] = last_key + ","

        new_lines = []
        for i, k in enumerate(ORDER):
            comma = "," if i < len(ORDER) - 1 else ""
            new_lines.append(u'    "%s":  "%s"%s' % (k, VALUES[k][lang], comma))
        out_lines = lines[:idx] + new_lines + lines[idx:]
        out = "\n".join(out_lines)
        if not trailing_nl:
            out = out.rstrip("\n")

        after = json.loads(out)
        if len(after) != EXPECT_NEW:
            fails.append(u"%s 改后 %d 键（预期 %d）" % (lang, len(after), EXPECT_NEW))
            continue
        changed = [k for k in before if after.get(k) != before[k]]
        if changed:
            fails.append(u"%s 原有键被改动了: %s" % (lang, changed[:5]))
            continue
        bad = [k for k in ORDER if after.get(k) != VALUES[k][lang]]
        if bad:
            fails.append(u"%s 新键没写对: %s" % (lang, bad))
            continue

        io.open(path, "w", encoding="utf-8", newline="\n").write(out)
        print(u"  [OK] %-10s %d -> %d 键（原有 %d 个键的值逐键比对一致）" % (lang, len(before), len(after), len(before)))

    print(u"\n写入 4 个语言文件，每个 +%d 键（共 +%d 键）" % (len(ORDER), len(ORDER) * 4))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
