# -*- coding: utf-8 -*-
u"""_zf122_textures.py —— ZF122「星仪图之章」的四张天空盒贴图

素材：用户给的四张 NASA 图（真 JPEG，已归档到 `build\\用户素材\\星仪图\\`，原名与 sha256 记在
`_来源凭据.json`）。用户原话：「图我给你了 你想怎么编辑都可以 我感觉这个图真的很好看！」

**本脚本做的三件事**（每一步都为了"贴到球幕上不难看 + 别把 jar 撑爆"）：

1. **裁成 2:1 再缩到 1024×512**：天空盒走**等距圆柱投影**（经度→u、纬度→v），
   2:1 是它的标准比例；源图是 1.35:1 ⇒ 上下各裁掉一点（不是拉伸，避免星云变形）。
2. **两版一起出**：`_pal`（中位切分 256 色 + Floyd–Steinberg 抖动，PNG colorType 3）
   与 `_rgb`（直接 RGBA，colorType 6）—— 体积差一个数量级，**出图给眼睛看**再定用哪版
   （档案 §4.23/§4.35：判颜色/画质一律看图与统计量，不看文件名与印象）。
3. **落盘前出预览**：1024×512 直接看太大，另出 512×256 的预览 PNG。

通道顺序：WPF 解出来是 **BGRA**，这里按 R=a[2], G=a[1], B=a[0] 读 —— 已经出图肉眼验过
（绿星云是绿的、蜘蛛星云是青红），不是凭印象。

跑法：
    python build\\zftools\\_zf122_textures.py            # 只出到 _zf122_out\\
    python build\\zftools\\_zf122_textures.py --write     # 同时写进 textures/skybox/
"""
import io
import os
import struct
import sys
import zlib

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

RAW = os.path.join(os.environ["TEMP"], "zf122_raw")
OUT = r"E:\PotatoST\build\zftools\_zf122_out"
DEST = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\skybox"
W, H = 1024, 512

SOURCES = {
    u"sky_verdant":   (2380, 1761),   # 绿星云（GSFC e002020）
    u"sky_mystic":    (2484, 1687),   # 青褐崖（GSFC e002076，"神秘山"那种）
    u"sky_ember":     (2411, 1739),   # 赤色银河（PIA03654）
    u"sky_tarantula": (2424, 1730),   # 青红蛛（PIA04200）
}


# ---------------------------------------------------------------- PNG 写出
def _chunk(tag, body):
    return (struct.pack(">I", len(body)) + tag + body
            + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))


def write_png_palette(path, w, h, idx, palette):
    u"""colorType 3（调色板）：每像素 1 字节 + PLTE。照片类图这样能小一个数量级。"""
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += bytes(idx[y])
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 3, 0, 0, 0))
    png += _chunk(b"PLTE", bytes(np.asarray(palette, dtype=np.uint8).reshape(-1)))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    io.open(path, "wb").write(png)


def write_png_rgb(path, w, h, rgb):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += bytes(rgb[y].reshape(-1))
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    io.open(path, "wb").write(png)


# ---------------------------------------------------------------- 图像处理
def load(name):
    w, h = SOURCES[name]
    a = np.fromfile(os.path.join(RAW, name + u".bgra"), dtype=np.uint8).reshape(h, w, 4)
    return a[:, :, [2, 1, 0]].astype(np.float32)     # BGRA -> RGB（已看图确认）


def resize(img, w, h):
    u"""双线性（星云是平滑的摄影图，双线性足够；不做锐化也不加对比度——保持原样最好看）"""
    sh, sw = img.shape[:2]
    ys = np.linspace(0, sh - 1, h)
    xs = np.linspace(0, sw - 1, w)
    y0 = np.floor(ys).astype(np.int64); y1 = np.minimum(y0 + 1, sh - 1); fy = (ys - y0)[:, None, None]
    x0 = np.floor(xs).astype(np.int64); x1 = np.minimum(x0 + 1, sw - 1); fx = (xs - x0)[None, :, None]
    top = img[y0][:, x0] * (1 - fx) + img[y0][:, x1] * fx
    bot = img[y1][:, x0] * (1 - fx) + img[y1][:, x1] * fx
    return np.clip(top * (1 - fy) + bot * fy, 0, 255)


def center_crop_2to1(img):
    h, w = img.shape[:2]
    target = w // 2
    if h <= target:
        return img
    off = (h - target) // 2
    return img[off:off + target]


