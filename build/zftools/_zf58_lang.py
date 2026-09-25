# -*- coding: utf-8 -*-
"""_zf58_lang.py —— 给部件格起个名字（Jade 不该显示 id）

用户报：Jade 上显示的是 `block.potato_s_t.alloy_smelter_part`（原始 key）⇒ 部件格没有 lang 条目。
电力高炉的部件格早就有名字了（`electric_blast_furnace_part` = "Electric Blast Furnace"），
这里照同样的做法，给合金炉部件格用**整台机器**的名字（挖出来看到的就是"合金冶炼炉"）。

只做**行级插入**（插在 `..._port` 那一行后面），其余字节不动。
"""
import io
import json
import os
import sys

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
PORT = u"block.potato_s_t.alloy_smelter_port"
PART = u"block.potato_s_t.alloy_smelter_part"

NAMES = {
    "zh_cn": u"合金冶炼炉",
    "en_us": u"Alloy Smelter",
    "ja_jp": u"合金精錬炉",
    "ru_ru": u"Плавильня сплавов",
}

fails = []


def main():
    for lang in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        path = os.path.join(LANG, lang + ".json")
        raw = io.open(path, "rb").read()
        text = raw.decode("utf-8")
        eol = u"\r\n" if "\r\n" in text else u"\n"
        lines = text.split(eol)
        if any(l.startswith(u'    "' + PART + u'":') for l in lines):
            print(u"  [--] %-8s 已有 %s，跳过" % (lang, PART))
            continue
        idx = [i for i, l in enumerate(lines) if l.startswith(u'    "' + PORT + u'":')]
        if len(idx) != 1:
            fails.append(u"%s: 找不到 %s 那一行（找到 %d 行）" % (lang, PORT, len(idx)))
            continue
        new_line = (u'    "' + PART + u'":  '
                    + json.dumps(NAMES[lang], ensure_ascii=False) + u",")
        lines.insert(idx[0] + 1, new_line)
        out = eol.join(lines)
        data = json.loads(out)
        if data.get(PART) != NAMES[lang]:
            fails.append(u"%s: 写回后读不到 %s" % (lang, PART))
            continue
        io.open(path, "wb").write(out.encode("utf-8"))
        print(u"  [OK] %-8s + %s = %s" % (lang, PART, NAMES[lang]))

    # 键集必须四语言一致（LangCheck 也会查，这里先自查一遍）
    keys = {}
    for lang in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        keys[lang] = set(json.loads(io.open(os.path.join(LANG, lang + ".json"),
                                           encoding="utf-8").read()))
    base = keys["zh_cn"]
    for lang, k in keys.items():
        if k != base:
            fails.append(u"%s 键集与 zh_cn 不一致（多 %d 少 %d）"
                         % (lang, len(k - base), len(base - k)))
    print(u"\n键数 = %d   失败项 = %d" % (len(base), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
