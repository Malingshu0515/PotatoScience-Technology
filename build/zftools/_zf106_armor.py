# -*- coding: utf-8 -*-
r"""_zf106_armor.py —— 把用户给的**两张套装原图**做成盔甲层贴图（0.11 ZF106）

用户本轮原话（问答）：

  「当【穿在身上】的盔甲外观（我就是想要身上显示这个）」
  「我存到 build\用户素材\ 下（推荐）」

⇒ 目标文件（Java 侧 `ModArmorMaterials` 已经指过去，见那个类的 Layer 注释）：

    assets/potato_s_t/textures/models/armor/titanium_alloy_layer_1.png   （外层：头/胸/靴）
    assets/potato_s_t/textures/models/armor/titanium_alloy_layer_2.png   （内层：护腿）
    assets/potato_s_t/textures/models/armor/star_steel_layer_1.png
    assets/potato_s_t/textures/models/armor/star_steel_layer_2.png

游戏读的路径就是 `models/armor/<Layer 资源名>_layer_1|2.png`（本轮已从
`ArmorMaterial.Layer.resolveTexture` 核实）。

**输入**（按优先级找，找到就用）：
  ① `build/用户素材/titanium_alloy_set.png` / `star_steel_set.png`（用户准备放这里的名字）
  ② `build/用户素材/钛合金套装.png` / `星璨钢套装.png`（用户上传时的原名）
  ③ `build/用户素材/titanium_alloy.png` / `star_steel_armor.png`（备选名）
  ④ 已经躺在目标路径上的同名文件 ⇒ **一律不覆盖**（用户手放的一律优先）

**为什么要"去白底"**：两张素材是**白底不透明**的（背景不是透明的），
直接当盔甲用 ⇒ 身上会糊一块白板。所以做**四边泛洪**把连通的白背景抹成透明
（档案 §4.56 的教训：**不能一刀切"白色全透明"**，图形内部的白高光必须留下）。

**为什么是"可复现"脚本而不是手改图**：素材尺寸/格式都可能变（预览是 webp 转的 PNG），
脚本每次重跑都得到同一结果；且换素材只要重跑，不动 Java。

用法：
    python build/zftools/_zf106_armor.py            # 只看：报告找到了什么、会写哪些文件
    python build/zftools/_zf106_armor.py --write    # 真写
"""
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import write_png   # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
MAT = os.path.join(PROJ, "build", u"用户素材")
OUT = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t",
                   "textures", "models", "armor")

# 目标材料名 → 候选输入文件名（按优先级）
SETS = [
    (u"titanium_alloy", [u"titanium_alloy_set.png", u"titanium_alloy.png", u"钛合金套装.png"]),
    (u"star_steel", [u"star_steel_set.png", u"star_steel_armor.png", u"星璨钢套装.png"]),
]
TARGET = 64          # 盔甲层贴图的宽度（高 = 宽 / 2）
WHITE_MIN = 244      # 三通道都 >= 这个值才算"白"（背景候选）
ALPHA_MIN = 8        # alpha <= 这个值算"已经透明"


def decode_png(path):
    u"""只解 8 位 RGB/RGBA（素材就这两种）。返回 (w, h, bytearray RGBA)。"""
    d = open(path, "rb").read()
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(u"%s 不是 PNG（可能是 webp 换了扩展名，见档案 §4.23）"
                         % os.path.basename(path))
    pos, idat, dims, ct = 8, b"", None, None
    while pos < len(d):
        ln = struct.unpack_from(">I", d, pos)[0]
        ctype = d[pos + 4:pos + 8]
        if ctype == b"IHDR":
            w, h, depth, ct = struct.unpack_from(">IIBB", d, pos + 8)
            if depth != 8 or ct not in (2, 6):
                raise ValueError(u"%s：只支持 8 位 RGB/RGBA（实际 depth=%d colortype=%d）"
                                 % (os.path.basename(path), depth, ct))
            dims = (w, h)
        elif ctype == b"IDAT":
            idat += d[pos + 8:pos + 8 + ln]
        pos += 12 + ln
    ch = 4 if ct == 6 else 3
    stride = dims[0] * ch
    raw = zlib.decompress(idat)
    p, prev, rows = 0, bytearray(stride), []
    for _y in range(dims[1]):
        f = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if f == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        rows.append(bytes(line))
        prev = line
    w0, h0 = dims
    out = bytearray()
    for y in range(h0):
        for x in range(w0):
            o = x * ch
            if ch == 4:
                out += rows[y][o:o + 4]
            else:
                out += rows[y][o:o + 3] + b"\xff"
    return w0, h0, out


