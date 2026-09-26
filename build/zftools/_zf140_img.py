# -*- coding: utf-8 -*-
u"""_zf140_img.py —— ZF140 用的图像小工具（本机没有 Pillow，只有 numpy）

为什么另起一个而不是复用 `_zf66_png.py`：那个是**纯标准库 + 逐像素 Python 循环**，
读一张 690x1227 要好几秒、写一张同样慢。这里统一走 numpy + zlib，快两个数量级，
但**读写口径与 `_zf66_png.py` 完全一致**（8 位、非隔行、colorType 2/6），
所以两边可以互相验：`_zf140_verify.py` 里拿 `_zf66_png.read_png` 交叉复核。
"""
import struct
import zlib

import numpy as np


def _chunk(tag, body):
    return (struct.pack(">I", len(body)) + tag + body
            + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))


def _png(path, arr, ctype):
    h, w, c = arr.shape
    raw = np.zeros((h, w * c + 1), dtype=np.uint8)
    raw[:, 1:] = arr.reshape(h, w * c)
    head = struct.pack(">IIBBBBB", w, h, 8, ctype, 0, 0, 0)
    body = _chunk(b"IHDR", head) + _chunk(b"IDAT", zlib.compress(raw.tobytes(), 9)) + _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + body)
    return path


def write_rgb(path, arr):
    u"""arr: HxWx3 uint8"""
    return _png(path, np.ascontiguousarray(arr, dtype=np.uint8), 2)


def write_rgba(path, arr):
    u"""arr: HxWx4 uint8（直存、不预乘 —— 与 _zf66_png.write_png 同口径）"""
    return _png(path, np.ascontiguousarray(arr, dtype=np.uint8), 6)


def read_png_np(path):
    u"""读 8 位非隔行 PNG -> (H,W,C) uint8（C=3 或 4）。只认 colorType 2/6，其余报错。"""
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not png: " + path
    pos, idat = 8, bytearray()
    w = h = ctype = None
    while pos + 8 <= len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype, comp, filt, inter = struct.unpack(">IIBBBBB", body)
            assert depth == 8 and inter == 0, "只支持 8 位非隔行"
            assert ctype in (2, 6), "只支持 colorType 2/6，收到 %d" % ctype
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        pos += 12 + ln
    c = 3 if ctype == 2 else 4
    raw = np.frombuffer(zlib.decompress(bytes(idat)), dtype=np.uint8)
    stride = w * c
    assert raw.size == h * (stride + 1), u"IDAT 长度 %d 与 %dx%d 不符" % (raw.size, w, h)
    rows = raw.reshape(h, stride + 1)
    assert (rows[:, 0] == 0).all(), u"只支持 filter=0 的 PNG（本工程自己写出来的都是 0）"
    return rows[:, 1:].reshape(h, w, c).copy()


def resize_bilinear(img, w, h):
    u"""双线性缩放（img 可以是 HxWx3 或 HxWx4；用 float 算完再夹回 0..255）"""
    img = img.astype(np.float32)
    sh, sw = img.shape[:2]
    ys = np.linspace(0, sh - 1, h)
    xs = np.linspace(0, sw - 1, w)
    y0 = np.floor(ys).astype(np.int64)
    y1 = np.minimum(y0 + 1, sh - 1)
    fy = (ys - y0)[:, None, None]
    x0 = np.floor(xs).astype(np.int64)
    x1 = np.minimum(x0 + 1, sw - 1)
    fx = (xs - x0)[None, :, None]
    top = img[y0][:, x0] * (1 - fx) + img[y0][:, x1] * fx
    bot = img[y1][:, x0] * (1 - fx) + img[y1][:, x1] * fx
    return np.clip(top * (1 - fy) + bot * fy, 0, 255)


def crop_scale(img, cx, cy, half, size):
    u"""以 (cx,cy) 为中心、边长 2*half 的方框 -> size x size（越界处补 0）"""
    sh, sw = img.shape[:2]
    x0 = int(round(cx - half))
    y0 = int(round(cy - half))
    side = int(round(2 * half))
    pad = np.zeros((side, side) + img.shape[2:], dtype=img.dtype)
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(sw, x0 + side), min(sh, y0 + side)
    pad[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = img[sy0:sy1, sx0:sx1]
    return resize_bilinear(pad, size, size)


def blur3(a):
    u"""3x3 箱型模糊（用于给 alpha 边缘一点过渡，不加权、可重复叠加）"""
    p = np.pad(a.astype(np.float32), 1, mode="edge")
    return (p[:-2, :-2] + p[:-2, 1:-1] + p[:-2, 2:] +
            p[1:-1, :-2] + p[1:-1, 1:-1] + p[1:-1, 2:] +
            p[2:, :-2] + p[2:, 1:-1] + p[2:, 2:]) / 9.0


def flood(mask, seeds):
    u"""4 邻域洪泛：mask 为 True 处可通行；seeds 是 [(y,x), ...]。返回 visited 布尔图。"""
    h, w = mask.shape
    vis = np.zeros((h, w), dtype=bool)
    stack = []
    for (y, x) in seeds:
        if 0 <= y < h and 0 <= x < w and mask[y, x] and not vis[y, x]:
            vis[y, x] = True
            stack.append((y, x))
    while stack:
        y, x = stack.pop()
        if y > 0 and mask[y - 1, x] and not vis[y - 1, x]:
            vis[y - 1, x] = True
            stack.append((y - 1, x))
        if y + 1 < h and mask[y + 1, x] and not vis[y + 1, x]:
            vis[y + 1, x] = True
            stack.append((y + 1, x))
        if x > 0 and mask[y, x - 1] and not vis[y, x - 1]:
            vis[y, x - 1] = True
            stack.append((y, x - 1))
        if x + 1 < w and mask[y, x + 1] and not vis[y, x + 1]:
            vis[y, x + 1] = True
            stack.append((y, x + 1))
    return vis
