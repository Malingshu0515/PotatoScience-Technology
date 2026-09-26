# -*- coding: utf-8 -*-
u"""_zf142_poleblur.py —— ZF142：给四张星图的**极带**加一点点横向模糊（极滤波）

用户原话（接在我上一轮"条纹只是被盖住、没治好"那段之后）：「可以尝试加一点点模糊」

**为什么是"横向"**：天空盒是等距圆柱投影，靠近极点时贴图的 u 方向（方位角）被压缩
（θ=5° 处一个纹素列只占屏幕 ~0.43 px），而 v 方向（径向）被放大（一行 = 0.35° ≈ 5 px）。
两头一夹，极带里那点横向结构就变成了放射状的"扇子"。所以要糊的是**沿着行**（u 方向、环绕），
而且**离极点越近糊得越狠** —— 极点那一行干脆变成常数（整圈收敛到一个点，本来就该是常数）。

**为什么不做成"重新量化整张图"**：那会把四张图**整张**改一遍（虽然肉眼几乎一样）。
本脚本守的是一条更硬的规矩：**极带以外一个字节都不许动** ——
调色板原样保留、带外每一行的**索引**原样保留，只把带内的行按同一个调色板重新取最近色。
这条性质可以直接验（`_zf142_verify.py` 的 C 组）。

跑法：
    python build\\zftools\\_zf142_poleblur.py --y0 96 --r0 96 --p 1.0 --tag t1   # 出预览
    python build\\zftools\\_zf142_poleblur.py --y0 96 --r0 96 --p 1.0 --write    # 写进资源树
"""
import argparse
import io
import os
import struct
import sys
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _zf140_img import write_rgb  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
SKY = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "textures", "skybox")
OUT = os.path.join(ROOT, "build", "zftools", "_zf142_out")
NAMES = ["sky_verdant", "sky_mystic", "sky_ember", "sky_tarantula"]


# ---------------------------------------------------------------- 调色板 PNG
def read_pal_png(path):
    u"""只认 8 位非隔行 colorType 3（本工程四张星图就是），返回 (w,h,idx,plte)"""
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not png"
    pos, idat = 8, bytearray()
    w = h = ctype = None
    plte = None
    while pos + 8 <= len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype, comp, filt, inter = struct.unpack(">IIBBBBB", body)
            assert depth == 8 and inter == 0 and ctype == 3, "只支持 8 位非隔行调色板 PNG"
        elif typ == b"IDAT":
            idat += body
        elif typ == b"PLTE":
            plte = body
        elif typ == b"IEND":
            break
        pos += 12 + ln
    raw = zlib.decompress(bytes(idat))
    assert len(raw) == h * (w + 1), u"IDAT 长度不对：%d" % len(raw)
    rows = np.frombuffer(raw, dtype=np.uint8).reshape(h, w + 1)
    assert (rows[:, 0] == 0).all(), u"只支持 filter=0（本工程自己写的都是 0）"
    return w, h, rows[:, 1:].copy(), np.frombuffer(plte, dtype=np.uint8).reshape(-1, 3).copy()


def write_pal_png(path, idx, plte):
    h, w = idx.shape

    def chunk(tag, body):
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))

    raw = np.zeros((h, w + 1), dtype=np.uint8)
    raw[:, 1:] = idx
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 3, 0, 0, 0))
    png += chunk(b"PLTE", plte.tobytes())
    png += chunk(b"IDAT", zlib.compress(raw.tobytes(), 9))
    png += chunk(b"IEND", b"")
    io.open(path, "wb").write(png)


