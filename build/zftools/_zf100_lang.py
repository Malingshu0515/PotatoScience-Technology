# -*- coding: utf-8 -*-
u"""_zf100_lang.py —— ZF100 的四语言新键（11 键 × 4 份）

  · `block.potato_s_t.combustion_chamber`          —— 方块名
  · `tooltip.potato_s_t.combustion_chamber`        —— Shift 说明
  · `gui.potato_s_t.combustion_chamber.status.*`   —— 7 条状态灯文案（含本轮新起的 12/13 号）
  · `gui.potato_s_t.combustion_chamber.pour.*`     —— 手倒氧气的两句
  · `fluid_type.potato_s_t.carbon_dioxide`         —— 新气体"二氧化碳"

⚠ §4.64 的规矩：**先解析、再写**；解析不过就一个字节都不动。
  四份 lang 的**结尾换行习惯不一致**（zh/en 没有、ja/ru 有），所以插入位置统一取
  "最后一个键那一行之后"，并且给插入的那几行都补上逗号。
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
        "block.potato_s_t.combustion_chamber": u"燃烧反应室",
        "tooltip.potato_s_t.combustion_chamber":
            u"燃料槽放原版熔炉认的燃料（岩浆桶 10 秒、柴油/汽油桶 30 秒，其余 3 秒）\n"
            u"消耗 1 份燃料 + 10 mB 氧气开始反应；反应期间每 tick 给动力能源捕获器 800 点动力\n"
            u"（柴油 1200 / 汽油 1000）⇒ 把它贴在捕获器旁边就行\n"
            u"原木 → 10 mB 二氧化碳 + 1 个木炭；柴油/汽油桶 → 200 mB 二氧化碳 + 50 mB 水；其余 → 5 mB 二氧化碳\n"
            u"氧气罐只进不出（接泵或用气罐右键倒），二氧化碳罐与水罐只出不进（接泵抽走）；有红石信号即停机",
        "gui.potato_s_t.combustion_chamber.status.running": u"正在燃烧反应",
        "gui.potato_s_t.combustion_chamber.status.disabled": u"已停机（红石信号）",
        "gui.potato_s_t.combustion_chamber.status.empty": u"燃料槽是空的",
        "gui.potato_s_t.combustion_chamber.status.invalid": u"这个物品不能当燃料（原版熔炉认的才行）",
        "gui.potato_s_t.combustion_chamber.status.output_full": u"二氧化碳罐或水罐满了，接泵抽走",
        "gui.potato_s_t.combustion_chamber.status.no_oxygen": u"氧气不足：一次反应要 10 mB",
        "gui.potato_s_t.combustion_chamber.status.byproduct": u"副产物槽放不下（木炭/空桶要腾出位置）",
        "gui.potato_s_t.combustion_chamber.pour.empty": u"手里的容器是空的",
        "gui.potato_s_t.combustion_chamber.pour.rejected": u"倒不进去：氧气罐只收氧气（现在是 %s）",
        "fluid_type.potato_s_t.carbon_dioxide": u"二氧化碳",
    },
    "en_us": {
        "block.potato_s_t.combustion_chamber": u"Combustion Reaction Chamber",
        "tooltip.potato_s_t.combustion_chamber":
            u"Fuel slot takes anything a vanilla furnace burns (lava bucket 10 s, diesel/gasoline bucket 30 s, everything else 3 s)\n"
            u"One fuel item + 10 mB oxygen starts a reaction; while it runs it feeds 800 Power/tick to an adjacent Power Capturer\n"
            u"(diesel 1200, gasoline 1000), so put it next to one\n"
            u"Logs -> 10 mB carbon dioxide + 1 charcoal; diesel/gasoline bucket -> 200 mB carbon dioxide + 50 mB water; anything else -> 5 mB carbon dioxide\n"
            u"The oxygen tank only takes oxygen in, the carbon dioxide and water tanks only let fluid out; a redstone signal stops it",
        "gui.potato_s_t.combustion_chamber.status.running": u"Burning",
        "gui.potato_s_t.combustion_chamber.status.disabled": u"Switched off (redstone signal)",
        "gui.potato_s_t.combustion_chamber.status.empty": u"The fuel slot is empty",
        "gui.potato_s_t.combustion_chamber.status.invalid": u"This item is not a fuel (a vanilla furnace must accept it)",
        "gui.potato_s_t.combustion_chamber.status.output_full": u"The carbon dioxide or water tank is full - pump it out",
        "gui.potato_s_t.combustion_chamber.status.no_oxygen": u"Not enough oxygen: one reaction needs 10 mB",
        "gui.potato_s_t.combustion_chamber.status.byproduct": u"The byproduct slot is full (make room for charcoal / an empty bucket)",
        "gui.potato_s_t.combustion_chamber.pour.empty": u"The held container is empty",
        "gui.potato_s_t.combustion_chamber.pour.rejected": u"Cannot pour: the oxygen tank only takes oxygen (holding %s)",
        "fluid_type.potato_s_t.carbon_dioxide": u"Carbon Dioxide",
    },
    "ja_jp": {
        "block.potato_s_t.combustion_chamber": u"燃焼反応室",
        "tooltip.potato_s_t.combustion_chamber":
            u"燃料スロットにはバニラのかまどが燃料として認めるもの（溶岩入りバケツは 10 秒、ディーゼル/ガソリン入りバケツは 30 秒、それ以外は 3 秒）\n"
            u"燃料 1 個 + 酸素 10 mB で反応開始。反応中は隣の動力エネルギー捕獲器へ毎 tick 800 動力（ディーゼル 1200 / ガソリン 1000）\n"
            u"原木 -> 二酸化炭素 10 mB + 木炭 1 個、ディーゼル/ガソリンのバケツ -> 二酸化炭素 200 mB + 水 50 mB、それ以外 -> 二酸化炭素 5 mB\n"
            u"酸素タンクは投入専用、二酸化炭素と水のタンクは排出専用。レッドストーン信号で停止します",
        "gui.potato_s_t.combustion_chamber.status.running": u"燃焼反応中",
        "gui.potato_s_t.combustion_chamber.status.disabled": u"停止中（レッドストーン信号）",
        "gui.potato_s_t.combustion_chamber.status.empty": u"燃料スロットが空です",
        "gui.potato_s_t.combustion_chamber.status.invalid": u"これは燃料ではありません（バニラのかまどが認めるもののみ）",
        "gui.potato_s_t.combustion_chamber.status.output_full": u"二酸化炭素または水のタンクが満杯です - ポンプで排出してください",
        "gui.potato_s_t.combustion_chamber.status.no_oxygen": u"酸素が足りません：1 回の反応に 10 mB 必要です",
        "gui.potato_s_t.combustion_chamber.status.byproduct": u"副産物スロットがいっぱいです（木炭／空バケツの場所を空けてください）",
        "gui.potato_s_t.combustion_chamber.pour.empty": u"持っている容器が空です",
        "gui.potato_s_t.combustion_chamber.pour.rejected": u"注げません：酸素タンクは酸素のみ（現在 %s）",
        "fluid_type.potato_s_t.carbon_dioxide": u"二酸化炭素",
    },
    "ru_ru": {
        "block.potato_s_t.combustion_chamber": u"Камера сгорания",
        "tooltip.potato_s_t.combustion_chamber":
            u"В слот топлива подходит всё, что принимает обычная печь (ведро лавы — 10 с, ведро дизеля/бензина — 30 с, остальное — 3 с)\n"
            u"1 единица топлива + 10 mB кислорода запускают реакцию; во время неё соседний уловитель получает 800 единиц силы за тик\n"
            u"(дизель 1200, бензин 1000)\n"
            u"Брёвна -> 10 mB углекислого газа + 1 древесный уголь; ведро дизеля/бензина -> 200 mB углекислого газа + 50 mB воды; остальное -> 5 mB углекислого газа\n"
            u"Бак кислорода только принимает, баки углекислого газа и воды только отдают. Сигнал редстоуна останавливает машину",
        "gui.potato_s_t.combustion_chamber.status.running": u"Идёт горение",
        "gui.potato_s_t.combustion_chamber.status.disabled": u"Выключено (сигнал редстоуна)",
        "gui.potato_s_t.combustion_chamber.status.empty": u"Слот топлива пуст",
        "gui.potato_s_t.combustion_chamber.status.invalid": u"Это не топливо (нужно то, что принимает обычная печь)",
        "gui.potato_s_t.combustion_chamber.status.output_full": u"Бак углекислого газа или воды полон — откачайте насосом",
        "gui.potato_s_t.combustion_chamber.status.no_oxygen": u"Не хватает кислорода: на реакцию нужно 10 mB",
        "gui.potato_s_t.combustion_chamber.status.byproduct": u"Слот побочного продукта заполнен (освободите место под уголь/пустое ведро)",
        "gui.potato_s_t.combustion_chamber.pour.empty": u"Контейнер в руке пуст",
        "gui.potato_s_t.combustion_chamber.pour.rejected": u"Не вылить: бак кислорода принимает только кислород (сейчас %s)",
        "fluid_type.potato_s_t.carbon_dioxide": u"Углекислый газ",
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
        data = json.loads(raw)        # ① 先解析（解析不过就别写）
        dup = [k for k in table if k in data]
        if dup:
            fails.append(u"%s：这些键已经有了 %s" % (name, dup))
            continue
        lines = raw.split(u"\n")
        # 最后一个键所在的行（跳过收尾的 "}" 与空行）
        last = max(i for i, l in enumerate(lines) if l.strip().startswith(u'"'))
        if not lines[last].rstrip().endswith(u","):
            lines[last] = lines[last].rstrip() + u","
        # ⚠ 插进去的每行都要**自带逗号**（后面还跟着收尾的 "}"），但**最后一行不能有**
        #   —— 否则就是 "Illegal trailing comma before end of object"。
        #   两版都被 §4.64 那条"先解析再写"当场拦下：**一个字节都没落盘**。
        block = [u'    %s:  %s,' % (json.dumps(k, ensure_ascii=False),
                                    json.dumps(v, ensure_ascii=False))
                 for k, v in table.items()]
        block[-1] = block[-1][:-1]
        lines[last + 1:last + 1] = block
        text = u"\n".join(lines)
        back = json.loads(text)       # ② 回读（写出去的东西自己能解析回来吗）
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
