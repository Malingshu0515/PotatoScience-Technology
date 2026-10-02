# -*- coding: utf-8 -*-
u"""_zf117_show.py —— 从**模型 JSON 本体**解析每个面用哪张贴图，再渲染复核图

这一版不是手写"我以为的映射"，而是**读模型文件**：
  parent=cube_bottom_top 时，按 Mojang 的约定展开成六个面
  （up->top, down->bottom, north/south/east/west->side），逐个把贴图取出来画。
⇒ 图上看到的，就是游戏里会看到的。
"""
import io
import json
import os
import struct
import sys
import zlib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

ASSETS = r"E:\PotatoST\src\main\resources\assets\potato_s_t"
MODELB = os.path.join(ASSETS, "models", "block")
TEXB = os.path.join(ASSETS, "textures", "block")
TEXI = os.path.join(ASSETS, "textures", "item")
OUT = r"E:\PotatoST\build\zftools\_zf117_show.png"
Z = 11
PAD = 8

# cube_bottom_top 的官方面 -> 贴图槽映射（1.21.1）
FACE_SLOT = {"up": "top", "down": "bottom",
             "north": "side", "south": "side", "east": "side", "west": "side"}
# cube_all：六面都取 all
CUBE_ALL = {"up": "all", "down": "all", "north": "all",
            "south": "all", "east": "all", "west": "all"}


def resolve_face(model):
    """返回 {面: 贴图文件路径}，或 None（认不出的父级）"""
    parent = model.get("parent", "")
    tex = model.get("textures", {})
    if parent.endswith("cube_bottom_top"):
        slots = FACE_SLOT
    elif parent.endswith("cube_all"):
        slots = CUBE_ALL
    else:
        return None
    out = {}
    for face, slot in slots.items():
        ref = tex.get(slot)
        if not ref:
            return None
        name = ref.split(":")[-1].split("/")[-1]
        out[face] = os.path.join(TEXB, name + ".png")
    return out


def load(p):
    return read_png(p) if os.path.exists(p) else None


def wpng(path, w, h, buf):
    raw = b""
    for y in range(h):
        raw += b"\x00" + bytes(buf[y * w * 4:(y + 1) * w * 4])

    def ch(t, p):
        return struct.pack(">I", len(p)) + t + p + struct.pack(">I", zlib.crc32(t + p) & 0xFFFFFFFF)

    io.open(path, "wb").write(b"\x89PNG\r\n\x1a\n"
                              + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                              + ch(b"IDAT", zlib.compress(raw, 6)) + ch(b"IEND", b""))


def draw(buf, W, ox, oy, tile_px, w, h, rgba):
    """把 w×h 的贴图按最近邻缩放进 tile_px×tile_px 的格子。

    ⚠ 不能假设贴图正好 16×16 —— `lithium_battery` 那套是 **160×160**，
    第一版写死 16*zoom 直接 IndexError（缓冲区越界）。这里按格子采样。
    """
    for y in range(tile_px):
        sy = min(h - 1, y * h // tile_px)
        for x in range(tile_px):
            sx = min(w - 1, x * w // tile_px)
            si = (sy * w + sx) * 4
            a = rgba[si + 3]
            if a == 0:
                continue
            di = ((oy + y) * W + (ox + x)) * 4
            if a == 255:
                buf[di:di + 3] = bytes(rgba[si:si + 3])
            else:
                for c in range(3):
                    buf[di + c] = (rgba[si + c] * a + buf[di + c] * (255 - a)) // 255
            buf[di + 3] = 255


BLOCKS = ["lithium_battery_plant", "diesel_generator_controller", "lithium_battery"]
FACES = ["up", "down", "north", "south", "east", "west"]

rows = []
labels = []
for b in BLOCKS:
    mp = os.path.join(MODELB, b + ".json")
    if not os.path.exists(mp):
        print(u"  !! 缺模型 %s" % b)
        continue
    model = json.loads(io.open(mp, encoding="utf-8").read())
    faces = resolve_face(model)
    if faces is None:
        print(u"  !! %s 的父级 %s 认不出，跳过" % (b, model.get("parent")))
        continue
    row = []
    for f in FACES:
        img = load(faces[f])
        if img is None:
            print(u"  !! %s 的 %s 贴图缺失：%s" % (b, f, faces[f]))
            row = []
            break
        row.append((f, img))
    if row:
        rows.append(row)
        labels.append(b)
        print(u"  %s（parent=%s）" % (b, model.get("parent")))
        for f in FACES:
            print(u"      %-6s -> %s" % (f, os.path.basename(faces[f])))

tile = 16 * Z
cols = 6
W = PAD + cols * (tile + PAD)
H = PAD + len(rows) * (tile + PAD)
buf = bytearray(W * H * 4)
for i in range(W * H):
    x, y = i % W, i // W
    v = 52 if ((x // 8) + (y // 8)) % 2 == 0 else 78
    buf[i * 4:i * 4 + 4] = bytes((v, v, v + 4, 255))

for ri, row in enumerate(rows):
    oy = PAD + ri * (tile + PAD)
    for ci, (face, (w, h, rgba)) in enumerate(row):
        draw(buf, W, PAD + ci * (tile + PAD), oy, tile, w, h, rgba)

wpng(OUT, W, H, buf)
print(u"\n列序：UP / DOWN / 北 / 南 / 东 / 西   行序：%s" % u" / ".join(labels))
print(u"复核图: %s (%dx%d)" % (OUT, W, H))
