#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
_zf159_lang.py —— ZF159 多燃料：把柴油发电机那两句**已经过时的文案**改准。

⚠ 只改**值**，一个键都不加、不删 ⇒ 语言键数（594 / lzh 596）**一个都不动**，
   所以那 17 份写死键数的常驻门**都不用跟**。要加新键留给润色线。

改哪两句（都是**现在会让玩家理解错**的）：
  ① tooltip.potato_s_t.diesel_generator_controller
     里面「…每 tick 烧 1 mB 柴油发 7200 FE…」只对柴油成立；
  ② gui.potato_s_t.diesel_generator.pour.rejected
     「这台机器只烧柴油」现在会**骗玩家**（汽油/石脑油/液化气都能烧）。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠⚠ 这条门为什么必须拿**整行原文**当钥匙（第一版的血）：

  第一版按"行首 == 界面："定位，替换完只检查"新文案在不在"，**没有校验被替换的那一行
  到底是不是旧文案**。于是第二次跑的时候，它匹配到的正是自己上一次写进去的新行，
  把新文案**又插了一遍** —— 五份 lang 里「烧什么、发多少」那行变成了两行。
  更糟的是"幂等分支"也写错了判据（只看新首行在不在），所以第二次跑照样报"跳过"、
  看上去一切正常，**盘上已经坏了**（档案 §4.96 那一族：判据写错 ⇒ 假绿）。

  ⇒ 现在的规矩：**每一份语言都必须给出要替换的那一行"逐字原文"**（{@code OLD_LINE}）。
      · 命中 OLD_LINE  ⇒ 这才是"还没改"，替换之；
      · 命中 NEW_LINE  ⇒ 这才是"已经改过"，跳过；
      · 命中别的/命中多处 ⇒ **报红**，绝不猜（半成品要人看）。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

跑法：
    python build\\zftools\\_zf159_lang.py --dry     # 只看会改什么
    python build\\zftools\\_zf159_lang.py           # 真改（备份到 build\\zftools\\_zf159_lang_backup\\）