# ---------------------------------------------------------------- 极滤波
def circ_box_blur(rgb, radius):
    u"""每行沿 u（环绕）做一次箱型模糊；radius 是逐行的浮点半径（H,）"""
    h, w = rgb.shape[:2]
    out = rgb.astype(np.float32).copy()
    xs = np.arange(w)
    for y in range(h):
        r = float(radius[y])
        if r < 0.5:
            continue
        k = int(round(r))
        # 环绕前缀和：把行接两遍，取窗口均值
        row = rgb[y].astype(np.float32)
        if 2 * k + 1 >= w:
            out[y] = row.mean(axis=0)          # 极点整圈 = 常数（本来就该是）
            continue
        ext = np.concatenate([row, row, row], axis=0)
        c = np.cumsum(np.concatenate([np.zeros((1, row.shape[1]), np.float32), ext]), axis=0)
        lo = xs + w - k
        hi = xs + w + k + 1
        out[y] = (c[hi] - c[lo]) / float(2 * k + 1)
    return np.clip(out, 0, 255)


def polar_radius(h, y0, r0, p):
    u"""逐行半径：极点是**两个** —— 取到最近极点的行距，第 0 行与第 h-1 行都等于 r0，
    到 y0 行衰减到 0；p 越大越"只糊最靠极点的那几行"。
    （⚠ 第一版只按 y 算，南极那一半根本没糊到 —— 镜像半径是必须的。）"""
    d = np.minimum(np.arange(h), h - 1 - np.arange(h)).astype(np.float32)
    t = np.clip(1.0 - d / float(y0), 0.0, 1.0)
    return r0 * (t ** p)


def filter_sky(idx, plte, y0, r0, p):
    u"""返回新的索引图：带内按极滤波后的颜色取最近调色板色，**带外原样**"""
    h, w = idx.shape
    rgb = plte[idx].astype(np.float32)
    rad = polar_radius(h, y0, r0, p)
    band = rad >= 0.5
    blurred = circ_box_blur(rgb, rad)
    # rad 已经是**对称**的（两个极点都算到了）⇒ 带内每一行按最近调色板色重取索引
    new = idx.copy()
    for y in np.nonzero(band)[0]:
        col = blurred[y]
        d = ((col[:, None, :] - plte[None, :, :].astype(np.float32)) ** 2).sum(axis=2)
        new[y] = np.argmin(d, axis=1).astype(np.uint8)
    return new, band, rad


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--y0", type=int, default=96, help=u"极带高度（行）：0..y0 与 h-y0..h")
    ap.add_argument("--r0", type=float, default=96.0, help=u"极点那一行的模糊半径（像素）")
    ap.add_argument("--p", type=float, default=1.0, help=u"衰减指数")
    ap.add_argument("--tag", default="")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--strip", action="store_true", help=u"另出一张极带放大预览")
    a = ap.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)

    print(u"参数：y0=%d 行（%.1f°）  r0=%.0f px  p=%.2f" % (a.y0, a.y0 * 180.0 / 512, a.r0, a.p))
    for name in NAMES:
        p = os.path.join(SKY, name + ".png")
        w, h, idx, plte = read_pal_png(p)
        new, band, rad = filter_sky(idx, plte, a.y0, a.r0, a.p)
        changed = int((new != idx).sum())
        rows_changed = int((new != idx).any(axis=1).sum())
        # 带外必须逐字节不动
        outside = ~band
        assert (new[outside] == idx[outside]).all(), u"%s：带外被动到了！" % name
        print(u"  %-14s %dx%d 改 %d 行 / %d 像素（%.1f%%）；带外 %d 行逐字节未动"
              % (name, w, h, rows_changed, changed, 100.0 * changed / (w * h),
                 int(outside.sum())))

        if a.strip:
            rgb0 = plte[idx][:a.y0]
            rgb1 = plte[new][:a.y0]
            k = max(1, 512 // 512)
            tile = np.concatenate([rgb0[::k], np.full((6, w, 3), 255, np.uint8), rgb1[::k]], axis=0)
            write_rgb(os.path.join(OUT, "strip_%s%s.png" % (name, a.tag)), tile.astype(np.uint8))
        if a.write:
            write_pal_png(p, new, plte)
            print(u"      >>> 已写入 %s" % p)
    if a.strip:
        print(u"  极带放大预览 -> %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
