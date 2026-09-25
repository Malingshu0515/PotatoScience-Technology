# -*- coding: utf-8 -*-
u"""_zf87_convert.py —— 用户新放的 `油桶.jpg` → `oil_bucket.png` + 模型改指向自己

（`oil_bucket` 的物品图标一直借的是**原版铁锭**，见 models/item/oil_bucket.json。
 转档规则同 ZF83/ZF86：四边泛洪去背景 + 只留最大连通域 ⇒ 16×16 / 8 位 / RGBA；
 原图按 §4.24 挪到 build/用户素材/oil_bucket.jpg 并记哈希。）
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
TEX = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
MODELS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\item")
SRC = os.path.join(TEX, u"油桶.jpg")
TOL = 26
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


def strip_background(px):
    alpha = [255] * 256
    corners = [px[0], px[15], px[240], px[255]]
    bg = tuple(sorted(c[i] for c in corners)[1] for i in range(3))
    stack = [i for i in range(256)
             if (i // 16 in (0, 15) or i % 16 in (0, 15))
             and all(abs(px[i][c] - bg[c]) <= TOL for c in range(3))]
    seen = set(stack)
    while stack:
        i = stack.pop()
        alpha[i] = 0
        y, x = divmod(i, 16)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < 16 and 0 <= nx < 16:
                j = ny * 16 + nx
                if j not in seen and all(abs(px[j][c] - bg[c]) <= TOL for c in range(3)):
                    seen.add(j)
                    stack.append(j)
    visited, comps = set(), []
    for i in range(256):
        if alpha[i] == 0 or i in visited:
            continue
        comp, st = set(), [i]
        while st:
            k = st.pop()
            if k in comp:
                continue
            comp.add(k)
            ky, kx = divmod(k, 16)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = ky + dy, kx + dx
                    if 0 <= ny < 16 and 0 <= nx < 16:
                        j = ny * 16 + nx
                        if alpha[j] != 0 and j not in comp:
                            st.append(j)
        comps.append(comp)
        visited |= comp
    if comps:
        main = max(comps, key=len)
        for comp in comps:
            if comp is not main:
                for k in comp:
                    alpha[k] = 0
    return [(px[i][0], px[i][1], px[i][2], alpha[i]) for i in range(256)], bg


def main():
    if not os.path.exists(SRC):
        print(u"  !! 找不到 %s" % SRC)
        return 1
    d = json.loads(io.open(os.path.join(TOOLS, u"_zf87_oil_pixels.json"), encoding="utf-8").read())
    if d[u"w"] != 16 or d[u"h"] != 16 or len(d[u"px"]) != 256:
        print(u"  !! 源图不是 16×16（%sx%s / %d 个像素）" % (d[u"w"], d[u"h"], len(d[u"px"])))
        return 1
    src_px = [tuple(int(v) for v in s.split(u",")) for s in d[u"px"]]
    out, bg = strip_background(src_px)
    opaque = sum(1 for p in out if p[3] == 255)
    print(u"背景色 %s：去掉 %d 个，留下 %d 个主体像素" % (bg, 256 - opaque, opaque))
    if not (40 <= opaque <= 230):
        fails.append(u"留下 %d 个像素，不像一个物品图标" % opaque)
    for y in range(16):
        print(u"     " + u"".join(u"#" if out[y * 16 + x][3] == 255 else u"." for x in range(16)))
    write_png16(os.path.join(TEX, u"oil_bucket.png"), out)
    b = open(os.path.join(TEX, u"oil_bucket.png"), "rb").read()
    w, h = struct.unpack(">II", b[16:24])
    print(u"  [OK]   oil_bucket.png 写出：%d×%d 位深 %d 类型 %d，sha1 %s…"
          % (w, h, b[24], b[25], hashlib.sha1(b).hexdigest()[:8]))
    if (w, h, b[24], b[25]) != (16, 16, 8, 6):
        fails.append(u"写出的 PNG 格式不对")

    # 模型改指向自己
    p = os.path.join(MODELS, u"oil_bucket.json")
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(json.dumps(
        {"parent": "minecraft:item/generated", "textures": {"layer0": "potato_s_t:item/oil_bucket"}},
        indent=2, ensure_ascii=False) + u"\n")
    print(u"  [OK]   oil_bucket.json → potato_s_t:item/oil_bucket（原先借原版铁锭）")

    # 原图留档
    raw = open(SRC, "rb").read()
    os.makedirs(USERART, exist_ok=True)
    dst = os.path.join(USERART, u"oil_bucket.jpg")
    io.open(dst, "wb").write(raw)
    prov_p = os.path.join(USERART, u"_来源凭据.json")
    prov = json.loads(io.open(prov_p, encoding="utf-8").read()) if os.path.exists(prov_p) else {}
    prov[u"oil_bucket.jpg"] = {"sha1": hashlib.sha1(raw).hexdigest(), "bytes": len(raw),
                               "说明": u"用户放的油桶素材（油桶.jpg）⇒ 转档成 textures/item/oil_bucket.png"}
    io.open(prov_p, "w", encoding="utf-8", newline=u"\n").write(
        json.dumps(prov, indent=2, ensure_ascii=False) + u"\n")
    os.remove(SRC)
    print(u"  [OK]   原图挪到 build/用户素材/oil_bucket.jpg（资源目录不再留中文名）")

    left = [f for f in os.listdir(TEX) if any(ord(c) > 127 for c in f)]
    if left:
        fails.append(u"textures/item 下还有中文名：%s" % left)
    else:
        print(u"  [OK]   textures/item 下已无中文文件名")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