"""

import io
import json
import os
import shutil
import sys

ROOT = r"E:\PotatoST"
LANG = r"E:\PotatoST\build\zftools\_zf159_falsify\lang"
BACKUP = r"E:\PotatoST\build\zftools\_zf159_falsify\backup"

KEY_TOOLTIP = "tooltip.potato_s_t.diesel_generator_controller"
KEY_REJECT = "gui.potato_s_t.diesel_generator.pour.rejected"

# 每份语言：OLD_LINE = **从 git HEAD 抄下来的那一行逐字原文**（拿它当钥匙，安全）
#            NEW_LINE = 换上去的新文案（两行：界面那句 + "烧什么、发多少"那句）
#            REJECT   = pour.rejected 的新值
PLAN = {
    "zh_cn.json": (
        u"界面：一个 8000 mB 柴油罐 ＋ 一盏工作指示灯；每 tick 烧 1 mB 柴油发 7200 FE，有红石信号即停机。",
        u"界面：一个 8000 mB 燃油罐 ＋ 一盏工作指示灯；每 tick 烧 1 mB 燃料，有红石信号即停机。"
        u"\n烧什么、发多少：柴油 7200 FE/t（沉浸原油的柴油 / 含硫柴油、沉浸工程的生物柴油 / 高能生物柴油也认）、"
        u"汽油 6120、石脑油 5400、液化石油气 4320 —— 按通用标签 "
        u"c:diesel / c:biodiesel / c:high_power_biodiesel / c:gasoline / c:naphtha / c:lpg 判定。",
        u"倒不进去：%s（这台机器只烧柴油、汽油、石脑油或液化石油气）",
    ),
    "en_us.json": (
        u"GUI: an 8000 mB diesel tank and a status lamp; 1 mB of diesel per tick makes 7200 FE; "
        u"a redstone signal halts it.",
        u"GUI: an 8000 mB fuel tank and a status lamp; 1 mB of fuel per tick; a redstone signal halts it."
        u"\nFuels and output: diesel 7200 FE/t (Immersive Petroleum's diesel / sour diesel and "
        u"Immersive Engineering's biodiesel / high-power biodiesel count too), gasoline 6120, "
        u"naphtha 5400, LPG 4320 - matched through the common tags "
        u"c:diesel / c:biodiesel / c:high_power_biodiesel / c:gasoline / c:naphtha / c:lpg.",
        u"Cannot pour in: %s (this machine only burns diesel, gasoline, naphtha or LPG)",
    ),
    "ja_jp.json": (
        u"界面：8000 mB のディーゼルタンク ＋ 動作ランプ。毎 tick ディーゼル 1 mB を燃やして 7200 FE を発電、"
        u"レッドストーン信号で停止します。",
        u"界面：8000 mB の燃料タンク ＋ 動作ランプ。毎 tick 燃料 1 mB を燃やし、レッドストーン信号で停止します。"
        u"\n燃料と発電量：軽油 7200 FE/t（Immersive Petroleum の軽油 / 含硫軽油、Immersive Engineering の"
        u"バイオディーゼル / 高効率バイオディーゼルも可）、ガソリン 6120、ナフサ 5400、LPG 4320 —— 共通タグ "
        u"c:diesel / c:biodiesel / c:high_power_biodiesel / c:gasoline / c:naphtha / c:lpg で判定。",
        u"注げません：%s（この機械は軽油・ガソリン・ナフサ・LPG のみ）",
    ),
    "ru_ru.json": (
        u"Интерфейс: бак дизеля на 8000 mB и лампа работы; 1 mB дизеля за тик даёт 7200 FE; "
        u"сигнал редстоуна останавливает.",
        u"Интерфейс: бак топлива на 8000 mB и лампа работы; 1 mB топлива за тик; сигнал редстоуна останавливает."
        u"\nТопливо и выработка: дизель 7200 FE/т (дизель / сернистый дизель Immersive Petroleum и "
        u"биодизель / высокоэнергетический биодизель Immersive Engineering тоже подходят), бензин 6120, "
        u"нафта 5400, сжиженный газ 4320 — по общим тегам "
        u"c:diesel / c:biodiesel / c:high_power_biodiesel / c:gasoline / c:naphtha / c:lpg.",
        u"Не залить: %s (эта машина работает только на дизеле, бензине, нафте или сжиженном газе)",
    ),
    "lzh.json": (
        u"界面：一 8000 mB 柴油罐 ＋ 一盞作工之燈；每 tick 焚 1 mB 柴油發 7200 FE，有紅石信號即停機。",
        u"界面：一 8000 mB 燃油罐 ＋ 一盞作工之燈；每 tick 焚 1 mB 燃料，有紅石信號即停機。"
        u"\n所焚與所發：柴油 7200 FE/t（沉浸原油之柴油 / 含硫柴油、沉浸工程之生物柴油 / 高能生物柴油亦認）、"
        u"汽油 6120、石腦油 5400、液化石油氣 4320 —— 依通用標籤 "
        u"c:diesel / c:biodiesel / c:high_power_biodiesel / c:gasoline / c:naphtha / c:lpg 判定。",
        u"倒之不入：%s（此機只焚柴油、汽油、石腦油或液化石油氣）",
    ),
}

dry = "--dry" in sys.argv
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

problems = []
notes = []

for fname in sorted(PLAN.keys()):
    path = os.path.join(LANG, fname)
    raw = io.open(path, "rb").read()
    data = json.loads(raw.decode("utf-8"))
    old_line, new_line, new_reject = PLAN[fname]
    new_lines_full = new_line.split("\n")

    before_keys = len(data)
    tooltip = data.get(KEY_TOOLTIP)
    if tooltip is None or KEY_REJECT not in data:
        problems.append("%s：找不到那两个键之一" % fname)
        continue

    lines = tooltip.split("\n")
    hits_old = [i for i, ln in enumerate(lines) if ln == old_line]
    hits_new = [i for i, ln in enumerate(lines) if ln == new_lines_full[0]]

    # ---- 已经改过？（三个条件全中才算完成，半成品一律报红）----
    if len(hits_new) == 1:
        i = hits_new[0]
        tail_ok = lines[i + 1:i + len(new_lines_full)] == new_lines_full[1:]
        reject_ok = data[KEY_REJECT] == new_reject
        if tail_ok and reject_ok:
            notes.append("%s：已经改过（第 %d 行起两行 + pour.rejected，键数 %d）—— 跳过"
                         % (fname, i, before_keys))
            continue
        problems.append("%s：**半成品**（新首行在、但尾部/ reject 对不上）—— 请人工核对" % fname)
        continue

    # ---- 还没改？（必须**正好一处**命中旧文案原文）----
    if len(hits_old) != 1:
        problems.append("%s：按逐字原文命中旧文案 %d 处（必须正好 1 处）—— 别猜，人工看"
                        % (fname, len(hits_old)))
        continue
    idx = hits_old[0]

    lines = lines[:idx] + new_lines_full + lines[idx + 1:]
    data[KEY_TOOLTIP] = "\n".join(lines)
    data[KEY_REJECT] = new_reject

    if len(data) != before_keys:
        problems.append("%s：键数变了（%d -> %d）—— 本轮不许动键数" % (fname, before_keys, len(data)))
        continue

    if dry:
        notes.append("%s：[dry] 第 %d 行（旧 1 行 -> 新 %d 行）+ pour.rejected 会被换掉（键数仍 %d）"
                     % (fname, idx, len(new_lines_full), before_keys))
        continue

    os.makedirs(BACKUP, exist_ok=True)
    shutil.copyfile(path, os.path.join(BACKUP, fname + ".before"))
    io.open(path, "w", encoding="utf-8", newline="\n").write(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    # ---- 回读核对：前缀/后缀逐字未动、目标处恰是新文案、键数不变、无 BOM/CR ----
    again = json.loads(io.open(path, encoding="utf-8").read())
    if len(again) != before_keys:
        problems.append("%s：回读键数不符" % fname)
        continue
    nl = again[KEY_TOOLTIP].split("\n")
    if nl[:idx] != lines[:idx]:
        problems.append("%s：目标行之前的行被动过" % fname)
        continue
    if nl[idx:idx + len(new_lines_full)] != new_lines_full:
        problems.append("%s：目标处不是预期的新文案" % fname)
        continue
    if nl[idx + len(new_lines_full):] != lines[idx + len(new_lines_full):]:
        problems.append("%s：新文案之后的尾巴对不上" % fname)
        continue
    if again[KEY_REJECT] != new_reject:
        problems.append("%s：pour.rejected 没写对" % fname)
        continue
    b = io.open(path, "rb").read()
    if b.startswith(b"\xef\xbb\xbf") or b"\r" in b:
        problems.append("%s：写出了 BOM 或 CR（违反 §4.8）" % fname)
        continue
    notes.append("%s：第 %d 行已换（1 -> %d 行）+ pour.rejected；键数仍 %d；前后文逐字未动；无 BOM / 纯 LF"
                 % (fname, idx, len(new_lines_full), before_keys))

print("\n".join(notes) if notes else "(没有改动)")
print("")
if problems:
    print("失败 %d 项：" % len(problems))
    for p in problems:
        print("  [FAIL] " + p)
    sys.exit(1)
print("结论：5 份语言各改 2 个值，键数一个没动" + ("（--dry 模式，什么都没写）" if dry else ""))
sys.exit(0)
