# -*- coding: utf-8 -*-
u"""_zf102_lang.py —— ZF102 的四语言新键（每份 3 键）

  · `fluid_type.potato_s_t.hydrochloric_acid`                    —— 新流体名（盐酸）
  · `gui.potato_s_t.acidic_reaction_chamber.recipe.name.3`       —— 第 4 个按钮的名字
  · `gui.potato_s_t.acidic_reaction_chamber.recipe.info.3`       —— 第 4 个按钮的悬停说明

⚠ §4.64：先解析、再写；插进去的每行自带逗号，**最后一行不能有**。
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"

KEYS = {
    "zh_cn": {
        "gui.potato_s_t.acidic_reaction_chamber.recipe.name.3": u"盐酸",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.info.3":
            u"盐酸：每 tick 10 mB 氢气 + 10 mB 氯气 + 5 mB 水 → 5 mB 盐酸",
        "fluid_type.potato_s_t.hydrochloric_acid": u"盐酸",
    },
    "en_us": {
        "gui.potato_s_t.acidic_reaction_chamber.recipe.name.3": u"Hydrochloric",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.info.3":
            u"Hydrochloric acid: 10 mB hydrogen + 10 mB chlorine + 5 mB water -> 5 mB per tick",
        "fluid_type.potato_s_t.hydrochloric_acid": u"Hydrochloric Acid",
    },
    "ja_jp": {
        "gui.potato_s_t.acidic_reaction_chamber.recipe.name.3": u"塩酸",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.info.3":
            u"塩酸：毎 tick 水素 10 mB + 塩素 10 mB + 水 5 mB -> 塩酸 5 mB",
        "fluid_type.potato_s_t.hydrochloric_acid": u"塩酸",
    },
    "ru_ru": {
        "gui.potato_s_t.acidic_reaction_chamber.recipe.name.3": u"Соляная",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.info.3":
            u"Соляная кислота: 10 mB водорода + 10 mB хлора + 5 mB воды -> 5 mB за тик",
        "fluid_type.potato_s_t.hydrochloric_acid": u"Соляная кислота",
    },
}

fails = []


def main():
    if len(KEYS) != 4:
        print(u"!! 语言份数不对：%d" % len(KEYS))
        return 1
    for name, table in sorted(KEYS.items()):
        path = os.path.join(LANG, name + u".json")
        raw = io.open(path, encoding="utf-8").read()
        data = json.loads(raw)
        dup = [k for k in table if k in data]
        if dup:
            fails.append(u"%s：这些键已经有了 %s" % (name, dup))
            continue
        lines = raw.split(u"\n")
        last = max(i for i, l in enumerate(lines) if l.strip().startswith(u'"'))
        if not lines[last].rstrip().endswith(u","):
            lines[last] = lines[last].rstrip() + u","
        block = [u'    %s:  %s,' % (json.dumps(k, ensure_ascii=False),
                                    json.dumps(v, ensure_ascii=False))
                 for k, v in table.items()]
        block[-1] = block[-1][:-1]
        lines[last + 1:last + 1] = block
        text = u"\n".join(lines)
        back = json.loads(text)
        if len(back) != len(data) + len(table):
            fails.append(u"%s：回读键数 %d ≠ %d" % (name, len(back), len(data) + len(table)))
            continue
        io.open(path, "w", encoding="utf-8", newline=u"").write(text)
        print(u"  [OK]   %-12s %d → %d 键（+%d）" % (name + u".json", len(data), len(back), len(table)))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
