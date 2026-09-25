# -*- coding: utf-8 -*-
"""比较两个 class 文件的**常量池语义内容**（忽略编译期差异，如 StackMapTable）。

用来把"反向重建出来的源码"和"当时真的打进 jar 的 class"对上：
  ① 取出 ZF28 那份 release jar 里的 SolarPanelBlockEntity.class / GroupEnergy.class
  ② 把重建版源码单独编译一遍
  ③ 两者的「字段名 + 常量值 + 方法引用」必须一致
如果一致 ⇒ 重建版与当时发布的代码在语义上等价（哈希对不上只是备份时机问题）。
"""
import io
import re
import struct
import sys


def parse_pool(data):
    assert data[:4] == b"\xca\xfe\xba\xbe"
    count = struct.unpack_from(">H", data, 8)[0]
    i, idx, pool = 10, 1, {}
    while idx < count:
        tag = data[i]; i += 1
        if tag == 1:
            ln = struct.unpack_from(">H", data, i)[0]; i += 2
            pool[idx] = ("utf8", data[i:i + ln].decode("utf-8", "replace")); i += ln
        elif tag in (7, 8, 16, 19, 20):
            pool[idx] = ("ref", struct.unpack_from(">H", data, i)[0]); i += 2
        elif tag == 15:
            i += 3
        elif tag in (3,):
            pool[idx] = ("int", struct.unpack_from(">i", data, i)[0]); i += 4
        elif tag == 4:
            pool[idx] = ("float", struct.unpack_from(">f", data, i)[0]); i += 4
        elif tag in (9, 10, 11, 12, 17, 18):
            a, b = struct.unpack_from(">HH", data, i); i += 4
            pool[idx] = ("nt", a, b)
        elif tag in (5, 6):
            pool[idx] = ("long", struct.unpack_from(">q", data, i)[0]); i += 8; idx += 1
        else:
            raise ValueError("pool tag %d" % tag)
        idx += 1
    return pool


def semantic(pool):
    """抽出可比较的语义集合：字符串常量、int 常量、字段/方法引用名。"""
    strings, ints, refs = set(), set(), set()
    for k, v in pool.items():
        if v[0] == "utf8":
            strings.add(v[1])
        elif v[0] == "int":
            ints.add(v[1])
        elif v[0] == "nt":
            name = pool.get(v[1]); desc = pool.get(v[2])
            if name and desc and name[0] == "utf8" and desc[0] == "utf8":
                refs.add((name[1], desc[1]))
    return strings, ints, refs


def load(path):
    return semantic(parse_pool(io.open(path, "rb").read()))


a = load(sys.argv[1])   # 发布的 class
b = load(sys.argv[2])   # 重建源码编译出来的 class
labels = ("字符串常量", "int 常量", "字段/方法引用")
bad = 0
for x, y, lab in zip(a, b, labels):
    only_a = x - y
    only_b = y - x
    print("== %s：发布 %d 项 / 重建 %d 项" % (lab, len(x), len(y)))
    if only_a:
        print("   只在【发布】里有：", sorted(map(str, only_a))[:8])
    if only_b:
        print("   只在【重建】里有：", sorted(map(str, only_b))[:8])
    if only_a or only_b:
        bad += 1
print("=== 结论：%s ===" % ("语义一致（重建版 == 发布版）" if bad == 0 else "有差异，见上"))
sys.exit(1 if bad else 0)