def flood_white(w, h, pix):
    u"""从**四边**泛洪，把连通的白背景变透明；图形内部的白高光不会被碰到（§4.56）。

    返回 (改过的 pix, 抹掉的像素数)。
    """
    def is_white(i):
        o = i * 4
        return (pix[o] >= WHITE_MIN and pix[o + 1] >= WHITE_MIN and pix[o + 2] >= WHITE_MIN)

    seen = bytearray(w * h)
    stack = []
    for x in range(w):
        for y in (0, h - 1):
            i = y * w + x
            if not seen[i] and is_white(i):
                seen[i] = 1
                stack.append(i)
    for y in range(h):
        for x in (0, w - 1):
            i = y * w + x
            if not seen[i] and is_white(i):
                seen[i] = 1
                stack.append(i)
    cleared = 0
    while stack:
        i = stack.pop()
        o = i * 4
        pix[o + 3] = 0
        cleared += 1
        x, y = i % w, i // w
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                j = ny * w + nx
                if not seen[j] and is_white(j):
                    seen[j] = 1
                    stack.append(j)
    return pix, cleared


def resize_area(w, h, pix, nw, nh):
    u"""面积平均（alpha 加权）缩放 —— 与 `_zf103_textures.py` 同一套算法。"""
    out = bytearray()
    for y in range(nh):
        y0 = y * h // nh
        y1 = max(y0 + 1, (y + 1) * h // nh)
        for x in range(nw):
            x0 = x * w // nw
            x1 = max(x0 + 1, (x + 1) * w // nw)
            r = g = b = a = n = 0
            for sy in range(y0, min(y1, h)):
                for sx in range(x0, min(x1, w)):
                    o = (sy * w + sx) * 4
                    av = pix[o + 3]
                    r += pix[o] * av
                    g += pix[o + 1] * av
                    b += pix[o + 2] * av
                    a += av
                    n += 1
            out += (b"\x00\x00\x00\x00" if a == 0 or n == 0
                    else bytes((r // a, g // a, b // a, a // n)))
    return bytes(out)


def find_input(cands):
    for c in cands:
        p = os.path.join(MAT, c)
        if os.path.isfile(p):
            return p
    return None


def main():
    write = "--write" in sys.argv
    print(u"素材目录：%s" % MAT)
    print(u"目标目录：%s\n" % OUT)
    total_written = 0
    missing = []
    for name, cands in SETS:
        src = find_input(cands)
        print(u"==== %s ====" % name)
        if src is None:
            wanted = u" 或 ".join(cands)
            print(u"  [缺] 找不到输入（找过：%s）" % wanted)
            print(u"       ⇒ 这一套**什么都不写**（不用占位图占掉用户素材的位置）")
            missing.append((name, cands))
            continue
        w, h, pix = decode_png(src)
        print(u"  输入：%s  %d×%d" % (os.path.basename(src), w, h))
        pix, cleared = flood_white(w, h, pix)
        print(u"  去白底：泛洪抹掉 %d 个像素（%.1f%%）" % (cleared, 100.0 * cleared / (w * h)))
        tw, th = TARGET, TARGET // 2
        if (w, h) != (tw, th):
            pix = resize_area(w, h, pix, tw, th)
            print(u"  定尺：%d×%d → %d×%d（面积平均）" % (w, h, tw, th))
        else:
            print(u"  定尺：已经是 %d×%d，不动" % (tw, th))
        opaque = sum(1 for i in range(tw * th) if pix[i * 4 + 3] > 8)
        print(u"  成品不透明像素：%d/%d（%.1f%%）" % (opaque, tw * th, 100.0 * opaque / (tw * th)))
        if opaque == 0:
            print(u"  [FAIL] 全透明 ⇒ 不写（去白底把图形也吃掉了，阈值要调）")
            missing.append((name, cands))
            continue
        for layer in (1, 2):
            dst = os.path.join(OUT, u"%s_layer_%d.png" % (name, layer))
            if os.path.isfile(dst):
                print(u"  [保留] %s 已存在 ⇒ **不覆盖**（用户手放的一律优先）" % os.path.basename(dst))
                continue
            if write:
                os.makedirs(OUT, exist_ok=True)
                write_png(dst, tw, th, pix)
                total_written += 1
                print(u"  [写出] %s  %d B" % (os.path.basename(dst), os.path.getsize(dst)))
            else:
                print(u"  [只看] 会写 %s（未落盘）" % os.path.basename(dst))
        print(u"  ⚠ 外层/内层目前用**同一张图**（图层 1 与图层 2 都写它）——")
        print(u"     真实盔甲通常外层=胸甲样式、内层=护腿样式；你要分成两张就说一声，我按名字收。")
    print(u"")
    if missing:
        print(u"缺输入的：%s" % [n for n, _c in missing])
        print(u"把原图存成下面任一名字再跑一次即可：")
        for n, cands in missing:
            print(u"  %s  ←  %s" % (n, u" 或 ".join(cands)))
    print(u"写出文件 %d 个%s" % (total_written, u"" if write else u"（dry run，没落盘）"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
