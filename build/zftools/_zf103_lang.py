# -*- coding: utf-8 -*-
u"""_zf103_lang.py —— ZF103（两套盔甲 + 星璨钢锭）的四语言新键（每份 14 键）

  · item.potato_s_t.star_steel_ingot                       —— 星璨钢锭
  · item.potato_s_t.titanium_alloy_{helmet,chestplate,leggings,boots}
  · item.potato_s_t.star_steel_{helmet,chestplate,leggings,boots}
  · tooltip.potato_s_t.titanium_alloy_set                  —— 钛合金套的 Shift 说明
  · tooltip.potato_s_t.star_steel_set                      —— 星璨钢套的 Shift 说明
  · message.potato_s_t.star_steel_void_{block,swap,failed} —— 虚空救援的三条提示

⚠ §4.64：先解析、再写；插进去的每行自带逗号，**最后一行不能有**。
⚠ 换行风格、缩进、`：` 前的两个空格都跟随既有文件（档案 §6.4 铁律 4）。
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
        "item.potato_s_t.star_steel_ingot": u"星璨钢锭",
        "item.potato_s_t.titanium_alloy_helmet": u"钛合金头盔",
        "item.potato_s_t.titanium_alloy_chestplate": u"钛合金胸甲",
        "item.potato_s_t.titanium_alloy_leggings": u"钛合金护腿",
        "item.potato_s_t.titanium_alloy_boots": u"钛合金靴子",
        "item.potato_s_t.star_steel_helmet": u"星璨钢头盔",
        "item.potato_s_t.star_steel_chestplate": u"星璨钢胸甲",
        "item.potato_s_t.star_steel_leggings": u"星璨钢护腿",
        "item.potato_s_t.star_steel_boots": u"星璨钢靴子",
        "tooltip.potato_s_t.titanium_alloy_set":
            u"钛合金套：附魔权重 25（金是 22）。头盔 耐久 2801 / 护甲值 +2.5；"
            u"胸甲 耐久 4096 / 护甲值 +8；护腿 耐久 3412 / 护甲值 +6；靴子 耐久 2048 / 护甲值 +4.5。"
            u"修理材料：轻质钛合金",
        "tooltip.potato_s_t.star_steel_set":
            u"星璨钢套：每件在夜晚获得抗性提升 I（多件也只有 I），夜晚装备耐久不消耗。"
            u"穿满四件：主世界夜晚获得力量 I、抗性提升 II，每 45 秒获得 10 秒的伤害吸收 III；"
            u"末地获得生命恢复 I、抗性提升 III、力量 II，每 15 秒获得 12 秒的伤害吸收 VI；"
            u"受到虚空伤害时传送到 20×20（Y 轴不限）内最近的方块上，找不到就与附近的生物交换位置。"
            u"修理材料：星璨钢锭",
        "message.potato_s_t.star_steel_void_block": u"星璨钢套：已传送到最近的方块上",
        "message.potato_s_t.star_steel_void_swap": u"星璨钢套：附近没有方块，已与生物交换位置",
        "message.potato_s_t.star_steel_void_failed": u"星璨钢套：既没有方块也没有生物可换位",
    },
    "en_us": {
        "item.potato_s_t.star_steel_ingot": u"Star Steel Ingot",
        "item.potato_s_t.titanium_alloy_helmet": u"Titanium Alloy Helmet",
        "item.potato_s_t.titanium_alloy_chestplate": u"Titanium Alloy Chestplate",
        "item.potato_s_t.titanium_alloy_leggings": u"Titanium Alloy Leggings",
        "item.potato_s_t.titanium_alloy_boots": u"Titanium Alloy Boots",
        "item.potato_s_t.star_steel_helmet": u"Star Steel Helmet",
        "item.potato_s_t.star_steel_chestplate": u"Star Steel Chestplate",
        "item.potato_s_t.star_steel_leggings": u"Star Steel Leggings",
        "item.potato_s_t.star_steel_boots": u"Star Steel Boots",
        "tooltip.potato_s_t.titanium_alloy_set":
            u"Titanium Alloy set: enchantment value 25 (gold is 22). "
            u"Helmet 2801 durability / +2.5 armor; chestplate 4096 / +8; leggings 3412 / +6; boots 2048 / +4.5. "
            u"Repair material: Light Titanium Alloy",
        "tooltip.potato_s_t.star_steel_set":
            u"Star Steel set: every piece grants Resistance I at night (four pieces still only I) and no "
            u"durability loss at night. Full set: in the Overworld at night, Strength I and Resistance II, "
            u"plus 10 s of Absorption III every 45 s; in the End, Regeneration I, Resistance III and "
            u"Strength II, plus 12 s of Absorption VI every 15 s; when you take void damage you are "
            u"teleported to the nearest block within 20x20 (any height), or swapped with a nearby mob if "
            u"there is none. Repair material: Star Steel Ingot",
        "message.potato_s_t.star_steel_void_block": u"Star Steel set: teleported to the nearest block",
        "message.potato_s_t.star_steel_void_swap": u"Star Steel set: no block nearby, swapped with a mob",
        "message.potato_s_t.star_steel_void_failed": u"Star Steel set: no block and no mob to swap with",
    },
    "ja_jp": {
        "item.potato_s_t.star_steel_ingot": u"星燦鋼インゴット",
        "item.potato_s_t.titanium_alloy_helmet": u"チタン合金のヘルメット",
        "item.potato_s_t.titanium_alloy_chestplate": u"チタン合金のチェストプレート",
        "item.potato_s_t.titanium_alloy_leggings": u"チタン合金のレギンス",
        "item.potato_s_t.titanium_alloy_boots": u"チタン合金のブーツ",
        "item.potato_s_t.star_steel_helmet": u"星燦鋼のヘルメット",
        "item.potato_s_t.star_steel_chestplate": u"星燦鋼のチェストプレート",
        "item.potato_s_t.star_steel_leggings": u"星燦鋼のレギンス",
        "item.potato_s_t.star_steel_boots": u"星燦鋼のブーツ",
        "tooltip.potato_s_t.titanium_alloy_set":
            u"チタン合金セット：エンチャント値 25（金は 22）。"
            u"ヘルメット 耐久 2801 / 防具 +2.5、チェストプレート 4096 / +8、"
            u"レギンス 3412 / +6、ブーツ 2048 / +4.5。修理素材：軽量チタン合金",
        "tooltip.potato_s_t.star_steel_set":
            u"星燦鋼セット：各部位は夜間に耐性 I（何枚でも I のまま）と、夜間は耐久を消費しない。"
            u"4 部位そろうと：主世界の夜は力 I と耐性 II、45 秒ごとに 10 秒の衝撃吸収 III。"
            u"エンドでは再生 I・耐性 III・力 II、15 秒ごとに 12 秒の衝撃吸収 VI。"
            u"ヴォイドダメージを受けると 20×20（高さ無制限）で最も近いブロックへ転送され、"
            u"無ければ近くのモブと位置を交換する。修理素材：星燦鋼インゴット",
        "message.potato_s_t.star_steel_void_block": u"星燦鋼セット：最寄りのブロックへ転送しました",
        "message.potato_s_t.star_steel_void_swap": u"星燦鋼セット：ブロックが無いためモブと位置を交換しました",
        "message.potato_s_t.star_steel_void_failed": u"星燦鋼セット：ブロックもモブも見つかりません",
    },
    "ru_ru": {
        "item.potato_s_t.star_steel_ingot": u"Слиток звёздной стали",
        "item.potato_s_t.titanium_alloy_helmet": u"Титановый шлем",
        "item.potato_s_t.titanium_alloy_chestplate": u"Титановый нагрудник",
        "item.potato_s_t.titanium_alloy_leggings": u"Титановые поножи",
        "item.potato_s_t.titanium_alloy_boots": u"Титановые ботинки",
        "item.potato_s_t.star_steel_helmet": u"Шлем из звёздной стали",
        "item.potato_s_t.star_steel_chestplate": u"Нагрудник из звёздной стали",
        "item.potato_s_t.star_steel_leggings": u"Поножи из звёздной стали",
        "item.potato_s_t.star_steel_boots": u"Ботинки из звёздной стали",
        "tooltip.potato_s_t.titanium_alloy_set":
            u"Титановый набор: уровень зачарования 25 (у золота 22). "
            u"Шлем 2801 прочности / +2.5 брони; нагрудник 4096 / +8; поножи 3412 / +6; ботинки 2048 / +4.5. "
            u"Материал починки: лёгкий титановый сплав",
        "tooltip.potato_s_t.star_steel_set":
            u"Набор звёздной стали: каждая часть даёт ночью Сопротивление I (даже четыре части — только I) "
            u"и ночью не расходует прочность. Полный набор: в Верхнем мире ночью — Сила I и Сопротивление II, "
            u"а также 10 с Поглощения III каждые 45 с; в Крае — Регенерация I, Сопротивление III и Сила II, "
            u"а также 12 с Поглощения VI каждые 15 с; при уроне от пустоты вы телепортируетесь к ближайшему "
            u"блоку в пределах 20x20 (по высоте без ограничений), а если блоков нет — меняетесь местами с "
            u"ближайшим мобом. Материал починки: слиток звёздной стали",
        "message.potato_s_t.star_steel_void_block": u"Звёздная сталь: телепорт к ближайшему блоку",
        "message.potato_s_t.star_steel_void_swap": u"Звёздная сталь: блоков нет, обмен местами с мобом",
        "message.potato_s_t.star_steel_void_failed": u"Звёздная сталь: нет ни блока, ни моба для обмена",
    },
}

fails = []


def main():
    if len(KEYS) != 4:
        print(u"!! 语言份数不对：%d" % len(KEYS))
        return 1
    counts = set(len(t) for t in KEYS.values())
    if len(counts) != 1:
        print(u"!! 四份的键数不一致：%s" % sorted(counts))
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
        block = [u'  %s:  %s,' % (json.dumps(k, ensure_ascii=False),
                                  json.dumps(v, ensure_ascii=False))
                 for k, v in table.items()]
        block[-1] = block[-1][:-1]
        lines[last + 1:last + 1] = block
        text = u"\n".join(lines)
        back = json.loads(text)
        if len(back) != len(data) + len(table):
            fails.append(u"%s：回读键数 %d ≠ %d" % (name, len(back), len(data) + len(table)))
            continue
        if not back[u"tooltip.potato_s_t.hold_shift"]:
            fails.append(u"%s：插入后丢了既有键" % name)
            continue
        io.open(path, "w", encoding="utf-8", newline=u"").write(text)
        print(u"  [OK]   %-12s %d → %d 键（+%d）" % (name + u".json", len(data), len(back), len(table)))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
