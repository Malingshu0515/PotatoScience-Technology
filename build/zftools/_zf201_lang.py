# -*- coding: utf-8 -*-
"""_zf201_lang.py —— 0.16 ZF201 钢套 / 钢制工具的**五语言**物品名

用户原话：「做钢的全套盔甲 钢镐 钢剑 钢斧 …」。名称口径照同材料那几套的现成写法：
  · 中文：钢头盔 / 钢胸甲 / 钢护腿 / 钢靴子 / 钢镐 / 钢剑 / 钢斧
    （对照 zh_cn 里 `star_steel_helmet` = 星璨钢头盔 那一套的句式）；
  · 文言（lzh）：胄 / 鎧 / 護腿 / 靴 / 鎬 / 劍 / 斧（对照 `star_steel_helmet` = 星璨鋼胄）；
  · 英/日/俄：Steel Helmet / 鋼のヘルメット / Стальной шлем
    （对照 `star_steel_*` 与 `titanium_alloy_*` 三种语言的既成句式）。

插入位置：统一插在各自 `item.potato_s_t.steel_plate`（钢板，钢套的配方材料）那一行**后面**，
这样七行钢的新键在文件里是挨着的，一眼能看出是一批。

跑法：
    python build/zftools/_zf201_lang.py            # 只体检
    python build/zftools/_zf201_lang.py --write
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST\PotatoSTneoforge1.21.1"
# 两个工程的语言文件结构相同（同一批键、同一种一行一条的排版）⇒ 同一个脚本跑两遍
PROJECTS = [PROJ, r"E:\PotatoST\PotatoSTforge1.20.1"]
ANCHOR = u"  \"item.potato_s_t.steel_plate\":"

# id → 五种语言的名字（顺序：zh_cn / en_us / ja_jp / lzh / ru_ru）
NAMES = [
    (u"steel_helmet", u"钢头盔", u"Steel Helmet", u"鋼のヘルメット", u"鋼胄",
     u"Стальной шлем"),
    (u"steel_chestplate", u"钢胸甲", u"Steel Chestplate", u"鋼のチェストプレート", u"鋼鎧",
     u"Стальной нагрудник"),
    (u"steel_leggings", u"钢护腿", u"Steel Leggings", u"鋼のレギンス", u"鋼護腿",
     u"Стальные поножи"),
    (u"steel_boots", u"钢靴子", u"Steel Boots", u"鋼のブーツ", u"鋼靴", u"Стальные ботинки"),
    (u"steel_pickaxe", u"钢镐", u"Steel Pickaxe", u"鋼のツルハシ", u"鋼鎬", u"Стальная кирка"),
    (u"steel_sword", u"钢剑", u"Steel Sword", u"鋼の剣", u"鋼劍", u"Стальной меч"),
    (u"steel_axe", u"钢斧", u"Steel Axe", u"鋼の斧", u"鋼斧", u"Стальной топор"),
]
LANGS = [u"zh_cn.json", u"en_us.json", u"ja_jp.json", u"lzh.json", u"ru_ru.json"]

fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def main(argv):
    write = u"--write" in argv
    for proj in PROJECTS:
        LANG = os.path.join(proj, "src", "main", "resources", "assets", "potato_s_t", "lang")
        if not os.path.isdir(LANG):
            fails.append(u"语言目录不存在：%s" % LANG)
            continue
        print(u"===== %s" % os.path.basename(proj))
        for idx, name in enumerate(LANGS):
            path = os.path.join(LANG, name)
            raw = read(path)
            table = json.loads(raw)
            before = len(table)
            lines = raw.split(u"\n")
            anchor_idx = [i for i, l in enumerate(lines) if l.startswith(ANCHOR)]
            if len(anchor_idx) != 1:
                fails.append(u"%s：锚点 `item.potato_s_t.steel_plate` 命中 %d 次" % (name, len(anchor_idx)))
                print(u"  [FAIL] %s：锚点命中 %d 次" % (name, len(anchor_idx)))
                continue
            insert_at = anchor_idx[0] + 1
            new_lines = []
            for row in NAMES:
                rid = row[0]
                value = row[1 + idx]
                key = u"item.potato_s_t.%s" % rid
                if key in table:
                    print(u"  [SKIP] %s：%s 已经有了" % (name, key))
                    continue
                new_lines.append(u'  "%s": "%s",' % (key, value))
            if not new_lines:
                continue
            lines[insert_at:insert_at] = new_lines
            text = u"\n".join(lines)
            try:
                back = json.loads(text)
            except ValueError as e:
                fails.append(u"%s：插入后 JSON 坏掉：%s" % (name, e))
                continue
            if len(back) != before + len(new_lines):
                fails.append(u"%s：键数 %d → %d（应 +%d）" % (name, before, len(back), len(new_lines)))
                continue
            for row in NAMES:
                k = u"item.potato_s_t.%s" % row[0]
                if back.get(k) != row[1 + idx]:
                    fails.append(u"%s：%s 的值不对（%r）" % (name, k, back.get(k)))
            if write:
                io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)
            print(u"  [%s] %-12s 插 %d 行（键数 %d → %d）"
                  % (u"写出" if write else u"将写", name, len(new_lines), before, len(back)))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
