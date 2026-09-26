# -*- coding: utf-8 -*-
u"""_zf142_probe.py —— ZF142 的**判因实验**：极区那些放射条纹，到底是"采样混叠"还是"真实结构"？

不先搞清楚这个，模糊就是瞎糊。做法：拿同一张星图，只在**存盘之后、贴之前**换不同的模糊律，
正对极点出图排一行比：

  none            原样
  u8              **沿 u 均匀糊 8 个纹素**（跟极点无关）
  u32             沿 u 均匀糊 32 个纹素（糊到亲妈都不认识）
  inv             物理律：半径 = 0.22 / tanθ（≈ 屏幕像素在 u 方向的**缩小倍数的一半**）
  inv3            上面那个 ×3（偏方，看能不能把条纹压死）

判读方法：**如果 u32 之后条纹消失** ⇒ 病根是混叠（u 方向被缩小采样），
          那就该用 `inv` 这一律、而且是**一点点**就够；
          **如果 u32 之后条纹还在** ⇒ 那是星图本身的纤维结构被径向拉长，模糊治不了根
          （只能压对比度，或者干脆接受它 —— 黑洞盖片的活）。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _zf140_sim as sim  # noqa: E402
import _zf142_look as LOOK  # noqa: E402
import _zf142_poleblur as PB  # noqa: E402
from _zf140_img import write_rgb  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OUT = os.path.join(sim.ROOT, "build", "zftools", "_zf142_out")


def laws(h):
    d = np.minimum(np.arange(h), h - 1 - np.arange(h)).astype(np.float64)
    theta = np.pi * d / float(h)                      # 0（极点）到 π/2（赤道）
    inv = np.where(theta < 1e-6, 1e9, 0.22 / np.tan(np.maximum(theta, 1e-6)))
    return {
        "none": np.zeros(h),
        "u8": np.full(h, 8.0),
        "u32": np.full(h, 32.0),
        "inv": np.minimum(inv, h / 2.0),
        "inv3": np.minimum(inv * 3.0, h / 2.0),
    }


def render_params(rgb, idx, plte, par):
    u"""按 (y0,r0,p) 在内存里滤一遍（与正式滤镜同一条路），返回 RGB"""
    h, w = idx.shape
    rad = PB.polar_radius(h, par[0], par[1], par[2])
    if not (rad >= 0.5).any():
        return rgb
    b = PB.circ_box_blur(rgb, rad)
    new = idx.copy()
    for y in np.nonzero(rad >= 0.5)[0]:
        dd = ((b[y][:, None, :] - plte[None, :, :].astype(np.float32)) ** 2).sum(axis=2)
        new[y] = np.argmin(dd, axis=1).astype(np.uint8)
    return plte[new].astype(np.float32)


def main(argv):
    argv = list(argv)
    name = argv[0] if argv and not argv[0][0].isdigit() else "sky_mystic"
    specs = [a for a in argv if a[0].isdigit()] or ["96,16,1.0", "128,32,1.0", "160,64,0.7"]
    w, h, idx, plte = PB.read_pal_png(os.path.join(sim.SKY_DIR, name + ".png"))
    rgb = plte[idx].astype(np.float32)
    r_in, r_out = np.tan(np.radians(3.0)), np.tan(np.radians(20.0))
    tiles, head = [], []

    def score(img):
        view, r = LOOK.pole_view(img, 300)
        hf, _ = LOOK.ring_hf(view, 300 / 2.0 / np.tan(np.radians(35.0)) * r_in,
                             300 / 2.0 / np.tan(np.radians(35.0)) * r_out)
        return view, hf

    view0, hf0 = score(rgb)
    print(u"  %-12s 细条纹 %6.2f   改动 0.000/255" % (u"原样", hf0))
    tiles.append(view0[:, :, :3].astype(np.uint8))
    head.append(u"原样 %.1f" % hf0)
    for spec in specs:
        y0, r0, p = (float(v) for v in spec.split(","))
        img = render_params(rgb, idx, plte, (int(y0), r0, p))
        view, hf = score(img)
        op = float(np.abs(img - rgb).mean())
        print(u"  %-12s 细条纹 %6.2f（%+.0f%%）  改动 %5.3f/255"
              % (spec, hf, 100.0 * (hf / hf0 - 1.0), op))
        tiles.append(view[:, :, :3].astype(np.uint8))
        head.append(u"%s  %.1f" % (spec, hf))
    strip = np.concatenate(tiles, axis=0)
    out = os.path.join(OUT, "cmp_%s.png" % name)
    write_rgb(out, strip)
    print(u"  自上而下：%s" % u" | ".join(head))
    print(u"  -> %s（%dx%d）" % (out, strip.shape[1], strip.shape[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
