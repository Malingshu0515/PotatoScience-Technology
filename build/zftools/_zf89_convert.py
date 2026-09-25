# -*- coding: utf-8 -*-
u"""_zf89_convert.py —— 用户新放的流体贴图 → 本工程的 still + flow（可反复跑、幂等）

用户这一轮是**一张一张往 `textures/block` 里丢**（和 ZF88 的石油/柴油同一套）：
  · `汽油.png`   → `gasoline_still.png` + `gasoline_flow.png`
  · `石脑油.png` → `naphtha_still.png`  + `naphtha_flow.png`
（`JOBS` 里没出现的流体不动；将来再加液化石油气只需往表里添一行。）

做法沿用 ZF88：读像素**原样写出**（零重采样、零调色），并核：
  ① 16×16 / 8 位 / RGBA（本工程规格）；② alpha 全 255；③ 与旧图**逐字节不同**。
原图按 §4.24 挪到 `build/用户素材/` 并记哈希。

**幂等**：源图已经处理过（被挪走）时，不报错 —— 改为"用留档原图复查盘上的成品像素是否一致"，
所以这个脚本可以在同一轮里反复跑（用户还在继续丢图）。
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
TEXI = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
USERART = os.path.join(ROOT, "build", u"用户素材")
JOBS = [(u"汽油.png", u"gasoline", u"gasoline.png"),
        (u"石脑油.png", u"naphtha", u"naphtha.png")]
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


def pixels(path):
    w, h, ctype, px0 = _zf66_png.read_png(path)
    return (w, h, ctype, [p if len(p) == 4 else (p[0], p[1], p[2], 255) for p in px0])


def main():
    prov_p = os.path.join(USERART, u"_来源凭据.json")
    prov = json.loads(io.open(prov_p, encoding="utf-8").read()) if os.path.exists(prov_p) else {}
    os.makedirs(USERART, exist_ok=True)
    changed = 0

    for src_name, fluid, ascii_name in JOBS:
        src = os.path.join(TEXB, src_name)
        keep = os.path.join(USERART, ascii_name)
        print(u"== %s ==" % src_name)
        if not os.path.exists(src):
            if os.path.exists(keep):
                w, h, ctype, src_px = pixels(keep)
                same = True
                for suffix in (u"_still", u"_flow"):
                    dst = os.path.join(TEXB, fluid + suffix + u".png")
                    if not os.path.exists(dst):
                        fails.append(u"%s：源图已挪走，而 %s%s.png 不存在" % (src_name, fluid, suffix))
                        same = False
                        continue
                    _, _, _, px = pixels(dst)
                    n = sum(1 for a, b in zip(src_px, px) if a == b)
                    if n != 256:
                        fails.append(u"%s%s.png 与留档原图不一致（%d/256）" % (fluid, suffix, n))
                        same = False
                print(u"   [SKIP] 已处理过；复查留档原图 → 盘上成品像素一致：%s" % (u"是" if same else u"否"))
                continue
            fails.append(u"既没有源图 %s，也没有留档 %s" % (src_name, ascii_name))
            continue

        w, h, ctype, px = pixels(src)
        print(u"   %d×%d ctype %s" % (w, h, ctype))
        if (w, h) != (16, 16):
            fails.append(u"%s 不是 16×16（%d×%d）" % (src_name, w, h))
        trans = sum(1 for p in px if p[3] != 255)
        cols = len(set((p[0], p[1], p[2]) for p in px))
        avg = tuple(sum(p[i] for p in px) // len(px) for i in range(3))
        print(u"   %d 种颜色，平均 RGB %s，非全不透明像素 %d 个" % (cols, avg, trans))
        if trans:
            fails.append(u"%s：有 %d 个像素不是全不透明 —— 流体贴图不该有透明" % (src_name, trans))

        for suffix in (u"_still", u"_flow"):
            dst = os.path.join(TEXB, fluid + suffix + u".png")
            old_sha = (hashlib.sha1(open(dst, "rb").read()).hexdigest()
                       if os.path.exists(dst) else None)
            write_png16(dst, px)
            new_sha = hashlib.sha1(open(dst, "rb").read()).hexdigest()
            print(u"   [OK]   %s%s.png（%s… → %s…）"
                  % (fluid, suffix, (old_sha or u"无")[:8], new_sha[:8]))
            if old_sha == new_sha:
                fails.append(u"%s%s 与旧图逐字节相同 ⇒ 等于没换" % (fluid, suffix))
            b = open(dst, "rb").read()
            if (struct.unpack(">II", b[16:24]), b[24], b[25]) != ((16, 16), 8, 6):
                fails.append(u"%s%s 写出的格式不对" % (fluid, suffix))

        raw = open(src, "rb").read()
        io.open(keep, "wb").write(raw)
        prov[ascii_name] = {
            "sha1": hashlib.sha1(raw).hexdigest(), "bytes": len(raw),
            "说明": u"用户放的流体素材（%s）⇒ 转档成 textures/block/%s_still.png 与 %s_flow.png"
                    % (src_name, fluid, fluid)}
        os.remove(src)
        changed += 1
        print(u"   [OK]   原图挪到 build/用户素材/%s（sha1 %s…）"
              % (ascii_name, prov[ascii_name]["sha1"][:8]))

    if changed:
        io.open(prov_p, "w", encoding="utf-8", newline=u"\n").write(
            json.dumps(prov, indent=2, ensure_ascii=False) + u"\n")

    for folder, label in ((TEXB, u"textures/block"), (TEXI, u"textures/item")):
        left = [f for f in os.listdir(folder) if any(ord(c) > 127 for c in f)
                and not f.endswith(u".原名件")]
        if left:
            fails.append(u"%s 下还有中文名（非 .原名件）：%s" % (label, left))
        else:
            print(u"\n   [OK]   %s 下已无中文名（.原名件 除外）" % label)
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
