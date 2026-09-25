# -*- coding: utf-8 -*-
u"""_zf108_palette.py —— 量一下现有机器/方块贴图的调色板（只读，不改任何文件）

目的：新画的合金冶炼炉贴图要**跟现有家族一个色系**，别自己发明颜色。
"""
import collections
import os
import struct
import sys
import zlib

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DIR = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"
FILES = ["micro_crusher_side", "micro_crusher_top", "heat_resistant_metal_block",
         "advanced_metal_block", "common_metal_block", "low_generator_side",
         "low_generator_top", "combustion_chamber_side", "combustion_chamber_top",
         "acidic_reaction_chamber_side", "acidic_reaction_chamber_top",
         "wiring_block", "heater", "heat_sink", "stable_metal_block", "alloy_smelter"]


def read_png(path):
    u"""够用的 PNG 读入：只支持 8 位 RGBA/RGB 非隔行（本工程自己生成的图都是这种）"""
    b = open(path, "rb").read()
    pos, w, h, idat = 8, 0, 0, b""
    while pos < len(b):
        (ln,) = struct.unpack(">I", b[pos:pos + 4])
        typ = b[pos + 4:pos + 8]
        data = b[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, color = struct.unpack(">IIBB", data[:10])
            if depth != 8 or color not in (2, 6):
                raise ValueError("只支持 8 位 RGB/RGBA（这个文件 color=%d depth=%d）" % (color, depth))
            ch = 4 if color == 6 else 3
        elif typ == b"IDAT":
            idat += data
        elif typ == b"IEND":
            break
        pos += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * ch
    out, prev = [], bytearray(stride)
    i = 0
    for _y in range(h):
        f = raw[i]
        i += 1
        line = bytearray(raw[i:i + stride])
        i += stride
        for x in range(stride):                    # 反过滤（本工程的图基本都是 0/1/2/4）
            a = line[x - ch] if x >= ch else 0
            bb = prev[x]
            c = prev[x - ch] if x >= ch else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + bb) & 255
            elif f == 3:
                line[x] = (line[x] + (a + bb) // 2) & 255
            elif f == 4:
                p = a + bb - c
                pa, pb, pc = abs(p - a), abs(p - bb), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (bb if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        out.append(bytes(line))
        prev = line
    px = []
    for row in out:
        px.append([tuple(row[x * ch:x * ch + ch]) for x in range(w)])
    return w, h, px


def main():
    for name in FILES:
        p = os.path.join(DIR, name + ".png")
        if not os.path.exists(p):
            print(u"%-34s （没有）" % name)
            continue
        try:
            w, h, px = read_png(p)
        except Exception as e:
            print(u"%-34s 读不了：%s" % (name, e))
            continue
        cnt = collections.Counter()
        for row in px:
            for c in row:
                cnt[c] += 1
        top = cnt.most_common(6)
        s = u"  ".join(u"#%02x%02x%02x(α%d)×%d" % (c[0], c[1], c[2], c[3] if len(c) > 3 else 255, n)
                       for c, n in top)
        print(u"%-30s %2dx%-2d 色数 %-3d %s" % (name, w, h, len(cnt), s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
