# -*- coding: utf-8 -*-
u"""_zf142_quotefix.py —— 把「中文字符串里混进来的 ASCII 双引号」自动换成「」

这个坑在本工程已经咬了三次（ZF133 的 `_zf133_docs.py`、ZF140 的 `_zf140_docs.py`、ZF142 的
`_zf142_docs.py`）。症状固定：`SyntaxError: invalid syntax. Perhaps you forgot a comma?` ——
**指向的行是对的，但原因看着完全不搭**（看着像少个逗号，其实字符串被提前截断了）。

写这个工具本身踩了三个坑，都记在这里（免得下次再走一遍）：
  ① 只看相邻字符 ⇒ 把**收尾引号**也当成正文（`……旧成品与 `.sha1`；"` 里那个 `"` 前面是中文分号）；
  ② 不认**三引号** ⇒ 状态机在模块 docstring 第一行就"进了字符串"再没出来；
  ③ 状态**逐行重置** ⇒ `SECTION = u\"\"\"…\"\"\"` 这种跨行三引号，第二行起又被当成单引号串。
  ⇒ 现在是**整份文件走一遍**的状态机：out / single / triple 三态，跨行保持。

跑法：python build\\zftools\\_zf142_quotefix.py <file.py> [--write]
"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

AFTER = set(u",) \t+%:;].}\n")     # 这些字符跟在引号后面 ⇒ 那是一个**收尾**引号


def fix_text(text):
    out, problems = [], []
    state = u"out"          # out / single / triple
    n, line, i = 0, 1, 0
    while i < len(text):
        if text[i:i + 3] == u'"""' and state != u"single":
            state = u"triple" if state == u"out" else u"out"
            out.append(u'"""')
            i += 3
            continue
        c = text[i]
        if c == "\n":
            if state == u"single":
                problems.append((line, u"单引号字符串没闭合就到行尾了"))
                state = u"out"
            line += 1
            out.append(c)
            i += 1
            continue
        if c == '"':
            if state == u"out":
                state = u"single"
                out.append(c)
            elif state == u"triple":
                out.append(c)                      # 三引号里面的引号是正文，合法
            else:
                nxt = text[i + 1] if i + 1 < len(text) else ""
                if nxt in AFTER or nxt == "":
                    state = u"out"
                    out.append(c)
                else:
                    out.append(u"\u300c" if n % 2 == 0 else u"\u300d")
                    n += 1
            i += 1
            continue
        out.append(c)
        i += 1
    if state != u"out":
        problems.append((line, u"文件走完还在 %s 状态里" % state))
    return u"".join(out), n, problems


def main(argv):
    path = argv[0]
    write = "--write" in argv
    text = io.open(path, encoding="utf-8", newline="").read()
    new, n, problems = fix_text(text)
    lines = new.split("\n")
    print(u"%s：换掉 %d 处（正文里的 ASCII 双引号 → 「」）" % (path, n))
    for ln, why in problems:
        print(u"  !! 第 %d 行：%s —— %s" % (ln, why, lines[ln - 1][:90]))
    if problems:
        print(u"  ⇒ 有问题，**不写盘**，先人工看一眼")
        return 1
    if write:
        io.open(path, "w", encoding="utf-8", newline="").write(new)
        print(u"  >>> 已写回")
    else:
        print(u"  （只试算；加 --write 才写回）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
