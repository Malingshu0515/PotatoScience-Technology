# -*- coding: utf-8 -*-
"""_zf62_lang2.py —— JEI 那条新说明行 `gui.potato_s_t.jei.tag_inputs`（四语言）"""
import io
import json
import os
import sys

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
ANCHOR = u"gui.potato_s_t.jei.energy"
KEY = u"gui.potato_s_t.jei.tag_inputs"

VALUES = {
    "zh_cn": u"输入按通用锭标签（c:ingots）判定：别的 mod 的铝锭/钛锭/银锭一样能用",
    "en_us": u"Inputs are matched by the common ingot tags (c:ingots): other mods' aluminium, "
             u"titanium and silver ingots work too",
    "ja_jp": u"入力は共通インゴットタグ（c:ingots）で判定します。他 MOD のアルミ/チタン/銀インゴットでも可",
    "ru_ru": u"Входы определяются по общим тегам слитков (c:ingots): слитки алюминия, титана и "
             u"серебра из других модов тоже подойдут",
}

fails = []


def main():
    for lang in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        path = os.path.join(LANG, lang + ".json")
        text = io.open(path, "rb").read().decode("utf-8")
        eol = u"\r\n" if "\r\n" in text else u"\n"
        lines = text.split(eol)
        if any(l.startswith(u'    "' + KEY + u'":') for l in lines):
            print(u"  [--] %-8s 已有，跳过" % lang)
            continue
        idx = [i for i, l in enumerate(lines) if l.startswith(u'    "' + ANCHOR + u'":')]
        if len(idx) != 1:
            fails.append(u"%s: 找不到 %s 那一行（找到 %d）" % (lang, ANCHOR, len(idx)))
            continue
        lines.insert(idx[0] + 1, u'    "' + KEY + u'":  ' + json.dumps(VALUES[lang], ensure_ascii=False) + u",")
        out = eol.join(lines)
        if json.loads(out).get(KEY) != VALUES[lang]:
            fails.append(u"%s: 写回后读不到 %s" % (lang, KEY))
            continue
        io.open(path, "wb").write(out.encode("utf-8"))
        print(u"  [OK] %-8s + %s" % (lang, KEY))

    keys = {l: set(json.loads(io.open(os.path.join(LANG, l + ".json"), encoding="utf-8").read()))
            for l in ("zh_cn", "en_us", "ja_jp", "ru_ru")}
    base = keys["zh_cn"]
    for lang, k in keys.items():
        if k != base:
            fails.append(u"%s 键集与 zh_cn 不一致" % lang)
    print(u"\n键数 = %d   失败项 = %d" % (len(base), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
