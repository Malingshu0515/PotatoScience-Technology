# -*- coding: utf-8 -*-
u"""_zf82_lang.py —— ZF82 往四份 lang 里加 13 个键（2 个桶 + 2 个液体方块 + 换流器 + 7 条状态）

键位插在柏油块那两行之后（不整份重写，免得搅乱别人手写的顺序）。
自检：四份键数一致、键集合一致、占位符签名一致、无 BOM、行尾不变。
"""
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
LANGS = ["zh_cn", "en_us", "ja_jp", "ru_ru"]
ANCHOR = u'"item.potato_s_t.bitumen"'
EXPECT_NEW = 13

NEW = [
    (u"item.potato_s_t.diesel_bucket", {
        u"zh_cn": u"柴油桶",
        u"en_us": u"Diesel Bucket",
        u"ja_jp": u"ディーゼル入りバケツ",
        u"ru_ru": u"Ведро дизеля",
    }),
    (u"item.potato_s_t.gasoline_bucket", {
        u"zh_cn": u"汽油桶",
        u"en_us": u"Gasoline Bucket",
        u"ja_jp": u"ガソリン入りバケツ",
        u"ru_ru": u"Ведро бензина",
    }),
    (u"block.potato_s_t.diesel", {
        u"zh_cn": u"柴油",
        u"en_us": u"Diesel",
        u"ja_jp": u"ディーゼル",
        u"ru_ru": u"Дизель",
    }),
    (u"block.potato_s_t.gasoline", {
        u"zh_cn": u"汽油",
        u"en_us": u"Gasoline",
        u"ja_jp": u"ガソリン",
        u"ru_ru": u"Бензин",
    }),
    (u"block.potato_s_t.fluid_exchanger", {
        u"zh_cn": u"容器换流器",
        u"en_us": u"Container Fluid Exchanger",
        u"ja_jp": u"容器換装器",
        u"ru_ru": u"Обменник жидкостей",
    }),
    (u"tooltip.potato_s_t.fluid_exchanger", {
        u"zh_cn": u"左槽：装了流体的油桶 / 高压气罐；右槽：刚好 1 个空桶\n"
                  u"3 秒取出 1000 mB，把空桶变成那种流体的桶（水→水桶、柴油→柴油桶；"
                  u"别的 mod 的流体也行，前提是它有自己的桶）\n"
                  u"没有桶形式的流体（原油 / 石脑油 / 液化石油气）会被拒绝\n"
                  u"气体（高压气罐）接流体泵从本机抽：泵抽的就是左槽那件容器里的流体，有多少抽多少",
        u"en_us": u"Left slot: an oil bucket / gas tank with fluid in it. Right slot: exactly 1 empty bucket\n"
                  u"After 3 s it takes 1000 mB out and turns that empty bucket into the bucket of that fluid "
                  u"(water -> water bucket, diesel -> diesel bucket; fluids from other mods work too, as long "
                  u"as they have a bucket of their own)\n"
                  u"Fluids without a bucket form (crude oil / naphtha / LPG) are refused\n"
                  u"For gases (gas tank) hook a fluid pump to this block: the pump drains the container in the "
                  u"left slot directly, as much as there is",
        u"ja_jp": u"左スロット：流体入りの油バケツ / 高圧ガスタンク。右スロット：空のバケツちょうど1個\n"
                  u"3秒で 1000 mB を取り出し、その空バケツをその流体のバケツに変えます"
                  u"（水→水入りバケツ、ディーゼル→ディーゼル入りバケツ。他の MOD の流体も、"
                  u"その流体専用のバケツがあれば可）\n"
                  u"バケツの形がない流体（原油 / ナフサ / LPG）は拒否されます\n"
                  u"気体（高圧ガスタンク）は流体ポンプを本機に接続してください："
                  u"ポンプは左スロットの容器から直接汲み出します（ある分だけ）",
        u"ru_ru": u"Левый слот: нефтяное ведро / газовый баллон с жидкостью. Правый слот: ровно 1 пустое ведро\n"
                  u"Через 3 с забирается 1000 mB, и пустое ведро становится ведром этой жидкости "
                  u"(вода → ведро воды, дизель → ведро дизеля; жидкости других модов тоже, "
                  u"если у них есть собственное ведро)\n"
                  u"Жидкости без формы ведра (нефть / нафта / СНГ) отклоняются\n"
                  u"Для газов (газовый баллон) подключите жидкостный насос: насос качает напрямую "
                  u"из контейнера в левом слоте, сколько есть",
    }),
    (u"gui.potato_s_t.fluid_exchanger.status.empty", {
        u"zh_cn": u"[容器换流器] 左槽空着（或容器里没流体）",
        u"en_us": u"[Fluid Exchanger] Left slot is empty (or the container holds nothing)",
        u"ja_jp": u"[容器換装器] 左スロットが空です（または容器が空です）",
        u"ru_ru": u"[Обменник жидкостей] Левый слот пуст (или контейнер пуст)",
    }),
    (u"gui.potato_s_t.fluid_exchanger.status.invalid", {
        u"zh_cn": u"[容器换流器] 左槽那件东西不是流体容器 —— 放油桶或高压气罐",
        u"en_us": u"[Fluid Exchanger] The left slot does not hold a fluid container - use an oil bucket or a gas tank",
        u"ja_jp": u"[容器換装器] 左スロットは流体容器ではありません — 油バケツかガスタンクを入れてください",
        u"ru_ru": u"[Обменник жидкостей] В левом слоте не контейнер для жидкости — нужен нефтяное ведро или газовый баллон",
    }),
    (u"gui.potato_s_t.fluid_exchanger.status.output_full", {
        u"zh_cn": u"[容器换流器] 右槽要放「刚好 1 个」空桶 —— 桶会原地变成那种流体的桶",
        u"en_us": u"[Fluid Exchanger] The right slot needs exactly 1 empty bucket - it turns into that fluid's bucket in place",
        u"ja_jp": u"[容器換装器] 右スロットには空のバケツを「ちょうど1個」— その場でその流体のバケツに変わります",
        u"ru_ru": u"[Обменник жидкостей] В правом слоте нужно ровно 1 пустое ведро — оно на месте станет ведром этой жидкости",
    }),
    (u"gui.potato_s_t.fluid_exchanger.status.running", {
        u"zh_cn": u"[容器换流器] 正在换装（3 秒 / 1000 mB）",
        u"en_us": u"[Fluid Exchanger] Exchanging (3 s / 1000 mB)",
        u"ja_jp": u"[容器換装器] 換装中（3秒 / 1000 mB）",
        u"ru_ru": u"[Обменник жидкостей] Идёт обмен (3 с / 1000 mB)",
    }),
    (u"gui.potato_s_t.fluid_exchanger.status.material", {
        u"zh_cn": u"[容器换流器] 左槽的液体不到 1000 mB —— 够一次就自动开工（进度保留）",
        u"en_us": u"[Fluid Exchanger] Less than 1000 mB in the left container - it resumes as soon as there is enough",
        u"ja_jp": u"[容器換装器] 左スロットの液体が 1000 mB 未満です — 足り次第そのまま再開します",
        u"ru_ru": u"[Обменник жидкостей] В левом слоте меньше 1000 mB — работа продолжится, как только хватит",
    }),
    (u"gui.potato_s_t.fluid_exchanger.status.no_bucket", {
        u"zh_cn": u"[容器换流器] 这种流体没有对应的桶（原油 / 石脑油 / 液化石油气只能装在油桶里）",
        u"en_us": u"[Fluid Exchanger] This fluid has no bucket form (crude oil / naphtha / LPG live only in oil buckets)",
        u"ja_jp": u"[容器換装器] この流体にはバケツがありません（原油 / ナフサ / LPG は油バケツのみ）",
        u"ru_ru": u"[Обменник жидкостей] У этой жидкости нет ведра (нефть / нафта / СНГ живут только в нефтяном ведре)",
    }),
    (u"gui.potato_s_t.fluid_exchanger.status.gas", {
        u"zh_cn": u"[容器换流器] 左槽是气体 —— 界面不做气体，请接流体泵抽走",
        u"en_us": u"[Fluid Exchanger] The left slot holds a gas - the GUI does not handle gases, hook up a fluid pump",
        u"ja_jp": u"[容器換装器] 左スロットは気体です — 界面では扱いません。流体ポンプを接続してください",
        u"ru_ru": u"[Обменник жидкостей] В левом слоте газ — интерфейс газы не обрабатывает, подключите насос",
    }),
]

