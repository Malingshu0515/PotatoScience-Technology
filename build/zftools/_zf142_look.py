# -*- coding: utf-8 -*-
u"""_zf142_look.py —— ZF142：**出图 + 量数**（改之前 / 改之后各跑一次，比出差别）

量的东西只有一条，而且量在**屏幕上**（不是量贴图）：
把摄像机正对极点摆好，取极点到 20° 之间的环带，**逐环算一圈上的亮度标准差**再平均 ——
"放射状的扇子"在数学上就是**环向方差大**；糊掉之后它必然掉下来。
（判据：环向 std 至少降 40%，且**赤道带一个数都不许动**。）

跑法：
    python build\\zftools\\_zf142_look.py --tag before
    python build\\zftools\\_zf142_look.py --tag after
"""
import argparse
import io
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _zf140_sim as sim  # noqa: E402
from _zf140_img import write_rgb  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OUT = os.path.join(sim.ROOT, "build", "zftools", "_zf142_out")
NAMES = ["sky_verdant", "sky_mystic", "sky_ember", "sky_tarantula"]


def pole_view(sky, size=520, fov=70.0):
    u"""正对极点的视图（gnomonic）。不画黑洞 —— 要量的是星图自己。"""
    f = size / 2.0 / math.tan(math.radians(fov) / 2.0)
    ys, xs = np.mgrid[0:size, 0:size]
    gx = (xs + 0.5 - size / 2.0) / f
    gy = (size / 2.0 - (ys + 0.5)) / f
    # 世界方向：y 朝极点，屏幕 x/z 就是本地的 x/z（与 SkyboxRenderer 的姿态一致）
    local = np.stack([gx, np.ones_like(gx), -gy], axis=-1)
    local /= np.linalg.norm(local, axis=2, keepdims=True)
    v = 0.5 - np.arcsin(np.clip(local[..., 1], -1, 1)) / math.pi
    u = np.mod(np.arctan2(local[..., 2], local[..., 0]) / (2 * math.pi), 1.0)
    img = sim.sample_bilinear(sky.astype(np.float32), u, v)
    return img, np.sqrt(gx ** 2 + gy ** 2)


def ring_std(img, r, r_in, r_out):
    u"""极点到 20° 之间：逐环取一圈像素算 std，再平均（扇子越大这个数越大）"""
    luma = img.mean(axis=2)
    vals = []
    for rr in np.arange(r_in, r_out, r_out / 40.0):
        m = (r >= rr) & (r < rr + r_out / 40.0)
        if m.sum() < 32:
            continue
        vals.append(float(luma[m].std()))
    return float(np.mean(vals)), len(vals)


def ring_hf(img, r_in, r_out, rings=12, samples=720, smooth_deg=20.0):
    u"""**细条纹**强度（这才是"刺眼的放射条纹"，环向总 std 会被大块明暗带带偏）

    做法：把每一圈按角度重采样成 1D，减掉"绕圈 20° 滑动平均"之后再取 std ——
    大块的明暗过渡（真实内容）被减掉了，剩下的就是一根根细条纹。
    """
    luma = img.mean(axis=2)
    h, w = luma.shape
    cx = cy = (w - 1) / 2.0
    phi = np.linspace(0, 2 * np.pi, samples, endpoint=False)
    k = max(1, int(round(samples * smooth_deg / 360.0)))
    vals = []
    for rr in np.linspace(r_in, r_out, rings):
        xs = cx + rr * np.cos(phi)
        ys = cy + rr * np.sin(phi)
        x0 = np.clip(np.floor(xs).astype(int), 0, w - 2)
        y0 = np.clip(np.floor(ys).astype(int), 0, h - 2)
        fx = (xs - x0)[:, None]
        fy = (ys - y0)[:, None]
        a = luma[y0, x0] * (1 - fx[:, 0]) + luma[y0, x0 + 1] * fx[:, 0]
        b = luma[y0 + 1, x0] * (1 - fx[:, 0]) + luma[y0 + 1, x0 + 1] * fx[:, 0]
        sig = a * (1 - fy[:, 0]) + b * fy[:, 0]
        ext = np.concatenate([sig, sig, sig])
        ker = np.ones(2 * k + 1) / (2 * k + 1)
        base = np.convolve(ext, ker, mode="same")[samples:2 * samples]
        vals.append(float((sig - base).std()))
    return float(np.mean(vals)), len(vals)


def equator_std(img):
    u"""赤道那一带的横向细节（对照：改极带**不该**动到它）"""
    return float(img[:, :, :].mean(axis=2).std())


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--size", type=int, default=520)
    ap.add_argument("--in-deg", type=float, default=3.0)
    ap.add_argument("--out-deg", type=float, default=20.0)
    ap.add_argument("--params", default=None,
                    help=u"y0,r0,p —— 给了就在**内存里**滤一遍再量（不写盘，方便扫参数）")
    a = ap.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)
    par = None
    if a.params:
        y0, r0, p = a.params.split(",")
        par = (int(y0), float(r0), float(p))
        print(u"内存滤一遍：y0=%d r0=%.0f p=%.2f" % par)

    f = a.size / 2.0 / math.tan(math.radians(70.0) / 2.0)
    # ⚠ `pole_view` 返回的半径是 **gnomonic 坐标**（= tan θ），不是像素 ——
    #   第一版拿像素去比，一个环都选不中，量出来是 nan（判据自己先哑了）。
    r_in = math.tan(math.radians(a.in_deg))
    r_out = math.tan(math.radians(a.out_deg))
    print(u"环带 %g°~%g°（gnomonic %.4f~%.4f，屏幕上 %.0f~%.0f px）"
          % (a.in_deg, a.out_deg, r_in, r_out, f * r_in, f * r_out))

    tiles, rows = [], []
    for name in NAMES:
        if par is None:
            sky = sim.load_sky(name)
        else:
            import _zf142_poleblur as PB
            src = os.path.join(sim.SKY_DIR, name + ".png")
            w, h, idx, plte = PB.read_pal_png(src)
            new, band, rad = PB.filter_sky(idx, plte, par[0], par[1], par[2])
            sky = plte[new]
        img, r = pole_view(sky, a.size)
        s, n = ring_std(img, r, r_in, r_out)
        hf, hn = ring_hf(img, f * r_in, f * r_out)   # ⚠ 这里要的是**像素**半径（gnomonic 只给 ring_std 用）
        eq = equator_std(sky)
        rows.append((name, s, n, eq, hf))
        print(u"  %-14s 环向总 std %6.2f   细条纹 %6.2f（%d 环）   星图整体 std %6.2f"
              % (name, s, hf, hn, eq))
        tiles.append(img[:, :, :3].astype(np.uint8))
    strip = np.concatenate(tiles, axis=1)
    p = os.path.join(OUT, "pole4_%s.png" % a.tag)
    write_rgb(p, strip)
    print(u"  四张星图正对极点的样子 -> %s（%dx%d）" % (p, strip.shape[1], strip.shape[0]))
    with io.open(os.path.join(OUT, "metric_%s.txt" % a.tag), "w", encoding="utf-8",
                 newline="\n") as fh:
        for name, s, n, eq, hf in rows:
            fh.write(u"%s\t%.6f\t%d\t%.6f\t%.6f\n" % (name, s, n, eq, hf))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
