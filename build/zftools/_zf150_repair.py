# -*- coding: utf-8 -*-
"""_zf150_repair.py —— 修 3 份**本来就坏**的门（别人的 ZF147 留下的伤）+ 顺带跟平键数

## 坏在哪（都**不是我造成的**，证据在下面）

`_zf150_retarget3.py` 写盘前有 `ast.parse` 自检；它报这三份"改后语法错误**没写盘**"，
而**同一行号**在"原样自检"里也报 ⇒ 改之前就是坏的。而我那两个脚本**只替换含 579 的行**，
坏的那几行（`_zf73:237`、`_zf79:283`、`_zf78:315`）**一个 579 都没有** ⇒ 不可能是它们碰的。

根因是另一条线的 `ZF147`（版本线抬到 0.12）留下一处**丢了缩进**的改写：

  `_zf73_verify.py:236-237`  注释与 `check(` 写到了**第 0 列**（原来在函数体里，缩进 8）
  `_zf79_verify.py:283`      同上
  `_zf78_verify.py:315`      中文串里用了 **ASCII 双引号**：`按"错格数最少"挑`
                             ⇒ 字符串在那对引号处被截断，后面全成了语法垃圾

## 修法

① 缩进：把顶格的 `check(` 与它后面的续行**还原成函数体内的缩进**（8 空格）。
② 引号：按本工程 §4.24 族的规矩换成**中文引号「」**（代码里本来就在中文字符串里）。
③ 顺带把这 3 份里**还写着的 579 判据**跟到 583（这是本轮的活）。

每处改完都 `ast.parse` 自检；不通过就**不写盘**并把原文打出来。
"""
import ast
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOOLS = r"E:\PotatoST\build\zftools"
fails = []

PATCHES = [
    # ---- _zf73_verify.py：顶格的注释与 check 缩回函数体 ----
    ("_zf73_verify.py",
     u"#   判据没放宽：仍是逐字比 `mod_version` 那一个常量。\n"
     u'check(u"C1 mod_version = 0.12", re.search(r"mod_version=0\\.12", props) is not None)',
     u"#   判据没放宽：仍是逐字比 `mod_version` 那一个常量。\n"
     u'    check(u"C1 mod_version = 0.12", re.search(r"mod_version=0\\.12", props) is not None)'),
    # ---- _zf79_verify.py：同上 ----
    ("_zf79_verify.py",
     u"# ⚠ ZF147：0.12 任务来了（用户点名）⇒ 跟到 0.12。\n"
     u'check(u"mod_version 现在是 0.12（ZF147 抬的版本线）",\n'
     u'          props is not None and u"mod_version=0.11" in props)',
     u"# ⚠ ZF147：0.12 任务来了（用户点名）⇒ 跟到 0.12。\n"
     u'    #    ⚠ ZF150 顺带修：这条的断言原来还写着 `mod_version=0.11`，与标签自相矛盾\n'
     u'    #      （标签说 0.12、断言查 0.11）—— 那是 ZF147 改标签时漏改的断言。\n'
     u'    check(u"mod_version 现在是 0.12（ZF147 抬的版本线）",\n'
     u'          props is not None and u"mod_version=0.12" in props)'),
    # ---- _zf78_verify.py：中文串里的 ASCII 双引号 -> 「」 ----
    ("_zf78_verify.py",
     u'check(u"诊断按"错格数最少"挑，并报第一处不符的格子",',
     u'check(u"诊断按「错格数最少」挑，并报第一处不符的格子",'),
]


def main():
    for fn, old, new in PATCHES:
        p = os.path.join(TOOLS, fn)
        if not os.path.exists(p):
            fails.append(u"%s 不在" % fn)
            print(u"  !! %s 不在" % fn)
            continue
        t = io.open(p, encoding="utf-8").read()
        if new in t and old not in t:
            print(u"  [幂等] %s" % fn)
            continue
        n = t.count(old)
        if n != 1:
            fails.append(u"%s 锚点 %d 次" % (fn, n))
            print(u"  !! %s 锚点 %d 次，没写盘" % (fn, n))
            continue
        out = t.replace(old, new)
        try:
            ast.parse(out)
        except SyntaxError as e:
            fails.append(u"%s 修完仍语法错误 %s" % (fn, e))
            print(u"  !! %s 修完仍语法错误，没写盘：%s" % (fn, e))
            continue
        io.open(p, "w", encoding="utf-8", newline="\n").write(out)
        print(u"  [OK] %s 已修 + 语法自检通过" % fn)

    # ---- 顺带：这 3 份里剩下的 579 判据跟到 583（整段替换，不逐行） ----
    print(u"\n== 顺带跟平这 3 份里的 579 ==")
    MORE = [
        ("_zf73_verify.py",
         u'check(u"B11 四语言各 579 键（… + ZF109 采油机 10）", all(v == 579 for v in counts.values()), str(counts))',
         u'check(u"B11 四语言各 583 键（… + ZF109 采油机 10 + ZF150 四种粒 4）",\n'
         u'          all(v == 583 for v in counts.values()), str(counts))'),
        ("_zf78_verify.py",
         u'check(u"四份语言键数一致且 = 579（ZF107 +48；ZF109 +10）",\n'
         u'          len(set(counts.values())) == 1 and list(counts.values())[0] == 579)',
         u'check(u"四份语言键数一致且 = 583（ZF107 +48；ZF109 +10；ZF150 四种粒 +4）",\n'
         u'          len(set(counts.values())) == 1 and list(counts.values())[0] == 583)'),
        ("_zf79_verify.py",
         u'check(u"四份语言键数一致且 = 579（ZF107 +48；ZF109 +10）",\n'
         u'          len(set(counts.values())) == 1 and list(counts.values())[0] == 579)',
         u'check(u"四份语言键数一致且 = 583（ZF107 +48；ZF109 +10；ZF150 四种粒 +4）",\n'
         u'          len(set(counts.values())) == 1 and list(counts.values())[0] == 583)'),
    ]
    for fn, old, new in MORE:
        p = os.path.join(TOOLS, fn)
        t = io.open(p, encoding="utf-8").read()
        if new in t and old not in t:
            print(u"  [幂等] %s" % fn)
            continue
        if t.count(old) != 1:
            fails.append(u"%s（跟平）锚点 %d 次" % (fn, t.count(old)))
            print(u"  !! %s（跟平）锚点 %d 次" % (fn, t.count(old)))
            continue
        out = t.replace(old, new)
        try:
            ast.parse(out)
        except SyntaxError as e:
            fails.append(u"%s 跟平后语法错误 %s" % (fn, e))
            print(u"  !! %s 跟平后语法错误：%s" % (fn, e))
            continue
        io.open(p, "w", encoding="utf-8", newline="\n").write(out)
        print(u"  [OK] %s 跟到 583" % fn)

    print(u"\n== 全部 _zf*_verify.py 语法自检 ==")
    bad = []
    for f in sorted(os.listdir(TOOLS)):
        if not (f.startswith("_zf") and f.endswith("_verify.py")):
            continue
        try:
            ast.parse(io.open(os.path.join(TOOLS, f), encoding="utf-8").read())
        except SyntaxError as e:
            bad.append(f)
            print(u"  !! %s : %s" % (f, e))
    if not bad:
        print(u"  [OK] 全部 %d 份都能解析"
              % len([f for f in os.listdir(TOOLS)
                     if f.startswith("_zf") and f.endswith("_verify.py")]))

    print(u"\n失败项 = %d" % (len(fails) + len(bad)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if (fails or bad) else 0


if __name__ == "__main__":
    sys.exit(main())
