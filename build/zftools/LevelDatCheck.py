# -*- coding: utf-8 -*-
"""LevelDatCheck.py —— 直接读 level.dat，打印每个维度的生成器与群系源（0.10 ZF18 新增）

**为什么需要它**：世界类型（超平坦/放大化/大型生物群系/单一生物群系）有没有真正生效，
**看日志看不出来** —— 日志只会说 `Preparing level "x"` 和 `Done (…)`。
真正记录"这个世界到底用什么生成器"的地方是 `level.dat` 里的 `WorldGenSettings.dimensions`。

ZF18 就是靠它定位的：用户选超平坦，`level.dat` 里却写着 `generator=minecraft:noise`，
与默认世界一字不差 ⇒ 世界类型被模组覆盖掉了。

`level.dat` = gzip 压缩的 NBT，这里用标准库自己解（NBT 格式很小，见 nbt_read/nbt_payload）。

跑法：
    python build/zftools/LevelDatCheck.py                       # 自动找 run/server/*/level.dat
    python build/zftools/LevelDatCheck.py <level.dat 路径...>
"""
import glob
import gzip
import os
import struct
import sys


def nbt_payload(buf, i, t):
    if t == 1: return struct.unpack(">b", buf[i:i + 1])[0], i + 1
    if t == 2: return struct.unpack(">h", buf[i:i + 2])[0], i + 2
    if t == 3: return struct.unpack(">i", buf[i:i + 4])[0], i + 4
    if t == 4: return struct.unpack(">q", buf[i:i + 8])[0], i + 8
    if t == 5: return struct.unpack(">f", buf[i:i + 4])[0], i + 4
    if t == 6: return struct.unpack(">d", buf[i:i + 8])[0], i + 8
    if t == 7:
        n = struct.unpack(">i", buf[i:i + 4])[0]; i += 4
        return list(buf[i:i + n]), i + n
    if t == 8:
        ln = struct.unpack(">H", buf[i:i + 2])[0]; i += 2
        return buf[i:i + ln].decode("utf-8", "replace"), i + ln
    if t == 9:
        et = buf[i]; n = struct.unpack(">i", buf[i + 1:i + 5])[0]; i += 5
        out = []
        for _ in range(n):
            v, i = nbt_payload(buf, i, et)
            out.append(v)
        return out, i
    if t == 10:
        out = {}
        while True:
            if buf[i] == 0:
                return out, i + 1
            (nm, _tt, vv), i = nbt_read(buf, i)
            out[nm] = vv
    if t == 11:
        n = struct.unpack(">i", buf[i:i + 4])[0]; i += 4
        return [struct.unpack(">i", buf[i + 4 * k:i + 4 * k + 4])[0] for k in range(n)], i + 4 * n
    if t == 12:
        n = struct.unpack(">i", buf[i:i + 4])[0]; i += 4
        return [struct.unpack(">q", buf[i + 8 * k:i + 8 * k + 8])[0] for k in range(n)], i + 8 * n
    raise ValueError("未知 NBT 类型 {0}".format(t))


def nbt_read(buf, i):
    t = buf[i]; i += 1
    if t == 0:
        return None, i
    ln = struct.unpack(">H", buf[i:i + 2])[0]; i += 2
    name = buf[i:i + ln].decode("utf-8", "replace"); i += ln
    val, i = nbt_payload(buf, i, t)
    return (name, t, val), i


def report(path):
    with gzip.open(path, "rb") as fh:
        raw = fh.read()
    root, _ = nbt_read(raw, 0)
    data = root[2]["Data"]
    print("==== {0} ====".format(path))
    wgs = data.get("WorldGenSettings") or data.get("worldGenSettings")
    if not wgs:
        print("   没有 WorldGenSettings；顶层键 = {0}".format(list(data.keys())[:16]))
        return
    dims = wgs.get("dimensions", {})
    for dim in sorted(dims):
        spec = dims[dim] or {}
        gen = spec.get("generator") or {}
        bs = gen.get("biome_source") or gen.get("biomeSource") or {}
        gt = gen.get("type")
        bt = bs.get("type") if isinstance(bs, dict) else None
        flag = ""
        if dim == "minecraft:overworld":
            flag = "   ← 世界类型的最终结果"
        print("   {0:<22} generator={1:<18} biome_source={2}{3}".format(dim, gt, bt, flag))
        if gt == "minecraft:flat":
            st = gen.get("settings") or {}
            lay = st.get("layers")
            print("        flat layers = {0}   biome={1}   features={2}".format(
                lay, st.get("biome"), st.get("features")))
        if bt == "potato_s_t:salty_river":
            print("        delegate = {0}   salty_biome = {1}   chance = {2}".format(
                (bs.get("delegate") or {}).get("preset"), bs.get("salty_biome"), bs.get("chance")))
    print("")


def main(argv):
    paths = argv if argv else sorted(glob.glob(os.path.join(
        "E:\\PotatoST", "run", "server", "*", "level.dat")))
    if not paths:
        print("没找到 level.dat")
        return 1
    for p in paths:
        try:
            report(p)
        except Exception as exc:
            print("==== {0} ====\n   解析失败：{1}\n".format(p, exc))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
