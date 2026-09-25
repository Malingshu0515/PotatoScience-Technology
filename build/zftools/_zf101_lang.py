# -*- coding: utf-8 -*-
u"""_zf101_lang.py —— ZF101 的四语言新键

  · `block.potato_s_t.acidic_reaction_chamber`          —— 方块名
  · `tooltip.potato_s_t.acidic_reaction_chamber`        —— Shift 说明（三个配方 + 七个罐）
  · `gui.potato_s_t.acidic_reaction_chamber.status.*`   —— 6 条状态灯文案（含新号 14）
  · `gui.potato_s_t.acidic_reaction_chamber.recipe.*`   —— 三个按钮的名字 + 悬停说明（各 3 条）
  · `fluid_type.potato_s_t.*`                           —— 三种新流体名（碳酸/硝酸/硫酸）

⚠ §4.64 的规矩：**先解析、再写**；解析不过就一个字节都不动。
⚠ 插入的每一行都要自带逗号，**但最后一行不能有**（ZF100 那轮在这里连栽两次）。
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
        "block.potato_s_t.acidic_reaction_chamber": u"酸性反应室",
        "tooltip.potato_s_t.acidic_reaction_chamber":
            u"四个原料罐（各 1000 mB）：二氧化碳 / 氧气 / 氨气 / 水；三个产物罐：碳酸 / 硝酸 / 硫酸\n"
            u"三个按钮选配方（点哪个跑哪个）：①10 mB 二氧化碳 + 1 mB 水 → 1 mB 碳酸 ②1 mB 氧气 + 1 mB 氨气 → 1 mB 硝酸\n"
            u"③10 个硫 + 100 mB 水 → 100 mB 硫酸（一批 5 秒，材料在最后一刻才扣）\n"
            u"耗电都是 500 FE/t，缓冲 12400 FE（必须持续供电）；有红石信号即停机",
        "gui.potato_s_t.acidic_reaction_chamber.status.running": u"正在反应",
        "gui.potato_s_t.acidic_reaction_chamber.status.disabled": u"已停机（红石信号）",
        "gui.potato_s_t.acidic_reaction_chamber.status.no_power": u"电力不足：每 tick 要 500 FE",
        "gui.potato_s_t.acidic_reaction_chamber.status.output_full": u"产物罐满了，接泵抽走",
        "gui.potato_s_t.acidic_reaction_chamber.status.material": u"硫不够一批（要 10 个）",
        "gui.potato_s_t.acidic_reaction_chamber.status.inputs": u"流体原料不足（这个配方要的原料罐没料，接泵或用气罐补）",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.name.0": u"碳酸",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.name.1": u"硝酸",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.name.2": u"硫酸",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.info.0": u"碳酸：每 tick 10 mB 二氧化碳 + 1 mB 水 → 1 mB 碳酸",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.info.1": u"硝酸：每 tick 1 mB 氧气 + 1 mB 氨气 → 1 mB 硝酸",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.info.2": u"硫酸：一批 10 个硫 + 100 mB 水 → 100 mB 硫酸（5 秒）",
        "fluid_type.potato_s_t.carbonic_acid": u"碳酸",
        "fluid_type.potato_s_t.nitric_acid": u"硝酸",
        "fluid_type.potato_s_t.sulfuric_acid": u"硫酸",
    },
    "en_us": {
        "block.potato_s_t.acidic_reaction_chamber": u"Acidic Reaction Chamber",
        "tooltip.potato_s_t.acidic_reaction_chamber":
            u"Four input tanks (1,000 mB each): carbon dioxide / oxygen / ammonia / water; three output tanks: carbonic / nitric / sulfuric acid\n"
            u"Pick a recipe with the three buttons: (1) 10 mB carbon dioxide + 1 mB water -> 1 mB carbonic acid, (2) 1 mB oxygen + 1 mB ammonia -> 1 mB nitric acid\n"
            u"(3) 10 sulfur + 100 mB water -> 100 mB sulfuric acid (one batch every 5 seconds; the materials are only taken on the last tick)\n"
            u"All three draw 500 FE/t with a 12,400 FE buffer, so it needs a steady supply; a redstone signal stops it",
        "gui.potato_s_t.acidic_reaction_chamber.status.running": u"Reacting",
        "gui.potato_s_t.acidic_reaction_chamber.status.disabled": u"Switched off (redstone signal)",
        "gui.potato_s_t.acidic_reaction_chamber.status.no_power": u"Not enough power: 500 FE per tick",
        "gui.potato_s_t.acidic_reaction_chamber.status.output_full": u"An output tank is full - pump it out",
        "gui.potato_s_t.acidic_reaction_chamber.status.material": u"Not enough sulfur for one batch (10 needed)",
        "gui.potato_s_t.acidic_reaction_chamber.status.inputs": u"Not enough fluid input (fill the tanks this recipe needs)",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.name.0": u"Carbonic",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.name.1": u"Nitric",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.name.2": u"Sulfuric",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.info.0": u"Carbonic acid: 10 mB carbon dioxide + 1 mB water -> 1 mB per tick",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.info.1": u"Nitric acid: 1 mB oxygen + 1 mB ammonia -> 1 mB per tick",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.info.2": u"Sulfuric acid: 10 sulfur + 100 mB water -> 100 mB per 5 s batch",
        "fluid_type.potato_s_t.carbonic_acid": u"Carbonic Acid",
        "fluid_type.potato_s_t.nitric_acid": u"Nitric Acid",
        "fluid_type.potato_s_t.sulfuric_acid": u"Sulfuric Acid",
    },
    "ja_jp": {
        "block.potato_s_t.acidic_reaction_chamber": u"酸性反応室",
        "tooltip.potato_s_t.acidic_reaction_chamber":
            u"原料タンク 4 つ（各 1,000 mB）：二酸化炭素 / 酸素 / アンモニア / 水、製品タンク 3 つ：炭酸 / 硝酸 / 硫酸\n"
            u"3 つのボタンでレシピを選択：(1) 二酸化炭素 10 mB + 水 1 mB -> 炭酸 1 mB、(2) 酸素 1 mB + アンモニア 1 mB -> 硝酸 1 mB\n"
            u"(3) 硫黄 10 個 + 水 100 mB -> 硫酸 100 mB（1 バッチ 5 秒、材料は最後の 1 tick で消費）\n"
            u"いずれも 500 FE/t、蓄電 12,400 FE（安定した電力が必要）。レッドストーン信号で停止します",
        "gui.potato_s_t.acidic_reaction_chamber.status.running": u"反応中",
        "gui.potato_s_t.acidic_reaction_chamber.status.disabled": u"停止中（レッドストーン信号）",
        "gui.potato_s_t.acidic_reaction_chamber.status.no_power": u"電力不足：毎 tick 500 FE 必要",
        "gui.potato_s_t.acidic_reaction_chamber.status.output_full": u"製品タンクが満杯です - ポンプで排出してください",
        "gui.potato_s_t.acidic_reaction_chamber.status.material": u"硫黄が 1 バッチ分（10 個）足りません",
        "gui.potato_s_t.acidic_reaction_chamber.status.inputs": u"液体原料が足りません（このレシピに必要なタンクを満たしてください）",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.name.0": u"炭酸",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.name.1": u"硝酸",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.name.2": u"硫酸",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.info.0": u"炭酸：毎 tick 二酸化炭素 10 mB + 水 1 mB -> 炭酸 1 mB",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.info.1": u"硝酸：毎 tick 酸素 1 mB + アンモニア 1 mB -> 硝酸 1 mB",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.info.2": u"硫酸：硫黄 10 個 + 水 100 mB -> 硫酸 100 mB（5 秒）",
        "fluid_type.potato_s_t.carbonic_acid": u"炭酸",
        "fluid_type.potato_s_t.nitric_acid": u"硝酸",
        "fluid_type.potato_s_t.sulfuric_acid": u"硫酸",
    },
    "ru_ru": {
        "block.potato_s_t.acidic_reaction_chamber": u"Кислотная реакционная камера",
        "tooltip.potato_s_t.acidic_reaction_chamber":
            u"Четыре входных бака (по 1 000 mB): углекислый газ / кислород / аммиак / вода; три выходных: угольная / азотная / серная кислота\n"
            u"Рецепт выбирается тремя кнопками: (1) 10 mB углекислого газа + 1 mB воды -> 1 mB угольной кислоты, (2) 1 mB кислорода + 1 mB аммиака -> 1 mB азотной кислоты\n"
            u"(3) 10 серы + 100 mB воды -> 100 mB серной кислоты (партия за 5 секунд; материалы списываются в последний тик)\n"
            u"Все три требуют 500 FE/тик при буфере 12 400 FE, поэтому нужно постоянное питание; сигнал редстоуна останавливает машину",
        "gui.potato_s_t.acidic_reaction_chamber.status.running": u"Идёт реакция",
        "gui.potato_s_t.acidic_reaction_chamber.status.disabled": u"Выключено (сигнал редстоуна)",
        "gui.potato_s_t.acidic_reaction_chamber.status.no_power": u"Не хватает энергии: 500 FE за тик",
        "gui.potato_s_t.acidic_reaction_chamber.status.output_full": u"Выходной бак полон — откачайте насосом",
        "gui.potato_s_t.acidic_reaction_chamber.status.material": u"Серы меньше одной партии (нужно 10)",
        "gui.potato_s_t.acidic_reaction_chamber.status.inputs": u"Не хватает жидкого сырья (заполните нужные баки)",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.name.0": u"Угольная",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.name.1": u"Азотная",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.name.2": u"Серная",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.info.0": u"Угольная кислота: 10 mB углекислого газа + 1 mB воды -> 1 mB за тик",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.info.1": u"Азотная кислота: 1 mB кислорода + 1 mB аммиака -> 1 mB за тик",
        "gui.potato_s_t.acidic_reaction_chamber.recipe.info.2": u"Серная кислота: 10 серы + 100 mB воды -> 100 mB за партию (5 с)",
        "fluid_type.potato_s_t.carbonic_acid": u"Угольная кислота",
        "fluid_type.potato_s_t.nitric_acid": u"Азотная кислота",
        "fluid_type.potato_s_t.sulfuric_acid": u"Серная кислота",
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
        data = json.loads(raw)        # ① 先解析
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
        block[-1] = block[-1][:-1]    # 最后一行不能有逗号
        lines[last + 1:last + 1] = block
        text = u"\n".join(lines)
        back = json.loads(text)       # ② 回读
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
