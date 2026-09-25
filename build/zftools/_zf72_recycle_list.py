# -*- coding: utf-8 -*-
u"""_zf72_recycle_list.py —— 只读：把回收站里名字含 PotatoST 的条目列出来（含 $R 实体是否还在、里面有什么）

用途：ZF71 的备份根 `C:\\Users\\Administrator\\Desktop\\PotatoST救援_20260917_183054`
在 2026-09-19 13:36 被删进了回收站。开工前先确认**能不能还原**、里面有哪些子目录。
只读，不动回收站里任何东西。
"""
import os
import struct
import sys

ROOTS = [u"C:\\$RECYCLE.BIN", u"E:\\$RECYCLE.BIN"]
NEEDLE = u"PotatoST"


def orig_path(info_path):
    with open(info_path, "rb") as fh:
        data = fh.read()
    size = struct.unpack("<Q", data[8:16])[0]
    return data[28:].decode("utf-16-le", "ignore").rstrip(u"\x00"), size


def tree(path, depth=2, prefix=u"      "):
    lines = []
    try:
        names = sorted(os.listdir(path))
    except Exception as exc:
        return [u"%s<无法读取: %s>" % (prefix, exc)]
    for name in names[:40]:
        full = os.path.join(path, name)
        is_dir = os.path.isdir(full)
        try:
            size = 0 if is_dir else os.path.getsize(full)
        except Exception:
            size = -1
        lines.append(u"%s%s %s  %d B" % (prefix, u"[DIR]" if is_dir else u"[FILE]", name, size))
        if is_dir and depth > 1:
            lines.extend(tree(full, depth - 1, prefix + u"   "))
    if len(names) > 40:
        lines.append(u"%s... 共 %d 项" % (prefix, len(names)))
    return lines


def main():
    found = 0
    for root in ROOTS:
        if not os.path.isdir(root):
            continue
        for sid in sorted(os.listdir(root)):
            sid_dir = os.path.join(root, sid)
            if not os.path.isdir(sid_dir):
                continue
            for name in sorted(os.listdir(sid_dir)):
                if not name.startswith(u"$I"):
                    continue
                info = os.path.join(sid_dir, name)
                try:
                    orig, size = orig_path(info)
                except Exception:
                    continue
                if NEEDLE not in orig:
                    continue
                found += 1
                pair = os.path.join(sid_dir, u"$R" + name[2:])
                print(u"原始路径: %s" % orig)
                print(u"  记录大小: %d B" % size)
                print(u"  回收实体: %s" % (u"存在 " + pair if os.path.exists(pair) else u"已不存在（不可还原）"))
                if os.path.isdir(pair):
                    for line in tree(pair, 2):
                        print(line)
                print(u"")
    print(u"命中条目 = %d" % found)
    return 0


if __name__ == "__main__":
    sys.exit(main())
