# -*- coding: utf-8 -*-
u"""_zf72_recycle_probe.py —— 查「上一轮的改前件备份到哪去了」

背景：ZF71 的备份根是 `C:\\Users\\Administrator\\Desktop\\PotatoST救援_20260917_183054`，
本轮开工前核对时该目录**不存在**了。这个探针只读：把各盘回收站里的 `$I` 元数据解出来，
看是不是被删进了回收站（以及原始路径 / 大小 / 删除时间）。

只读，不改任何东西。
"""
import os
import struct
import sys
import datetime

ROOTS = [u"E:\\$RECYCLE.BIN", u"C:\\$RECYCLE.BIN", u"D:\\$RECYCLE.BIN"]

FMT = None


def filetime(raw):
    global FMT
    if FMT is None:
        FMT = struct.Struct("<Q")
    (value,) = FMT.unpack(raw)
    if value == 0:
        return u"-"
    # FILETIME: 100ns since 1601-01-01
    epoch = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=value // 10)
    return epoch.strftime("%Y-%m-%d %H:%M:%S")


def main():
    total = 0
    for root in ROOTS:
        if not os.path.isdir(root):
            print(u"NO ROOT  %s" % root)
            continue
        print(u"=== %s" % root)
        for sid in sorted(os.listdir(root)):
            sid_dir = os.path.join(root, sid)
            if not os.path.isdir(sid_dir):
                continue
            for name in sorted(os.listdir(sid_dir)):
                full = os.path.join(sid_dir, name)
                if not name.startswith(u"$I"):
                    continue
                try:
                    with open(full, "rb") as fh:
                        data = fh.read()
                    size = struct.unpack("<Q", data[8:16])[0]
                    deleted = filetime(data[16:24])
                    orig = data[28:].decode("utf-16-le", "ignore").rstrip(u"\x00")
                except Exception as exc:  # pragma: no cover
                    print(u"   ERR %s: %s" % (name, exc))
                    continue
                total += 1
                pair = os.path.join(sid_dir, u"$R" + name[2:])
                kind = u"[DIR]" if os.path.isdir(pair) else (u"[FILE]" if os.path.isfile(pair) else u"[GONE]")
                print(u"   %s %s  size=%d  deleted=%s" % (kind, orig, size, deleted))
    print(u"\n回收站条目数 = %d" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
