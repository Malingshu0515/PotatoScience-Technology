# -*- coding: utf-8 -*-
u"""_zf167_lang.py —— 本轮的五语言键（0.13 ZF167），13 个键 × 5 份

    item.potato_s_t.empty_aluminum_can / item.potato_s_t.cola          两个物品名
    tooltip.potato_s_t.cola.1 / .2                                     可乐的两行说明
    block.potato_s_t.beverage_canning_machine                          机器名
    tooltip.potato_s_t.beverage_canning_machine                        机器说明（Shift）
    gui.potato_s_t.beverage_canning_machine.status.{disabled,empty,invalid,no_power,
                                                    output_full,running,no_fluid}   七种状态

纪律（与 ZF153 那份同一套）：
  ① **先证明写回器与盘上格式逐字节一致**（parse→dump 比一遍），再动手插键；
  ② 插键位置照现有**分组**（物品名跟物品名、状态跟状态），插在锚点**之后**；
  ③ 键集合五份必须一致（zh/en/ja/ru 四份 + lzh；lzh 另有 language.name/region 两键）；
  ④ 中文串里**不许出现 ASCII 双引号**（用「」）—— 这个坑本会话踩过 9 次。

跑法：python build\\zftools\\_zf167_lang.py
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
CODES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]

AFTER_ITEM = u"item.potato_s_t.vibranium_sword"
AFTER_BLOCK = u"block.potato_s_t.micro_crusher"
AFTER_TOOLTIP = u"tooltip.potato_s_t.filling_machine"
AFTER_STATUS = u"gui.potato_s_t.micro_crusher.status.running"

ITEM_KEYS = [u"item.potato_s_t.empty_aluminum_can", u"item.potato_s_t.cola",
             u"tooltip.potato_s_t.cola.1", u"tooltip.potato_s_t.cola.2"]
BLOCK_KEYS = [u"block.potato_s_t.beverage_canning_machine"]
TIP_KEYS = [u"tooltip.potato_s_t.beverage_canning_machine",
            u"gui.potato_s_t.canning.pour.poured", u"gui.potato_s_t.canning.pour.rejected"]
STATUS_KEYS = [u"gui.potato_s_t.beverage_canning_machine.status."
               + s for s in (u"disabled", u"empty", u"invalid", u"no_power",
                             u"output_full", u"running", u"no_fluid")]

VALUES = {
    u"zh_cn": {
        ITEM_KEYS[0]: u"空铝罐",
        ITEM_KEYS[1]: u"可乐",
        ITEM_KEYS[2]: u"食物。急迫 120 秒、生命恢复 I 3 秒，恢复 3 点饥饿值与 9 点饱和度",
        ITEM_KEYS[3]: u"喝完把空铝罐还给你（原版容器返还那套）",
        BLOCK_KEYS[0]: u"饮料罐装机",
        TIP_KEYS[0]: u"三只罐：碳酸 100 mB / 水 1000 mB / 乙醇 100 mB（乙醇收 c:乙醇 标签，兼容别的模组）。"
                     u"三个输入槽：糖 / 可可豆 / 空铝罐；600 FE/t，5 秒出一罐可乐。\n"
                     u"手拿桶或气罐右键 = 往罐里倒；空手右键 = 打开界面。",
        TIP_KEYS[1]: u"倒进%s：%s mB",
        TIP_KEYS[2]: u"这三只罐都不收%s",
        STATUS_KEYS[0]: u"已关闭：检测到红石信号",
        STATUS_KEYS[1]: u"待机：三个输入槽是空的",
        STATUS_KEYS[2]: u"配方无效：这三个槽的组合没有配方",
        STATUS_KEYS[3]: u"电力不足：它需要持续供电",
        STATUS_KEYS[4]: u"输出槽满了，等腾位置",
        STATUS_KEYS[5]: u"正在罐装",
        STATUS_KEYS[6]: u"流体不够：看看碳酸罐、水罐和乙醇罐",
    },
    u"en_us": {
        ITEM_KEYS[0]: u"Empty Aluminum Can",
        ITEM_KEYS[1]: u"Cola",
        ITEM_KEYS[2]: u"Food. Haste for 120 s and Regeneration I for 3 s; restores 3 hunger and 9 saturation",
        ITEM_KEYS[3]: u"The empty can comes back to you when you finish it",
        BLOCK_KEYS[0]: u"Beverage Canning Machine",
        TIP_KEYS[0]: u"Three tanks: carbonic acid 100 mB / water 1000 mB / ethanol 100 mB "
                     u"(the ethanol tank takes the c:ethanol tag, so other mods' ethanol works). "
                     u"Three input slots: sugar / cocoa beans / empty can; 600 FE/t, one cola every 5 s.\n"
                     u"Right-click with a bucket or gas tank to pour; right-click empty-handed to open the GUI.",
        TIP_KEYS[1]: u"Poured %2$s mB of %1$s",
        TIP_KEYS[2]: u"None of the three tanks takes %s",
        STATUS_KEYS[0]: u"Off: redstone signal detected",
        STATUS_KEYS[1]: u"Idle: the three input slots are empty",
        STATUS_KEYS[2]: u"No recipe for this combination of the three slots",
        STATUS_KEYS[3]: u"Not enough power: it needs a steady supply",
        STATUS_KEYS[4]: u"Output slot is full - waiting for room",
        STATUS_KEYS[5]: u"Canning",
        STATUS_KEYS[6]: u"Not enough fluid: check the carbonic acid, water and ethanol tanks",
    },
    u"ja_jp": {
        ITEM_KEYS[0]: u"空のアルミ缶",
        ITEM_KEYS[1]: u"コーラ",
        ITEM_KEYS[2]: u"食べ物。120 秒の衝撃吸収（採掘速度上昇）と 3 秒の再生 I、"
                     u"満腹度 3・隠し満腹度 9 を回復",
        ITEM_KEYS[3]: u"飲み終わると空のアルミ缶が戻ってくる",
        BLOCK_KEYS[0]: u"飲料缶詰機",
        TIP_KEYS[0]: u"タンク三本：炭酸 100 mB ／ 水 1000 mB ／ エタノール 100 mB"
                     u"（エタノールは c:ethanol タグなので他 MOD のものでも入る）。"
                     u"入力スロット三つ：砂糖 ／ カカオ豆 ／ 空のアルミ缶。600 FE/t、5 秒でコーラ 1 本。\n"
                     u"バケツやガスタンクを持って右クリックで注入、素手で右クリックで GUI。",
        TIP_KEYS[1]: u"%1$s を %2$s mB 注ぎました",
        TIP_KEYS[2]: u"三本のタンクはどれも %s を受け付けません",
        STATUS_KEYS[0]: u"停止中：レッドストーン信号を検出",
        STATUS_KEYS[1]: u"待機中：入力スロットが空です",
        STATUS_KEYS[2]: u"この三つのスロットの組み合わせにレシピがありません",
        STATUS_KEYS[3]: u"電力不足：継続的な供給が必要です",
        STATUS_KEYS[4]: u"出力スロットが満杯です",
        STATUS_KEYS[5]: u"缶詰中",
        STATUS_KEYS[6]: u"流体不足：炭酸・水・エタノールのタンクを確認してください",
    },
    u"ru_ru": {
        ITEM_KEYS[0]: u"Пустая алюминиевая банка",
        ITEM_KEYS[1]: u"Кола",
        ITEM_KEYS[2]: u"Еда. Спешка на 120 с и Регенерация I на 3 с; "
                     u"восстанавливает 3 голода и 9 насыщения",
        ITEM_KEYS[3]: u"Допив, вы получаете пустую банку обратно",
        BLOCK_KEYS[0]: u"Машина для розлива напитков",
        TIP_KEYS[0]: u"Три бака: угольная кислота 100 mB / вода 1000 mB / этанол 100 mB "
                     u"(бак этанола принимает тег c:ethanol, так что подходит этанол других модов). "
                     u"Три входных слота: сахар / какао-бобы / пустая банка; 600 FE/t, "
                     u"одна кола за 5 с.\n"
                     u"ПКМ ведром или газовым баллоном — налить; ПКМ пустой рукой — открыть интерфейс.",
        TIP_KEYS[1]: u"Налито %2$s mB: %1$s",
        TIP_KEYS[2]: u"Ни один из трёх баков не принимает %s",
        STATUS_KEYS[0]: u"Выключено: обнаружен сигнал редстоуна",
        STATUS_KEYS[1]: u"Простой: три входных слота пусты",
        STATUS_KEYS[2]: u"Для такого набора в трёх слотах рецепта нет",
        STATUS_KEYS[3]: u"Не хватает энергии: нужно постоянное питание",
        STATUS_KEYS[4]: u"Выходной слот заполнен — ждём место",
        STATUS_KEYS[5]: u"Идёт розлив",
        STATUS_KEYS[6]: u"Не хватает жидкости: проверьте баки кислоты, воды и этанола",
    },
    u"lzh": {
        ITEM_KEYS[0]: u"空鋁罐",
        ITEM_KEYS[1]: u"可樂",
        ITEM_KEYS[2]: u"食也。急迫百二十秒、生命復原一三秒，復三點饑、九點飽",
        ITEM_KEYS[3]: u"飲盡則空罐歸汝",
        BLOCK_KEYS[0]: u"飲料罐裝機",
        TIP_KEYS[0]: u"三罐：碳酸百 mB ／ 水千 mB ／ 乙醇百 mB（乙醇收 c:ethanol 標籤，兼容他模）。"
                     u"三輸入槽：糖 ／ 可可豆 ／ 空鋁罐。六百 FE 每刻，五秒成一罐可樂。\n"
                     u"手持桶或氣罐右鍵則注之；空手右鍵則啟其界面。",
        TIP_KEYS[1]: u"注 %s 者 %s mB",
        TIP_KEYS[2]: u"三罐皆不受 %s",
        STATUS_KEYS[0]: u"已止：見紅石之訊",
        STATUS_KEYS[1]: u"待機：三輸入槽皆空",
        STATUS_KEYS[2]: u"三槽之合無方",
        STATUS_KEYS[3]: u"電力不足：須持續供之",
        STATUS_KEYS[4]: u"輸出槽已滿，待其位",
        STATUS_KEYS[5]: u"方罐裝之",
        STATUS_KEYS[6]: u"流體不足：觀碳酸、水、乙醇三罐",
    },
}

GROUPS = [(AFTER_ITEM, ITEM_KEYS), (AFTER_BLOCK, BLOCK_KEYS),
          (AFTER_TOOLTIP, TIP_KEYS), (AFTER_STATUS, STATUS_KEYS)]

fails, notes = [], []


def check(label, ok, detail=u""):
    print(u"  [%s] %s%s" % (u"OK" if ok else u"!!", label, (u"   " + detail) if detail else u""))
    if not ok:
        fails.append(label)
    return ok


def load(code):
    p = os.path.join(LANG, code + u".json")
    raw = io.open(p, encoding="utf-8").read()
    return p, raw, json.loads(raw)


def dump(d):
    return json.dumps(d, ensure_ascii=False, indent=2) + u"\n"


def insert_after(d, anchor, keys, vals):
    ks = list(d.keys())
    if anchor not in ks:
        raise KeyError(anchor)
    i = ks.index(anchor) + 1
    out = {}
    for k in ks[:i]:
        out[k] = d[k]
    for k in keys:
        out[k] = vals[k]
    for k in ks[i:]:
        out[k] = d[k]
    return out


def main():
    print(u"① 写回器自检（parse→dump 与盘上逐字节比）")
    for code in CODES:
        _p, raw, d = load(code)
        if dump(d) == raw:
            print(u"      %-6s %5d 键  逐字节一致" % (code, len(d)))
        else:
            check(u"%s 的排版/转义写回后变了" % code, False)

    print(u"\n② 插键（五份各 +%d）" % (len(ITEM_KEYS) + len(BLOCK_KEYS) + len(TIP_KEYS) + len(STATUS_KEYS)))
    total = len(ITEM_KEYS) + len(BLOCK_KEYS) + len(TIP_KEYS) + len(STATUS_KEYS)
    for code in CODES:
        p, _raw, d = load(code)
        before = len(d)
        vals = VALUES[code]
        check(u"%s 的 %d 条文案齐全" % (code, total), all(k in vals for k in
                                                        ITEM_KEYS + BLOCK_KEYS + TIP_KEYS + STATUS_KEYS))
        allkeys = ITEM_KEYS + BLOCK_KEYS + TIP_KEYS + STATUS_KEYS
        if all(d.get(k) == vals[k] for k in allkeys):
            notes.append(u"%s 已是目标状态（幂等重跑）" % code)
            continue
        stale = [k for k in allkeys if k in d and d[k] != vals[k]]
        if stale:
            check(u"%s 里这些键已存在且值不同（拒绝覆盖）：%s" % (code, stale[:2]), False)
            continue
        new = d
        for anchor, keys in GROUPS:
            new = insert_after(new, anchor, keys, vals)
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(dump(new))
        back = json.loads(io.open(p, encoding="utf-8").read())
        # ⚠ 期望键数要按"**这次真的缺几个**"算，不能一律 before + total：
        #   补第二次（比如后来又加了 hand-pour 那两条键）时，前 13 个已经在盘上了
        #   ⇒ 写死 total 会当场假红（本轮踩到）。
        missing_before = len([k for k in allkeys if k not in d])
        check(u"%s：%d → %d 键（本次新增 %d）" % (code, before, len(back), missing_before),
              len(back) == before + missing_before)
        check(u"%s 回读：%d 条键值全对" % (code, total),
              all(back.get(k) == vals[k] for k in allkeys))

    print(u"\n③ 键集合一致性")
    tables = {}
    for code in CODES:
        tables[code] = json.loads(io.open(os.path.join(LANG, code + u".json"),
                                          encoding="utf-8").read())
    four = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]
    check(u"zh/en/ja/ru 四份键集合完全相同",
          len(set(frozenset(tables[c]) for c in four)) == 1,
          u" / ".join(u"%s %d" % (c, len(tables[c])) for c in CODES))
    check(u"lzh 与四份的差集恰好是 language.name / language.region",
          set(tables[u"lzh"]) - set(tables[u"zh_cn"]) == {u"language.name", u"language.region"})
    # ⚠ 键数是**活体数字**：本轮开工时四语言是 605（不是 ZF153 那轮的 587 —— 期间别的线
    #   又加了 18 个键）。所以这里断言的是**不变式**（四份彼此相等、lzh = 四份 + 2），
    #   不是某个写死的数；具体数字打出来给"跟平"用（第一版写死 587 当场假红）。
    check(u"四份键数彼此相等（各 %d）" % len(tables[u"zh_cn"]),
          len(set(len(tables[c]) for c in four)) == 1,
          str({c: len(tables[c]) for c in four}))
    check(u"lzh = 四份 + 2（language.name / language.region）",
          len(tables[u"lzh"]) == len(tables[u"zh_cn"]) + 2, str(len(tables[u"lzh"])))

    print(u"\n④ 五份的这批键都不是空串 + 中文串里没有 ASCII 双引号")
    allkeys = ITEM_KEYS + BLOCK_KEYS + TIP_KEYS + STATUS_KEYS
    check(u"都不是空串", all(tables[c].get(k) for c in CODES for k in allkeys))
    bad = [(c, k) for c in CODES for k in allkeys if u'"' in tables[c].get(k, u"")]
    check(u"文案里没有 ASCII 双引号（一律用「」）", not bad, str(bad[:3]))

    print(u"\n⑤ 新增键的全文（zh_cn）")
    for k in allkeys:
        print(u"      %-64s %s" % (k, tables[u"zh_cn"][k][:70]))

    print(u"\n备注：")
    for n in notes:
        print(u"  - " + n)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
