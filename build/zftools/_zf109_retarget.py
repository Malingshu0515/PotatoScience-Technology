# -*- coding: utf-8 -*-
u"""_zf109_retarget.py —— ZF109：往轮校验器里的"活体数字" **398 → 408**（采油机 10 个新键）

§4.36 口径不变：**改锚点，不放宽断言**。规则照 `_zf107_retarget.py`：
  · 每份都在"要写的那一刻"重新从盘上读；
  · 每条替换要求**正好命中 1 次**（0 次或 ≥2 次都报错退出，不猜）；
  · 写前 `compile()` 一遍，语法不过就不落盘；
  · 只动"键数"这一件事。

本轮多出来的第 17 份是 `_zf107_verify.py` —— 它自己也是"键数耦合"的（上一轮没把它自己列进去）。
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, r"build\zftools")
NOTE = u"… + ZF109 采油机 10 键"
EK = u"EXPECT_KEYS = 398           # … + ZF107 成就 48 键"

# (文件, [(正则, 替换, 说明), …])
PLAN = [
    (u"_zf71_verify.py", [
        (r"set\(keys\.values\(\)\) == \{398\}", u"set(keys.values()) == {408}", u"集合里的键数"),
        (r'u"398 keys each"', u'u"408 keys each"', u"公告里的键数串"),
    ]),
    (u"_zf73_verify.py", [
        (r'u"B11 四语言各 398 键[^"]*"', u'u"B11 四语言各 408 键（… + ZF109 采油机 10）"', u"标题文案"),
        (r"all\(v == 398 for v in counts\.values\(\)\)",
         u"all(v == 408 for v in counts.values())", u"断言值"),
    ]),
    (u"_zf75_verify.py", [
        (r'u"C2 四语言各 398 键[^"]*"', u'u"C2 四语言各 408 键（ZF104 起；ZF107 +48；ZF109 +10）"',
         u"标题文案"),
        (r"all\(v == 398 for v in counts\.values\(\)\)",
         u"all(v == 408 for v in counts.values())", u"断言值"),
    ]),
    (u"_zf78_verify.py", [
        (r'u"四份语言键数一致且 = 398[^"]*"', u'u"四份语言键数一致且 = 408（ZF107 +48；ZF109 +10）"',
         u"标题文案"),
        (r"list\(counts\.values\(\)\)\[0\] == 398", u"list(counts.values())[0] == 408", u"断言值"),
    ]),
    (u"_zf79_verify.py", [
        (r'u"四份语言键数一致且 = 398[^"]*"', u'u"四份语言键数一致且 = 408（ZF107 +48；ZF109 +10）"',
         u"标题文案"),
        (r"list\(counts\.values\(\)\)\[0\] == 398", u"list(counts.values())[0] == 408", u"断言值"),
    ]),
    (u"_zf80_verify.py", [(r"EXPECT_KEYS = 398[^\n]*", u"EXPECT_KEYS = 408           # " + NOTE, u"常量")]),
    (u"_zf81_verify.py", [(r'u"语言键数（ZF107 起 398）", 398,',
                           u'u"语言键数（ZF109 起 408）", 408,', u"标题 + 断言")]),
    (u"_zf82_verify.py", [
        (r"EXPECT_KEYS = 398[^\n]*", u"EXPECT_KEYS = 408           # " + NOTE, u"常量"),
        (r'and u"398 keys each" in ann\)', u'and u"408 keys each" in ann)', u"公告里的键数串"),
    ]),
    (u"_zf93_verify.py", [(r"EXPECT_KEYS = 398[^\n]*", u"EXPECT_KEYS = 408           # " + NOTE, u"常量")]),
    (u"_zf96_verify.py", [(r"EXPECT_KEYS = 398[^\n]*", u"EXPECT_KEYS = 408           # " + NOTE, u"常量")]),
    (u"_zf97_verify.py", [(r"EXPECT_KEYS = 398[^\n]*", u"EXPECT_KEYS = 408           # " + NOTE, u"常量")]),
    (u"_zf98_verify.py", [(r"EXPECT_KEYS = 398[^\n]*", u"EXPECT_KEYS = 408           # " + NOTE, u"常量")]),
    (u"_zf100_verify.py", [(r"EXPECT_KEYS = 398[^\n]*", u"EXPECT_KEYS = 408           # " + NOTE, u"常量")]),
    (u"_zf101_verify.py", [(r"EXPECT_KEYS = 398[^\n]*", u"EXPECT_KEYS = 408           # " + NOTE, u"常量")]),
    (u"_zf102_verify.py", [(r"EXPECT_KEYS = 398[^\n]*", u"EXPECT_KEYS = 408           # " + NOTE, u"常量")]),
    (u"_zf103_verify.py", [
        (r"len\(table\) == 398", u"len(table) == 408", u"断言值"),
        (r'u"%s：总键数 398[^"]*"', u'u"%s：总键数 408（… + ZF109 采油机 10）"', u"标题文案"),
    ]),
    (u"_zf107_verify.py", [(r"EXPECT_KEYS = 398[^\n]*", u"EXPECT_KEYS = 408           # " + NOTE, u"常量")]),
]

fails = []


def main():
    n = 0
    for f, subs in PLAN:
        p = os.path.join(TOOLS, f)
        if not os.path.exists(p):
            fails.append(u"%s 不在盘上" % f)
            continue
        text = io.open(p, encoding="utf-8").read()          # ← 写前重读
        after = text
        for pat, rep, why in subs:
            after, cnt = re.subn(pat, rep, after)
            if cnt != 1:
                fails.append(u"%s：%s 的替换命中 %d 次（要求 1 次）" % (f, why, cnt))
        if after == text:
            fails.append(u"%s：一个字节都没变（正则过时了？）" % f)
            continue
        try:
            compile(after, f, u"exec")
        except SyntaxError as e:
            fails.append(u"%s：改完语法不过（第 %s 行：%s）—— 不落盘" % (f, e.lineno, e.msg))
            continue
        io.open(p, "w", encoding="utf-8", newline=u"").write(after)
        back = io.open(p, encoding="utf-8").read()           # 回读
        # 只把"像断言"的残留当错；注释里的历史数字不算（本工程的文档/注释本来就会留旧数）
        bad = [i + 1 for i, line in enumerate(back.split(u"\n"))
               if re.search(r"(==|=|\{)\s*398\b|398\s*keys each|总键数 398|各 398 键", line)]
        print(u"  [OK]   %-22s 替换 %d 处；像断言的残留 398 = %d" % (f, len(subs), len(bad)))
        if bad:
            fails.append(u"%s：还有 %d 行像断言的 398（行 %s）" % (f, len(bad), bad[:5]))
        n += 1
    print(u"\n改到的文件 %d 份" % n)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
