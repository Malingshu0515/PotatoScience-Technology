# -*- coding: utf-8 -*-
"""_zf55_gatesum.py —— 把门日志里的关键行抽成 UTF-8 摘要（控制台是 GBK，直接 print 会炸）"""
import io
import re

SRC = r"E:\PotatoST\build\zftools\_zf55_gates.log"
DST = r"E:\PotatoST\build\zftools\_zf55_gates_summary.txt"

PAT = re.compile(u"\u5931\u8d25|\u7ed3\u8bba|WARN|FAIL|ERROR|\u5171|\u603b|\u672a\u7ffb\u8bd1")


def main():
    raw = io.open(SRC, "rb").read()
    # PowerShell 5.1 的 *> 重定向默认写 UTF-16LE（带 BOM），先认它
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        text = raw.decode("utf-16", "replace")
    else:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("gbk", "replace")
    out = []
    for block in text.split("===================="):
        body = block.strip("\n")
        if not body.strip():
            continue
        lines = body.splitlines()
        out.append(u"---- " + lines[0][:70])
        for line in lines:
            if PAT.search(line):
                out.append(u"    " + line[:200])
    io.open(DST, "w", encoding="utf-8").write(u"\n".join(out))
    print(u"lines = %d" % len(out))


if __name__ == "__main__":
    main()
