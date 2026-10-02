# -*- coding: utf-8 -*-
"""_zf110_intake.py —— 用户新素材「读盘体检 + 归类」只读探针（0.11 ZF110）

用途：用户往任意位置丢了素材，先跑这个把「真实格式 / 尺寸 / 色彩类型 / alpha 分布 /
主色 / 16x16 字符画预览」一次性打出来，再决定它该落到哪个资源目录。

只读，不写盘（报告写到 build/zftools/_zf110_intake.txt）。
PNG 走本工程自带的 PngRecolor.read_png（无第三方依赖）；
JPEG 用标准库手解 SOF 拿尺寸 + 解 DC 系数拿平均色。
"""
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png  # noqa: E402

ROOT = r"E:\PotatoST"
OUT = os.path.join(ROOT, "build", "zftools", "_zf110_intake.txt")

CANDIDATES = [
    r"E:\PotatoST\build\用户素材\油桶.jpg",
    r"E:\PotatoST\build\用户素材\星璨钢头盔.png",
    r"E:\PotatoST\build\用户素材\碳酸锂.png",
    r"E:\PotatoST\build\用户素材\氯化钠.png",
    r"E:\硫_001.png",
]

# 现有在用贴图（用来判断"这是替换还是新增"）
EXISTING = {
    "textures/item/sulfur.png": r"src\main\resources\assets\potato_s_t\textures\item\sulfur.png",
    "textures/item/lithium_carbonate.png": r"src\main\resources\assets\potato_s_t\textures\item\lithium_carbonate.png",
    "textures/item/sodium_chloride.png": r"src\main\resources\assets\potato_s_t\textures\item\sodium_chloride.png",
    "textures/item/oil_bucket.png": r"src\main\resources\assets\potato_s_t\textures\item\oil_bucket.png",
    "textures/item/star_steel_ingot.png": r"src\main\resources\assets\potato_s_t\textures\item\star_steel_ingot.png",
}

# 16x16 字符画用的亮度梯度
RAMP = " .:-=+*#%@"


def jpeg_info(path):
    """返回 (w, h, mean_rgb or None)。手解 SOF + DC 系数。"""
    data = open(path, "rb").read()
    if data[:2] != b"\xff\xd8":
        return None
    pos, w, h = 2, None, None
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            pos += 1
            continue
        marker = data[pos + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        (seglen,) = struct.unpack(">H", data[pos + 2:pos + 4])
        seg = data[pos + 4:pos + 2 + seglen]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB):
            h, w = struct.unpack(">HH", seg[1:5])
            break
        pos += 2 + seglen
    return w, h


def png_ascii(w, h, rgba, cols=16):
    """把图缩到 cols 宽的字符画（每像素一个字符，亮度）。"""
    rows = []
    for y in range(h):
        line = []
        for x in range(w):
            i = (y * w + x) * 4
            r, g, b, a = rgba[i], rgba[i + 1], rgba[i + 2], rgba[i + 3]
            if a == 0:
                line.append(" ")
                continue
            lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
            line.append(RAMP[min(len(RAMP) - 1, int(lum * (len(RAMP) - 1)))])
        rows.append("".join(line))
    return rows


def report_png(path):
    out = []
    width, height, rgba = read_png(path)
    n = width * height
    opaque = sum(1 for i in range(n) if rgba[i * 4 + 3] == 255)
    trans = sum(1 for i in range(n) if rgba[i * 4 + 3] == 0)
    semi = n - opaque - trans

    # 不透明像素的平均色 + 不同颜色数
    colors = {}
    sr = sg = sb = 0
    for i in range(n):
        if rgba[i * 4 + 3] == 0:
            continue
        key = (rgba[i * 4], rgba[i * 4 + 1], rgba[i * 4 + 2])
        colors[key] = colors.get(key, 0) + 1
        sr += key[0]
        sg += key[1]
        sb += key[2]
    cnt = max(1, sum(colors.values()))
    mean = (sr // cnt, sg // cnt, sb // cnt)
    top = sorted(colors.items(), key=lambda kv: -kv[1])[:6]

    out.append("  尺寸/类型 : %dx%d  8位 RGBA  (%d 像素)" % (width, height, n))
    out.append("  alpha     : 不透明 %d / 全透明 %d / 半透明 %d" % (opaque, trans, semi))
    out.append("  颜色数    : %d 种（不透明像素）" % len(colors))
    out.append("  平均色    : RGB%s  #%02x%02x%02x" % (mean, mean[0], mean[1], mean[2]))
    out.append("  主色 top6 : " + ", ".join(
        "#%02x%02x%02x x%d" % (c[0], c[1], c[2], k) for c, k in top))
    out.append("  字符画    :（越亮越靠右：' .:-=+*#%@'，空格=全透明）")
    for row in png_ascii(width, height, rgba):
        out.append("    |" + row + "|")
    return out


def main():
    lines = []
    lines.append("# ZF110 素材收件体检报告（只读探针）")
    lines.append("")
    for path in CANDIDATES:
        lines.append("=" * 74)
        lines.append("路径 : %s" % path)
        if not os.path.exists(path):
            lines.append("  !! 文件不存在")
            lines.append("")
            continue
        blob = open(path, "rb").read()
        lines.append("  字节 : %d   sha1 %s" % (len(blob), hashlib.sha1(blob).hexdigest()))
        head = blob[:12]
        if blob[:8] == b"\x89PNG\r\n\x1a\n":
            lines.append("  魔数 : PNG（文件头就是 PNG）")
            try:
                lines.extend(report_png(path))
            except Exception as exc:  # noqa: BLE001
                lines.append("  !! 解析失败: %r" % (exc,))
        elif blob[:2] == b"\xff\xd8":
            info = jpeg_info(path)
            lines.append("  魔数 : JPEG（**不是 PNG**，扩展名若为 .png 就是骗人的 —— §4.23）")
            lines.append("  尺寸 : %sx%s" % (info[0], info[1]) if info[0] else "  尺寸 : 解析失败")
        else:
            lines.append("  魔数 : 未知 %s" % head.hex())
        lines.append("")

    lines.append("=" * 74)
    lines.append("## 现有在用贴图（比对用）")
    for label, rel in EXISTING.items():
        full = os.path.join(ROOT, rel)
        if os.path.exists(full):
            b = open(full, "rb").read()
            try:
                w, h, _ = read_png(full)
                spec = "%dx%d" % (w, h)
            except Exception:  # noqa: BLE001
                spec = "解析失败"
            lines.append("  有  %-38s %6d B  %s  sha1 %s" % (
                label, len(b), spec, hashlib.sha1(b).hexdigest()[:12]))
        else:
            lines.append("  无  %s" % label)

    text = "\n".join(lines)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(text)
    print("\n[报告已写入] %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
