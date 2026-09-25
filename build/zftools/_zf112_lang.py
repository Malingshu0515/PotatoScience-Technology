# -*- coding: utf-8 -*-
u"""_zf112_lang.py —— 锂电池构造间 + 锂电池原件 的四语言键（0.11 ZF112）

新增 9 个键 × 4 语言（**408 → 417**）：
  block.potato_s_t.lithium_battery_plant / tooltip.potato_s_t.lithium_battery_plant
  item.potato_s_t.lithium_battery_component
  gui.potato_s_t.lithium_battery_plant.status.{running,disabled,no_acid,inputs,output_full,empty}

插在第一条 advancements 键之前（四份文件的同一个边界）。行内插入，不做整份重排（§4.76）。
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LANG = os.path.join(r"E:\PotatoST", r"src\main\resources\assets\potato_s_t\lang")
FILES = ["zh_cn.json", "en_us.json", "ja_jp.json", "ru_ru.json"]
EXPECT_BEFORE = 408
KEYS = ["block.potato_s_t.lithium_battery_plant",
        "tooltip.potato_s_t.lithium_battery_plant",
        "item.potato_s_t.lithium_battery_component",
        "gui.potato_s_t.lithium_battery_plant.status.running",
        "gui.potato_s_t.lithium_battery_plant.status.disabled",
        "gui.potato_s_t.lithium_battery_plant.status.no_acid",
        "gui.potato_s_t.lithium_battery_plant.status.inputs",
        "gui.potato_s_t.lithium_battery_plant.status.output_full",
        "gui.potato_s_t.lithium_battery_plant.status.empty"]

TEXT = {
    "zh_cn.json": [
        u"锂电池构造间",
        u"四样原料，每个槽认「或」：粗锰/粗铝 · 镍锭/粗镍 · 碳酸锂 · 钴锭/粗钴。\n"
        u"通入硫酸：每 tick 10 mB，一炉 30 秒一共 6000 mB（罐 2000 mB，接管道或泵持续供酸）。\n"
        u"30 秒产出一件「锂电池原件」；四样原料在最后一 tick 才各扣 1 个。\n"
        u"⚠ 这台机器不耗电 —— 它靠的是化学，不是电费。有红石信号即停机（进度保留）。",
        u"锂电池原件",
        u"正在构造锂电池",
        u"已停机（红石信号）",
        u"硫酸不够：每 tick 要 10 mB（一炉 6000 mB）",
        u"四样原料不齐：粗锰/粗铝 · 镍锭/粗镍 · 碳酸锂 · 钴锭/粗钴",
        u"输出槽放不下了",
        u"还没开工",
    ],
    "en_us.json": [
        u"Lithium Battery Plant",
        u"Four inputs, each slot takes an either/or: raw manganese/raw aluminium, nickel ingot/raw "
        u"nickel, lithium carbonate, cobalt ingot/raw cobalt.\n"
        u"Sulfuric acid: 10 mB per tick, so 6000 mB for one 30-second batch (the tank holds 2000 mB; "
        u"keep it fed with pipes or a pump).\n"
        u"One batch produces a single Lithium Battery Component; the four inputs are consumed on the "
        u"last tick only.\n"
        u"⚠ This machine uses no power at all - it is chemistry, not electricity. A redstone signal "
        u"stops it (progress is kept).",
        u"Lithium Battery Component",
        u"Building a lithium battery",
        u"Stopped (redstone signal)",
        u"Not enough sulfuric acid: 10 mB per tick (6000 mB per batch)",
        u"Missing inputs: raw manganese/raw aluminium, nickel/raw nickel, lithium carbonate, "
        u"cobalt/raw cobalt",
        u"The output slot is full",
        u"Idle",
    ],
    "ja_jp.json": [
        u"リチウム電池工房",
        u"原料は 4 つ、各スロットは「または」：粗マンガン/粗アルミ · ニッケルインゴット/粗ニッケル · "
        u"炭酸リチウム · コバルトインゴット/粗コバルト。\n"
        u"硫酸を通す：毎 tick 10 mB、1 バッチ 30 秒で合計 6000 mB（タンクは 2000 mB、"
        u"パイプかポンプで供給し続けてください）。\n"
        u"30 秒で「リチウム電池部品」を 1 つ生産；4 つの原料は最後の tick にまとめて 1 つずつ消費されます。\n"
        u"⚠ この機械は電力を消費しません — 化学反応で動きます。レッドストーン信号で停止（進捗は保持）。",
        u"リチウム電池部品",
        u"リチウム電池を製造中",
        u"停止中（レッドストーン信号）",
        u"硫酸が足りません：毎 tick 10 mB（1 バッチ 6000 mB）",
        u"原料不足：粗マンガン/粗アルミ · ニッケル/粗ニッケル · 炭酸リチウム · コバルト/粗コバルト",
        u"出力スロットが満杯です",
        u"待機中",
    ],
    "ru_ru.json": [
        u"Цех литиевых батарей",
        u"Четыре входа, каждый слот принимает «или»: сырой марганец/сырой алюминий, "
        u"никелевый слиток/сырой никель, карбонат лития, кобальтовый слиток/сырой кобальт.\n"
        u"Серная кислота: 10 mB за тик, то есть 6000 mB на партию в 30 секунд (бак на 2000 mB; "
        u"подавайте трубами или насосом).\n"
        u"За партию выходит один компонент литиевой батареи; четыре входа списываются "
        u"только на последнем тике.\n"
        u"⚠ Машина не потребляет энергию — здесь работает химия, а не электричество. "
        u"Сигнал редстоуна останавливает её (прогресс сохраняется).",
        u"Компонент литиевой батареи",
        u"Идёт сборка литиевой батареи",
        u"Остановлено (сигнал редстоуна)",
        u"Не хватает серной кислоты: 10 mB за тик (6000 mB на партию)",
        u"Не хватает сырья: сырой марганец/алюминий, никель/сырой никель, карбонат лития, "
        u"кобальт/сырой кобальт",
        u"Выходной слот заполнен",
        u"Простой",
    ],
}

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
    return cond


def main():
    write = "--write" in sys.argv
    order_ref = None
    for name in FILES:
        path = os.path.join(LANG, name)
        raw = io.open(path, encoding="utf-8", newline="").read()
        check(not raw.startswith(u"\ufeff"), u"%s：有 BOM" % name)
        check("\r" not in raw, u"%s：有 CR" % name)
        before = json.loads(raw)
        check(len(before) == EXPECT_BEFORE,
              u"%s：改前键数 %d ≠ %d" % (name, len(before), EXPECT_BEFORE))
        for k in KEYS:
            check(k not in before, u"%s：键 %s 已经存在" % (name, k))
        lines = raw.split("\n")
        anchor = None
        for i, line in enumerate(lines):
            if line.lstrip().startswith(u"\"advancements."):
                anchor = i
                break
        if not check(anchor is not None, u"%s：找不到 advancements 边界" % name):
            continue
        new_lines = []
        for key, value in zip(KEYS, TEXT[name]):
            check(u"\"" not in value, u"%s：%s 的值里有 ASCII 双引号" % (name, key))
            new_lines.append(u"    \"%s\":  %s," % (key, json.dumps(value, ensure_ascii=False)))
        out = u"\n".join(lines[:anchor] + new_lines + lines[anchor:])
        after = json.loads(out)
        check(len(after) == EXPECT_BEFORE + len(KEYS),
              u"%s：改后键数 %d" % (name, len(after)))
        if order_ref is None:
            order_ref = list(after)
        else:
            check(list(after) == order_ref, u"%s：键序与第一份不一致" % name)
        for k, v in before.items():
            check(k in after and after[k] == v, u"%s：动了别的键 %s" % (name, k))
        print(u"%-12s %d → %d 键（插在第 %d 行前）" % (name, len(before), len(after), anchor + 1))
        if write:
            io.open(path, "w", encoding="utf-8", newline="\n").write(out)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    if not fails and not write:
        print(u"（体检通过；加 --write 才真写）")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
