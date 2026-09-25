# -*- coding: utf-8 -*-
r"""_zf106_lang2.py —— ZF106 再改一次 tooltip：把"吸收是**周期给**、不是常驻护盾"写清楚

用户原话：「没有伤害吸收效果不需要立即重置 末地15s给12伤害吸收 晚上45秒才给10s是为了平衡
护盾不要立马就恢复」

⇒ 文案里要把"**每 15 秒 / 每 45 秒给一次**"和"**等这一次结束才给下一次**"写明，
   否则玩家会以为护盾是常驻的。只动 `tooltip.potato_s_t.star_steel_set` 一个键。
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
KEY = "tooltip.potato_s_t.star_steel_set"

NEW = {
    "zh_cn": u"星璨钢套：每件在夜晚获得抗性提升 I（多件也只有 I），夜晚装备耐久不消耗；"
             u"穿满四件时：末地永久不掉耐久。"
             u"穿满四件：主世界夜晚获得力量 I、抗性提升 II，每 45 秒给一次 10 秒的伤害吸收 III；"
             u"末地获得生命恢复 I、抗性提升 III、力量 II，每 15 秒给一次 12 秒的伤害吸收 VI。"
             u"伤害吸收是周期性给的一次性护盾：这一次的时长走完（或者被打空）才会给下一次，"
             u"不会提前补满。"
             u"受到虚空伤害时传送到 20×20（Y 轴不限）内最近的方块上（传送前给缓降并清空坠落距离，不会摔死），"
             u"找不到方块就与附近的生物交换位置。修理材料：星璨钢锭",
    "en_us": u"Star Steel set: every piece grants Resistance I at night (four pieces still only I) and no "
             u"durability loss at night; with all four pieces worn, durability is never consumed in the End. "
             u"Full set: in the Overworld at night, Strength I and Resistance II, plus 10 s of Absorption III "
             u"every 45 s; in the End, Regeneration I, Resistance III and Strength II, plus 12 s of Absorption VI "
             u"every 15 s. Absorption is a periodic one-shot shield: the next one is granted only after the "
             u"current one runs out (or is used up) - it is never topped up early. When you take void damage you "
             u"are teleported to the nearest block within 20x20 (any height) - Slow Falling is applied and fall "
             u"distance cleared first, so you will not die from the drop - or swapped with a nearby mob if there "
             u"is no block. Repair material: Star Steel Ingot",
    "ja_jp": u"星燦鋼セット：各部位は夜間に耐性 I（何枚でも I のまま）と、夜間は耐久を消費しない。"
             u"4 部位そろうと、エンドでは耐久を一切消費しない。"
             u"4 部位そろうと：主世界の夜は力 I と耐性 II、45 秒ごとに 10 秒の衝撃吸収 III。"
             u"エンドでは再生 I・耐性 III・力 II、15 秒ごとに 12 秒の衝撃吸収 VI。"
             u"衝撃吸収は周期的な一度きりのシールドで、今回の効果が切れる（または使い切る）まで次は付与されず、"
             u"早めに補充されることはない。"
             u"ヴォイドダメージを受けると 20×20（高さ無制限）で最も近いブロックへ転送され"
             u"（転送前に落下速度低下を付与し落下距離をリセットするので落下死しない）、"
             u"無ければ近くのモブと位置を交換する。修理素材：星燦鋼インゴット",
    "ru_ru": u"Набор звёздной стали: каждая часть даёт ночью Сопротивление I (даже четыре части — только I) "
             u"и ночью не расходует прочность; в полном наборе прочность никогда не расходуется в Крае. "
             u"Полный набор: в Верхнем мире ночью — Сила I и Сопротивление II, а также 10 с Поглощения III "
             u"каждые 45 с; в Крае — Регенерация I, Сопротивление III и Сила II, а также 12 с Поглощения VI "
             u"каждые 15 с. Поглощение — это периодический одноразовый щит: следующий выдаётся только после "
             u"того, как текущий закончится (или будет израсходован), досрочного пополнения нет. При уроне от "
             u"пустоты вы телепортируетесь к ближайшему блоку в пределах 20x20 (по высоте без ограничений) — "
             u"перед этим выдаётся медленное падение и сбрасывается высота падения, так что вы не разобьётесь — "
             u"либо меняетесь местами с ближайшим мобом, если блоков нет. Материал починки: слиток звёздной стали",
}

fails = []


def main():
    for name, value in sorted(NEW.items()):
        path = os.path.join(LANG, name + ".json")
        raw = io.open(path, encoding="utf-8").read()
        data = json.loads(raw)
        if KEY not in data:
            fails.append(u"%s：缺键" % name)
            continue
        lines = raw.split(u"\n")
        hit = None
        for i, l in enumerate(lines):
            if (u'"%s":' % KEY) in l:
                hit = i
                break
        if hit is None:
            fails.append(u"%s：找不到那一行" % name)
            continue
        indent = lines[hit][:len(lines[hit]) - len(lines[hit].lstrip())]
        comma = u"," if lines[hit].rstrip().endswith(u",") else u""
        lines[hit] = u'%s"%s":  %s%s' % (indent, KEY, json.dumps(value, ensure_ascii=False), comma)
        text = u"\n".join(lines)
        back = json.loads(text)
        if back.get(KEY) != value or len(back) != len(data):
            fails.append(u"%s：回读不一致" % name)
            continue
        if u"**" in value:
            fails.append(u"%s：文案里还有 Markdown 星号（MC tooltip 不认）" % name)
            continue
        io.open(path, "w", encoding="utf-8", newline=u"").write(text)
        print(u"  [OK]   %-14s 已更新（%d 字，无 Markdown 星号）" % (name, len(value)))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
