# -*- coding: utf-8 -*-
"""_zf70_docs2.py —— ZF70 补充档案：新增第 9 道门 ToolLint.py

第一遍 `_zf70_docs.py` 已经写完 §4.42/§4.43/§5/§6.17/§9；
这一遍补的是**写完之后才做出来**的东西（工具脚本自检门），所以单独一个脚本，
一样要求每处替换恰好命中 1 次。
"""
import io
import sys

DOCS = r"E:\PotatoST\docs\开发档案.md"

fails = []
applied = []


def rep(text, old, new, why):
    n = text.count(old)
    if n != 1:
        fails.append(u"%s：命中 %d 次（要求恰好 1 次）" % (why, n))
        return text
    applied.append(why)
    return text.replace(old, new, 1)


def main():
    with io.open(DOCS, encoding="utf-8") as fh:
        text = fh.read()
    before = text.count("\n") + 1

    # ---------- ① §11.1 门清单加 ToolLint.py ----------
    old = u"| `GroupEnergyCheck.java` | **纯算法验算**"
    new = (u"| `ToolLint.py` | **工具脚本自检**：`build\\zftools\\*.py` 逐个 `py_compile`（语法）+ "
           u"阶段脚本的硬规矩（publish 必须先查后拷、backup/archive 必须核哈希、docs 必须要求恰好命中 1 次）"
           u" | 失败项 = 0 |\n"
           u"| `GroupEnergyCheck.java` | **纯算法验算**")
    text = rep(text, old, new, u"§11.1 加 ToolLint 行")

    old = u"> `TextureCheck.py` 是 **0.10 ZF61 新增**的第 8 项"
    new = (u"> `ToolLint.py` 是 **0.10 ZF70 新增**的第 9 项。来历很直白：我在这些脚本上**反复**踩两类错 ——\n"
           u"> ① 在 Python 字符串里用 ASCII 引号包中文（ZF64/65/66/67/69/70 各一次，每次白花一轮）；\n"
           u"> ② 把该守的流程漏了（ZF63 的 publish **先拷后报错**，留下一个「幽灵旧 jar」）。\n"
           u"> ① 交给 `py_compile`（206 个脚本 1 秒内编译完，语法错误当场现形）；\n"
           u"> ② 按命名约定查 `_zfNN_publish/backup/archive/docs.py` 有没有写全那几条规矩。\n"
           u"> **首跑就把历史债点出来了**：`_zf55_~_zf63_publish.py` 全部是「先 `copy2` 后判 fails」——\n"
           u"> 这正是 ZF63 那次事故的形状（那一轮之后才改成先查后拷）；`_zf34_~_zf49_archive.py` 也没有核哈希。\n"
           u"> 这些历史脚本已经交付过，所以只报 WARN 不判失败；**本轮及以后**的同类问题一律 FAIL。\n"
           u"\n"
           u"> `TextureCheck.py` 是 **0.10 ZF61 新增**的第 8 项")
    text = rep(text, old, new, u"§11.1 ToolLint 说明")

    # ---------- ② §5 ZF70 行补 ⑧ ----------
    old = u"新写常驻 `_zf70_verify.py`（**87 项**）"
    new = (u"新写常驻 `_zf70_verify.py`（**87 项**）；⑧ 顺手立了**第 9 道门 `ToolLint.py`**"
           u"（工具脚本 `py_compile` + 阶段脚本硬规矩，首跑 206 个脚本语法全过、并把 zf55~zf63 的"
           u"publish「先拷后报错」历史债以 27 条 WARN 点出来）")
    text = rep(text, old, new, u"§5 ZF70 行补 ⑧")

    if fails:
        print(u"**有失败项，未写盘**：")
        for f in fails:
            print(u"  !! " + f)
        return 1
    with io.open(DOCS, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(u"已改 %d 处：" % len(applied))
    for a in applied:
        print(u"  [OK] " + a)
    print(u"行数 %d -> %d" % (before, text.count("\n") + 1))
    print(u"失败项 = 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
