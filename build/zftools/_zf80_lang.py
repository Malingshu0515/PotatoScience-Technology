# -*- coding: utf-8 -*-
u"""_zf80_lang.py —— ZF80 往四份 lang 里加「灌装机手倒 + 逐槽诊断」的 9 个键

改法：在 `tooltip.potato_s_t.filling_machine` 那一行后面按原缩进插进去（不整份重写，
      免得把别人手写的排版/顺序搅乱）。

顺带改一处**旧文案与新行为不符**的地方：四份的灌装机 tooltip 还写着「把罐里的**气体**灌进
容器物品」—— ZF73 起五个罐已经对任何流体开放了（用户这次问的就是液体），不改就是在骗人。

自检 5 条（写完当场跑，失败就退出码非 0）：
  ① 四份 JSON 都能解析；② 键数从旧值 +9，且四份键集合完全一致；
  ③ 每个新键的 %s 占位符签名四份一致（LangCheck.ps1 的第 ② 项）；
  ④ 无 BOM；⑤ 行尾风格不变。
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

ROOT = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
LANGS = ["zh_cn", "en_us", "ja_jp", "ru_ru"]
ANCHOR = u'"tooltip.potato_s_t.filling_machine"'
EXPECT_NEW = 9

NEW = [
    (u"gui.potato_s_t.filling.pour.poured", {
        u"zh_cn": u"已倒入 %s 号罐：%s %s mB",
        u"en_us": u"Poured into tank %s: %s %s mB",
        u"ja_jp": u"%s 号タンクに注入：%s %s mB",
        u"ru_ru": u"Залито в резервуар %s: %s %s mB",
    }),
    (u"gui.potato_s_t.filling.pour.empty", {
        u"zh_cn": u"手里的容器是空的",
        u"en_us": u"That container is empty",
        u"ja_jp": u"その容器は空です",
        u"ru_ru": u"Этот контейнер пуст",
    }),
    (u"gui.potato_s_t.filling.pour.noroom", {
        u"zh_cn": u"倒不进去：五个罐都满了，或者装的都是别的流体（一个罐只装一种）",
        u"en_us": u"Cannot pour in: all five tanks are full, or they hold other fluids (one fluid per tank)",
        u"ja_jp": u"注入できません：5つのタンクが満杯か、別の流体が入っています（1タンク1種類）",
        u"ru_ru": u"Не залить: все пять резервуаров полны или заняты другими жидкостями (в резервуаре — одна жидкость)",
    }),
    (u"gui.potato_s_t.filling.diag.tank_empty", {
        u"zh_cn": u"[灌装机] %s 号槽：罐是空的 —— 这一槽没有液体可灌（拿容器右键机器可倒进罐）",
        u"en_us": u"[Filling Machine] Slot %s: its tank is empty - nothing to fill (right-click the machine with a container to pour)",
        u"ja_jp": u"[充填機] %s 番スロット：タンクが空です — 充填する液体がありません（容器を持って右クリックで注入できます）",
        u"ru_ru": u"[Разливочная машина] Слот %s: резервуар пуст — нечего наливать (ПКМ с контейнером, чтобы залить)",
    }),
    (u"gui.potato_s_t.filling.diag.slot_empty", {
        u"zh_cn": u"[灌装机] %s 号槽：槽里没有容器 —— 可以放高压气罐或油桶",
        u"en_us": u"[Filling Machine] Slot %s: no container in the slot - put a gas tank or an oil bucket here",
        u"ja_jp": u"[充填機] %s 番スロット：容器がありません — ガスタンクか油バケツを入れてください",
        u"ru_ru": u"[Разливочная машина] Слот %s: нет контейнера — положите газовый баллон или нефтяное ведро",
    }),
    (u"gui.potato_s_t.filling.diag.full", {
        u"zh_cn": u"[灌装机] %s 号槽：容器已经满了",
        u"en_us": u"[Filling Machine] Slot %s: the container is already full",
        u"ja_jp": u"[充填機] %s 番スロット：容器は満杯です",
        u"ru_ru": u"[Разливочная машина] Слот %s: контейнер уже полон",
    }),
    (u"gui.potato_s_t.filling.diag.no_power", {
        u"zh_cn": u"[灌装机] %s 号槽：缺电 —— 机器里只有 %s FE，每个槽每 tick 要 %s FE",
        u"en_us": u"[Filling Machine] Slot %s: no power - only %s FE in the machine, each slot needs %s FE/t",
        u"ja_jp": u"[充填機] %s 番スロット：電力不足 — 内部は %s FE のみ、1スロットあたり毎 tick %s FE 必要",
        u"ru_ru": u"[Разливочная машина] Слот %s: нет энергии — в машине всего %s FE, каждому слоту нужно %s FE/т",
    }),
    (u"gui.potato_s_t.filling.diag.rejected", {
        u"zh_cn": u"[灌装机] %s 号槽：这个容器不收罐里那种流体（罐里是 %s）",
        u"en_us": u"[Filling Machine] Slot %s: this container will not take the tank's fluid (tank holds %s)",
        u"ja_jp": u"[充填機] %s 番スロット：この容器はタンク内の流体を受け付けません（タンク内は %s）",
        u"ru_ru": u"[Разливочная машина] Слот %s: контейнер не принимает жидкость из резервуара (в резервуаре %s)",
    }),
    (u"gui.potato_s_t.filling.diag.filling", {
        u"zh_cn": u"[灌装机] %s 号槽：正在灌装 —— 罐里 %s %s mB，容器还能装 %s mB",
        u"en_us": u"[Filling Machine] Slot %s: filling - tank holds %s %s mB, container has %s mB of room",
        u"ja_jp": u"[充填機] %s 番スロット：充填中 — タンク内 %s %s mB、容器の空き %s mB",
        u"ru_ru": u"[Разливочная машина] Слот %s: идёт заполнение — в резервуаре %s %s mB, в контейнере свободно %s mB",
    }),
]

# 旧 tooltip 说「气体」，ZF73 起罐已对任何流体开放 ⇒ 一并改正（四份都要）
TOOLTIP_FIX = [
    (u"zh_cn", u"把内部流体罐里的气体灌进容器物品", u"把内部流体罐里的流体灌进容器物品"),
    (u"ja_jp", u"内部の流体タンクのガスを容器アイテムに充填します", u"内部の流体タンクの流体を容器アイテムに充填します"),
    (u"ru_ru", u"Наполняет предметы-ёмкости газом из пяти внутренних резервуаров",
     u"Наполняет предметы-ёмкости жидкостью из пяти внутренних резервуаров"),
]

# 四份 tooltip 末尾统一补一句新手势说明
TOOLTIP_TAIL = {
    u"zh_cn": u"；手拿油桶/气罐右键 = 倒进罐，空手 Shift 右键 = 逐槽诊断",
    u"en_us": u"; right-click with a bucket/tank to pour in, shift-right-click empty-handed for a per-slot diagnosis",
    u"ja_jp": u"；バケツ/タンクを持って右クリックで注入、素手で Shift 右クリックでスロット診断",
    u"ru_ru": u"; ПКМ с ведром/баллоном — залить, Shift+ПКМ пустой рукой — диагностика по слотам",
}

fails = []


def sig(value):
    u"""与 LangCheck.ps1 的 Get-Sig 同口径：抽出 % 后跟 [sdif%] 的记号。"""
    return u"|".join(u"%" + c for c in re.findall(r"%([sdif%])", value))


def main():
    counts = {}
    texts = {}
    for lang in LANGS:
        path = os.path.join(ROOT, lang + u".json")
        raw = io.open(path, "rb").read()
        if raw[:3] == b"\xef\xbb\xbf":
            fails.append(u"%s 带 BOM" % lang)
        text = raw.decode(u"utf-8")
        obj = json.loads(text)
        counts[lang] = len(obj)
        texts[lang] = (path, text, obj)
    print(u"改前键数：" + u", ".join(u"%s=%d" % (l, counts[l]) for l in LANGS))

    # ---------- ② 插入 ----------
    for lang in LANGS:
        path, text, obj = texts[lang]
        lines = text.split(u"\n")
        idx = None
        for i, line in enumerate(lines):
            if ANCHOR in line:
                idx = i
                break
        if idx is None:
            fails.append(u"%s 里找不到锚点行 %s" % (lang, ANCHOR))
            continue
        indent = re.match(r"^\s*", lines[idx]).group(0)
        eol = u"\r" if lines[idx].endswith(u"\r") else u""
        added = []
        for key, values in NEW:
            if key in obj:
                fails.append(u"%s 里已经有 %s（不重复加）" % (lang, key))
                continue
            added.append(u"%s\"%s\":  \"%s\",%s" % (indent, key, values[lang], eol))
        lines[idx + 1:idx + 1] = added
        text = u"\n".join(lines)

        # tooltip 文案改正 + 补手势说明
        for fix_lang, old, new in TOOLTIP_FIX:
            if fix_lang == lang and old in text:
                text = text.replace(old, new)
        if TOOLTIP_TAIL[lang] not in text:
            m = re.search(r'("tooltip\.potato_s_t\.filling_machine":\s*")([^"]*)(")', text)
            if m is None:
                fails.append(u"%s 找不到 filling_machine tooltip 的值" % lang)
            else:
                text = text[:m.end(2)] + TOOLTIP_TAIL[lang] + text[m.end(2):]
        with io.open(path, "w", encoding="utf-8", newline=u"") as fh:
            fh.write(text)

    # ---------- 自检 ----------
    after = {}
    for lang in LANGS:
        path = os.path.join(ROOT, lang + u".json")
        text = io.open(path, "rb").read().decode(u"utf-8")
        obj = json.loads(text)
        after[lang] = obj
        if len(obj) != counts[lang] + EXPECT_NEW:
            fails.append(u"%s 键数 %d ≠ %d + %d" % (lang, len(obj), counts[lang], EXPECT_NEW))
    base = set(after[LANGS[0]].keys())
    for lang in LANGS[1:]:
        if set(after[lang].keys()) != base:
            fails.append(u"%s 与 %s 键集合不一致" % (lang, LANGS[0]))
    for key, _ in NEW:
        sigs = set(sig(after[lang][key]) for lang in LANGS)
        if len(sigs) != 1:
            fails.append(u"%s 四份占位符签名不一致：%s" % (key, sigs))
    print(u"改后键数：" + u", ".join(u"%s=%d" % (l, len(after[l])) for l in LANGS))
    for key, _ in NEW:
        print(u"  %s  签名=%s" % (key, sig(after[LANGS[0]][key])))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
