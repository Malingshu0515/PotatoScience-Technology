# -*- coding: utf-8 -*-
r"""_rzh_run_one.py —— 跑一个门并把**失败项**单独落成 UTF-8 文件。

为什么需要：门自己的失败列表只写在内存里、最后汇总打印，而 PowerShell 控制台
按 GBK 解码 UTF-8 输出 ⇒ 中文全成乱码、`Select-String` 也筛不出来。这里直接
抓子进程的字节流，按 UTF-8 解，只留结论与失败项。

用法：`python build/zftools/_rzh_run_one.py _zf117_verify.py`
"""
from __future__ import print_function
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, u"_rzh_one.txt")


def main():
    if len(sys.argv) < 2:
        print(u"用法: python _rzh_run_one.py <门文件名> [更多...]")
        return 1
    lines = []
    for name in sys.argv[1:]:
        p = subprocess.run([sys.executable, os.path.join(HERE, name)],
                           cwd=ROOT, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=600)
        text = p.stdout.decode(u"utf-8", u"replace")
        lines.append(u"=" * 72)
        lines.append(u"== %s  (exit %d)" % (name, p.returncode))
        lines.append(u"=" * 72)
        # 结论行 + 失败项：门的失败列表通常带 [FAIL] / 失败项 / 期望
        keep = []
        for l in text.split(u"\n"):
            if (u"[FAIL]" in l or u"\u5931\u8d25" in l or u"\u671f\u671b" in l
                    or u"\u901a\u8fc7" in l or u"\u7ed3\u8bba" in l):
                keep.append(l)
        if not keep:
            keep = text.split(u"\n")[-12:]
        lines.extend(keep)
        lines.append(u"")
    with io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n") as f:
        f.write(u"\n".join(lines) + u"\n")
    print(u"wrote %s" % OUT)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
