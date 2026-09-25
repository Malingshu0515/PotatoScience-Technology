# -*- coding: utf-8 -*-
u"""_zf86_convert.py —— 用户刚放的四张：铜板（被存成了 JPEG）+ 氯化钠 + 电容 + 碳酸锂

用户这一批是"又放了几张图进 item 文件夹"（和 ZF83 的板材同一套流程）：
  · `copper_plate.png` —— 扩展名是 .png，**内容其实是 JPEG**（用户重存时被存成 jpg），
    游戏里会当坏图 ⇒ 解出来重写成真 PNG（**保留用户的画**）；
  · `氯化钠.jpg` → `sodium_chloride.png`（该物品原先借原版**糖**的贴图）
  · `电容.jpg`   → `capacitor.png`（原先借原版**铁粒**）
  · `碳酸锂.png`（**20×20**，自带 alpha）→ `lithium_carbonate.png`（裁到 16×16，不重采样）

做法沿用 ZF83/ZF84 的规矩：
  ① 白/深底素材**从四边泛洪**去背景（不是一刀切白色）；
  ② 只保留最大连通域（清掉 JPEG 噪点在主体外留的孤立像素）；
  ③ 一律写成 **16×16 / 8 位 / RGBA**；
  ④ 原图按 §4.24 挪到 `build/用户素材/`（ASCII 名）并记哈希，**资源目录里不留中文名**。
"""
import hashlib
import io
import json
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _zf66_png  # noqa: E402  （本工程既有的 PNG 读写器：支持全部 filter / PLTE / tRNS）

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
USERART = os.path.join(ROOT, "build", u"用户素材")
TEX = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
MODELS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\item")
TOL = 26
fails = []

# (物品名, 原图文件名, 目标贴图名, 原图来源)
JPEG_JOBS = [
    (u"copper_plate", u"copper_plate.png", u"copper_plate.png", u"jpg_in_png_name"),
    (u"sodium_chloride", u"氯化钠.jpg", u"sodium_chloride.png", u"plain"),
    (u"capacitor", u"电容.jpg", u"capacitor.png", u"plain"),
]


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


def strip_background(px, w, h):
    u"""从四边泛洪去背景（同 ZF83），再只留最大连通域。px = [(r,g,b,a)]，返回新的 a 列表。"""
    alpha = [p[3] for p in px]
    corners = [px[0], px[w - 1], px[(h - 1) * w], px[h * w - 1]]
    bg = tuple(sorted(c[i] for c in corners)[1] for i in range(3))
    stack = []
    for i in range(w * h):
        y, x = divmod(i, w)
        if (y in (0, h - 1) or x in (0, w - 1)) and all(
                abs(px[i][c] - bg[c]) <= TOL for c in range(3)):
            stack.append(i)
    seen = set(stack)
    while stack:
        i = stack.pop()
        alpha[i] = 0
        y, x = divmod(i, w)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w:
                j = ny * w + nx
                if j not in seen and all(abs(px[j][c] - bg[c]) <= TOL for c in range(3)):
                    seen.add(j)
                    stack.append(j)
    # 只留最大连通域（8 邻接）
    visited = set()
    comps = []
    for i in range(w * h):
        if alpha[i] == 0 or i in visited:
            continue
        comp = set()
        st = [i]
        while st:
            k = st.pop()
            if k in comp:
                continue
            comp.add(k)
            ky, kx = divmod(k, w)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = ky + dy, kx + dx
                    if 0 <= ny < h and 0 <= nx < w:
                        j = ny * w + nx
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
    return alpha, bg


def preview(px, label):
    print(u"  %s：" % label)
    for y in range(16):
        row = u""
        for x in range(16):
            a = px[y * 16 + x][3]
            row += u"#" if a == 255 else (u"." if a == 0 else u"+")
        print(u"     " + row)


