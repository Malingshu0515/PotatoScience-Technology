# -*- coding: utf-8 -*-
u"""_zf162_lang.py —— ZF162 五份 lang 的机械改动（**只动这四类行**）。

本轮语言改动（键数 594 → 593；lzh 596 → 595）：
  ① 删 `item.potato_s_t.wrench`（扳手物品整个删了）
  ② 删 `tooltip.potato_s_t.electric_blast_furnace`（那个 BlockItem 删了 ⇒ tooltip 没有载体）
  ③ 新增 `gui.potato_s_t.filling.diag.unsupported`（灌装机：槽里是"灌不了的东西"）
  ④ 改值 `gui.potato_s_t.filling.diag.slot_empty`（旧值写死"可以放高压气罐或油桶"，
     现在什么都能放 ⇒ 那句话得跟着改）

插在**同一个位置**（紧跟 `diag.slot_empty` 之后）—— `_zf109_verify.py` 有一条「四语键序与 zh_cn
逐位相同」的判据，插错位置就会红。行尾风格（LF）与"文件末尾有没有换行"都按原样保留
（zh_cn 没有末尾换行、其余有）。

跑法：python build\\zftools\\_zf162_lang.py            # 干跑：只报告，不写盘
      python build\\zftools\\_zf162_lang.py --write    # 落盘 + 复核
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

PROJ = r"E:\PotatoST"
LANGDIR = os.path.join(PROJ, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]

KILL = [u"item.potato_s_t.wrench", u"tooltip.potato_s_t.electric_blast_furnace"]
ANCHOR = u"gui.potato_s_t.filling.diag.slot_empty"
NEWKEY = u"gui.potato_s_t.filling.diag.unsupported"

# 新文案：`{name}` 用各语言自己的机器名（block.potato_s_t.filling_machine）填，
# 槽位占位符统一是 %s（与旧值一致）。
SLOT_EMPTY = {
    u"zh_cn": u"[{name}] %s 号槽：槽里没东西——什么都能放，但只有能灌装的容器才会被灌",
    u"en_us": u"[{name}] Slot %s: empty - anything can go in, but only a fillable container gets filled",
    u"ja_jp": u"[{name}] %s 番スロット：空です——何でも入れられますが、充填できる容器だけが充填されます",
    u"ru_ru": u"[{name}] Слот %s: пусто — положить можно что угодно, но заполняются только заполняемые контейнеры",
    u"lzh": u"[{name}] %s 號槽：槽中無物——凡物皆可入，唯可灌者乃灌",
}
UNSUPPORTED = {
    u"zh_cn": u"[{name}] %s 号槽：这个东西灌不了——它不是流体容器（放高压气罐、油桶，或别的 mod 的流体容器）",
    u"en_us": u"[{name}] Slot %s: this item cannot be filled - it is not a fluid container (use a gas tank or an oil bucket, or another mod's fluid container)",
    u"ja_jp": u"[{name}] %s 番スロット：このアイテムは充填できません——流体容器ではありません（高圧ガスタンク、オイルバケツ、または他 MOD の流体容器をお使いください）",
    u"ru_ru": u"[{name}] Слот %s: этот предмет нельзя заполнить — это не контейнер для жидкости (используйте газовый баллон, бочку для нефти или контейнер другого мода)",
    u"lzh": u"[{name}] %s 號槽：此物不可灌——非流體之器也（可用高壓氣罐、油桶，或他模組之流體容器）",
}


def read(p):
    with io.open(p, encoding="utf-8", newline=u"") as fh:
        return fh.read()


def write(p, text):
    with io.open(p, "w", encoding="utf-8", newline=u"") as fh:
        fh.write(text)


def key_of(line):
    s = line.strip()
    if not s.startswith(u'"'):
        return None
    i = s.find(u'":')
    if i < 0:
        return None
    return s[1:i]


def main(argv):
    do_write = u"--write" in argv
    fails, notes = [], []
    after = {}
    index_of_new = {}
    for loc in LOCALES:
        p = os.path.join(LANGDIR, loc + u".json")
        text = read(p)
        eol = u"\r\n" if u"\r\n" in text else u"\n"
        trailing = text.endswith(u"\n")
        before = json.loads(text)
        name = before[u"block.potato_s_t.filling_machine"]

        lines = text.split(eol)
        out, dropped, anchor_at = [], [], -1
        for ln in lines:
            k = key_of(ln)
            if k in KILL:
                dropped.append(k)
                continue
            if k == ANCHOR:
                ind = ln[:len(ln) - len(ln.lstrip())]
                out.append(ind + u'"%s": %s,' % (ANCHOR, json.dumps(
                    SLOT_EMPTY[loc].format(name=name), ensure_ascii=False)))
                anchor_at = len(out) - 1
                out.append(ind + u'"%s": %s,' % (NEWKEY, json.dumps(
                    UNSUPPORTED[loc].format(name=name), ensure_ascii=False)))
                continue
            out.append(ln)

        if sorted(dropped) != sorted(KILL):
            fails.append(u"%s：要删的两行没找齐（找到 %s）" % (loc, dropped))
            continue
        if anchor_at < 0:
            fails.append(u"%s：没找到锚点行 %s" % (loc, ANCHOR))
            continue
        if len(out) != len(lines) - 1:
            fails.append(u"%s：行数不对（%d -> %d）" % (loc, len(lines), len(out)))
            continue
        new_text = eol.join(out)
        if not new_text.endswith(eol) and trailing:
            new_text += eol
        if new_text.endswith(eol) and not trailing:
            new_text = new_text[:-len(eol)]
        try:
            parsed = json.loads(new_text)
        except Exception as exc:      # noqa: BLE001
            fails.append(u"%s：改完 JSON 解析失败 %s" % (loc, exc))
            continue
        if len(parsed) != len(before) - 1:
            fails.append(u"%s：键数 %d -> %d（应为 -1）" % (loc, len(before), len(parsed)))
            continue
        for k in KILL:
            if k in parsed:
                fails.append(u"%s：%s 还在" % (loc, k))
        if parsed.get(NEWKEY, u"").count(u"%s") != 1:
            fails.append(u"%s：新键的 %%s 占位符不是 1 个" % loc)
        if parsed.get(ANCHOR, u"").count(u"%s") != 1:
            fails.append(u"%s：锚点行的 %%s 占位符不是 1 个" % loc)
        after[loc] = parsed
        index_of_new[loc] = list(parsed.keys()).index(NEWKEY)
        notes.append(u"%s：删 %d 键 + 加 1 键 ⇒ %d，新键在第 %d 位（0 起）" % (
            loc, len(dropped), len(parsed), index_of_new[loc]))
        if do_write:
            write(p, new_text)

    # 跨语言：键**集合**必须完全一致（lzh 允许 language.name / language.region 两个额外键）；
    # ⚠ **键序不查**：四语的键序在本轮开工前就已经与 zh_cn 不同（`_zf109_verify.py` 开工前就是红的
    # 那 3 条，属别人的账，见 `_zf162_gatesnap_before.txt`）。本脚本只保证自己插的那一行
    # 紧跟在锚点之后（下一段断言）。
    ref = u"zh_cn"
    refset = set(after[ref].keys())
    for loc in LOCALES[1:]:
        lk = set(after[loc].keys()) - {u"language.name", u"language.region"}
        if lk != refset:
            fails.append(u"%s：键集合与 zh_cn 不一致（多 %s / 少 %s）" % (
                loc, sorted(lk - refset)[:4], sorted(refset - lk)[:4]))
    for loc in LOCALES:
        keys = list(after[loc].keys())
        if keys.index(NEWKEY) != keys.index(ANCHOR) + 1:
            fails.append(u"%s：新键没有紧跟锚点（锚点 %d，新键 %d）" % (
                loc, keys.index(ANCHOR), keys.index(NEWKEY)))
    ok = not fails
    print(u"模式：%s" % (u"落盘" if do_write else u"干跑（不写）"))
    for n in notes:
        print(u"  " + n)
    print(u"zh_cn 新值的占位符数 = %d / 五语键集合 = %s / 新键一律紧跟锚点 = %s" % (
        after[ref][NEWKEY].count(u"%s"), u"一致" if ok else u"不一致", u"是" if ok else u"否"))
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    rep = os.path.join(PROJ, u"build", u"zftools", u"_zf162_lang.txt")
    with io.open(rep, "w", encoding="utf-8", newline=u"\n") as fh:
        fh.write(u"\n".join(notes) + u"\n" + u"\n".join(u"!! " + f for f in fails) + u"\n")
        fh.write(u"模式：%s\n" % (u"落盘" if do_write else u"干跑"))
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
