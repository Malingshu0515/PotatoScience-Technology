# -*- coding: utf-8 -*-
"""ToolLint.py —— 工具脚本自检（第 9 道门，0.10 ZF70 新增）

来历：我在这套脚本上反复踩两类坑 ——
 ① **语法**：在 Python 字符串里用 ASCII 双引号包中文（`u"... 他说"就这样" ..."`），
    ZF64/65/66/67/69/70 各踩一次，每次白花一轮（`py_compile` 能当场抓住）；
 ② **流程**：某一轮的脚本把该守的规矩漏了（ZF63 的 publish 先拷再报错 ⇒ 留下"幽灵旧 jar"；
    ZF34 的备份清单凭记忆写 ⇒ 漏文件）。这类错误**跑起来不报**，只能靠检查脚本本身。

于是这道门干两件事：
  ① 把 `build/zftools/*.py` 逐个**真编译**，语法错误 = FAIL；
  ② 按**命名约定**检查每个阶段脚本有没有写全那几条硬规矩：
     · `_zfNN_publish.py`：`shutil.copy2` 必须出现在 `if fails` 之后（先查后拷）；
     · `_zfNN_backup.py` / `_zfNN_archive.py`：必须**核哈希**（sha1 比对），不是只 copy；
     · `_zfNN_docs.py`：必须要求"恰好命中 1 次"（`count(` + `!= 1` 这类断言）。

Java 探针不在这里编译（要整条 Minecraft classpath，成本高），语法由 `runServer` 兜着。

退出码 0 = 无语法错误、无流程缺失（历史的旧脚本若不合规会报 WARN，不判失败）。
"""
import io
import os
import py_compile
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 本轮（当前最高轮次）的脚本才判 FAIL；更早的历史脚本只 WARN（它们已经交付过，不改）
ROUNDS = sorted(set(int(m.group(1)) for m in
                    (re.match(r"_zf(\d+)_", n) for n in os.listdir(HERE) if n.endswith(".py")) if m))
LATEST = ROUNDS[-1] if ROUNDS else 0

fails = []
warns = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def lint_publish(name, text):
    """先查后拷：copy2 必须在 if fails 之后"""
    if "shutil.copy2" not in text:
        return u"没有 shutil.copy2（是不是没出成品？）"
    i_copy = text.find("shutil.copy2")
    i_fail = text.find("if fails")
    if i_fail < 0:
        return u"没有 `if fails` 关卡（必须先查完再拷）"
    if i_copy < i_fail:
        return u"`shutil.copy2` 出现在 `if fails` **之前** —— 就是 ZF63 那个「先拷后报错」的坑"
    return None


def lint_hash(name, text):
    if "sha1(" not in text and "Get-FileHash" not in text:
        return u"没有核哈希（备份/归档必须逐份比对拷贝前后的哈希）"
    return None


def lint_docs(name, text):
    if "count(" not in text and u"命中" not in text:
        return u"没有『恰好命中 1 次』的唯一性断言（§4.36：模糊匹配会顺手改到别处）"
    return None


CHECKS = (("publish", lint_publish), ("backup", lint_hash), ("archive", lint_hash), ("docs", lint_docs))


def main():
    scripts = sorted(n for n in os.listdir(HERE) if n.endswith(".py"))
    print(u"== ① 语法：逐个 py_compile ==")
    n_ok = 0
    for n in scripts:
        p = os.path.join(HERE, n)
        try:
            py_compile.compile(p, cfile=os.path.join(HERE, "__pycache__", n + "c"), doraise=True)
            n_ok += 1
        except py_compile.PyCompileError as e:
            msg = str(e).replace("\n", " ")
            fails.append(u"%s 语法错误：%s" % (n, msg[-220:]))
            print(u"  [FAIL] %s" % n)
        except Exception as e:
            fails.append(u"%s 编译异常：%s" % (n, e))
            print(u"  [FAIL] %s" % n)
    print(u"  编译通过 %d / %d 个脚本" % (n_ok, len(scripts)))

    print()
    print(u"== ② 阶段脚本的硬规矩（本轮 zf%d 判失败，更早的只提示） ==" % LATEST)
    n_checked = 0
    for n in scripts:
        m = re.match(r"_zf(\d+)_(.+)\.py$", n)
        if not m:
            continue
        rnd, kind = int(m.group(1)), m.group(2)
        for suffix, fn in CHECKS:
            if kind == suffix:
                n_checked += 1
                problem = fn(n, read(os.path.join(HERE, n)))
                if problem:
                    line = u"%s（%s）" % (problem, n)
                    if rnd == LATEST:
                        fails.append(line)
                        print(u"  [FAIL] " + line)
                    else:
                        warns.append(line)
                        print(u"  [WARN] " + line)
                else:
                    print(u"  [OK]   %s" % n)
    print(u"  检查了 %d 个阶段脚本（round %d 为当前轮次）" % (n_checked, LATEST))

    print()
    print(u"脚本 %d 个；语法失败 = %d；流程失败 = %d；历史提示 = %d"
          % (len(scripts), len(fails), len([f for f in fails if u"语法" not in f]), len(warns)))
    for f in fails:
        print(u"  !! " + f)
    print(u"结论: %s" % (u"有问题" if fails else u"通过"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
