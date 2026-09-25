# -*- coding: utf-8 -*-
u"""_zf84_gasoline.py —— 把用户这张新图写成汽油的流体贴图（still + flow）

用户原话：「**汽油的新贴图**」（附 16×16 JPEG）。

事实与做法：
  · 汽油现在的两张贴图 `gasoline_still.png` / `gasoline_flow.png` **逐字节相同**
    （ZF78 约定：同一张图兼作 still / flow）⇒ 这次也两张一起换、保持约定；
  · 格式照旧：**16×16 / 8 位 / RGBA**、**全不透明**（流体贴图不该有透明像素）；
  · 原图按 §4.24 存 `build/用户素材/gasoline_new.jpg`（ASCII 名）并记哈希；
  · 顺手把"换了没有"做成可判据：新图必须**与旧图不同**，且颜色分布确实是用户那张
    （取新图前几行像素与写出的 PNG 逐像素比对）。
"""
import hashlib
import io
import json
import os
import struct
import sys
import zlib

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
USERART = os.path.join(ROOT, "build", u"用户素材")
TEXB = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "textures", "block")
NEW_JPG = os.path.join(USERART, u"gasoline_new.jpg")
TARGETS = [u"gasoline_still.png", u"gasoline_flow.png"]
fails = []


def write_png16(path, px):
    u"""16×16 / 8 位 / RGBA。px = 256 个 (r,g,b,a)。"""
    raw = b""
    for y in range(16):
        raw += b"\x00" + b"".join(bytes(px[y * 16 + x]) for x in range(16))

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", 16, 16, 8, 6, 0, 0, 0)
    io.open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                              + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def read_png_rgba(path):
    b = io.open(path, "rb").read()
    w, h = struct.unpack(">II", b[16:24])
    idat = b""
    i = 8
    while i < len(b):
        ln = struct.unpack(">I", b[i:i + 4])[0]
        tag = b[i + 4:i + 8]
        if tag == b"IDAT":
            idat += b[i + 8:i + 8 + ln]
        i += 12 + ln
    raw = zlib.decompress(idat)
    px = []
    for y in range(h):
        off = y * (w * 4 + 1)
        if raw[off] != 0:
            return None
        for x in range(w):
            px.append(tuple(raw[off + 1 + x * 4:off + 5 + x * 4]))
    return px


def main():
    if not os.path.exists(NEW_JPG):
        print(u"  !! 找不到原图 %s（上一步 .NET 导出前应先把它拷进来）" % NEW_JPG)
        return 1
    jpg_sha = hashlib.sha1(open(NEW_JPG, "rb").read()).hexdigest()
    px_json = json.loads(io.open(os.path.join(TOOLS, u"_zf84_pixels.json"), encoding="utf-8").read())
    if len(px_json) != 256:
        print(u"  !! 像素数不是 256（%d）—— 这张不是 16×16？" % len(px_json))
        return 1
    rgb = [tuple(int(v) for v in s.split(u",")) for s in px_json]
    new_px = [(r, g, b, 255) for (r, g, b) in rgb]

    # 旧图（判"换了没有"）
    old_sha = {}
    for name in TARGETS:
        p = os.path.join(TEXB, name)
        old_sha[name] = hashlib.sha1(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None

    for name in TARGETS:
        write_png16(os.path.join(TEXB, name), new_px)
        p = os.path.join(TEXB, name)
        b = open(p, "rb").read()
        w, h = struct.unpack(">II", b[16:24])
        back = read_png_rgba(p)
        same_px = sum(1 for a, c in zip(back, new_px) if a == c)
        print(u"  [OK]   %s：%d×%d 位深 %d 类型 %d，写回核对 %d/256 像素一致，sha1 %s…"
              % (name, w, h, b[24], b[25], same_px, hashlib.sha1(b).hexdigest()[:8]))
        if (w, h, b[24], b[25]) != (16, 16, 8, 6):
            fails.append(u"%s：格式不对（%d×%d 位深 %d 类型 %d）" % (name, w, h, b[24], b[25]))
        if same_px != 256:
            fails.append(u"%s：写出来与源像素不一致（%d/256）" % (name, same_px))
        if old_sha[name] and hashlib.sha1(b).hexdigest() == old_sha[name]:
            fails.append(u"%s：与旧图逐字节相同 ⇒ 等于没换" % name)

    # 两张必须一致（ZF78 约定）
    a = hashlib.sha1(open(os.path.join(TEXB, TARGETS[0]), "rb").read()).hexdigest()
    c = hashlib.sha1(open(os.path.join(TEXB, TARGETS[1]), "rb").read()).hexdigest()
    if a != c:
        fails.append(u"still 与 flow 不一致（ZF78 约定是同一张图）")

    # 颜色分布（让汇报里能写清"确实是你那张"）
    uniq = len(set(rgb))
    avg = tuple(sum(p[i] for p in rgb) // 256 for i in range(3))
    print(u"  —— 这张图：%d 种颜色，平均 RGB %s，原图 sha1 %s…" % (uniq, avg, jpg_sha[:8]))

    # 来源凭据
    prov_p = os.path.join(USERART, u"_来源凭据.json")
    prov = json.loads(io.open(prov_p, encoding="utf-8").read()) if os.path.exists(prov_p) else {}
    prov[u"gasoline_new.jpg"] = {
        "sha1": jpg_sha,
        "bytes": os.path.getsize(NEW_JPG),
        "说明": u"用户 2026-09-24 发来的「汽油的新贴图」（16×16 JPEG）⇒ 转档成 "
                u"textures/block/gasoline_still.png 与 gasoline_flow.png（16×16 / 8 位 / RGBA / 全不透明）",
    }
    io.open(prov_p, "w", encoding="utf-8", newline=u"\n").write(
        json.dumps(prov, indent=2, ensure_ascii=False) + u"\n")
    print(u"  [OK]   来源凭据已更新（%s）" % prov_p)

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
