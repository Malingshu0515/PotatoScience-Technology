# -*- coding: utf-8 -*-
u"""_zf115_lang.py —— 锂电池构造间介绍里的三个数字跟着砍到十分之一（0.11 ZF115）

只改**值**（键一个都不动，键数仍 417）：`tooltip.potato_s_t.lithium_battery_plant` 整条换新，
四语言一起。⚠ 顺带修一处旧账：ja/ru 那份当时只把"罐 2000"留在了原地（ZF112 只补了 zh/en）。
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
KEY = u"tooltip.potato_s_t.lithium_battery_plant"
EXPECT_KEYS = 417

TEXT = {
    "zh_cn.json": u"四样原料，每个槽认「或」：粗锰/粗铝 · 镍锭/粗镍 · 碳酸锂 · 钴锭/粗钴。\n"
                  u"通入硫酸：每 tick 1 mB，一炉 30 秒一共 600 mB（罐 800 mB，装满一罐够跑完一炉）。\n"
                  u"30 秒产出一件「锂电池原件」；四样原料在最后一 tick 才各扣 1 个。\n"
                  u"⚠ 这台机器不耗电 —— 它靠的是化学，不是电费。有红石信号即停机（进度保留）。",
    "en_us.json": u"Four inputs, each slot takes an either/or: raw manganese/raw aluminium, nickel "
                  u"ingot/raw nickel, lithium carbonate, cobalt ingot/raw cobalt.\n"
                  u"Sulfuric acid: 1 mB per tick, so 600 mB for one 30-second batch (the tank holds "
                  u"800 mB, enough for a whole batch).\n"
                  u"One batch produces a single Lithium Battery Component; the four inputs are "
                  u"consumed on the last tick only.\n"
                  u"⚠ This machine uses no power at all - it is chemistry, not electricity. "
                  u"A redstone signal stops it (progress is kept).",
    "ja_jp.json": u"原料は 4 つ、各スロットは「または」：粗マンガン/粗アルミ · ニッケルインゴット/"
                  u"粗ニッケル · 炭酸リチウム · コバルトインゴット/粗コバルト。\n"
                  u"硫酸を通す：毎 tick 1 mB、1 バッチ 30 秒で合計 600 mB"
                  u"（タンクは 800 mB、満タンで 1 バッチぶん足ります）。\n"
                  u"30 秒で「リチウム電池部品」を 1 つ生産；4 つの原料は最後の tick にまとめて "
                  u"1 つずつ消費されます。\n"
                  u"⚠ この機械は電力を消費しません — 化学反応で動きます。"
                  u"レッドストーン信号で停止（進捗は保持）。",
    "ru_ru.json": u"Четыре входа, каждый слот принимает «или»: сырой марганец/сырой алюминий, "
                  u"никелевый слиток/сырой никель, карбонат лития, кобальтовый слиток/сырой кобальт.\n"
                  u"Серная кислота: 1 mB за тик, то есть 600 mB на партию в 30 секунд "
                  u"(бак на 800 mB — полного хватает на целую партию).\n"
                  u"За партию выходит один компонент литиевой батареи; четыре входа списываются "
                  u"только на последнем тике.\n"
                  u"⚠ Машина не потребляет энергию — здесь работает химия, а не электричество. "
                  u"Сигнал редстоуна останавливает её (прогресс сохраняется).",
}

fails = []


def main():
    write = "--write" in sys.argv
    for name in FILES:
        path = os.path.join(LANG, name)
        raw = io.open(path, encoding="utf-8", newline="").read()
        before = json.loads(raw)
        if len(before) != EXPECT_KEYS:
            fails.append(u"%s：键数 %d ≠ %d" % (name, len(before), EXPECT_KEYS))
            continue
        lines = raw.split(u"\n")
        hit = 0
        out = []
        for line in lines:
            if line.strip().startswith(u"\"" + KEY + u"\""):
                out.append(u"    \"%s\":  %s," % (KEY, json.dumps(TEXT[name], ensure_ascii=False)))
                hit += 1
                continue
            out.append(line)
        if hit != 1:
            fails.append(u"%s：%s 命中 %d 次" % (name, KEY, hit))
            continue
        new_raw = u"\n".join(out)
        after = json.loads(new_raw)
        if len(after) != EXPECT_KEYS:
            fails.append(u"%s：改后键数 %d" % (name, len(after)))
        if list(after) != list(before):
            fails.append(u"%s：键序被动了" % name)
        for k, v in before.items():
            if k != KEY and after[k] != v:
                fails.append(u"%s：动了别的键 %s" % (name, k))
        tip = after[KEY]
        for num in (u"1 mB", u"600 mB", u"800 mB"):
            if num not in tip:
                fails.append(u"%s：新介绍里缺 %s" % (name, num))
        if u"6000" in tip or u"8000" in tip or u"10 mB" in tip:
            fails.append(u"%s：旧数字还在" % name)
        print(u"%-12s 介绍换新（%d → %d 字）" % (name, len(before[KEY]), len(tip)))
        if write:
            io.open(path, "w", encoding="utf-8", newline="\n").write(new_raw)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    if not fails and not write:
        print(u"（体检通过；加 --write 才真写）")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
