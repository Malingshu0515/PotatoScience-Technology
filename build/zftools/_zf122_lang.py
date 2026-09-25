# -*- coding: utf-8 -*-
u"""_zf122_lang.py —— ZF122 四语言补键：星仪图之章（10 键）

键的来处：物品名 1、Shift 说明 3、五种天空的名字 5、切换提示 1 = 10。

占位符：只有 `message.potato_s_t.star_chart.switched` 带 1 个 `%s`（换成了哪片天），
四语言必须一致（LangCheck 也查这条，这里先自查）。

行插入 + 写盘前 json.loads + 幂等 + `--verify` 只读复核（照 §4.6/§4.28）。

    python build\\zftools\\_zf122_lang.py [--write|--verify]
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
LANGS = ("zh_cn", "en_us", "ja_jp", "ru_ru")

ENTRY = re.compile(u'^    "([^"]+)":  "')

# (键, zh, en, ja, ru)
DATA = [
    (u"item.potato_s_t.star_chart_tome",
     u"星仪图之章", u"Star Chart Tome", u"星儀図の書", u"Звёздный атлас"),
    (u"message.potato_s_t.star_chart.switched",
     u"星仪图：%s", u"Star chart: %s", u"星儀図：%s", u"Звёздный атлас: %s"),
    (u"sky.potato_s_t.0",
     u"原版星空", u"Vanilla Sky", u"バニラの星空", u"Обычное небо"),
    (u"sky.potato_s_t.1",
     u"碧霄星云", u"Verdant Nebula", u"碧霄の星雲", u"Зелёная туманность"),
    (u"sky.potato_s_t.2",
     u"星海幽峦", u"Mystic Mountain", u"神秘の山", u"Мистическая гора"),
    (u"sky.potato_s_t.3",
     u"赤河星汉", u"Ember River", u"紅蓮の銀河", u"Багровая река"),
    (u"sky.potato_s_t.4",
     u"蛛巢星云", u"Tarantula Nebula", u"タランチュラ星雲", u"Туманность Тарантул"),
    (u"tooltip.potato_s_t.star_chart.1",
     u"右键顺次切换主世界的天空盒（潜行右键往回切）",
     u"Right-click to cycle the Overworld skybox (sneak-right-click to go back)",
     u"右クリックで主世界のスカイボックスを順に切り替え（スニーク右クリックで戻る）",
     u"ПКМ — переключить скайбокс Верхнего мира (ПКМ с Shift — назад)"),
    (u"tooltip.potato_s_t.star_chart.2",
     u"四张星图与原版星空循环，设定记在这本书里",
     u"Cycles through four star charts and the vanilla sky; the choice is stored in the book",
     u"4 枚の星図とバニラの星空を巡回。設定はこの本に保存されます",
     u"Четыре карты звёздного неба и обычное небо по кругу; выбор хранится в книге"),
    (u"tooltip.potato_s_t.star_chart.3",
     u"只有你自己看得见 —— 不会改别人的天",
     u"Only you see it - it does not change anyone else's sky",
     u"見えるのは自分だけ ― 他の人の空は変わりません",
     u"Видно только вам — чужое небо не меняется"),
]


def read(p):
    return io.open(p, encoding="utf-8").read()


def insert_entry(lines, key, value):
    target = None
    last_entry = None
    for i, line in enumerate(lines):
        m = ENTRY.match(line)
        if not m:
            continue
        last_entry = i
        if target is None and m.group(1) > key:
            target = i
    new_line = u'    "%s":  "%s"' % (key, value)
    if target is not None:
        lines.insert(target, new_line + u",")
        return
    if last_entry is None:
        raise ValueError(u"文件里找不到任何条目行")
    tail = lines[last_entry].rstrip()
    if not tail.endswith(u","):
        lines[last_entry] = tail + u","
    lines.insert(last_entry + 1, new_line)


def main(argv):
    write = "--write" in argv
    verify = "--verify" in argv
    n_fail = 0

    if verify:
        print(u"=== 只读复核 ===")
        texts = dict((l, json.loads(read(os.path.join(LANG, l + u".json")))) for l in LANGS)
        for l in LANGS:
            print(u"   %-6s 键数 = %d" % (l, len(texts[l])))
        base = set(texts["zh_cn"])
        for l in LANGS[1:]:
            if set(texts[l]) != base:
                print(u"   [FAIL] %s 键集合不一致" % l)
                n_fail += 1
        for key, zh, en, ja, ru in DATA:
            want = dict(zip(LANGS, (zh, en, ja, ru)))
            for l in LANGS:
                if texts[l].get(key) != want[l]:
                    print(u"   [FAIL] %s / %s\n     期望 %r\n     实际 %r" % (l, key, want[l], texts[l].get(key)))
                    n_fail += 1
            if len(set(v.count(u"%s") for v in (zh, en, ja, ru))) != 1:
                print(u"   [FAIL] %s 的四语言占位符个数不一致" % key)
                n_fail += 1
        print(u"   失败 = %d（期望 %d 键 × 四语言）" % (n_fail, len(DATA)))
        return 1 if n_fail else 0

    for l in LANGS:
        path = os.path.join(LANG, l + u".json")
        text = read(path)
        before = json.loads(text)
        lines = text.split(u"\n")
        added = []
        for key, zh, en, ja, ru in DATA:
            if key in before:
                continue
            insert_entry(lines, key, {u"zh_cn": zh, u"en_us": en, u"ja_jp": ja, u"ru_ru": ru}[l])
            added.append(key)
        new_text = u"\n".join(lines)
        after = json.loads(new_text)                 # 写盘前必须先解析得过
        if len(after) != len(before) + len(added):
            raise SystemExit(u"%s 键数对不上" % l)
        for key, zh, en, ja, ru in DATA:
            want = {u"zh_cn": zh, u"en_us": en, u"ja_jp": ja, u"ru_ru": ru}[l]
            if after.get(key) != want:
                raise SystemExit(u"%s / %s 的值不对" % (l, key))
        print(u"   %-6s %d -> %d 键（新增 %d）%s" % (l, len(before), len(after), len(added),
                                                 u"  [已写盘]" if write else u"  [仅体检]"))
        if write:
            io.open(path, "w", encoding="utf-8", newline=u"").write(new_text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
