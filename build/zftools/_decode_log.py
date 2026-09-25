# -*- coding: utf-8 -*-
"""_decode_log.py —— 把日志转成 UTF-8（PowerShell 的 `>`/`*>` 默认写 UTF-16LE，read 工具会当二进制）

用法： python build/zftools/_decode_log.py <日志路径> [输出路径]
不写输出路径时，默认写 <原名>.utf8.txt。
"""
import io
import sys


def main(argv):
    src = argv[0]
    dst = argv[1] if len(argv) > 1 else src + ".utf8.txt"
    raw = io.open(src, "rb").read()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        text, used = raw.decode("utf-16", "replace"), "utf-16"
    else:
        try:
            text, used = raw.decode("utf-8"), "utf-8"
        except UnicodeDecodeError:
            text, used = raw.decode("gbk", "replace"), "gbk"
    io.open(dst, "w", encoding="utf-8", newline="\n").write(text)
    print(u"%s -> %s（按 %s 解，%d 字符）" % (src, dst, used, len(text)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
