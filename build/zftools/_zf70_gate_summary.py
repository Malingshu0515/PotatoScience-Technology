# -*- coding: utf-8 -*-
"""_zf70_gate_summary.py —— 把门日志（UTF-8 版）按段汇总成一张表

用法: python build/zftools/_zf70_gate_summary.py <日志路径>
"""
import io
import re
import sys

PAT = re.compile(u"(失败项|非法|失败 =|警告 =|待画 =|结论:|检查项 =|总数 =|Loaded |条\\)|通过 =)")


def main(argv):
    path = argv[0]
    lines = io.open(path, encoding="utf-8").read().split("\n")
    name = u"(开头)"
    fails = 0
    for ln in lines:
        if "[FAIL]" in ln:
            fails += 1
        m = re.match(r"^=+ (.+?) =+$", ln.strip())
        if m:
            name = m.group(1)
            continue
        s = ln.strip()
        if PAT.search(s):
            print(u"%-16s %s" % (name, s))
    print(u"---- 整份日志里的 [FAIL] = %d" % fails)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
