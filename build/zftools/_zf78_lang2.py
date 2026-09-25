# -*- coding: utf-8 -*-
u"""_zf78_lang2.py —— 分馏塔「倒油 + 排查显示」两句功能的 5 个键（四语言）

插在 ZF78 那批键的最后一行（`tooltip.potato_s_t.distillation_operator`）后面。
规矩同 `_zf78_assets.py`：锚点断言正好 1 次、写完 json 解析、四份键数必须相等且 = 246。
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
ANCHOR = u'"tooltip.potato_s_t.distillation_operator"'
EXPECT_KEYS = 246

VALUES = {
    u"zh_cn.json": [
        (u"gui.potato_s_t.distillation.diagnosis.found", u"检测到 %s 座分馏塔（最多认 4 座）"),
        (u"gui.potato_s_t.distillation.diagnosis.none",
         u"没找到分馏塔：最像的一处 112 格里错了 %s 格 —— 第 %s 层 第 %s 排 第 %s 列"
         u"（坐标 %s）应该是「%s」，实际是「%s」"),
        (u"gui.potato_s_t.distillation.diagnosis.empty",
         u"32×32×10 里没有像分馏塔的结构（先把第 1 层的四角摆上）"),
        (u"gui.potato_s_t.distillation.pour.rejected",
         u"倒不进去：%s（石油罐只收原油；罐满或流体不对都不行）"),
        (u"gui.potato_s_t.distillation.pour.empty", u"手里的容器是空的"),
    ],
    u"en_us.json": [
        (u"gui.potato_s_t.distillation.diagnosis.found",
         u"Detected %s distillation tower(s) - up to 4 are recognised"),
        (u"gui.potato_s_t.distillation.diagnosis.none",
         u"No tower found: the closest candidate has %s of 112 cells wrong - layer %s, row %s, "
         u"column %s (at %s) should be '%s' but is '%s'"),
        (u"gui.potato_s_t.distillation.diagnosis.empty",
         u"Nothing within 32x32x10 looks like a distillation tower (start with the four corners "
         u"of layer 1)"),
        (u"gui.potato_s_t.distillation.pour.rejected",
         u"Cannot pour %s in (the oil tank only takes crude oil; a full tank or a wrong fluid "
         u"will not go in)"),
        (u"gui.potato_s_t.distillation.pour.empty", u"That container is empty"),
    ],
    u"ja_jp.json": [
        (u"gui.potato_s_t.distillation.diagnosis.found", u"%s 基の分留塔を検出（最大 4 基まで）"),
        (u"gui.potato_s_t.distillation.diagnosis.none",
         u"分留塔が見つかりません：最も近い候補は 112 マス中 %s マス不一致 — 第 %s 層 "
         u"第 %s 行 第 %s 列（%s）は「%s」であるべきですが「%s」です"),
        (u"gui.potato_s_t.distillation.diagnosis.empty",
         u"32×32×10 に分留塔らしき構造がありません（まず第 1 層の四隅から）"),
        (u"gui.potato_s_t.distillation.pour.rejected",
         u"%s を注げません（原油タンクは原油のみ／満杯か種類違い）"),
        (u"gui.potato_s_t.distillation.pour.empty", u"その容器は空です"),
    ],
    u"ru_ru.json": [
        (u"gui.potato_s_t.distillation.diagnosis.found",
         u"Обнаружено башен: %s (распознаётся до 4)"),
        (u"gui.potato_s_t.distillation.diagnosis.none",
         u"Башня не найдена: у ближайшего варианта %s из 112 клеток неверны — слой %s, ряд %s, "
         u"столбец %s (%s): должно быть «%s», а там «%s»"),
        (u"gui.potato_s_t.distillation.diagnosis.empty",
         u"В радиусе 32×32×10 нет ничего похожего на башню (начните с четырёх углов 1-го слоя)"),
        (u"gui.potato_s_t.distillation.pour.rejected",
         u"Не удалось залить %s (бак принимает только нефть; полный бак или другая жидкость "
         u"не зальются)"),
        (u"gui.potato_s_t.distillation.pour.empty", u"Этот контейнер пуст"),
    ],
}

fails = []


def fix_line(text, key, value):
    u"""把某个键那一行**整行换成规范写法**（自愈：哪怕上一版写成非法 JSON 也能救回来）。

    ⚠ 为什么需要它：英文那条 `none` 我第一版在值里写了 ASCII 双引号
    （`should be "%s" but is "%s"`）⇒ 写出去就是非法 JSON，`json.loads` 当场炸。
    这是"中文串里混 ASCII 引号"那个老坑的**英文版**：只要值里出现 `"`，就必须用别的引号。
    """
    marker = u'  "%s":' % key
    i = text.find(marker)
    if i < 0:
        return text, False
    j = text.index(u"\n", i) + 1
    return text[:i] + (u'  "%s":  "%s",\n' % (key, value)) + text[j:], True


def main():
    counts = {}
    for name, pairs in VALUES.items():
        path = os.path.join(LANG, name)
        text = io.open(path, encoding="utf-8").read()

        # ① 自愈：键已在、但那一行不规范（含非法 JSON）⇒ 逐行换掉
        healed = 0
        for k, v in pairs:
            line_ok = (u'  "%s":  "%s",' % (k, v)) in text
            if not line_ok:
                text, done = fix_line(text, k, v)
                healed += 1 if done else 0
        if healed:
            io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)
            print(u"  [FIX]  %s：修好 %d 行（上一版写坏了）" % (name, healed))

        # ② 缺键就插在锚点后面
        missing = [(k, v) for k, v in pairs if (u'"%s"' % k) not in text]
        if missing:
            hits = text.count(ANCHOR)
            if hits != 1:
                fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (name, hits))
                continue
            i = text.index(ANCHOR)
            eol = text.index(u"\n", i) + 1
            block = u"".join(u'  "%s":  "%s",\n' % (k, v) for k, v in missing)
            text = text[:eol] + block + text[eol:]
            io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)
            print(u"  [OK]   %s：+%d 键" % (name, len(missing)))
        else:
            print(u"  [SKIP] %s：键齐了（幂等）" % name)

        try:
            data = json.loads(io.open(path, encoding="utf-8").read())
        except Exception as exc:
            fails.append(u"%s：解析失败 %s" % (name, exc))
            continue
        counts[name] = len(data)
        for k, v in pairs:
            if data.get(k) != v:
                fails.append(u"%s：键 %s 的值不对" % (name, k))

    print(u"\n各语言键数：%s" % u", ".join(u"%s=%d" % (k, v) for k, v in sorted(counts.items())))
    if len(set(counts.values())) != 1:
        fails.append(u"四份键数不一致：%s" % counts)
    elif list(counts.values()) and list(counts.values())[0] != EXPECT_KEYS:
        fails.append(u"键数不是 %d（实际 %d）" % (EXPECT_KEYS, list(counts.values())[0]))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
