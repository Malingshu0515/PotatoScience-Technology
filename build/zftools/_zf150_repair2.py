# -*- coding: utf-8 -*-
"""_zf150_repair2.py —— 系统修那批"顶格"的伤（别人的 ZF147 改写丢了缩进）+ 中文串里的 ASCII 引号

## 病症（同一种，散在多份门里）

`ZF147` 那轮（把版本线抬到 0.12）用脚本改注释 + 改 `check(...)` 时，
把**函数体内的**语句写到了**第 0 列**，例如：

    _zf73_verify.py:237   check(u"C1 mod_version = 0.12", ...)      ← 应为 8 空格缩进
    _zf78_verify.py:557   check(u"mod_version 现在是 0.12（…）",
                              props is not None and u"mod_version=0.11" in props)
    _zf79_verify.py:283   check(u"mod_version 现在是 0.12（…）", …)

另有 `_zf78_verify.py` 两处**中文串里用了 ASCII 双引号**（把字符串截断）。

## 修法

逐行扫：**缩进比前一行浅、且这行以 `check(` 开头** ⇒ 判定是"被压到第 0 列"，
按前一行的缩进还原（并把它后面直到下一个等/浅缩进的非空行一起带走）。
中文串里的 ASCII 引号按 §4.24 族换成「」。
每份改完 `ast.parse` 自检；不过就不写盘。

⚠ 本脚本**只修语法**，不改任何判据数值。
"""
import ast
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOOLS = r"E:\PotatoST\build\zftools"
fails = []


def indent_of(ln):
    return len(ln) - len(ln.lstrip(u" "))


def fix_indent(text):
    """把被压到第 0 列的 check(...) 还原缩进；返回 (新文本, 修了几处)"""
    lines = text.split(u"\n")
    out = list(lines)
    fixed = 0
    for i, ln in enumerate(lines):
        if not ln.startswith(u"check("):
            continue
        # 往前找最近的非空行，拿它的缩进当基准
        j = i - 1
        while j >= 0 and not lines[j].strip():
            j -= 1
        if j < 0:
            continue
        base = indent_of(lines[j])
        if base <= 0:
            continue          # 前一行也是顶格 ⇒ 这里本来就该顶格（模块级），不动
        out[i] = u" " * base + ln
        fixed += 1
        # 把它后面缩进在 (0, base) 之间、且不是注释独立段的续行一起抬起
        k = i + 1
        while k < len(lines):
            nxt = lines[k]
            if not nxt.strip():
                break
            ni = indent_of(nxt)
            if ni == 0:
                break
            need = base + (ni - 0) if ni > 0 else base
            # 续行原本是相对 check( 的 6 空格，现在要整体平移 base
            out[k] = u" " * (ni + base) + nxt.lstrip(u" ")
            fixed += 1
            k += 1
    return u"\n".join(out), fixed


def fix_quotes(text):
    """中文串里的 ASCII 双引号 -> 「」；只动 `check(u"..."` 这种明显形态"""
    pat = re.compile(u'(check\\(u"[^"]*)"([^"]*)"([^"]*",)')
    new, n = pat.subn(lambda m: u'%s「%s」%s' % (m.group(1), m.group(2), m.group(3)), text)
    return new, n


def main():
    total_fixed = 0
    for f in sorted(os.listdir(TOOLS)):
        if not (f.startswith("_zf") and f.endswith("_verify.py")):
            continue
        p = os.path.join(TOOLS, f)
        t = io.open(p, encoding="utf-8").read()
        try:
            ast.parse(t)
            continue                       # 本来就好的，跳过
        except SyntaxError:
            pass
        # 先修引号，再修缩进
        t2, nq = fix_quotes(t)
        t3, ni = fix_indent(t2)
        try:
            ast.parse(t3)
        except SyntaxError as e:
            fails.append((f, str(e)))
            print(u"  !! %-24s 修完仍错：%s" % (f, e))
            lines = t3.split(u"\n")
            for k in range(max(0, e.lineno - 3), min(len(lines), e.lineno + 1)):
                print(u"        %4d: %s" % (k + 1, lines[k]))
            continue
        io.open(p, "w", encoding="utf-8", newline="\n").write(t3)
        total_fixed += 1
        print(u"  [OK] %-24s 修了 %d 处引号 + %d 处缩进" % (f, nq, ni))

    print(u"\n共修好 %d 份" % total_fixed)
    print(u"\n== 最终语法自检 ==")
    bad, total = [], 0
    for f in sorted(os.listdir(TOOLS)):
        if not (f.startswith("_zf") and f.endswith("_verify.py")):
            continue
        total += 1
        try:
            ast.parse(io.open(os.path.join(TOOLS, f), encoding="utf-8").read())
        except SyntaxError as e:
            bad.append((f, str(e)))
    print(u"  %d 份，有问题 %d 份" % (total, len(bad)))
    for f, e in bad:
        print(u"   !! %s : %s" % (f, e))
    print(u"\n失败项 = %d" % (len(fails) + len(bad)))
    return 1 if (fails or bad) else 0


if __name__ == "__main__":
    sys.exit(main())
