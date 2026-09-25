# -*- coding: utf-8 -*-
u"""_zf104_lang.py —— ZF104 的四语言新键（每份 1 键）：新物品「硬质钛合金」

⚠ §4.64：先解析、再写；插进去的每行自带逗号，**最后一行不能有**。
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

KEYS = {
    "zh_cn": {u"item.potato_s_t.hard_titanium_alloy": u"硬质钛合金"},
    "en_us": {u"item.potato_s_t.hard_titanium_alloy": u"Hard Titanium Alloy"},
    "ja_jp": {u"item.potato_s_t.hard_titanium_alloy": u"硬質チタン合金"},
    "ru_ru": {u"item.potato_s_t.hard_titanium_alloy": u"Твёрдый титановый сплав"},
}

fails = []


def main():
    for name, table in sorted(KEYS.items()):
        path = os.path.join(LANG, name + u".json")
        raw = io.open(path, encoding="utf-8").read()
        data = json.loads(raw)
        dup = [k for k in table if k in data]
        if dup:
            fails.append(u"%s：这些键已经有了 %s" % (name, dup))
            continue
        lines = raw.split(u"\n")
        last = max(i for i, l in enumerate(lines) if l.strip().startswith(u'"'))
        if not lines[last].rstrip().endswith(u","):
            lines[last] = lines[last].rstrip() + u","
        block = [u'    %s:  %s,' % (json.dumps(k, ensure_ascii=False),
                                    json.dumps(v, ensure_ascii=False))
                 for k, v in table.items()]
        block[-1] = block[-1][:-1]
        lines[last + 1:last + 1] = block
        text = u"\n".join(lines)
        back = json.loads(text)
        if len(back) != len(data) + len(table):
            fails.append(u"%s：回读键数 %d ≠ %d" % (name, len(back), len(data) + len(table)))
            continue
        io.open(path, "w", encoding="utf-8", newline=u"").write(text)
        print(u"  [OK]   %-12s %d → %d 键（+%d）" % (name + u".json", len(data), len(back), len(table)))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
