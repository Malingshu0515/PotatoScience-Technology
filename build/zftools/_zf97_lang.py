# -*- coding: utf-8 -*-
u"""_zf97_lang.py —— ZF97 给四份语言各加 **19 个键**（284 → 303）

做法照 ZF96 那套（**先探测格式、先解析、过了才落盘** —— §4.64 那两条规矩就是上轮立的）：

  ① 逐份探测"有没有结尾换行"（四份**不一致**，别假设）
  ② 只在文件末尾加行；最后一行**不带逗号**，上一行末尾补逗号
  ③ 先在内存里 `json.loads`，过了才写盘；写完再读回来核（键集合 / 旧键的值 / 结尾换行）
  ④ 幂等：已经加过就跳过

新增的 19 个键：
  fluid_type.potato_s_t.nitrogen / .ammonia                  ← 两种新流体
  block.potato_s_t.air_separator / .ammonia_synthesis_chamber ← 两台新机器
  tooltip.potato_s_t.air_separator / .ammonia_synthesis_chamber
  gui.potato_s_t.air_separator.status.{running,disabled,no_power,output_full}
  gui.potato_s_t.ammonia_synthesis.status.{running,disabled,no_power,output_full,
                                          no_hydrogen,no_nitrogen,no_catalyst}
  gui.potato_s_t.ammonia_synthesis.catalyst                   ← 用户点名要在槽位上标的字
  gui.potato_s_t.jei.catalyst
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
LANG_DIR = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
EXPECT_BEFORE = 284
EXPECT_AFTER = 303

KEYS = [
    "fluid_type.potato_s_t.nitrogen",
    "fluid_type.potato_s_t.ammonia",
    "block.potato_s_t.air_separator",
    "block.potato_s_t.ammonia_synthesis_chamber",
    "tooltip.potato_s_t.air_separator",
    "tooltip.potato_s_t.ammonia_synthesis_chamber",
    "gui.potato_s_t.air_separator.status.running",
    "gui.potato_s_t.air_separator.status.disabled",
    "gui.potato_s_t.air_separator.status.no_power",
    "gui.potato_s_t.air_separator.status.output_full",
    "gui.potato_s_t.ammonia_synthesis.status.running",
    "gui.potato_s_t.ammonia_synthesis.status.disabled",
    "gui.potato_s_t.ammonia_synthesis.status.no_power",
    "gui.potato_s_t.ammonia_synthesis.status.output_full",
    "gui.potato_s_t.ammonia_synthesis.status.no_hydrogen",
    "gui.potato_s_t.ammonia_synthesis.status.no_nitrogen",
    "gui.potato_s_t.ammonia_synthesis.status.no_catalyst",
    "gui.potato_s_t.ammonia_synthesis.catalyst",
    "gui.potato_s_t.jei.catalyst",
]

TEXT = {
    "zh_cn": [
        u"氮气",
        u"氨气",
        u"空气分离器",
        u"氨气组成室",
        (u"每 30 秒：8 mB 氮气 + 2 mB 氧气（原料就是空气）\n"
         u"耗电 200 FE/t，储能 5000 FE\n"
         u"两个储罐只出不进：管道/泵能抽走，但灌不进去（也不能手倒）\n"
         u"有红石信号即停机（进度保留）"),
        (u"每 tick：1 mB 氮气 + 1 mB 氢气 + 200 FE → 1 mB 氨气\n"
         u"催化剂槽要放铁粉（不消耗）；原料罐下方的气罐槽按 50 mB/t 把气罐里的氮/氢灌进机器\n"
         u"输出罐下方的气罐槽是反向的：50 mB/t 把氨气灌进气罐\n"
         u"泵只能泵入氮气/氢气、泵出氨气；有红石信号即停机"),
        u"正在分离空气",
        u"已停机（红石信号）",
        u"电力不足：每 tick 要 200 FE",
        u"储罐满了（氮气或氧气装不下这一批），等泵抽走",
        u"正在合成氨气",
        u"已停机（红石信号）",
        u"电力不足：每 tick 要 200 FE",
        u"氨气罐满了，等泵抽走或换气罐",
        u"氢气不足（原料罐空了：接泵或用气罐槽补）",
        u"氮气不足（原料罐空了：接泵或用气罐槽补）",
        u"催化剂槽里要放铁粉（不消耗）",
        u"催化剂(铁粉)",
        u"需要铁粉作催化剂（不消耗）",
    ],
    "en_us": [
        u"Nitrogen",
        u"Ammonia",
        u"Air Separator",
        u"Ammonia Synthesis Chamber",
        (u"Per 30 s: 8 mB nitrogen + 2 mB oxygen (the raw material is air)\n"
         u"200 FE/t, 5,000 FE buffer\n"
         u"The two tanks are output-only: pumps can drain them, but nothing can be poured or piped in\n"
         u"A redstone signal stops it (progress is kept)"),
        (u"Per tick: 1 mB nitrogen + 1 mB hydrogen + 200 FE -> 1 mB ammonia\n"
         u"The catalyst slot needs iron dust (it is NOT consumed); the gas-tank slot under each input "
         u"tank moves 50 mB/t from the tank item into the machine\n"
         u"The gas-tank slot under the output tank works the other way: 50 mB/t of ammonia into the tank item\n"
         u"Pipes can only push nitrogen/hydrogen in and pull ammonia out; a redstone signal stops it"),
        u"Separating air",
        u"Stopped (redstone signal)",
        u"Not enough power: 200 FE per tick",
        u"A tank is full (no room for the next batch) - pump it out",
        u"Synthesising ammonia",
        u"Stopped (redstone signal)",
        u"Not enough power: 200 FE per tick",
        u"The ammonia tank is full - pump it out or swap the gas tank",
        u"Not enough hydrogen (input tank empty: use pipes or the gas-tank slot)",
        u"Not enough nitrogen (input tank empty: use pipes or the gas-tank slot)",
        u"Put iron dust in the catalyst slot (it is not consumed)",
        u"Catalyst (Iron Dust)",
        u"Needs iron dust as the catalyst (it is not consumed)",
    ],
    "ja_jp": [
        u"窒素",
        u"アンモニア",
        u"空気分離器",
        u"アンモニア合成室",
        (u"30 秒ごと：窒素 8 mB + 酸素 2 mB（原料は空気）\n"
         u"200 FE/t、蓄電 5000 FE\n"
         u"2 つのタンクは出すだけ：ポンプで抜けますが、注ぐことも配管で入れることもできません\n"
         u"レッドストーン信号で停止（進捗は保持）"),
        (u"毎 tick：窒素 1 mB + 水素 1 mB + 200 FE → アンモニア 1 mB\n"
         u"触媒スロットには鉄粉が必要（消費されません）。原料タンク下のガスタンクスロットは 50 mB/t でタンクから機械へ\n"
         u"出力タンク下のガスタンクスロットは逆方向：アンモニアを 50 mB/t でタンクへ\n"
         u"ポンプは窒素／水素の注入とアンモニアの排出のみ。レッドストーン信号で停止"),
        u"空気を分離中",
        u"停止中（レッドストーン信号）",
        u"電力不足：毎 tick 200 FE",
        u"タンクが満杯です（次のバッチが入りません）—— ポンプで抜いてください",
        u"アンモニア合成中",
        u"停止中（レッドストーン信号）",
        u"電力不足：毎 tick 200 FE",
        u"アンモニアタンクが満杯です —— ポンプで抜くかガスタンクを交換してください",
        u"水素不足（原料タンクが空です：配管かガスタンクスロットで補給）",
        u"窒素不足（原料タンクが空です：配管かガスタンクスロットで補給）",
        u"触媒スロットに鉄粉を入れてください（消費されません）",
        u"触媒（鉄粉）",
        u"触媒として鉄粉が必要です（消費されません）",
    ],
    "ru_ru": [
        u"Азот",
        u"Аммиак",
        u"Разделитель воздуха",
        u"Камера синтеза аммиака",
        (u"Каждые 30 с: 8 mB азота + 2 mB кислорода (сырьё — воздух)\n"
         u"200 FE/т, буфер 5000 FE\n"
         u"Оба бака работают только на выход: насос может их откачать, но залить или подать "
         u"трубами ничего нельзя\n"
         u"Сигнал редстоуна останавливает (прогресс сохраняется)"),
        (u"За тик: 1 mB азота + 1 mB водорода + 200 FE → 1 mB аммиака\n"
         u"В слот катализатора нужен железный порошок (НЕ расходуется); слот баллона под каждым "
         u"входным баком перекачивает 50 mB/т из баллона в машину\n"
         u"Слот баллона под выходным баком работает наоборот: 50 mB/т аммиака в баллон\n"
         u"Насосы могут только подавать азот/водород и откачивать аммиак; сигнал редстоуна останавливает"),
        u"Разделение воздуха",
        u"Остановлено (сигнал редстоуна)",
        u"Недостаточно энергии: 200 FE за тик",
        u"Бак полон (новая партия не влезает) — откачайте насосом",
        u"Синтез аммиака",
        u"Остановлено (сигнал редстоуна)",
        u"Недостаточно энергии: 200 FE за тик",
        u"Бак аммиака полон — откачайте насосом или замените баллон",
        u"Недостаточно водорода (входной бак пуст: трубы или слот баллона)",
        u"Недостаточно азота (входной бак пуст: трубы или слот баллона)",
        u"Положите железный порошок в слот катализатора (он не расходуется)",
        u"Катализатор (железный порошок)",
        u"Нужен железный порошок как катализатор (не расходуется)",
    ],
}

fails = []
examined = 0


def check(ok, msg):
    global examined
    examined += 1
    print((u"  [OK]   " if ok else u"  [FAIL] ") + msg)
    if not ok:
        fails.append(msg)


def line_for(key, value):
    return u'    "%s":  %s,' % (key, json.dumps(value, ensure_ascii=False))


def main():
    for name in (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"):
        fails_before = len(fails)
        path = os.path.join(LANG_DIR, name + u".json")
        raw = io.open(path, encoding="utf-8", newline=u"").read()
        before = json.loads(raw)
        if len(before) == EXPECT_AFTER and all(k in before for k in KEYS):
            print(u"  [SKIP] %s：已经是 %d 键（本轮加过了）" % (name, EXPECT_AFTER))
            continue
        check(len(before) == EXPECT_BEFORE,
              u"%s：改前 %d 键（期望 %d）" % (name, len(before), EXPECT_BEFORE))
        dup = [k for k in KEYS if k in before]
        check(not dup, u"%s：19 个新键一个都还没存在（重复的 %d 个）" % (name, len(dup)))
        if len(before) != EXPECT_BEFORE or dup:
            continue

        had_nl = raw.endswith(u"\n")
        body = raw[:-1] if had_nl else raw
        lines = body.split(u"\n")
        check(lines[-1] == u"}", u"%s：末行是右花括号" % name)
        check(True, u"%s：原文%s结尾换行（按原样写回）" % (name, u"有" if had_nl else u"没有"))
        check(not lines[-2].rstrip().endswith(u","), u"%s：最后一个键那一行原本没有逗号" % name)
        lines[-2] = lines[-2].rstrip() + u","

        new_lines = [line_for(k, v) for (k, v) in zip(KEYS, TEXT[name])]
        new_lines[-1] = new_lines[-1][:-1]          # 最后一行不能带逗号
        out = lines[:-1] + new_lines + lines[-1:]
        text = u"\n".join(out) + (u"\n" if had_nl else u"")

        after = json.loads(text)                     # ⚠ 先解析、过了才落盘（§4.64）
        check(len(after) == EXPECT_AFTER, u"%s：新文本 %d 键（期望 %d）" % (name, len(after), EXPECT_AFTER))
        check(set(after) == set(before) | set(KEYS), u"%s：键集合 = 旧 + 19 个新键" % name)
        unchanged = [k for k in before if after.get(k) != before[k]]
        check(not unchanged, u"%s：旧键的值逐个不变（变了 %d 个）" % (name, len(unchanged)))
        if len(fails) != fails_before:
            check(False, u"%s：新文本有问题 ⇒ **不落盘**" % name)
            continue

        io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)
        back = json.loads(io.open(path, encoding="utf-8").read())
        check(back == after, u"%s：落盘后重新读回与写前一致（%d 键）" % (name, len(back)))
        check(io.open(path, encoding="utf-8", newline=u"").read().endswith(u"\n") == had_nl,
              u"%s：落盘后结尾换行与原文一致" % name)
        check(u"\\n" in text, u"%s：tooltip 的换行在文件里是反斜杠 + n" % name)

        old_lines = body.split(u"\n")
        kept = out[:len(out) - 1 - len(new_lines)] + out[len(out) - 1:]
        diff = [(i, a, b) for (i, (a, b)) in enumerate(zip(old_lines, kept)) if a != b]
        check(len(old_lines) == len(kept) and len(diff) == 1 and diff[0][0] == len(old_lines) - 2,
              u"%s：原文 %d 行里只有「最后一个键那行补逗号」一处变化（实际 %d 处）"
              % (name, len(old_lines), len(diff)))

    print()
    print(u"检查项 = %d" % examined)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"   - " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
