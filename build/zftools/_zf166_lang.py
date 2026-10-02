# -*- coding: utf-8 -*-
u"""_zf166_lang.py —— ZF166「流体转化器」的 12 个语言键 × 5 份 lang（只加键，不删不改别的）。

插在**同一个锚点键之后**（五份都用 `block.potato_s_t.fluid_exchanger`，它在五份里都在），
这样相对顺序一致；键数预计 **593 → 605**、lzh **595 → 607**。

跑法：python build\\zftools\\_zf166_lang.py [--write]
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
LANGDIR = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]
ANCHOR = u"block.potato_s_t.fluid_exchanger"

K = [u"block.potato_s_t.fluid_converter",
     u"tooltip.potato_s_t.fluid_converter",
     u"gui.potato_s_t.fluid_converter.tank.input",
     u"gui.potato_s_t.fluid_converter.tank.output",
     u"gui.potato_s_t.fluid_converter.status.input_empty",
     u"gui.potato_s_t.fluid_converter.status.target_empty",
     u"gui.potato_s_t.fluid_converter.status.same_fluid",
     u"gui.potato_s_t.fluid_converter.status.no_shared_tag",
     u"gui.potato_s_t.fluid_converter.status.output_full",
     u"gui.potato_s_t.fluid_converter.status.no_power",
     u"gui.potato_s_t.fluid_converter.status.running",
     u"gui.potato_s_t.fluid_converter.status.idle"]

V = {
    u"zh_cn": [
        u"流体转化器",
        u"把输入罐里的流体按「同名 c: 标签」1:1 转成输出罐里那一种（输出罐里先放一点目标流体当样板）。"
        u"50 mB/t、30 FE/t，两罐各 5000 mB，储能 2000 FE。\\n空手潜行右键 = 逐条诊断；"
        u"管子接到两个罐上就能进出。",
        u"输入",
        u"输出（样板）",
        u"[流体转化器] 输入罐是空的——没有东西可转",
        u"[流体转化器] 输出罐是空的——先往输出罐里放一点目标流体当样板（管道或手倒都行）",
        u"[流体转化器] 两边是同一种流体——不用转",
        u"[流体转化器] 这两种流体没有共同的 c: 标签（输入 %s / 样板 %s）——只按同名标签转",
        u"[流体转化器] 输出罐满了",
        u"[流体转化器] 缺电——每 tick 要 %s FE，机器里只有 %s FE",
        u"[流体转化器] 正在转：%s → %s（%s mB/t）",
        u"[流体转化器] 待机",
    ],
    u"en_us": [
        u"Fluid Converter",
        u"Converts the fluid in the input tank 1:1 into the fluid already sitting in the output tank "
        u"(that fluid is the sample / target), as long as the two share a c: tag. 50 mB/t, 30 FE/t, "
        u"5,000 mB per tank, 2,000 FE buffer.\\nSneak-right-click with an empty hand for a per-line "
        u"diagnosis; pipes connect to both tanks.",
        u"Input",
        u"Output (sample)",
        u"[Fluid Converter] the input tank is empty - nothing to convert",
        u"[Fluid Converter] the output tank is empty - put a little of the target fluid in it first "
        u"(that fluid is the sample)",
        u"[Fluid Converter] both tanks hold the same fluid - nothing to convert",
        u"[Fluid Converter] these two fluids share no c: tag (input %s / sample %s) - only same-tag "
        u"fluids are converted",
        u"[Fluid Converter] the output tank is full",
        u"[Fluid Converter] no power - %s FE per tick is needed, the machine has %s FE",
        u"[Fluid Converter] converting: %s -> %s (%s mB/t)",
        u"[Fluid Converter] idle",
    ],
    u"ja_jp": [
        u"流体変換器",
        u"入力タンクの流体を、出力タンクに入っている流体（それが見本）へ 1:1 で変換します"
        u"（同じ c: タグを持つ場合のみ）。50 mB/t、30 FE/t、各タンク 5,000 mB、蓄電 2,000 FE。\\n"
        u"素手でスニーク右クリック = 項目ごとの診断。配管は両方のタンクに接続できます。",
        u"入力",
        u"出力（見本）",
        u"[流体変換器] 入力タンクが空です——変換するものがありません",
        u"[流体変換器] 出力タンクが空です——先に目標の流体を少し入れてください（それが見本になります）",
        u"[流体変換器] 両方とも同じ流体です——変換の必要がありません",
        u"[流体変換器] この二つの流体に共通の c: タグがありません（入力 %s / 見本 %s）",
        u"[流体変換器] 出力タンクが満杯です",
        u"[流体変換器] 電力不足——1 tick に %s FE 必要、機械には %s FE しかありません",
        u"[流体変換器] 変換中：%s → %s（%s mB/t）",
        u"[流体変換器] 待機中",
    ],
    u"ru_ru": [
        u"Конвертер жидкостей",
        u"Преобразует жидкость во входном баке 1:1 в жидкость, уже находящуюся в выходном баке "
        u"(она служит образцом), если у них есть общий тег c:. 50 mB/т, 30 FE/т, по 5 000 mB на бак, "
        u"буфер 2 000 FE.\\nПриседая и щёлкнув пустой рукой, вы увидите построчную диагностику; "
        u"трубы подключаются к обоим бакам.",
        u"Вход",
        u"Выход (образец)",
        u"[Конвертер жидкостей] входной бак пуст — преобразовывать нечего",
        u"[Конвертер жидкостей] выходной бак пуст — сначала налейте немного нужной жидкости "
        u"(она станет образцом)",
        u"[Конвертер жидкостей] в обоих баках одна и та же жидкость — преобразование не нужно",
        u"[Конвертер жидкостей] у этих жидкостей нет общего тега c: (вход %s / образец %s)",
        u"[Конвертер жидкостей] выходной бак полон",
        u"[Конвертер жидкостей] не хватает энергии — нужно %s FE за тик, в машине только %s FE",
        u"[Конвертер жидкостей] преобразование: %s → %s (%s mB/т)",
        u"[Конвертер жидкостей] ожидание",
    ],
    u"lzh": [
        u"流體轉化器",
        u"以輸入罐之流體，依同名 c: 標籤，一比一化為輸出罐中者（輸出罐中先置少許目標流體以為樣本）。"
        u"每秒五十毫、每刻三十 FE，兩罐各五千毫，儲能二千 FE。\\n空手潛行右擊＝逐條診斷；"
        u"管接兩罐即可出入。",
        u"輸入",
        u"輸出（樣本）",
        u"[流體轉化器] 輸入罐空——無可轉者",
        u"[流體轉化器] 輸出罐空——請先置少許目標流體以為樣本",
        u"[流體轉化器] 兩罐同流——無須轉",
        u"[流體轉化器] 二者無共通之 c: 標籤（輸入 %s ／ 樣本 %s）",
        u"[流體轉化器] 輸出罐已滿",
        u"[流體轉化器] 乏電——每刻需 %s FE，器中僅有 %s FE",
        u"[流體轉化器] 方轉：%s → %s（每秒 %s 毫）",
        u"[流體轉化器] 待機",
    ],
}


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def main(argv):
    write = u"--write" in argv
    fails, notes = [], []
    after = {}
    for loc in LOCALES:
        p = os.path.join(LANGDIR, loc + u".json")
        text = read(p)
        eol = u"\r\n" if u"\r\n" in text else u"\n"
        trailing = text.endswith(u"\n")
        before = json.loads(text)
        lines = text.split(eol)
        idx, ind = -1, u"  "
        for i, ln in enumerate(lines):
            s = ln.strip()
            if s.startswith(u'"%s"' % ANCHOR):
                idx, ind = i, ln[:len(ln) - len(ln.lstrip())]
                break
        if idx < 0:
            fails.append(u"%s：找不到锚点 %s" % (loc, ANCHOR))
            continue
        if any(k in before for k in K):
            notes.append(u"%s：（已加过，跳过）" % loc)
            after[loc] = before
            continue
        vals = V[loc]
        if len(vals) != len(K):
            fails.append(u"%s：值个数 %d ≠ 键个数 %d" % (loc, len(vals), len(K)))
            continue
        new_lines = [ind + u'"%s": %s,' % (k, json.dumps(v, ensure_ascii=False))
                     for k, v in zip(K, vals)]
        out = lines[:idx + 1] + new_lines + lines[idx + 1:]
        new_text = eol.join(out)
        if trailing and not new_text.endswith(eol):
            new_text += eol
        try:
            parsed = json.loads(new_text)
        except Exception as exc:      # noqa: BLE001
            fails.append(u"%s：改完解析失败 %s" % (loc, exc))
            continue
        if len(parsed) != len(before) + len(K):
            fails.append(u"%s：键数 %d -> %d（应为 +%d）" % (loc, len(before), len(parsed), len(K)))
            continue
        if [k for k in parsed if k not in before] != K:
            fails.append(u"%s：新增键的顺序/集合不对" % loc)
            continue
        after[loc] = parsed
        notes.append(u"%s：%d -> %d 键" % (loc, len(before), len(parsed)))
        if write:
            io.open(p, "w", encoding="utf-8", newline=u"").write(new_text)
    # 五语键集合一致性（lzh 允许多 language.name/region）
    if len(after) == 5:
        ref = set(after[u"zh_cn"])
        for loc in LOCALES[1:]:
            got = set(after[loc]) - {u"language.name", u"language.region"}
            if got != ref:
                fails.append(u"%s：键集合与 zh_cn 不一致（多 %s / 少 %s）"
                             % (loc, sorted(got - ref)[:3], sorted(ref - got)[:3]))
    print(u"模式：%s" % (u"落盘" if write else u"干跑（不写）"))
    for n in notes:
        print(u"  " + n)
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
