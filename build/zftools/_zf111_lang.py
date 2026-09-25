# -*- coding: utf-8 -*-
u"""_zf111_lang.py —— ZF111：合金炉那两句话改「值」（**不增删键**）

改两个键的**值**（四语言）：
  · `gui.potato_s_t.alloy_smelter.consume_slot`：消耗槽「暂未开放」→ 现在放配方点名要消耗的东西
  · `tooltip.potato_s_t.alloy_smelter` 的**最后一行**（脚注）→ 写明消耗槽的用处 + 三条配方
    ⚠ 只换最后一行：前面那些是**摆放图**，`_zf52/_zf55/_zf57_verify.py` 逐格在比；
      而且 `_zf55_verify.py` 还盯着「≤20 行」「含 32768」两条，所以**行数不变**。

⚠ 因为**一个键都没加/删**，键数仍是 **408** ⇒ §4 那张"17 份校验器"的表一份都不用动。
本脚本自己会核对：键集合、键数、顺序、其它键的值逐字未变、JSON 仍可解析、无 CR。
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
EXPECT_KEYS = 408

KEY_CONSUME = u"gui.potato_s_t.alloy_smelter.consume_slot"
KEY_TIP = u"tooltip.potato_s_t.alloy_smelter"

CONSUME = {
    "zh_cn.json": u"消耗槽（放配方点名要消耗的东西）",
    "en_us.json": u"Consumption slot (takes the recipe's consumables)",
    "ja_jp.json": u"消費スロット（レシピ指定の消耗品）",
    "ru_ru.json": u"Расходный слот (для расходников рецепта)",
}

FOOT = {
    "zh_cn.json": u"5 输入槽只收锭、3 输出槽、2 消耗槽（放配方点名要消耗的东西）；"
                  u"储能 32768 FE，电只从接线口进。配方三条：轻质钛合金 / 硬质钛合金 / "
                  u"星璨钢锭（下界合金+4 高碳钢+钴+银+铜，另耗 1 深层钴矿石 + 1 末影水晶，12000 FE/t）。",
    "en_us.json": u"5 input slots that take ingots only, 3 output slots, 2 consumption slots "
                  u"(they take whatever a recipe names as its consumable); 32768 FE of storage, "
                  u"and power comes in through the port alone. Three recipes: Light Titanium Alloy / "
                  u"Hard Titanium Alloy / Star Steel Ingot (netherite + 4 high carbon steel + cobalt "
                  u"+ silver + copper, plus 1 deepslate cobalt ore and 1 end crystal, 12000 FE/t).",
    "ja_jp.json": u"入力 5（インゴットのみ）/ 出力 3 / 消費 2（レシピが指定した消耗品を入れる）；"
                  u"蓄電 32768 FE、電力は接続口からのみ。レシピ 3 種：軽質チタン合金 / 硬質チタン合金 / "
                  u"星璨鋼インゴット（ネザライト+高炭素鋼×4+コバルト+銀+銅、さらに深層コバルト鉱石 1 "
                  u"+ エンドクリスタル 1、12000 FE/t）。",
    "ru_ru.json": u"5 входных слотов только под слитки, 3 выходных, 2 расходных (туда кладётся то, "
                  u"что рецепт называет расходником); буфер 32768 FE, энергия только через порт. "
                  u"Три рецепта: лёгкий титановый сплав / твёрдый титановый сплав / слиток звёздной "
                  u"стали (незерит + 4 высокоуглеродистая сталь + кобальт + серебро + медь, плюс "
                  u"1 глубинная кобальтовая руда и 1 кристалл Края, 12000 FE/t).",
}

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
    return cond


def main():
    write = "--write" in sys.argv
    for name in FILES:
        path = os.path.join(LANG, name)
        raw = io.open(path, encoding="utf-8", newline="").read()
        before = json.loads(raw)
        check(len(before) == EXPECT_KEYS, u"%s：键数 %d ≠ %d" % (name, len(before), EXPECT_KEYS))
        check(KEY_CONSUME in before and KEY_TIP in before, u"%s：缺键" % name)

        lines = raw.split(u"\n")
        new_consume = CONSUME[name]
        tip = before[KEY_TIP]
        parts = tip.split(u"\n")
        check(len(parts) >= 2, u"%s：介绍少于 2 行，切不了脚注" % name)
        old_foot = parts[-1]
        new_tip = u"\n".join(parts[:-1] + [FOOT[name]])
        check(len(new_tip.split(u"\n")) == len(parts),
              u"%s：脚注换完行数变了（%d → %d）" % (name, len(parts), len(new_tip.split(u"\n"))))
        check(u"32768" in new_tip, u"%s：新介绍里没写 32768（_zf55 会红）" % name)
        check(u"58" in new_tip, u"%s：新介绍里没写 58（_zf55 会红）" % name)
        check(u"\"" not in new_tip and u"\"" not in new_consume,
              u"%s：新文案里有 ASCII 双引号" % name)

        out_lines, hit_c, hit_t = [], 0, 0
        for line in lines:
            s = line.strip()
            if s.startswith(u"\"" + KEY_CONSUME + u"\""):
                out_lines.append(u"    \"%s\":  %s," % (KEY_CONSUME,
                                                        json.dumps(new_consume, ensure_ascii=False)))
                hit_c += 1
                continue
            if s.startswith(u"\"" + KEY_TIP + u"\""):
                out_lines.append(u"    \"%s\":  %s," % (KEY_TIP,
                                                        json.dumps(new_tip, ensure_ascii=False)))
                hit_t += 1
                continue
            out_lines.append(line)
        check(hit_c == 1 and hit_t == 1,
              u"%s：consume_slot 命中 %d 次、tooltip 命中 %d 次（各要求 1）" % (name, hit_c, hit_t))

        out = u"\n".join(out_lines)
        after = json.loads(out)
        check(len(after) == EXPECT_KEYS, u"%s：改后键数 %d" % (name, len(after)))
        check(list(after) == list(before), u"%s：键序被动了" % name)
        for k, v in before.items():
            if k in (KEY_CONSUME, KEY_TIP):
                continue
            check(after[k] == v, u"%s：动了别的键 %s" % (name, k))
        check(after[KEY_CONSUME] == new_consume, u"%s：consume_slot 没换成新值" % name)
        check(after[KEY_TIP] == new_tip, u"%s：tooltip 没换成新值" % name)
        check(after[KEY_TIP].split(u"\n")[:-1] == parts[:-1],
              u"%s：摆放图那几行被动了（只该动脚注）" % name)
        print(u"%-12s 脚注: %s … → %s …" % (name, old_foot[:18], FOOT[name][:18]))
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
