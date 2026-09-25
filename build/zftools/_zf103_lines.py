# -*- coding: utf-8 -*-
u"""_zf103_lines.py —— 只读诊断：把 ModArmorItems.class 的**行号表**打出来

目的：给"韧性 1.0 被 dconst_1 内联、常量池里查不到"这件事找一条**可失败**的取证路径。
javac 带 `-g`（本项目默认）会在每个方法的 Code 属性里写 LineNumberTable，
于是"第 N 行用了哪个常量"是可以机械读出来的 —— 这正是 K4 那一刀需要的证据。
"""
import struct
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PATH = r"E:\PotatoST\build\classes\java\main\com\potatost\mod\ModArmorItems.class"
SRC = r"E:\PotatoST\src\main\java\com\potatost\mod\ModArmorItems.java"


def parse_pool(data):
    n = struct.unpack_from(">H", data, 8)[0]
    i, idx, pool = 10, 1, {}
    while idx < n:
        tag = data[i]
        i += 1
        if tag == 0:
            pool[idx] = ("end", None)
        elif tag == 1:
            ln = struct.unpack_from(">H", data, i)[0]
            i += 2
            pool[idx] = ("utf8", data[i:i + ln].decode("utf-8", "replace"))
            i += ln
        elif tag in (7, 8, 16, 19, 20):
            pool[idx] = ("ref", struct.unpack_from(">H", data, i)[0])
            i += 2
        elif tag == 15:
            i += 3
        elif tag == 3:
            pool[idx] = ("int", struct.unpack_from(">i", data, i)[0])
            i += 4
        elif tag == 4:
            pool[idx] = ("float", struct.unpack_from(">f", data, i)[0])
            i += 4
        elif tag == 6:
            pool[idx] = ("double", struct.unpack_from(">d", data, i)[0])
            i += 8
            idx += 1
        elif tag in (9, 10, 11, 12, 17, 18):
            a, b = struct.unpack_from(">HH", data, i)
            i += 4
            pool[idx] = ("nt", a, b)
        elif tag == 5:
            pool[idx] = ("long", struct.unpack_from(">q", data, i)[0])
            i += 8
            idx += 1
        else:
            raise ValueError("tag %d" % tag)
        idx += 1
    return pool, i

def skip_attributes(data, i, pool, out):
    cnt = struct.unpack_from(">H", data, i)[0]
    i += 2
    for _ in range(cnt):
        ni = struct.unpack_from(">H", data, i)[0]
        ln = struct.unpack_from(">I", data, i + 2)[0]
        body = i + 6
        out.append((pool.get(ni, ("?",))[1] if pool.get(ni) else "?", body, ln))
        i = body + ln
    return i


def main():
    data = open(PATH, "rb").read()
    pool, i = parse_pool(data)
    i += 6
    ifc = struct.unpack_from(">H", data, i)[0]
    i += 2 + 2 * ifc
    fields = struct.unpack_from(">H", data, i)[0]
    i += 2
    for _ in range(fields):
        i += 6
        i = skip_attributes(data, i, pool, [])
    methods = struct.unpack_from(">H", data, i)[0]
    i += 2
    for _ in range(methods):
        ni, di = struct.unpack_from(">HH", data, i)
        i += 6
        attrs = []
        i = skip_attributes(data, i, pool, attrs)
        name = pool[ni][1]
        if name not in ("<clinit>", "<init>"):
            continue
        for aname, body, ln in attrs:
            if aname != "Code":
                continue
            code_len = struct.unpack_from(">I", data, body + 4)[0]
            code = data[body + 8:body + 8 + code_len]
            # exception table
            et = struct.unpack_from(">H", data, body + 8 + code_len)[0]
            p = body + 8 + code_len + 2 + 8 * et
            sub = []
            skip_attributes(data, p, pool, sub)
            print(u"\n==== %s：Code %d 字节，子属性 %s ====" % (name, code_len, [s[0] for s in sub]))
            for sname, sbody, slen in sub:
                if sname != "LineNumberTable":
                    continue
                cnt = struct.unpack_from(">H", data, sbody)[0]
                lines = []
                for k in range(cnt):
                    start, line = struct.unpack_from(">HH", data, sbody + 2 + 4 * k)
                    lines.append((start, line))
                src = open(SRC, encoding="utf-8").read().split(u"\n")
                for k, (start, line) in enumerate(lines):
                    end = lines[k + 1][0] if k + 1 < len(lines) else code_len
                    # 扫这段字节码里的关键指令
                    tags = []
                    for b in range(start, min(end, len(code))):
                        op = code[b]
                        if op == 0x0E:
                            tags.append("dconst_0")
                        elif op == 0x0F:
                            tags.append("dconst_1")
                        elif op == 0x12 and b + 1 < len(code):
                            v = pool.get(code[b + 1])
                            if v and v[0] in ("utf8", "float", "double", "int"):
                                tags.append("ldc(%s)" % (v[1],))
                        elif op == 0x11 and b + 2 < len(code):
                            tags.append("sipush(%d)" % struct.unpack_from(">h", code, b + 1)[0])
                    txt = src[line - 1].strip() if line - 1 < len(src) else u""
                    print(u"  L%-4d off=%-5d %-42s | %s" % (line, start, u",".join(tags)[:42], txt[:80]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
