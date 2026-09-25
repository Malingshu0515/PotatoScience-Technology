# -*- coding: utf-8 -*-
r"""_zf109_textures.py —— 采油机的方块贴图（0.11 ZF109，**程序生成**）

用户没给贴图，也没要求画（原话里只有机器 / 界面 / 数值），但新方块没有 PNG 就是紫黑格。
⇒ 按 ZF97 / ZF101 / ZF108 的先例：**先用程序生成一张能看的 16×16 占位**，想换手绘的直接覆盖
`src/main/resources/assets/potato_s_t/textures/block/oil_pump.png`，**模型一个字都不用改**。

画的是"一台架在海面上的采油机"：深灰钢板底 + 四角铆钉 + 中间一台**横躺的油罐**
（向左伸出的出油口）+ 下面一个**朝下的吸油管口**（对应"下方要接含水锁链"）。

配色沿用本工程机器家族（与 `_zf108_textures.py` 同一张表，ZF108 从
`micro_crusher_side` / `combustion_chamber` 量出来的）：
  底 #4a4a52 / 暗 #34363b、#23232a / 亮 #6e6e78、#9aa2ac / 熔融 #c46022、#e8912f

用法：
  python build\zftools\_zf109_textures.py            # 只出预览（不写盘）
  python build\zftools\_zf109_textures.py --write    # 落盘 PNG
"""
import os
import struct
import sys
import zlib

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
OUT = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\block\oil_pump.png")
PREVIEW = os.path.join(ROOT, r"build\zftools\_zf109_preview.png")

# 图例（一张 16 行的字符图，人眼可读、也可直接改）
ART = [
    "################",
    "#++++++++++++++#",
    "#.+..........+.#",
    "#..oooooooooo..#",
    "#..oOOOOOOOOo..#",
    "#..oOooooooOo..#",
    "#..oOooooooOo..#",
    "#..oOOOOOOOOo..#",
    "#..oooooooooo..#",
    "#.+..........+.#",
    "#....######....#",
    "#....#....#....#",
    "#....#.oo.#....#",
    "#....#.OO.#....#",
    "#....#.oo.#....#",
    "################",
]

LEGEND = {
    ".": (0x4a, 0x4a, 0x52),   # 钢板底（家族基色）
    "#": (0x23, 0x23, 0x2a),   # 外框 / 暗边
    "+": (0x9a, 0xa2, 0xac),   # 四角铆钉（高光）
    "o": (0x34, 0x36, 0x3b),   # 罐体暗部 / 管壁
    "O": (0xe8, 0x91, 0x2f),   # 熔融亮色（罐里装的油）
}


def rgba(c):
    return (c[0], c[1], c[2], 255)


def render():
    px = []
    for row in ART:
        for ch in row:
            px.append(rgba(LEGEND[ch]))
    return px


def to_png(px, w=16, h=16):
    raw = b""
    for y in range(h):
        raw += b"\x00" + b"".join(struct.pack("4B", *px[y * w + x]) for x in range(w))
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def to_preview(px, w=16, h=16, scale=8):
    """把 16×16 放大成一张能看的预览（最近邻）。"""
    W, H = w * scale, h * scale
    raw = b""
    for y in range(H):
        raw += b"\x00"
        for x in range(W):
            raw += struct.pack("4B", *px[(y // scale) * w + (x // scale)])
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def main():
    bad = []
    for i, row in enumerate(ART):
        if len(row) != 16:
            bad.append(u"第 %d 行长度 %d（应为 16）" % (i + 1, len(row)))
        for ch in row:
            if ch not in LEGEND:
                bad.append(u"第 %d 行有图例外的字符 %r" % (i + 1, ch))
    if len(ART) != 16:
        bad.append(u"行数 %d（应为 16）" % len(ART))
    if bad:
        for b in bad:
            print(u"  !! " + b)
        return 1
    px = render()
    colors = len(set(px))
    png = to_png(px)
    prev = to_preview(px)
    write = "--write" in sys.argv
    os.makedirs(os.path.dirname(PREVIEW), exist_ok=True)
    open(PREVIEW, "wb").write(prev)
    print(u"预览 → %s（%d 字节）" % (PREVIEW, len(prev)))
    print(u"色数 = %d（家族调色板里一共 %d 种）" % (colors, len(LEGEND)))
    if write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        open(OUT, "wb").write(png)
        print(u"落盘 → %s（%d 字节）" % (OUT, len(png)))
    else:
        print(u"（只出预览；加 --write 才写 PNG）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
