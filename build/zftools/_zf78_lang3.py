# -*- coding: utf-8 -*-
u"""_zf78_lang3.py —— 把「倒不进去」那句提示改准（四语言），并**顺手缩短**（它显示在动作栏上）

原话：`倒不进去：%s（石油罐只收原油；罐满或流体不对都不行）`
       —— 漏了第三种情况：**一座分馏塔都没认出来时石油罐容量是 0**，那时也会被拒。
新话：`倒不进去：%s（只收原油；罐满 / 流体不对 / 还没认出分馏塔（容量 0））`

按**逐字锚点**替换（每份文件正好 1 次命中），写完 json 解析 + 键数仍是 246。
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
KEY = u"gui.potato_s_t.distillation.pour.rejected"
EXPECT_KEYS = 246

NEW = {
    u"zh_cn.json": u"倒不进去：%s（只收原油；罐满 / 流体不对 / 还没认出分馏塔（容量 0））",
    u"en_us.json": u"Cannot pour %s in (crude oil only; full tank / wrong fluid / no tower "
                   u"detected yet (capacity 0))",
    u"ja_jp.json": u"%s を注げません（原油のみ／満杯・種類違い・分留塔未検出で容量 0）",
    u"ru_ru.json": u"Не удалось залить %s (только нефть; полный бак / другая жидкость / "
                   u"башня ещё не найдена — ёмкость 0)",
}

fails = []


def main():
    counts = {}
    for name, new_value in NEW.items():
        path = os.path.join(LANG, name)
        text = io.open(path, encoding="utf-8").read()
        marker = u'  "%s":' % KEY
        i = text.find(marker)
        if i < 0:
            fails.append(u"%s：找不到键 %s" % (name, KEY))
            continue
        j = text.index(u"\n", i) + 1
        data = json.loads(text)
        if data.get(KEY) == new_value:
            print(u"  [SKIP] %s：已经是新文案（幂等）" % name)
        else:
            text = text[:i] + (u'  "%s":  "%s",\n' % (KEY, new_value)) + text[j:]
            io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)
            print(u"  [OK]   %s：改准「倒不进去」文案" % name)
        try:
            data = json.loads(io.open(path, encoding="utf-8").read())
        except Exception as exc:
            fails.append(u"%s：解析失败 %s" % (name, exc))
            continue
        counts[name] = len(data)
        if data.get(KEY) != new_value:
            fails.append(u"%s：文案没写对" % name)

    print(u"各语言键数：%s" % u", ".join(u"%s=%d" % (k, v) for k, v in sorted(counts.items())))
    if len(set(counts.values())) != 1 or (counts and list(counts.values())[0] != EXPECT_KEYS):
        fails.append(u"键数不对：%s" % counts)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
