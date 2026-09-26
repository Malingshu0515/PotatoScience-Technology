# -*- coding: utf-8 -*-
"""_zf133_lang.py —— ZF133 的四语言键（星璨钢斧）

规矩（§11.1 第 2 道门 LangCheck）：四个语言的键集**必须逐字一致**，少一个键就是 FAIL。

本轮加 4 个键：
    item.potato_s_t.star_steel_axe      物品名
    tooltip.potato_s_t.star_steel_axe.1 夜晚免耐久 + 手持急迫
    tooltip.potato_s_t.star_steel_axe.2 Shift 右键的冲击波（扣 120 / 15 秒冷却 / 6 格宽）
    tooltip.potato_s_t.star_steel_axe.3 破坏范围 + 两条消失条件 + 末地远程伤害

插入位置：紧跟 `item.potato_s_t.star_steel_ingot` 那一行之后
（文件开头就是"新物品那几行"的小簇，与 ZF103/ZF114/ZF122 的写法一致）。

⚠ 多线开发：这份文件别的会话也在改。脚本按**锚点唯一**插入（锚点出现次数 != 1 就停），
   写完立刻 `json.loads` 复核 + 报键数。
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")

ANCHOR_KEY = '"item.potato_s_t.star_steel_ingot":'
# ⚠ 四份文件的**缩进不统一**（zh_cn 那一簇是 4 空格，en/ja/ru 是 2 空格，
#   ZF103/ZF120 几轮分别手写/脚本写的，本工程一直没统一）⇒ 锚点只认键名那一截，
#   插入行的缩进照**锚点行自己的缩进**走。
ANCHOR_INDENTS = ["    ", "  ", "\t"]

KEYS = {
    "zh_cn": [
        ("item.potato_s_t.star_steel_axe", "星璨钢斧"),
        ("tooltip.potato_s_t.star_steel_axe.1",
         "夜晚不消耗耐久；手持时持续获得急迫 I。1192 耐久，挖掘等级钻石"),
        ("tooltip.potato_s_t.star_steel_axe.2",
         "Shift + 右键：扣 120 点耐久，朝面向放出一道 6 格宽的冲击波（15 秒冷却）"),
        ("tooltip.potato_s_t.star_steel_axe.3",
         "冲击波拆掉沿途所有原木 / 去皮原木与树叶；撞上斧子挖不动的方块、或 10 秒没碰到木头就消失。\n在末地：额外造成 10 + 0.5n 点远程伤害（n 为你自己的基础伤害）"),
    ],
    "en_us": [
        ("item.potato_s_t.star_steel_axe", "Star Steel Axe"),
        ("tooltip.potato_s_t.star_steel_axe.1",
         "No durability loss at night; Haste I while held. 1192 durability, diamond mining level"),
        ("tooltip.potato_s_t.star_steel_axe.2",
         "Shift + right-click: costs 120 durability to send a 6-block-wide shockwave along your facing (15 s cooldown)"),
        ("tooltip.potato_s_t.star_steel_axe.3",
         "The shockwave fells every log, stripped log and leaf in its path; it dies when it meets a block the axe cannot mine, or after 10 s without touching wood.\nIn the End it also deals 10 + 0.5n ranged damage (n is your own base damage)"),
    ],
    "ja_jp": [
        ("item.potato_s_t.star_steel_axe", "星燦鋼の斧"),
        ("tooltip.potato_s_t.star_steel_axe.1",
         "夜間は耐久を消費しない。手持ち中は採掘速度上昇 I。耐久 1192、採掘レベルはダイヤ相当"),
        ("tooltip.potato_s_t.star_steel_axe.2",
         "Shift + 右クリック：耐久を 120 消費し、向いている方向へ幅 6 ブロックの衝撃波を放つ（クールダウン 15 秒）"),
        ("tooltip.potato_s_t.star_steel_axe.3",
         "衝撃波は進路上の原木・樹皮を剥いだ原木・葉をすべて破壊する。斧で採掘できないブロックに当たるか、10 秒間木材に触れないと消える。\nエンドでは追加で 10 + 0.5n の遠距離ダメージ（n は自身の基礎ダメージ）"),
    ],
    "ru_ru": [
        ("item.potato_s_t.star_steel_axe", "Топор из звёздной стали"),
        ("tooltip.potato_s_t.star_steel_axe.1",
         "Ночью прочность не расходуется; в руке даёт Спешку I. Прочность 1192, уровень добычи — алмазный"),
        ("tooltip.potato_s_t.star_steel_axe.2",
         "Shift + ПКМ: расходует 120 прочности и посылает ударную волну шириной 6 блоков по направлению взгляда (перезарядка 15 с)"),
        ("tooltip.potato_s_t.star_steel_axe.3",
         "Волна уничтожает все брёвна, окорённые брёвна и листья на пути; исчезает, встретив блок, который топор не может добыть, или через 10 с без древесины.\nВ Крае дополнительно наносит 10 + 0.5n урона на расстоянии (n — ваша базовая атака)"),
    ],
}


def escape(value):
    """按本工程既有写法转义：\\ -> \\\\、换行 -> \\n、非 ASCII 原样（文件是 UTF-8）。"""
    out = value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
    return out


def main():
    counts = {}
    for lang, items in KEYS.items():
        path = os.path.join(LANG, lang + ".json")
        s = io.open(path, encoding="utf-8").read()
        idx = s.find(ANCHOR_KEY)
        assert idx > 0, "%s 里找不到锚点键 %s" % (lang, ANCHOR_KEY)
        assert s.count(ANCHOR_KEY) == 1, "%s 里锚点键出现多次" % lang
        line_start = s.rfind("\n", 0, idx) + 1
        indent = s[line_start:idx]
        assert indent in ANCHOR_INDENTS, "%s 的锚点缩进是 %r（没见过的写法）" % (lang, indent)
        doc_before = json.loads(s)
        before_keys = len(doc_before)

        # ⚠ 幂等：本轮我已经手工跑过一次（zh_cn 那 4 个键已经进去了），
        #   所以这里不能"见到键就报错"，而要**逐个核值**：
        #   已在且值一致 = 跳过；已在但值不同 = 当场停。
        todo = []
        for key, value in items:
            if key in doc_before:
                assert doc_before[key] == value, \
                    "%s 的 %s 已存在但值不同（预期 %r，实得 %r）" % (lang, key, value, doc_before[key])
                continue
            todo.append((key, value))
        if not todo:
            counts[lang] = before_keys
            print("[SKIP] %-6s 缩进=%-4r 4 个键都已就位（值逐个核过）" % (lang, indent))
            continue

        block = ""
        for key, value in todo:
            block += '%s"%s":  "%s",\n' % (indent, key, escape(value))
        line_end = s.index("\n", idx) + 1
        s2 = s[:line_end] + block + s[line_end:]
        # 逐字复核：JSON 能解 + 键数 +N + 每个键的值与预期一致
        doc = json.loads(s2)
        assert len(doc) == before_keys + len(todo), \
            "%s 键数 %d -> %d（预期 +%d）" % (lang, before_keys, len(doc), len(todo))
        for key, value in items:
            assert doc[key] == value, "%s 的 %s 值与预期不一致" % (lang, key)
        io.open(path, "w", encoding="utf-8", newline="\n").write(s2)
        counts[lang] = len(doc)
        print("[OK ] %-6s 缩进=%-4r %d -> %d 键（+%d）" % (lang, indent, before_keys, len(doc), len(todo)))

    assert len(set(counts.values())) == 1, "四语言键数不一致：%r" % counts
    print("-" * 60)
    print("四语言一致：%d 键" % list(counts.values())[0])


main()
