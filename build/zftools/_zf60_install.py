# -*- coding: utf-8 -*-
"""_zf60_install.py —— 把 _zf60_png 里那 7 张验一遍，再装进资源树 + 改对应模型

为什么先验：§4.23「别拿扩展名当格式证据」、§6.8「用户素材可能被缩放」。
这里自己做一次 PNG 解码（标准库 zlib，不依赖 Pillow），量出：
  · 真实尺寸（和用户说的对不对）
  · 不透明像素比例、不同颜色数（挡"空白图/纯色图/整张透明"）
然后把 5 个还在借原版贴图的模型改成指向自己的贴图（磁铁/铁粉本来就指对了，只换图）。
"""
import io
import json
import os
import shutil
import struct
import sys
import zlib

PROJ = r"E:\PotatoST"
STAGE = os.path.join(PROJ, "build", "zftools", "_zf60_png")
ASSETS = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t")

# (暂存名, 目标相对路径, 预期尺寸, 透明要求)
#   alpha  = 物品贴图，必须有透明底（否则游戏里是个白/花屏方块套着图案）
#   opaque = 方块贴图，本来就该全不透明
TEXTURES = [
    ("magnet", "textures/item/magnet.png", (32, 32), "alpha"),
    ("iron_powder", "textures/item/iron_powder.png", (16, 16), "alpha"),
    ("titanium_ore", "textures/block/titanium_ore.png", (16, 16), "opaque"),
    ("deepslate_titanium_ore", "textures/block/deepslate_titanium_ore.png", (16, 16), "opaque"),
    ("raw_titanium", "textures/item/raw_titanium.png", (32, 32), "alpha"),
    ("titanium_powder", "textures/item/titanium_powder.png", (32, 32), "alpha"),
    ("titanium_ingot", "textures/item/titanium_ingot.png", (32, 32), "alpha"),
]

# (模型文件, 现在指向, 应当指向)
MODELS = [
    ("models/item/raw_titanium.json", "minecraft:item/raw_iron", "potato_s_t:item/raw_titanium"),
    ("models/item/titanium_powder.json", "minecraft:item/gunpowder", "potato_s_t:item/titanium_powder"),
    ("models/item/titanium_ingot.json", "minecraft:item/iron_ingot", "potato_s_t:item/titanium_ingot"),
    ("models/block/titanium_ore.json", "minecraft:block/iron_ore", "potato_s_t:block/titanium_ore"),
    ("models/block/deepslate_titanium_ore.json", "minecraft:block/deepslate_iron_ore",
     "potato_s_t:block/deepslate_titanium_ore"),
]

fails = []


def check(cond, msg):
    print((u"  [OK]   " if cond else u"  [FAIL] ") + msg)
    if not cond:
        fails.append(msg)
    return cond


def read_png(path):
    """只认 8 位、非隔行的 RGB/RGBA/调色板 PNG（WPF 写出来就是这几种）。"""
    data = io.open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(u"不是 PNG: %s" % path)
    pos = 8
    idat = b""
    palette = b""
    width = height = depth = color = 0
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            width, height, depth, color, _comp, _filt, interlace = struct.unpack(">IIBBBBB", body)
            if interlace:
                raise ValueError(u"隔行 PNG 不支持: %s" % path)
        elif kind == b"PLTE":
            palette = body
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
        pos += 12 + length
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]
    raw = zlib.decompress(idat)
    stride = width * channels
    out = bytearray()
    prev = bytearray(stride)
    p = 0
    for _ in range(height):
        filt = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        for i in range(stride):
            a = line[i - channels] if i >= channels else 0
            b = prev[i]
            c = prev[i - channels] if i >= channels else 0
            if filt == 1:
                line[i] = (line[i] + a) & 0xFF
            elif filt == 2:
                line[i] = (line[i] + b) & 0xFF
            elif filt == 3:
                line[i] = (line[i] + ((a + b) >> 1)) & 0xFF
            elif filt == 4:
                pa = abs(b - c)
                pb = abs(a - c)
                pc = abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out += line
        prev = line
    return width, height, depth, color, channels, bytes(out)


def stats(width, height, channels, pixels, palette):
    colors = {}
    opaque = 0
    for i in range(0, len(pixels), channels):
        if channels == 1:
            if palette:
                r, g, b = palette[pixels[i] * 3], palette[pixels[i] * 3 + 1], palette[pixels[i] * 3 + 2]
            else:
                r = g = b = pixels[i]
            a = 255
        elif channels == 2:
            r = g = b = pixels[i]
            a = pixels[i + 1]
        elif channels == 3:
            r, g, b = pixels[i], pixels[i + 1], pixels[i + 2]
            a = 255
        else:
            r, g, b, a = pixels[i], pixels[i + 1], pixels[i + 2], pixels[i + 3]
        if a == 0:
            continue
        opaque += 1
        key = (r, g, b)
        colors[key] = colors.get(key, 0) + 1
    top = sorted(colors.items(), key=lambda kv: -kv[1])[:4]
    return opaque, len(colors), top


def main():
    for name, rel, want, mode in TEXTURES:
        src = os.path.join(STAGE, name + ".png")
        if not os.path.isfile(src):
            fails.append(u"暂存文件不在: %s" % src)
            continue
        width, height, depth, color, channels, pixels = read_png(src)
        palette = b""
        if color == 3:
            data = io.open(src, "rb").read()
            pos = data.find(b"PLTE")
            if pos > 0:
                length = struct.unpack(">I", data[pos - 4:pos])[0]
                palette = data[pos + 4:pos + 4 + length]
        opaque, ncolors, top = stats(width, height, channels, pixels, palette)
        ratio = 100.0 * opaque / (width * height)
        ok = check((width, height) == want, u"%s: 尺寸 %dx%d == 期望 %dx%d（深度 %d 色型 %d）"
                   % (name, width, height, want[0], want[1], depth, color))
        ok &= check(depth == 8 and color == 6, u"%s: 8 位 RGBA（色型 6，带 alpha）" % name)
        ok &= check(ncolors >= 4, u"%s: 真实内容（%d 种不透明颜色）" % (name, ncolors))
        if mode == "alpha":
            ok &= check(5.0 <= ratio <= 99.5,
                        u"%s: 物品贴图有透明底（不透明像素 %.1f%%）" % (name, ratio))
        else:
            ok &= check(ratio >= 99.9,
                        u"%s: 方块贴图整张不透明（%.1f%%）" % (name, ratio))
        print(u"         主色: " + u", ".join(u"#%02X%02X%02X x%d" % (c[0], c[1], c[2], n)
                                            for c, n in top))
        if ok:
            dst = os.path.join(ASSETS, rel.replace("/", os.sep))
            folder = os.path.dirname(dst)
            if not os.path.isdir(folder):
                os.makedirs(folder)
            shutil.copy2(src, dst)
            print(u"         -> 安装到 %s（%d 字节）" % (rel, os.path.getsize(dst)))

    print(u"")
    for rel, old, new in MODELS:
        path = os.path.join(ASSETS, rel.replace("/", os.sep))
        text = io.open(path, encoding="utf-8").read()
        if new in text:
            check(True, u"%s 已经指向 %s" % (rel, new))
            continue
        if old not in text:
            fails.append(u"%s 里找不到 %s" % (rel, old))
            check(False, u"%s 里找不到 %s" % (rel, old))
            continue
        io.open(path, "w", encoding="utf-8", newline="\n").write(text.replace(old, new))
        data = json.loads(io.open(path, encoding="utf-8").read())
        check(True, u"%s: %s -> %s（JSON 仍可解析）" % (rel, old, new))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
