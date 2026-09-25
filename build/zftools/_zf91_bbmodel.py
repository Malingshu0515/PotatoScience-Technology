# -*- coding: utf-8 -*-
r"""_zf91_bbmodel.py —— 读用户的 Blockbench 工程（`.bbmodel`），把"这份工程到底长什么样"摆清楚

⚠ 第一版踩的坑：这份工程是 **Free / mesh 模型**（`meta.model_format = "free"`，
元素是 `type: "mesh"` + `vertices`/`faces`），**不是** Java 方块那种 `cube`+`from/to`。
所以要从 mesh 的顶点表与面表里读几何，UV 是**逐顶点**给的（像素坐标）。

回答：
  ① 元信息：格式 / 分辨率；
  ② 内嵌贴图是什么（sha256、尺寸），与"成品在用的那张 / 用户图一 / 用户图二"是不是同一张（**逐像素**比）；
  ③ 面总数、UV 不同取值数（≤4 就是"整张贴图铺每个面"）、UV 矩形集合；
  ④ 几何包围盒（格）；
  ⑤ **与用户图二那张 UV 展开图对账**：面数、以及每个面的 UV 矩形能不能在图二里找到同一块。
只读。
"""
import base64
import hashlib
import io
import json
import os
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _zf66_png  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
BB = r"C:\Users\Administrator\.dsh\attachments\v1\files\15\15028bf3d0dc6e7234ea03ec6a697b72858bc12ff7383c401b7c394fd2aab366\电力高炉.bbmodel"
LIVE = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png"
IMG1 = r"C:\Users\Administrator\.dsh\attachments\v1\objects\24\24a0dfc0dcfe98a1c736773ec5d1cd1017107712da8c78951e873f61ff5214ee"
IMG2 = r"C:\Users\Administrator\.dsh\attachments\v1\objects\0d\0da6ba4523aa4e72b040c78bd0bc7581323722f9ae8b124c5c9b7d9734e25210"
OUT_TEX = os.path.join(HERE, "_zf91_bbmodel_tex.png")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def px_of(path):
    w, h, ct, p = _zf66_png.read_png(path)
    return [(q if len(q) == 4 else (q[0], q[1], q[2], 255)) for q in p]


def comps(w, h, mask):
    seen = bytearray(w * h)
    out = []
    for y0 in range(h):
        for x0 in range(w):
            if seen[y0 * w + x0] or not mask[y0 * w + x0]:
                continue
            q = deque([(x0, y0)])
            seen[y0 * w + x0] = 1
            minx, miny, maxx, maxy = x0, y0, x0, y0
            while q:
                x, y = q.popleft()
                minx = min(minx, x); miny = min(miny, y)
                maxx = max(maxx, x); maxy = max(maxy, y)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] \
                            and mask[ny * w + nx]:
                        seen[ny * w + nx] = 1
                        q.append((nx, ny))
            out.append((minx, miny, maxx, maxy))
    return out


def main():
    raw = io.open(BB, "rb").read()
    d = json.loads(raw.decode("utf-8"))
    print(u"工程文件 %d 字节  sha256 %s…" % (len(raw), sha(raw)[:16]))
    print(u"  name=%s  format=%s  model_format=%s  resolution=%s"
          % (d.get("name"), d.get("meta", {}).get("format_version"),
             d.get("meta", {}).get("model_format"), d.get("resolution")))
    W = d["resolution"]["width"]; H = d["resolution"]["height"]

    print(u"\n== ② 内嵌贴图 ==")
    b = None
    for i, t in enumerate(d.get("textures", [])):
        src = t.get("source", "")
        print(u"  [%d] name=%s" % (i, t.get("name")))
        if isinstance(src, str) and src.startswith("data:image"):
            b = base64.b64decode(src.split(",", 1)[1])
            io.open(OUT_TEX, "wb").write(b)
            print(u"      %d 字节  sha256 %s…" % (len(b), sha(b)[:16]))
            for label, p in ((u"成品在用的那张", LIVE), (u"用户图一", IMG1), (u"用户图二（展开图）", IMG2)):
                if not os.path.exists(p):
                    continue
                same_b = open(p, "rb").read() == b
                same_px = same_b or (px_of(p) == px_of(OUT_TEX))
                print(u"      与 %s：逐字节 %s；逐像素 %s"
                      % (label, u"同" if same_b else u"不同", u"同" if same_px else u"不同"))

    print(u"\n== ③ 元素与面 ==")
    els = d.get("elements", [])
    kinds = {}
    faces_all = []
    uvs = set()
    rects = set()
    xs, ys, zs = [], [], []
    for e in els:
        kinds[e.get("type")] = kinds.get(e.get("type"), 0) + 1
        if e.get("type") != "mesh":
            continue
        verts = e.get("vertices", {})
        for k, v in verts.items():
            xs.append(v[0]); ys.append(v[1]); zs.append(v[2])
        for fid, fc in e.get("faces", {}).items():
            vids = fc.get("vertices", [])
            uvd = fc.get("uv", {})
            faces_all.append((e.get("name"), fid, vids, uvd))
            us = [uvd[k][0] for k in vids if k in uvd]
            vs = [uvd[k][1] for k in vids if k in uvd]
            for k in vids:
                if k in uvd:
                    uvs.add((uvd[k][0], uvd[k][1]))
            if us:
                rects.add((min(us), min(vs), max(us), max(vs)))
    print(u"  元素类型：%s（共 %d 个）" % (kinds, len(els)))
    print(u"  面总数 = %d" % len(faces_all))
    print(u"  UV 的不同取值 = %d 个（≤4 就是「整张贴图铺每个面」）" % len(uvs))
    print(u"  不同的 UV 矩形 = %d 个" % len(rects))
    print(u"  包围盒（工程单位）：X %.4f..%.4f  Y %.4f..%.4f  Z %.4f..%.4f"
          % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    print(u"  跨度（格，除以 16）：X %.4f  Y %.4f  Z %.4f"
          % ((max(xs) - min(xs)) / 16.0, (max(ys) - min(ys)) / 16.0, (max(zs) - min(zs)) / 16.0))

    print(u"\n== ⑤ 与用户图二（UV 展开图）对账 ==")
    w2, h2, _, p2 = _zf66_png.read_png(IMG2)
    mask2 = [p[3] != 0 and not (p[0] > 245 and p[1] > 245 and p[2] > 245) for p in p2]
    lay = comps(w2, h2, mask2)
    print(u"  图二里的矩形 %d 个；工程里的 UV 矩形 %d 个" % (len(lay), len(rects)))
    lay_set = set(lay)
    eng_set = set(rects)
    print(u"  完全相同的 %d 个" % len(lay_set & eng_set))
    only_e = sorted(eng_set - lay_set)[:8]
    only_l = sorted(lay_set - eng_set)[:8]
    print(u"  只在工程里的（前 8）：%s" % (only_e,))
    print(u"  只在图二里的（前 8）：%s" % (only_l,))

    print(u"\n== ④ 每个元素的顶点/面数 ==")
    for e in els:
        if e.get("type") != "mesh":
            continue
        print(u"  %-18s v=%3d  f=%3d"
              % (e.get("name") or u"", len(e.get("vertices", {})), len(e.get("faces", {}))))
    print(u"\n内嵌贴图写出到 %s" % os.path.basename(OUT_TEX))


main()
