# -*- coding: utf-8 -*-
"""_zf62_lang.py —— 轻质钛合金的四语言名字（插在钛锭那一行后面，其余字节不动）"""
import io
import json
import os
import sys

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
ANCHOR = u"item.potato_s_t.titanium_ingot"
KEY = u"item.potato_s_t.light_titanium_alloy"

NAMES = {
    "zh_cn": u"轻质钛合金",
    "en_us": u"Lightweight Titanium Alloy",
    "ja_jp": u"軽量チタン合金",
    "ru_ru": u"Лёгкий титановый сплав",
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
        lines.insert(idx[0] + 1, u'    "' + KEY + u'":  ' + json.dumps(NAMES[lang], ensure_ascii=False) + u",")
        out = eol.join(lines)
        data = json.loads(out)
        if data.get(KEY) != NAMES[lang]:
            fails.append(u"%s: 写回后读不到 %s" % (lang, KEY))
            continue
        io.open(path, "wb").write(out.encode("utf-8"))
        print(u"  [OK] %-8s + %s = %s" % (lang, KEY, NAMES[lang]))

    keys = {}
    for lang in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        keys[lang] = set(json.loads(io.open(os.path.join(LANG, lang + ".json"), encoding="utf-8").read()))
    base = keys["zh_cn"]
    for lang, k in keys.items():
        if k != base:
            fails.append(u"%s 键集与 zh_cn 不一致（多 %d 少 %d）" % (lang, len(k - base), len(base - k)))
    print(u"\n键数 = %d   失败项 = %d" % (len(base), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
