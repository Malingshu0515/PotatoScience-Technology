# -*- coding: utf-8 -*-
u"""_zf112_retarget.py —— 四语言键数锚点 **408 → 417**（锂电池构造间 9 个新键）

§4.36 口径不变：**改锚点，不放宽断言**。规则照 `_zf107/_zf109_retarget.py`：
每份写前重读、每条替换 0/1 次、写完 `compile()` 过一遍、只动"键数"这一件事。
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TOOLS = os.path.join(r"E:\PotatoST", r"build\zftools")
NOTE = u"… + ZF112 锂电池构造间 9 键"
FILES = ["_zf71_verify.py", "_zf73_verify.py", "_zf75_verify.py", "_zf78_verify.py",
         "_zf79_verify.py", "_zf80_verify.py", "_zf81_verify.py", "_zf82_verify.py",
         "_zf93_verify.py", "_zf96_verify.py", "_zf97_verify.py", "_zf98_verify.py",
         "_zf100_verify.py", "_zf101_verify.py", "_zf102_verify.py", "_zf103_verify.py",
         "_zf107_verify.py", "_zf109_verify.py", "_zf111_verify.py"]

SUBS = [
    (r"EXPECT_KEYS = 408[^\n]*", u"EXPECT_KEYS = 417           # " + NOTE),
    (r"\{408\}", u"{417}"),
    (r'u"408 keys each"', u'u"417 keys each"'),
    (r"all\(v == 408 for v in counts\.values\(\)\)", u"all(v == 417 for v in counts.values())"),
    (r"list\(counts\.values\(\)\)\[0\] == 408", u"list(counts.values())[0] == 417"),
    (r'u"语言键数（ZF109 起 408）", 408,', u'u"语言键数（ZF112 起 417）", 417,'),
    (r"len\(table\) == 408", u"len(table) == 417"),
    (r'u"%s：总键数 408[^"]*"', u'u"%s：总键数 417（… + ZF112 锂电池构造间 9）"'),
    (r'u"四语言各 408 键[^"]*"', u'u"四语言各 417 键（ZF107 +48；ZF109 +10；ZF112 +9）"'),
    (r'总键数 408[^）]*）', u'总键数 417（… + ZF112 锂电池构造间 9）'),
    (r"B11 四语言各 408", u"B11 四语言各 417"),
    (r"C2 四语言各 408", u"C2 四语言各 417"),
    (r"四份语言键数一致且 = 408", u"四份语言键数一致且 = 417"),
    (r"408（ZF109 起）", u"417（ZF112 起）"),
]

fails = []


def main():
    n = 0
    for f in FILES:
        p = os.path.join(TOOLS, f)
        if not os.path.exists(p):
            fails.append(u"%s 不在盘上" % f)
            continue
        text = io.open(p, encoding="utf-8").read()
        after, hits = text, 0
        for pat, rep in SUBS:
            after, cnt = re.subn(pat, rep, after)
            if cnt > 1:
                fails.append(u"%s：%s 命中 %d 次（要求 ≤1）" % (f, pat[:28], cnt))
            hits += cnt
        if hits == 0:
            print(u"  [--]   %-22s 没有 408 锚点（不动）" % f)
            continue
        try:
            compile(after, f, u"exec")
        except SyntaxError as e:
            fails.append(u"%s：改完语法不过（第 %s 行：%s）" % (f, e.lineno, e.msg))
            continue
        io.open(p, "w", encoding="utf-8", newline=u"").write(after)
        back = io.open(p, encoding="utf-8").read()
        bad = [i + 1 for i, line in enumerate(back.split(u"\n"))
               if re.search(r"(==|=|\{)\s*408\b|408\s*keys each|总键数 408|各 408 键", line)]
        print(u"  [OK]   %-22s 替换 %d 处；像断言的残留 408 = %d" % (f, hits, len(bad)))
        if bad:
            fails.append(u"%s：还有像断言的 408（行 %s）" % (f, bad[:4]))
        n += 1
    print(u"\n改到的文件 %d 份" % n)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
