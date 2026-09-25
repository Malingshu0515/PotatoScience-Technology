# -*- coding: utf-8 -*-
"""_zf66_lang.py —— 四语言各加 2 个键（钛合金剑 / 钛合金镐）

锚点法（§4.8）：插在 `item.potato_s_t.light_titanium_alloy` 那一行后面，四份文件都插同样的位置。
每个键**必须**在四份文件里各出现一次，且插入前不许已存在（防止重复插入后 JSON 里有两个同名键）。
"""
import io
import sys

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
ANCHOR_KEY = u"item.potato_s_t.light_titanium_alloy"

KEYS = [
    (u"item.potato_s_t.titanium_alloy_sword",
     {u"zh_cn": u"钛合金剑", u"en_us": u"Titanium Alloy Sword",
      u"ja_jp": u"チタン合金の剣", u"ru_ru": u"Меч из титанового сплава"}),
    (u"item.potato_s_t.titanium_alloy_pickaxe",
     {u"zh_cn": u"钛合金镐", u"en_us": u"Titanium Alloy Pickaxe",
      u"ja_jp": u"チタン合金のツルハシ", u"ru_ru": u"Кирка из титанового сплава"}),
]


def main():
    fails = []
    files = {}
    for name in (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"):
        p = u"%s\\%s.json" % (LANG, name)
        files[name] = io.open(p, encoding="utf-8").read()

    for name, text in files.items():
        hits = text.count(u'"%s"' % ANCHOR_KEY)
        if hits != 1:
            fails.append(u"%s.json：锚点 %s 命中 %d 次（应为 1）" % (name, ANCHOR_KEY, hits))

    for key, values in KEYS:
        for name in files:
            if u'"%s"' % key in files[name]:
                fails.append(u"%s.json：键 %s 已经存在（不重复插）" % (name, key))

    if fails:
        print(u"有失败项，**不落盘**：")
        for f in fails:
            print(u"  !! " + f)
        return 1

    for name, text in files.items():
        lines = text.split(u"\n")
        out = []
        added = 0
        for line in lines:
            out.append(line)
            if u'"%s"' % ANCHOR_KEY in line:
                for key, values in KEYS:
                    out.append(u'    "%s":  "%s",' % (key, values[name]))
                    added += 1
        if added != len(KEYS):
            fails.append(u"%s.json：只插了 %d 个键" % (name, added))
            continue
        io.open(u"%s\\%s.json" % (LANG, name), "w", encoding="utf-8", newline="\n").write(u"\n".join(out))
        print(u"  %-8s 插入 %d 个键（%s）" % (name, added, u" / ".join(v[name] for _, v in KEYS)))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
