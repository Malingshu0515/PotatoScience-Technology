# -*- coding: utf-8 -*-
u"""_zf125_lang2.py —— ZF125 补第 12 个语言键：`block.potato_s_t.diesel_generator_port`

**为什么补**：常驻校验 `_zf123_langaudit.py` 的第 ④ 段是
「凡是 `ITEMS.register(\"x\")` / `BLOCKS.register(\"x\")` 的 id，四语言里都得有
`item.potato_s_t.x` 或 `block.potato_s_t.x`」—— 本轮的接线口（没有物品形态）被它抓出来了：
「1 个注册 id 没有语言键」。

盘上的先例就是合金炉那两个：`block.potato_s_t.alloy_smelter_port` / `alloy_smelter_part`
**都有语言键**（哪怕它们没有物品形态）⇒ 照同一条口径给接线口补一个，
键数 **475 → 476**（四份一起）。

跑法：
    python build\\zftools\\_zf125_lang2.py
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
LOCALES = (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru")
KEY = u"block.potato_s_t.diesel_generator_port"
VALUES = {
    u"zh_cn": u"柴油发电机接线口",
    u"en_us": u"Diesel Generator Port",
    u"ja_jp": u"ディーゼル発電機接続口",
    u"ru_ru": u"Порт дизельного генератора",
}
OLD_KEYS = 475
NEW_KEYS = 476

notes, fails = [], []


def main():
    for loc in LOCALES:
        p = os.path.join(LANG, loc + u".json")
        text = io.open(p, encoding=u"utf-8", newline=u"").read()
        before = json.loads(text)
        if KEY in before:
            notes.append(u"%s：这个键已经在了（本次只核对，%d 键）" % (loc, len(before)))
            continue
        if len(before) != OLD_KEYS:
            fails.append(u"%s：改前键数 %d（期望 %d）—— 有人动过，停手" % (loc, len(before), OLD_KEYS))
            continue
        idx = text.rindex(u"}")
        body = text[:idx].rstrip()
        if not body.endswith(u"\""):
            fails.append(u"%s：末尾 `}` 之前不是键值行结尾，别硬插" % loc)
            continue
        out = body + u",\n    \"%s\":  %s\n}\n" % (KEY, json.dumps(VALUES[loc], ensure_ascii=False))
        io.open(p, u"w", encoding=u"utf-8", newline=u"").write(out)
        back = json.loads(io.open(p, encoding=u"utf-8").read())
        if len(back) != NEW_KEYS or back.get(KEY) != VALUES[loc]:
            fails.append(u"%s：回读不对（%d 键）" % (loc, len(back)))
        else:
            notes.append(u"%s：+1 键 ⇒ %d 键（回读通过）" % (loc, len(back)))

    # 四份键集合必须仍然一致
    tables = {loc: json.loads(io.open(os.path.join(LANG, loc + u".json"), encoding=u"utf-8").read())
              for loc in LOCALES}
    base = set(tables[u"zh_cn"].keys())
    if all(set(tables[l].keys()) == base for l in LOCALES):
        notes.append(u"四份键集合仍完全一致（各 %d 键）" % len(base))
    else:
        fails.append(u"四份键集合不一致了")
    for loc in LOCALES:
        raw = open(os.path.join(LANG, loc + u".json"), "rb").read()
        if u"\r" in raw.decode(u"utf-8") or raw[:3] == b"\xef\xbb\xbf":
            fails.append(u"%s：换行/BOM 出问题了" % loc)

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
