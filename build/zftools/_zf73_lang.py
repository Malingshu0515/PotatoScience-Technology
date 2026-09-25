# -*- coding: utf-8 -*-
u"""_zf73_lang.py —— 给四份语言文件加 8 个键（0.11 ZF73 原油 / 油桶）

加在哪：紧跟在 `fluid_type.potato_s_t.chlorine` 那行后面（四份文件的行号与缩进完全一致，
已核对：都是第 56 行、两空格缩进、冒号后两空格）。

规矩：
  · 每份文件**断言锚点正好命中 1 次**，不中就不写（宁可不动，也不要把语言文件改花）；
  · 写完立刻用 json 解析一遍，并核对"四份键集合一致、各 218 键"；
  · 幂等：已经有这个键就跳过。
"""
import io
import json
import os
import sys

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
ANCHOR = u'"fluid.potato_s_t.chlorine"'
EXPECT_KEYS = 218

VALUES = {
    u"zh_cn.json": [
        (u"fluid_type.potato_s_t.crude_oil", u"原油"),
        (u"fluid.potato_s_t.crude_oil", u"原油"),
        (u"block.potato_s_t.crude_oil", u"原油"),
        (u"item.potato_s_t.oil_bucket", u"油桶"),
        (u"tooltip.potato_s_t.oil_bucket.total", u"液体：%s / %s mB"),
        (u"tooltip.potato_s_t.oil_bucket.empty", u"空桶"),
        (u"tooltip.potato_s_t.oil_bucket.entry", u"· %s：%s mB"),
        (u"tooltip.potato_s_t.oil_bucket.rule", u"只装一种液体 · 异种流体与气体都灌不进去"),
    ],
    u"en_us.json": [
        (u"fluid_type.potato_s_t.crude_oil", u"Crude Oil"),
        (u"fluid.potato_s_t.crude_oil", u"Crude Oil"),
        (u"block.potato_s_t.crude_oil", u"Crude Oil"),
        (u"item.potato_s_t.oil_bucket", u"Oil Bucket"),
        (u"tooltip.potato_s_t.oil_bucket.total", u"Liquid: %s / %s mB"),
        (u"tooltip.potato_s_t.oil_bucket.empty", u"Empty"),
        (u"tooltip.potato_s_t.oil_bucket.entry", u"- %s: %s mB"),
        (u"tooltip.potato_s_t.oil_bucket.rule",
         u"Holds a single liquid - a different fluid or a gas will not go in"),
    ],
    u"ja_jp.json": [
        (u"fluid_type.potato_s_t.crude_oil", u"原油"),
        (u"fluid.potato_s_t.crude_oil", u"原油"),
        (u"block.potato_s_t.crude_oil", u"原油"),
        (u"item.potato_s_t.oil_bucket", u"オイルバケツ"),
        (u"tooltip.potato_s_t.oil_bucket.total", u"液体：%s / %s mB"),
        (u"tooltip.potato_s_t.oil_bucket.empty", u"空"),
        (u"tooltip.potato_s_t.oil_bucket.entry", u"・%s：%s mB"),
        (u"tooltip.potato_s_t.oil_bucket.rule", u"一種類の液体のみ・別の液体や気体は入りません"),
    ],
    u"ru_ru.json": [
        (u"fluid_type.potato_s_t.crude_oil", u"Сырая нефть"),
        (u"fluid.potato_s_t.crude_oil", u"Сырая нефть"),
        (u"block.potato_s_t.crude_oil", u"Сырая нефть"),
        (u"item.potato_s_t.oil_bucket", u"Нефтяное ведро"),
        (u"tooltip.potato_s_t.oil_bucket.total", u"Жидкость: %s / %s mB"),
        (u"tooltip.potato_s_t.oil_bucket.empty", u"Пусто"),
        (u"tooltip.potato_s_t.oil_bucket.entry", u"· %s: %s mB"),
        (u"tooltip.potato_s_t.oil_bucket.rule",
         u"Только одна жидкость · другая жидкость или газ не зальются"),
    ],
}

fails = []


def main():
    counts = {}
    for name, pairs in VALUES.items():
        path = os.path.join(LANG, name)
        text = io.open(path, "r", encoding="utf-8").read()
        existing = [k for k, _ in pairs if (u'"%s"' % k) in text]
        if len(existing) == len(pairs):
            print(u"  [SKIP] %s：8 个键都在了（幂等）" % name)
        else:
            hits = text.count(ANCHOR)
            if hits != 1:
                fails.append(u"%s：锚点命中 %d 次（必须正好 1 次）" % (name, hits))
                continue
            idx = text.index(ANCHOR)
            eol = text.index(u"\n", idx) + 1
            block = u"".join(u'  "%s":  "%s",\n' % (k, v) for k, v in pairs)
            text = text[:eol] + block + text[eol:]
            io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)
            print(u"  [OK]   %s：+%d 键" % (name, len(pairs)))
        # 解析 + 计数
        try:
            data = json.loads(io.open(path, "r", encoding="utf-8").read())
        except Exception as exc:
            fails.append(u"%s：写完解析失败 %s" % (name, exc))
            continue
        counts[name] = len(data)
        for k, v in pairs:
            if data.get(k) != v:
                fails.append(u"%s：键 %s 的值不对（读到 %r）" % (name, k, data.get(k)))

    print(u"\n各语言键数：%s" % u", ".join(u"%s=%d" % (k, v) for k, v in sorted(counts.items())))
    if len(set(counts.values())) != 1:
        fails.append(u"四份语言键数不一致：%s" % counts)
    elif list(counts.values())[0] != EXPECT_KEYS:
        fails.append(u"键数不是预期的 %d，实际 %d" % (EXPECT_KEYS, list(counts.values())[0]))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