def median_cut(pixels, n):
    u"""中位切分：pixels 是 (N,3) float，返回 (n,3) uint8 调色板"""
    boxes = [pixels]
    while len(boxes) < n:
        # 挑"最长边最长"的那个盒子切
        best, best_len = -1, -1.0
        for i, b in enumerate(boxes):
            if len(b) < 2:
                continue
            span = b.max(axis=0) - b.min(axis=0)
            L = float(span.max())
            if L > best_len:
                best, best_len = i, L
        if best < 0:
            break
        b = boxes.pop(best)
        axis = int((b.max(axis=0) - b.min(axis=0)).argmax())
        order = np.argsort(b[:, axis])
        b = b[order]
        mid = len(b) // 2
        boxes.append(b[:mid])
        boxes.append(b[mid:])
    pal = np.array([b.mean(axis=0) for b in boxes if len(b)], dtype=np.float32)
    if len(pal) < n:                                  # 补足（纯色图会切不出来）
        pad = np.repeat(pal[-1:], n - len(pal), axis=0)
        pal = np.vstack([pal, pad])
    return np.clip(pal, 0, 255)


def dither_fs(img, pal):
    u"""Floyd–Steinberg 抖动（逐行 Python，524288 像素约 1 秒）"""
    h, w = img.shape[:2]
    buf = img.astype(np.float32).copy()
    idx = np.zeros((h, w), dtype=np.uint8)
    pl = pal.astype(np.float32)
    for y in range(h):
        row = buf[y]
        for x in range(w):
            old = row[x]
            d = ((pl - old) ** 2).sum(axis=1)
            k = int(d.argmin())
            idx[y, x] = k
            err = old - pl[k]
            if x + 1 < w:
                row[x + 1] += err * (7.0 / 16.0)
            if y + 1 < h:
                if x > 0:
                    buf[y + 1, x - 1] += err * (3.0 / 16.0)
                buf[y + 1, x] += err * (5.0 / 16.0)
                if x + 1 < w:
                    buf[y + 1, x + 1] += err * (1.0 / 16.0)
    return idx


def nearest_index(img, pal):
    pl = pal.astype(np.float32)
    flat = img.reshape(-1, 3)
    out = np.empty(len(flat), dtype=np.uint8)
    step = 65536
    for i in range(0, len(flat), step):
        chunk = flat[i:i + step]
        out[i:i + step] = ((chunk[:, None, :] - pl[None, :, :]) ** 2).sum(axis=2).argmin(axis=1)
    return out.reshape(img.shape[:2])