fails = []


def sig(value):
    return u"|".join(u"%" + c for c in re.findall(r"%([sdif%])", value))


def main():
    counts = {}
    for lang in LANGS:
        p = os.path.join(LANG, lang + u".json")
        raw = io.open(p, "rb").read()
        if raw[:3] == b"\xef\xbb\xbf":
            fails.append(u"%s 带 BOM" % lang)
        obj = json.loads(raw.decode(u"utf-8"))
        counts[lang] = len(obj)
    print(u"改前键数：" + u", ".join(u"%s=%d" % (l, counts[l]) for l in LANGS))

    for lang in LANGS:
        p = os.path.join(LANG, lang + u".json")
        text = io.open(p, "rb").read().decode(u"utf-8")
        lines = text.split(u"\n")
        idx = None
        for i, line in enumerate(lines):
            if ANCHOR in line:
                idx = i
                break
        if idx is None:
            fails.append(u"%s 找不到锚点 %s" % (lang, ANCHOR))
            continue
        indent = re.match(r"^\s*", lines[idx]).group(0)
        eol = u"\r" if lines[idx].endswith(u"\r") else u""
        added = []
        for key, values in NEW:
            esc = values[lang].replace(u"\\", u"\\\\").replace(u'"', u'\\"').replace(u"\n", u"\\n")
            added.append(u"%s\"%s\":  \"%s\",%s" % (indent, key, esc, eol))
        lines[idx + 1:idx + 1] = added
        with io.open(p, "w", encoding="utf-8", newline=u"") as fh:
            fh.write(u"\n".join(lines))

    after = {}
    for lang in LANGS:
        p = os.path.join(LANG, lang + u".json")
        obj = json.loads(io.open(p, "rb").read().decode(u"utf-8"))
        after[lang] = obj
        if len(obj) != counts[lang] + EXPECT_NEW:
            fails.append(u"%s 键数 %d ≠ %d + %d" % (lang, len(obj), counts[lang], EXPECT_NEW))
    base = set(after[LANGS[0]].keys())
    for lang in LANGS[1:]:
        if set(after[lang].keys()) != base:
            fails.append(u"%s 键集合与 zh_cn 不一致" % lang)
    for key, _ in NEW:
        if key not in base:
            fails.append(u"缺键：%s" % key)
            continue
        sigs = set(sig(after[lang][key]) for lang in LANGS)
        if len(sigs) != 1:
            fails.append(u"%s 四份占位符签名不一致：%s" % (key, sigs))
        # 多行文案：json.loads 之后应当都是**真的换行**，且四份行数一致
        # （第一版这条断言写错了：拿字符串 "\\n" 去比，永远假，白报一条 FAIL）
        nl = [after[lang][key].count(u"\n") for lang in LANGS]
        if len(set(nl)) != 1:
            fails.append(u"%s 四份换行数不一致：%s" % (key, nl))
    print(u"改后键数：" + u", ".join(u"%s=%d" % (l, len(after[l])) for l in LANGS))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
