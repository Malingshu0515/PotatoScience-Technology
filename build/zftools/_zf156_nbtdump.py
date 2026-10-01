# -*- coding: utf-8 -*-
"""ZF156 侦察用：把 .dat（gzip + NBT）读出来看关键键。

只读，不改任何东西。用法：
    python _zf156_nbtdump.py <file.dat> [键名 ...]
不给键名就打印根键清单 + NeoForgeData 的完整内容。
"""
import gzip
import sys


class Reader:
    def __init__(self, data):
        self.d = data
        self.i = 0

    def u1(self):
        v = self.d[self.i]
        self.i += 1
        return v

    def i2(self):
        v = int.from_bytes(self.d[self.i:self.i + 2], "big", signed=True)
        self.i += 2
        return v

    def u2(self):
        v = int.from_bytes(self.d[self.i:self.i + 2], "big")
        self.i += 2
        return v

    def i4(self):
        v = int.from_bytes(self.d[self.i:self.i + 4], "big", signed=True)
        self.i += 4
        return v

    def i8(self):
        v = int.from_bytes(self.d[self.i:self.i + 8], "big", signed=True)
        self.i += 8
        return v

    def f4(self):
        import struct
        v = struct.unpack(">f", self.d[self.i:self.i + 4])[0]
        self.i += 4
        return v

    def f8(self):
        import struct
        v = struct.unpack(">d", self.d[self.i:self.i + 8])[0]
        self.i += 8
        return v

    def s(self):
        n = self.u2()
        v = self.d[self.i:self.i + n].decode("utf-8", "replace")
        self.i += n
        return v

    def payload(self, t):
        if t == 1:
            return self.u1()
        if t == 2:
            return self.i2()
        if t == 3:
            return self.i4()
        if t == 4:
            return self.i8()
        if t == 5:
            return self.f4()
        if t == 6:
            return self.f8()
        if t == 7:
            n = self.i4()
            v = list(self.d[self.i:self.i + n])
            self.i += n
            return v
        if t == 8:
            return self.s()
        if t == 9:
            et = self.u1()
            n = self.i4()
            return [self.payload(et) for _ in range(n)]
        if t == 10:
            out = {}
            while True:
                tt = self.u1()
                if tt == 0:
                    return out
                name = self.s()
                out[name] = self.payload(tt)
        if t == 11:
            n = self.i4()
            v = [self.i4() for _ in range(n)]
            return v
        if t == 12:
            n = self.i4()
            v = [self.i8() for _ in range(n)]
            return v
        raise ValueError("unknown tag type " + str(t))


def short(v, limit=160):
    r = repr(v)
    if len(r) > limit:
        r = r[:limit] + "...(truncated)"
    return r


def main():
    path = sys.argv[1]
    want = sys.argv[2:]
    with gzip.open(path, "rb") as fh:
        raw = fh.read()
    r = Reader(raw)
    t = r.u1()
    if t != 10:
        print("root is not a compound, type=" + str(t))
        return
    r.s()
    root = r.payload(10)
    print("== " + path)
    print("root keys (" + str(len(root)) + "): " + ", ".join(sorted(root.keys())))
    keys = want if want else ["NeoForgeData"]
    for k in keys:
        if k not in root:
            print("[" + k + "] 不存在")
            continue
        print("[" + k + "] = " + short(root[k], 4000))


if __name__ == "__main__":
    main()