def write_preview(path, rgb, maxw=512):
    h, w = rgb.shape[:2]
    k = max(1, w // maxw)
    small = rgb[::k, ::k]
    write_png_rgb(path, small.shape[1], small.shape[0], small.astype(np.uint8))


# ---------------------------------------------------------------- 物品图标
ICON_DEST = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item"

# 调色板：`.` 透明；n 描边 / N 封面 / g 金边 / w 星芒 / W 星芯 / s 书脊
ICON_PALETTE = {
    u".": (0, 0, 0, 0),
    u"n": (12, 16, 34, 255),
    u"N": (38, 50, 96, 255),
    u"H": (58, 74, 132, 255),
    u"g": (219, 178, 74, 255),
    u"s": (122, 86, 40, 255),
    u"w": (168, 190, 255, 255),
    u"W": (245, 248, 255, 255),
}


def _row(*segs):
    line = [u"."] * 16
    for x0, seg in segs:
        for i, ch in enumerate(seg):
            assert line[x0 + i] == u".", u"第 %d 列写重了" % (x0 + i)
            line[x0 + i] = ch
    assert len(line) == 16
    return u"".join(line)


def make_icon(write):
    u"""星仪图之章的物品图标：一本深蓝封面的书，封面上金边 + 一颗四芒星"""
    art = [
        _row(),                                                     # y0
        _row((2, u"nnnnnnnnnnnn")),                                 # y1 上边
        _row((2, u"s"), (3, u"N" * 10), (13, u"n")),                # y2
        _row((2, u"s"), (3, u"N"), (4, u"gggggggg"), (12, u"N"), (13, u"n")),   # y3 金边上
        _row((2, u"s"), (3, u"N"), (4, u"g"), (5, u"NNNNNN"), (11, u"g"), (12, u"N"), (13, u"n")),
        _row((2, u"s"), (3, u"N"), (4, u"g"), (5, u"NNNNNN"), (11, u"g"), (12, u"N"), (13, u"n")),
        _row((2, u"s"), (3, u"N"), (4, u"g"), (5, u"NN"), (7, u"ww"), (9, u"NN"), (11, u"g"), (12, u"N"), (13, u"n")),
        _row((2, u"s"), (3, u"N"), (4, u"g"), (5, u"N"), (6, u"wWWw"), (10, u"N"), (11, u"g"), (12, u"N"), (13, u"n")),
        _row((2, u"s"), (3, u"N"), (4, u"g"), (5, u"N"), (6, u"wWWw"), (10, u"N"), (11, u"g"), (12, u"N"), (13, u"n")),
        _row((2, u"s"), (3, u"N"), (4, u"g"), (5, u"NN"), (7, u"ww"), (9, u"NN"), (11, u"g"), (12, u"N"), (13, u"n")),
        _row((2, u"s"), (3, u"N"), (4, u"g"), (5, u"NHHHN"), (11, u"g"), (12, u"N"), (13, u"n")),
        _row((2, u"s"), (3, u"N"), (4, u"g"), (5, u"HHHHHH"), (11, u"g"), (12, u"N"), (13, u"n")),
        _row((2, u"s"), (3, u"N"), (4, u"gggggggg"), (12, u"N"), (13, u"n")),   # y12 金边下
        _row((2, u"s"), (3, u"N" * 10), (13, u"n")),                # y13
        _row((2, u"nnnnnnnnnnnn")),                                 # y14 下边
        _row(),                                                     # y15
    ]
    px = []
    for y, row in enumerate(art):
        assert len(row) == 16, u"图标第 %d 行长度 %d" % (y, len(row))
        for ch in row:
            assert ch in ICON_PALETTE, u"图标出现调色板外的字符 %r" % ch
            px.append(ICON_PALETTE[ch])
    assert len(px) == 256, u"图标像素数 %d" % len(px)
    opaque = sum(1 for p in px if p[3] == 255)
    assert 0 < opaque < 256, u"图标不透明像素 %d（物品图必须有透明底）" % opaque

    from _zf66_png import write_png
    p = os.path.join(OUT, u"star_chart_tome.png")
    write_png(p, 16, 16, px)
    # 10 倍预览（16×16 直接看太小，档案 §6.8 的做法）
    big = []
    for y in range(16):
        row = px[y * 16:(y + 1) * 16]
        for _ in range(10):
            for q in row:
                big += [q] * 10
    write_png(os.path.join(OUT, u"star_chart_tome_x10.png"), 160, 160, big)
    print(u"   star_chart_tome  16x16 不透明 %d (%.1f%%) -> %s" % (opaque, 100.0 * opaque / 256, p))
    if write:
        import shutil
        shutil.copyfile(p, os.path.join(ICON_DEST, u"star_chart_tome.png"))
        print(u"   >>> 已写入 %s" % os.path.join(ICON_DEST, u"star_chart_tome.png"))


def main(argv):
    write = "--write" in argv
    os.makedirs(OUT, exist_ok=True)
    if write:
        os.makedirs(DEST, exist_ok=True)
        os.makedirs(ICON_DEST, exist_ok=True)
    make_icon(write)
    total_pal = total_rgb = 0
    for name in SOURCES:
        img = center_crop_2to1(load(name))
        img = resize(img, W, H)
        # 调色板：从图上抽 1/16 像素做中位切分（够代表，快得多）
        sample = img[::4, ::4].reshape(-1, 3)
        pal = median_cut(sample, 256)
        idx = dither_fs(img, pal)
        pal_rgb = pal[idx.astype(np.int64)]
        pal_path = os.path.join(OUT, name + u"_pal.png")
        rgb_path = os.path.join(OUT, name + u"_rgb.png")
        write_png_palette(pal_path, W, H, idx, pal)
        write_png_rgb(rgb_path, W, H, np.clip(img, 0, 255).astype(np.uint8))
        write_preview(os.path.join(OUT, name + u"_preview.png"), pal_rgb)
        sp, sr = os.path.getsize(pal_path), os.path.getsize(rgb_path)
        total_pal += sp
        total_rgb += sr
        # 量化误差（能失败的判据：均值绝对误差应当很小）
        err = np.abs(pal_rgb.astype(np.float32) - img).mean()
        print(u"   %-14s 调色板 %6.0f KB / 直存 %6.0f KB   量化平均误差 %.2f/255"
              % (name, sp / 1024.0, sr / 1024.0, err))
        if write:
            # 用调色板那版（体积小一个数量级，画质看预览图）
            import shutil
            shutil.copyfile(pal_path, os.path.join(DEST, name + u".png"))
    print(u"   合计：调色板 %.1f MB / 直存 %.1f MB" % (total_pal / 1048576.0, total_rgb / 1048576.0))
    if write:
        print(u"   已写入 %s" % DEST)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