def main():
    dump = json.loads(io.open(os.path.join(TOOLS, u"_zf86_jpg_pixels.json"),
                              encoding="utf-8").read())
    prov = {}
    prov_p = os.path.join(USERART, u"_来源凭据.json")
    if os.path.exists(prov_p):
        prov = json.loads(io.open(prov_p, encoding="utf-8").read())

    print(u"== ① 三张 JPEG 素材（含被存成 .png 的铜板）==")
    for item, src_name, dst_name, kind in JPEG_JOBS:
        src = os.path.join(TEX, src_name)
        if not os.path.exists(src):
            fails.append(u"找不到原图：%s" % src_name)
            continue
        raw = open(src, "rb").read()
        is_jpeg = raw[:2] == b"\xff\xd8"
        if kind == u"jpg_in_png_name" and not is_jpeg:
            print(u"  —— %s 现在已经是真 PNG 了（不用重写），只做去背景核对" % src_name)
        key = item
        d = dump.get(key)
        if d is None or d[u"w"] != 16 or d[u"h"] != 16:
            fails.append(u"%s：像素转储不是 16×16" % item)
            continue
        px = [tuple(int(v) for v in s.split(u",")) for s in d[u"px"]]
        alpha, bg = strip_background(px, 16, 16)
        out = [(px[i][0], px[i][1], px[i][2], alpha[i]) for i in range(256)]
        opaque = sum(1 for p in out if p[3] == 255)
        print(u"  %s → %s：背景色 %s，去掉 %d，留下 %d" % (src_name, dst_name, bg, 256 - opaque, opaque))
        if not (40 <= opaque <= 230):
            fails.append(u"%s：留下 %d 个像素，不像一件物品" % (item, opaque))
        preview(out, dst_name)
        write_png16(os.path.join(TEX, dst_name), out)

        # 原图挪去留档
        ascii_name = src_name if src_name.isascii() else {
            u"氯化钠.jpg": u"sodium_chloride.jpg", u"电容.jpg": u"capacitor.jpg"}.get(src_name)
        if ascii_name is None:
            fails.append(u"没给 %s 定 ASCII 名" % src_name)
            ascii_name = item + u".jpg"
        dst = os.path.join(USERART, ascii_name)
        os.makedirs(USERART, exist_ok=True)
        before = hashlib.sha1(raw).hexdigest()
        io.open(dst, "wb").write(raw)
        after = hashlib.sha1(open(dst, "rb").read()).hexdigest()
        if before != after:
            fails.append(u"%s：留档后哈希不一致" % src_name)
        prov[ascii_name] = {"sha1": after, "bytes": len(raw),
                            "说明": u"用户放的素材（%s）⇒ 转档成 textures/item/%s（16×16 / 8 位 / RGBA）"
                                    % (src_name, dst_name)}
        if not src_name.isascii():
            os.remove(src)
            print(u"  [OK]   原图 %s 已挪到 build/用户素材/%s（资源目录不再留中文名）" % (src_name, ascii_name))

    print(u"\n== ② 碳酸锂.png（20×20 RGBA）→ 16×16 ==")
    src = os.path.join(TEX, u"碳酸锂.png")
    if not os.path.exists(src):
        fails.append(u"找不到 碳酸锂.png")
    else:
        w, h, ctype, px0 = _zf66_png.read_png(src)
        print(u"  读到 %d×%d（ctype %s，%d 个像素）" % (w, h, ctype, len(px0)))
        px = [p if len(p) == 4 else (p[0], p[1], p[2], 255) for p in px0]
        xs = [x for y in range(h) for x in range(w) if px[y * w + x][3] != 0]
        ys = [y for y in range(h) for x in range(w) if px[y * w + x][3] != 0]
        if not xs:
            fails.append(u"碳酸锂：整张全透明？")
        else:
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            bw, bh = x1 - x0 + 1, y1 - y0 + 1
            print(u"  非透明包围盒：x %d..%d / y %d..%d（%d×%d）" % (x0, x1, y0, y1, bw, bh))
            scale = max(bw, bh) > 16
            out = [(0, 0, 0, 0)] * 256
            if not scale:
                # 裁出来居中放（**不重采样**，像素画保持锐利）
                ox = (16 - bw) // 2
                oy = (16 - bh) // 2
                for y in range(bh):
                    for x in range(bw):
                        out[(y + oy) * 16 + (x + ox)] = px[(y + y0) * w + (x + x0)]
                print(u"  做法：裁 %d×%d 居中放进 16×16（零重采样）" % (bw, bh))
            else:
                # 最近的邻居缩放（像素画别用双线性）
                for y in range(16):
                    for x in range(16):
                        sx = x0 + (x * bw) // 16
                        sy = y0 + (y * bh) // 16
                        out[y * 16 + x] = px[sy * w + sx]
                print(u"  做法：最近邻缩放到 16×16（包围盒 %d×%d 超出画布）" % (bw, bh))
            opaque = sum(1 for p in out if p[3] == 255)
            print(u"  写出后不透明像素 %d" % opaque)
            preview(out, u"lithium_carbonate.png")
            write_png16(os.path.join(TEX, u"lithium_carbonate.png"), out)
        raw = open(src, "rb").read()
        dst = os.path.join(USERART, u"lithium_carbonate.png")
        io.open(dst, "wb").write(raw)
        prov[u"lithium_carbonate.png"] = {
            "sha1": hashlib.sha1(raw).hexdigest(), "bytes": len(raw),
            "说明": u"用户放的 20×20 素材 ⇒ 转档成 textures/item/lithium_carbonate.png（16×16 / 8 位 / RGBA）"}
        os.remove(src)
        print(u"  [OK]   原图已挪到 build/用户素材/lithium_carbonate.png")

    print(u"\n== ③ 三件物品的模型指向自己的贴图 ==")
    for item in [u"lithium_carbonate", u"sodium_chloride", u"capacitor"]:
        p = os.path.join(MODELS, item + u".json")
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(
            json.dumps({"parent": "minecraft:item/generated",
                        "textures": {"layer0": "potato_s_t:item/" + item}},
                       indent=2, ensure_ascii=False) + u"\n")
        print(u"  [OK]   %s.json → potato_s_t:item/%s" % (item, item))

    io.open(prov_p, "w", encoding="utf-8", newline=u"\n").write(
        json.dumps(prov, indent=2, ensure_ascii=False) + u"\n")
    left = [f for f in os.listdir(TEX) if any(ord(c) > 127 for c in f)]
    if left:
        fails.append(u"textures/item 下还有中文文件名：%s" % left)
    else:
        print(u"\n  [OK]   textures/item 下已无中文文件名")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
