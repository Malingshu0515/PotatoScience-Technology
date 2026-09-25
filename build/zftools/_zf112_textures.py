r"""_zf112_textures.py —— 锂电池构造间 + 锂电池原件 的贴图（0.11 ZF112，程序生成占位）

两张：
  · `textures/block/lithium_battery_plant.png` —— 机器方块（六面同一张，cube_all）
  · `textures/item/lithium_battery_component.png` —— 新物品「锂电池原件」

配色沿用本工程机器家族（ZF108 从微型粉碎机/燃烧反应室量出来的那张表）：
  底 #4a4a52 / 暗 #34363b、#23232a / 亮 #6e6e78、#9aa2ac / 熔融 #c46022、#e8912f
再补一个"电芯绿" #3fc23f（状态灯那支绿，家族里已经有的颜色）。

用法：python build\zftools\_zf112_textures.py [--write]
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
OUT_BLOCK = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\block\lithium_battery_plant.png")
OUT_ITEM = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item\lithium_battery_component.png")
PREVIEW = os.path.join(ROOT, r"build\zftools\_zf112_preview.png")

# 机器：钢板 + 四角铆钉 + 左边一列硫酸罐窗口（青黄）+ 右边两格电芯（绿）
BLOCK = [
    "################",
    "#++++++++++++++#",
    "#s+ssssssssss+s#",
    "#ssooooooooooss#",
    "#ssoOOOOOOOOoss#",
    "#ssoOggggggOoss#",
    "#ssoOggggggOoss#",
    "#ssoOOOOOOOOoss#",
    "#ssooooooooooss#",
    "#s+ssssssssss+s#",
    "#ssggsggsggsggs#",
    "#ssggsggsggsggs#",
    "#ssOOsOOsOOsOOs#",
    "#ssggsggsggsggs#",
    "#ssggsggsggsggs#",
    "################",
]

# 物品：一节电芯（上面一个 + 极柱，中间绿色电量条）
ITEM = [
    "................",
    "................",
    "......####......",
    "......#++#......",
    "......#++#......",
    "....########....",
    "....#oooooo#....",
    "....#oOOOOo#....",
    "....#oggggo#....",
    "....#oggggo#....",
    "....#oOOOOo#....",
    "....#oooooo#....",
    "....########....",
    "................",
    "................",
    "................",
]

LEGEND = {
    ".": (0, 0, 0, 0),          # 透明（只有物品图用）
    "s": (0x4a, 0x4a, 0x52, 255),   # 钢板底（家族基色；方块图用它，**不透明**）
    "#": (0x23, 0x23, 0x2a, 255),
    "+": (0x9a, 0xa2, 0xac, 255),
    "o": (0x34, 0x36, 0x3b, 255),
    "O": (0xc4, 0x60, 0x22, 255),
    "g": (0x3f, 0xc2, 0x3f, 255),
}


def render(art):
    px = []
    for row in art:
        for ch in row:
            px.append(LEGEND[ch])
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


def preview(arts, scale=6):
    """两张并排放大成一张预览。"""
    W = 16 * scale * len(arts) + 2 * scale
    H = 16 * scale
    raw = b""
    for y in range(H):
        raw += b"\x00"
        for x in range(W):
            idx = x // (16 * scale + scale)
            local = x - idx * (16 * scale + scale)
            if idx >= len(arts) or local >= 16 * scale:
                raw += struct.pack("4B", 0x20, 0x20, 0x20, 255)
                continue
            px = arts[idx][(y // scale) * 16 + (local // scale)]
            raw += struct.pack("4B", *(px[:3] + (255,)) if px[3] == 0 else px)

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def main():
    bad = []
    for name, art in ((u"block", BLOCK), (u"item", ITEM)):
        if len(art) != 16:
            bad.append(u"%s：%d 行（应 16）" % (name, len(art)))
        for i, row in enumerate(art):
            if len(row) != 16:
                bad.append(u"%s 第 %d 行长度 %d（应 16）" % (name, i + 1, len(row)))
            for ch in row:
                if ch not in LEGEND:
                    bad.append(u"%s 第 %d 行有图例外的字符 %r" % (name, i + 1, ch))
    if bad:
        for b in bad:
            print(u"  !! " + b)
        return 1
    pxb, pxi = render(BLOCK), render(ITEM)
    # ⚠ 方块贴图**不许有透明像素**（它是 cube_all 的实心机器；有透明就是"方块上开洞"）
    if any(p[3] == 0 for p in pxb):
        print(u"  !! 方块贴图里有透明像素 —— 方块图必须用 s（钢板底），不能用 .")
        return 1
    if all(p[3] != 0 for p in pxi):
        print(u"  !! 物品贴图一个透明像素都没有（那样会是一整块方砖）")
        return 1
    write = "--write" in sys.argv
    os.makedirs(os.path.dirname(PREVIEW), exist_ok=True)
    open(PREVIEW, "wb").write(preview([pxb, pxi]))
    print(u"方块：色数 %d（含透明 %d 个像素）"
          % (len(set(pxb)), sum(1 for p in pxb if p[3] == 0)))
    print(u"物品：色数 %d（含透明 %d 个像素）"
          % (len(set(pxi)), sum(1 for p in pxi if p[3] == 0)))
    print(u"预览 → %s" % PREVIEW)
    if write:
        open(OUT_BLOCK, "wb").write(to_png(pxb))
        open(OUT_ITEM, "wb").write(to_png(pxi))
        print(u"落盘 → %s（%d B）" % (OUT_BLOCK, os.path.getsize(OUT_BLOCK)))
        print(u"落盘 → %s（%d B）" % (OUT_ITEM, os.path.getsize(OUT_ITEM)))
    else:
        print(u"（只出预览；加 --write 才写 PNG）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
