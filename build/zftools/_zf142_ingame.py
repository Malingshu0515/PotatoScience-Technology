# -*- coding: utf-8 -*-
u"""_zf142_ingame.py —— ZF142：**带上黑洞盖片**看最终画面（这才是玩家看到的）

只比贴图没用 —— 盖片会挡掉极区最里面那一块，要判断"糊到什么程度刚好"，
得把盖片一起画上再看。三行：原样 / 候选A / 候选B。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _zf140_sim as sim  # noqa: E402
import _zf142_poleblur as PB  # noqa: E402
from _zf140_img import read_png_np, write_rgb  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OUT = os.path.join(sim.ROOT, "build", "zftools", "_zf142_out")


def filtered(name, par):
    if par is None:
        return sim.load_sky(name)
    src = os.path.join(sim.SKY_DIR, name + ".png")
    w, h, idx, plte = PB.read_pal_png(src)
    hh, ww = idx.shape
    rad = PB.polar_radius(hh, par[0], par[1], par[2])
    rgb = plte[idx].astype(np.float32)
    b = PB.circ_box_blur(rgb, rad)
    new = idx.copy()
    for y in np.nonzero(rad >= 0.5)[0]:
        dd = ((b[y][:, None, :] - plte[None, :, :].astype(np.float32)) ** 2).sum(axis=2)
        new[y] = np.argmin(dd, axis=1).astype(np.uint8)
    return plte[new].astype(np.uint8)


def main(argv):
    name = argv[0] if argv else "sky_mystic"
    specs = [a for a in argv[1:] if a[0].isdigit()] or ["96,16,1.0", "128,32,1.0"]
    hole = read_png_np(os.path.join(sim.SKY_DIR, "black_hole.png"))
    tiles = []
    for spec in [None] + specs:
        par = None if spec is None else tuple(
            (int(v) if i != 1 else float(v)) for i, v in enumerate(spec.split(",")))
        sky = filtered(name, par)
        img = sim.render(sky, hole, 28.0, w=980, h=560, yaw=0, pitch=0,
                         day_angle=90.0, pole=2, ground=True)
        tiles.append(img[40:400, 150:830])
        print(u"  %-12s" % (u"原样" if par is None else spec))
    out = np.concatenate(tiles, axis=0)
    p = os.path.join(OUT, "ingame_%s.png" % name)
    write_rgb(p, out)
    print(u"  自上而下：原样 | %s" % u" | ".join(specs))
    print(u"  -> %s（%dx%d）" % (p, out.shape[1], out.shape[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
