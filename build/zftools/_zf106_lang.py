# -*- coding: utf-8 -*-
r"""_zf106_lang.py —— ZF106：把星璨钢套的 tooltip 改成"末地永久不掉耐久 + 传送前给缓降"

用户本轮两条修正：

  「星璨钢末地并不是不消耗耐久」
  「传送之前加个缓降还是什么免除一下摔落伤害 要不然就摔死了」

⇒ 旧文案里「夜晚装备耐久不消耗」没写末地那一条，而且没提缓降。
   本脚本**只替换那两个键的值**（不动键集合、不动其它任何键），四语言各一份。
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
             u"穿满四件：主世界夜晚获得力量 I、抗性提升 II，每 45 秒获得 10 秒的伤害吸收 III；"
             u"末地获得生命恢复 I、抗性提升 III、力量 II，每 15 秒获得 12 秒的伤害吸收 VI；"
             u"受到虚空伤害时传送到 20×20（Y 轴不限）内最近的方块上（传送前给缓降并清空坠落距离，不会摔死），"
             u"找不到方块就与附近的生物交换位置。修理材料：星璨钢锭",
    "en_us": u"Star Steel set: every piece grants Resistance I at night (four pieces still only I) and no "
             u"durability loss at night; with all four pieces worn, durability is never consumed in the End. "
             u"Full set: in the Overworld at night, Strength I and Resistance II, plus 10 s of Absorption III "
             u"every 45 s; in the End, Regeneration I, Resistance III and Strength II, plus 12 s of Absorption VI "
             u"every 15 s; when you take void damage you are teleported to the nearest block within 20x20 "
             u"(any height) — Slow Falling is applied and fall distance cleared first, so you will not die "
             u"from the drop — or swapped with a nearby mob if there is no block. Repair material: Star Steel Ingot",
    "ja_jp": u"星燦鋼セット：各部位は夜間に耐性 I（何枚でも I のまま）と、夜間は耐久を消費しない。"
             u"4 部位そろうと、エンドでは耐久を一切消費しない。"
             u"4 部位そろうと：主世界の夜は力 I と耐性 II、45 秒ごとに 10 秒の衝撃吸収 III。"
             u"エンドでは再生 I・耐性 III・力 II、15 秒ごとに 12 秒の衝撃吸収 VI。"
             u"ヴォイドダメージを受けると 20×20（高さ無制限）で最も近いブロックへ転送され"
             u"（転送前に落下速度低下を付与し落下距離をリセットするので落下死しない）、"
             u"無ければ近くのモブと位置を交換する。修理素材：星燦鋼インゴット",
    "ru_ru": u"Набор звёздной стали: каждая часть даёт ночью Сопротивление I (даже четыре части — только I) "
             u"и ночью не расходует прочность; в полном наборе прочность никогда не расходуется в Крае. "
             u"Полный набор: в Верхнем мире ночью — Сила I и Сопротивление II, а также 10 с Поглощения III "
             u"каждые 45 с; в Крае — Регенерация I, Сопротивление III и Сила II, а также 12 с Поглощения VI "
             u"каждые 15 с; при уроне от пустоты вы телепортируетесь к ближайшему блоку в пределах 20x20 "
             u"(по высоте без ограничений) — перед этим выдаётся медленное падение и сбрасывается высота "
             u"падения, так что вы не разобьётесь — либо меняетесь местами с ближайшим мобом, если блоков нет. "
             u"Материал починки: слиток звёздной стали",
}

fails = []


def main():
    for name, value in sorted(NEW.items()):
        path = os.path.join(LANG, name + ".json")
        raw = io.open(path, encoding="utf-8").read()
        data = json.loads(raw)
        if KEY not in data:
            fails.append(u"%s：缺键 %s" % (name, KEY))
            continue
        # 用 json 重写整份会打乱原格式 ⇒ 改成"只换这一行的值"
        old_line = u'"%s":' % KEY
        lines = raw.split(u"\n")
        hit = None
        for i, l in enumerate(lines):
            if old_line in l:
                hit = i
                break
        if hit is None:
            fails.append(u"%s：在文本里找不到 %s 那一行" % (name, KEY))
            continue
        indent = lines[hit][:len(lines[hit]) - len(lines[hit].lstrip())]
        comma = u"," if lines[hit].rstrip().endswith(u",") else u""
        # 语言文件里键与值之间是「两个空格 + 冒号 + 两个空格」（见既有文件）
        lines[hit] = u'%s"%s":  %s%s' % (indent, KEY,
                                         json.dumps(value, ensure_ascii=False), comma)
        text = u"\n".join(lines)
        back = json.loads(text)                       # 回读校验（§4.64：写回前先解析）
        if back.get(KEY) != value:
            fails.append(u"%s：回读的值与写入的不一致" % name)
            continue
        if len(back) != len(data):
            fails.append(u"%s：键数变了 %d → %d" % (name, len(data), len(back)))
            continue
        io.open(path, "w", encoding="utf-8", newline=u"").write(text)
        print(u"  [OK]   %-14s %s → 新版（%d 字）" % (name, KEY, len(value)))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
