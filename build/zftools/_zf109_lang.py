# -*- coding: utf-8 -*-
r"""_zf109_lang.py —— 采油机的四语言键（0.11 ZF109）

新增 10 个键 × 4 语言（398 → 408）：
  block.potato_s_t.oil_pump
  tooltip.potato_s_t.oil_pump
  gui.potato_s_t.oil_pump.chains
  gui.potato_s_t.oil_pump.rate
  gui.potato_s_t.oil_pump.status.{running,disabled,no_power,output_full,not_oilfield,no_chain}

⚠ 两件事必须守住：
  ① **行内插入**（不做整份 json.dumps 重排）—— 别的会话线也在改这几个文件，
     重排会把他们的行也一起弄脏（§4.76 共享树）；
  ② 插在**第一条 advancements 键之前** —— 四份文件的这个边界是同一处，
     插完四语言的键序仍然逐位相同（脚本自己会核对）。

用法：
  python build\zftools\_zf109_lang.py            # 只体检（不写盘）
  python build\zftools\_zf109_lang.py --write    # 真写
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LANGS = os.path.join(r"E:\PotatoST", r"src\main\resources\assets\potato_s_t\lang")
FILES = ["zh_cn.json", "en_us.json", "ja_jp.json", "ru_ru.json"]
EXPECT_BEFORE = 398
KEYS = ["block.potato_s_t.oil_pump",
        "tooltip.potato_s_t.oil_pump",
        "gui.potato_s_t.oil_pump.chains",
        "gui.potato_s_t.oil_pump.rate",
        "gui.potato_s_t.oil_pump.status.running",
        "gui.potato_s_t.oil_pump.status.disabled",
        "gui.potato_s_t.oil_pump.status.no_power",
        "gui.potato_s_t.oil_pump.status.output_full",
        "gui.potato_s_t.oil_pump.status.not_oilfield",
        "gui.potato_s_t.oil_pump.status.no_chain"]

TEXT = {
    "zh_cn.json": [
        u"采油机",
        u"只在海洋油田群系开工 —— 脚下不是海洋油田一律停机。\n"
        u"下方必须是水：从机器正下方一格一格往下数，数到几根含水锁链，n 就是几（最多数 64 格）。\n"
        u"耗电 8n² + 80n FE/t，产油 10n mB/s；n=10 时是 1600 FE/t、100 mB/s。\n"
        u"25B 大罐只出不进：接管道 / 流体泵能抽走，灌不进去。\n"
        u"每采出 25~80 桶，以机器为中心 10×10 个区块的海洋油田会变成旁边那种海洋"
        u"（冻洋 / 暖洋 / 温带海洋…）。\n"
        u"⚠ 那 100 个区块包含机器自己 ⇒ 抽一次之后得把机器挪到还剩油田的地方。",
        u"含水锁链：%s 根",
        u"耗电 %s FE/t · 产油 %s mB/s",
        u"正在采油",
        u"已停机（红石信号）",
        u"电力不足：每 tick 要 8n² + 80n FE（n = 下方含水锁链根数）",
        u"25B 大罐满了，等管道 / 流体泵抽走",
        u"不在海洋油田群系 —— 这台机器只在海洋油田开工",
        u"下方没有含水锁链：从机器正下方往下挂链子，而且要泡在水里",
    ],
    "en_us.json": [
        u"Oil Extractor",
        u"Only runs in the Ocean Oilfield biome - anywhere else it shuts down.\n"
        u"The column below must be water: count the waterlogged chains straight down from the "
        u"machine, and that count is n (at most 64 blocks).\n"
        u"Draws 8n² + 80n FE/t and produces 10n mB/s; at n=10 that is 1600 FE/t and 100 mB/s.\n"
        u"The 25-bucket tank is output-only: pipes and fluid pumps can drain it, nothing pours in.\n"
        u"Every 25-80 buckets pumped, the ocean oilfield in a 10x10 chunk area centred on the "
        u"machine turns into the surrounding ocean (frozen / warm / temperate ...).\n"
        u"⚠ That area includes the machine itself, so after one conversion move it to whatever "
        u"oilfield is left.",
        u"Waterlogged chains: %s",
        u"Draw %s FE/t · Output %s mB/s",
        u"Pumping oil",
        u"Stopped (redstone signal)",
        u"Not enough power: 8n² + 80n FE per tick (n = waterlogged chains below)",
        u"The 25-bucket tank is full; drain it with pipes or a fluid pump",
        u"Not in the Ocean Oilfield biome - this machine only runs there",
        u"No waterlogged chains below: hang chains straight down from the machine, under water",
    ],
    "ja_jp.json": [
        u"採油機",
        u"海洋油田バイオームでのみ稼働します — 足元が海洋油田でなければ停止します。\n"
        u"真下は水である必要があります：機械の真下から 1 マスずつ数え、含水チェーンの本数が n です"
        u"（最大 64 マス）。\n"
        u"消費電力 8n² + 80n FE/t、産油 10n mB/s（n=10 で 1600 FE/t・100 mB/s）。\n"
        u"25B タンクは出し専用：パイプ / 流体ポンプで抜けますが、注ぎ込めません。\n"
        u"25〜80 バケツ採油するごとに、機械を中心とした 10×10 チャンクの海洋油田が"
        u"周囲の海（凍った海 / 暖かい海 / 温帯の海…）に変わります。\n"
        u"⚠ その範囲には機械自身も含まれるため、1 回変換したら油田が残っている場所へ移動してください。",
        u"含水チェーン：%s 本",
        u"消費 %s FE/t · 産油 %s mB/s",
        u"採油中",
        u"停止中（レッドストーン信号）",
        u"電力不足：毎 tick 8n² + 80n FE（n = 下方の含水チェーン本数）",
        u"25B タンクが満杯です。パイプ / 流体ポンプで抜いてください",
        u"海洋油田バイオームではありません — この機械は海洋油田でのみ稼働します",
        u"下方に含水チェーンがありません：機械の真下からチェーンを吊り、水中に沈めてください",
    ],
    "ru_ru.json": [
        u"Нефтяной насос",
        u"Работает только в биоме морского нефтяного месторождения — в любом другом месте "
        u"останавливается.\n"
        u"Столб под машиной должен быть водой: считайте цепи с водой строго вниз от машины, "
        u"их число и есть n (не более 64 блоков).\n"
        u"Расход 8n² + 80n FE/т, добыча 10n mB/с; при n=10 это 1600 FE/т и 100 mB/с.\n"
        u"Бак на 25 вёдер работает только на выход: трубы и жидкостный насос его откачают, "
        u"а влить в него нельзя.\n"
        u"Каждые 25-80 вёдер добычи морское месторождение в области 10x10 чанков вокруг машины "
        u"превращается в окружающий океан (замёрзший / тёплый / умеренный ...).\n"
        u"⚠ Эта область включает саму машину, поэтому после первого превращения переставьте её "
        u"туда, где месторождение ещё осталось.",
        u"Цепей с водой: %s",
        u"Расход %s FE/t · Добыча %s mB/s",
        u"Идёт добыча нефти",
        u"Остановлено (сигнал редстоуна)",
        u"Не хватает энергии: 8n² + 80n FE за тик (n — число цепей с водой снизу)",
        u"Бак на 25 вёдер полон; откачайте трубами или жидкостным насосом",
        u"Это не биом морского нефтяного месторождения — машина работает только там",
        u"Снизу нет цепей с водой: повесьте цепи прямо под машиной, погрузив их в воду",
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
        path = os.path.join(LANGS, name)
        raw = io.open(path, "r", encoding="utf-8", newline="").read()
        check(not raw.startswith(u"\ufeff"), u"%s：有 BOM" % name)
        check("\r" not in raw, u"%s：有 CR（§4.8 要求 LF）" % name)
        before = json.loads(raw)
        check(len(before) == EXPECT_BEFORE,
              u"%s：改前键数 %d ≠ 预期 %d" % (name, len(before), EXPECT_BEFORE))
        for k in KEYS:
            check(k not in before, u"%s：键 %s 已经存在（不许插第二遍）" % (name, k))

        lines = raw.split("\n")
        anchor = None
        for i, line in enumerate(lines):
            if line.lstrip().startswith(u"\"advancements."):
                anchor = i
                break
        if not check(anchor is not None, u"%s：找不到 advancements 那一段的边界" % name):
            continue

        new_lines = []
        for key, value in zip(KEYS, TEXT[name]):
            check(u"\"" not in value, u"%s：%s 的值里有 ASCII 双引号" % (name, key))
            dumped = json.dumps(value, ensure_ascii=False)
            new_lines.append(u"    \"%s\":  %s," % (key, dumped))
        out = u"\n".join(lines[:anchor] + new_lines + lines[anchor:])

        after = json.loads(out)
        check(len(after) == EXPECT_BEFORE + len(KEYS),
              u"%s：改后键数 %d ≠ %d" % (name, len(after), EXPECT_BEFORE + len(KEYS)))
        keys_after = list(after)
        if order_ref is None:
            order_ref = keys_after
        else:
            check(keys_after == order_ref, u"%s：改后键序与第一份不一致" % name)
        # 改前那些键一个不能少、也不能改值
        for k, v in before.items():
            check(k in after and after[k] == v, u"%s：动了别的键 %s" % (name, k))
        for k in KEYS:
            check(k in after, u"%s：插完还是缺 %s" % (name, k))

        print(u"%-12s %d → %d 键，插入点 = 第 %d 行（第一条 advancements）"
              % (name, len(before), len(after), anchor + 1))
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
