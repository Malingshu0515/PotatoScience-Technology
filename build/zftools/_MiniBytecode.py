# -*- coding: utf-8 -*-
"""极简 class 文件常量池 + 方法体字节码扫描器（只为一个问题：Jade 怎么读能量）。

没有反编译器可用（JVM 里没有 CFR/Procyon，下载又会超时），所以自己走一遍
常量池 + Code 属性，把「调了哪些方法 / 用了哪些字符串 / 碰了哪些字段」打出来。
够用来回答"它是走能力还是走 NBT、是不是每帧查一次"。
"""
import io
import struct
import sys
import zipfile


def parse(data):
    assert data[:4] == b"\xca\xfe\xba\xbe", "不是 class 文件"
    pool_count = struct.unpack_from(">H", data, 8)[0]
    i = 10
    pool = {}
    idx = 1
    while idx < pool_count:
        tag = data[i]
        i += 1
        if tag == 1:                       # Utf8
            ln = struct.unpack_from(">H", data, i)[0]
            i += 2
            pool[idx] = data[i:i + ln].decode("utf-8", "replace")
            i += ln
        elif tag in (7, 8, 16, 19, 20):    # Class/String/MethodType/Module/Package
            pool[idx] = ("ref", struct.unpack_from(">H", data, i)[0])
            i += 2
        elif tag in (15,):                 # MethodHandle
            i += 3
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
            pool[idx] = struct.unpack_from(">I", data, i)[0]
            i += 4
        elif tag in (5, 6):                # Long/Double
            pool[idx] = struct.unpack_from(">q", data, i)[0]
            i += 8
            idx += 1
        else:
            raise ValueError("未知常量池 tag %d @%d" % (tag, i - 1))
        idx += 1

    def utf(k):
        v = pool.get(k)
        return v if isinstance(v, str) else ("?%s" % (v,))

    def cls(k):
        v = pool.get(k)
        if isinstance(v, tuple) and v[0] == "ref":
            return utf(v[1])
        return "?"

    def nat(k):
        v = pool.get(k)
        if isinstance(v, tuple) and v[0] == "ref":
            return utf(v[1])
        return "?"

    def ref(k):
        """9/10/11 → 类.名字:描述"""
        v = pool.get(k)
        if not isinstance(v, tuple) or len(v) < 3:
            return "?"
        return "%s.%s" % (cls(v[1]), nat(v[2]))

    # ---- 遍历方法，拿 Code 属性里的字节码 ----
    i += 6                                  # access_flags, this, super
    ifc = struct.unpack_from(">H", data, i)[0]
    i += 2 + ifc * 2
    fields = struct.unpack_from(">H", data, i)[0]
    i += 2
    for _ in range(fields):
        i += 6
        ac = struct.unpack_from(">H", data, i)[0]
        i += 2
        for _ in range(ac):
            ln = struct.unpack_from(">I", data, i + 2)[0]
            i += 6 + ln
    methods = struct.unpack_from(">H", data, i)[0]
    i += 2

    out = []
    for _ in range(methods):
        acc, name_i, desc_i = struct.unpack_from(">HHH", data, i)
        i += 6
        name, desc = utf(name_i), utf(desc_i)
        ac = struct.unpack_from(">H", data, i)[0]
        i += 2
        code = None
        for _ in range(ac):
            an_i = struct.unpack_from(">H", data, i)[0]
            ln = struct.unpack_from(">I", data, i + 2)[0]
            body = data[i + 6:i + 6 + ln]
            if utf(an_i) == "Code":
                code = body
            i += 6 + ln
        if code is None:
            continue
        clen = struct.unpack_from(">I", code, 4)[0]
        bc = code[8:8 + clen]
        hits = []
        j = 0
        while j < len(bc):
            op = bc[j]
            if op == 0xB2 or op == 0xB3:            # getstatic/putstatic
                k = struct.unpack_from(">H", bc, j + 1)[0]
                hits.append("fld  %s" % ref(k))
                j += 3
            elif op in (0xB4, 0xB5):                # getfield/putfield
                k = struct.unpack_from(">H", bc, j + 1)[0]
                hits.append("fld  %s" % ref(k))
                j += 3
            elif op in (0xB6, 0xB7, 0xB8, 0xB9):    # invoke*
                k = struct.unpack_from(">H", bc, j + 1)[0]
                hits.append("call %s" % ref(k))
                j += 5 if op == 0xB9 else 3
            elif op == 0x12:                        # ldc
                hits.append("str  %r" % utf(bc[j + 1]))
                j += 2
            elif op == 0x13:                        # ldc_w
                k = struct.unpack_from(">H", bc, j + 1)[0]
                hits.append("str  %r" % utf(k))
                j += 3
            elif op == 0x14:                        # ldc2_w
                j += 3
            else:
                j += 1
        out.append((name, desc, hits))
    return out


def main():
    jar = sys.argv[1]
    pat = sys.argv[2] if len(sys.argv) > 2 else ""
    z = zipfile.ZipFile(jar)
    for n in z.namelist():
        if not n.endswith(".class") or pat not in n:
            continue
        print("=" * 70)
        print(n)
        print("=" * 70)
        for name, desc, hits in parse(z.read(n)):
            print("  %s%s" % (name, desc))
            for h in hits:
                if any(k in h for k in ("energ", "Energ", "Capab", "capab", "View", "nbt", "Nbt",
                                        "NBT", "fetch", "Data", "sync", "Sync", "tag", "Tag",
                                        "Provider", "target", "Target", "BlockEntity", "blockEntity")):
                    print("      %s" % h)


main()
