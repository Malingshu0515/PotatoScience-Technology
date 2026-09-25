# -*- coding: utf-8 -*-
u"""_zf88_convert.py —— 用户新放的两张流体贴图（石油 / 柴油）→ 四种流体的 still+flow

用户这一批又是"直接放图进资源目录"（这次在 `textures/block`）：
  · `石油.png` → `crude_oil_still.png` + `crude_oil_flow.png`
  · `柴油.png` → `diesel_still.png`  + `diesel_flow.png`

两种都是 16×16 / 8 位 / RGBA 的**已是好格式**的 PNG（不用转档去背景，流体贴图本来就全不透明）。
但必须核两件事：
  ① alpha 是否全 255（流体贴图不该有透明像素；ZF84 的汽油那张就是全不透明）；
  ② 与旧图**不同**（否则等于没换）。
做法：读源图 → 直接把像素原样写成目标四张（**零重采样、零调色**，除非 alpha 有问题要报出来），
原图按 §4.24 挪到 `build/用户素材/` 并存哈希。
"""
import hashlib
import io
import json
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _zf66_png  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TEXB = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\block")
USERART = os.path.join(ROOT, "build", u"用户素材")
JOBS = [(u"石油.png", u"crude_oil", u"crude_oil.png"),
        (u"柴油.png", u"diesel", u"diesel.png")]
fails = []


def write_png16(path, px):
    raw = b""
    for y in range(16):
        raw += b"\x00" + b"".join(bytes(px[y * 16 + x]) for x in range(16))

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", 16, 16, 8, 6, 0, 0, 0)
    io.open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                              + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def main():
    prov_p = os.path.join(USERART, u"_来源凭据.json")
    prov = json.loads(io.open(prov_p, encoding="utf-8").read()) if os.path.exists(prov_p) else {}
    os.makedirs(USERART, exist_ok=True)
    for src_name, fluid, ascii_name in JOBS:
        src = os.path.join(TEXB, src_name)
        if not os.path.exists(src):
            fails.append(u"找不到 %s" % src_name)
            continue
        w, h, ctype, px0 = _zf66_png.read_png(src)
        px = [p if len(p) == 4 else (p[0], p[1], p[2], 255) for p in px0]
        print(u"== %s：%d×%d ctype %s ==" % (src_name, w, h, ctype))
        if (w, h) != (16, 16):
            fails.append(u"%s 不是 16×16（%d×%d）" % (src_name, w, h))
        trans = sum(1 for p in px if p[3] != 255)
        cols = len(set((p[0], p[1], p[2]) for p in px))
        avg = tuple(sum(p[i] for p in px) // len(px) for i in range(3))
        print(u"   %d 种颜色，平均 RGB %s，非全不透明像素 %d 个" % (cols, avg, trans))
        if trans:
            fails.append(u"%s：有 %d 个像素不是全不透明 —— 流体贴图不该有透明（要不要照旧？先报出来）"
                         % (src_name, trans))
        for suffix in (u"_still", u"_flow"):
            dst = os.path.join(TEXB, fluid + suffix + u".png")
            old_sha = (hashlib.sha1(open(dst, "rb").read()).hexdigest()
                       if os.path.exists(dst) else None)
            write_png16(dst, px)
            new_sha = hashlib.sha1(open(dst, "rb").read()).hexdigest()
            print(u"  [OK]   %s%s.png（%s… → %s…）"
                  % (fluid, suffix, (old_sha or u"无")[:8], new_sha[:8]))
            if old_sha == new_sha:
                fails.append(u"%s%s 与旧图逐字节相同 ⇒ 等于没换" % (fluid, suffix))
            b = open(dst, "rb").read()
            if (struct.unpack(">II", b[16:24]), b[24], b[25]) != ((16, 16), 8, 6):
                fails.append(u"%s%s 写出的格式不对" % (fluid, suffix))
        raw = open(src, "rb").read()
        dst_prov = os.path.join(USERART, ascii_name)
        io.open(dst_prov, "wb").write(raw)
        prov[ascii_name] = {"sha1": hashlib.sha1(raw).hexdigest(), "bytes": len(raw),
                            "说明": u"用户放的流体素材（%s）⇒ 转档成 textures/block/%s_still.png 与 %s_flow.png"
                                    % (src_name, fluid, fluid)}
        os.remove(src)
        print(u"  [OK]   原图挪到 build/用户素材/%s" % ascii_name)
    io.open(prov_p, "w", encoding="utf-8", newline=u"\n").write(
        json.dumps(prov, indent=2, ensure_ascii=False) + u"\n")
    left = [f for f in os.listdir(TEXB) if any(ord(c) > 127 for c in f) and not f.endswith(u".原名件")]
    if left:
        fails.append(u"textures/block 下还有中文名（非 .原名件）：%s" % left)
    else:
        print(u"\n  [OK]   textures/block 下已无中文名（.原名件 除外）")
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
