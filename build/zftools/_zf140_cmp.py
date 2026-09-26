# -*- coding: utf-8 -*-
u"""_zf140_cmp.py —— 把几个候选**渲染成一张对比图**（省得一张张翻着看，档案 §6.8）

用法： python build\\zftools\\_zf140_cmp.py [--theta 18,22,26,30] [--scene 0|1]
出来： _zf140_out\\cmp_theta.png / cmp_scene.png
"""
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

OUT = os.path.join(sim.ROOT, "build", "zftools", "_zf140_out")
HOLE = os.path.join(OUT, "black_hole.png")


def main(argv):
    thetas = [18.0, 22.0, 26.0, 30.0]
    if "--theta" in argv:
        thetas = [float(v) for v in argv[argv.index("--theta") + 1].split(",")]
    scene = int(argv[argv.index("--scene") + 1]) if "--scene" in argv else 0
    sky = sim.load_sky("sky_mystic")
    hole = sim.load_hole(HOLE)
    tiles = []
    for t in thetas:
        if scene == 0:      # 北极在地平线（angle=90），正对着看
            img = sim.render(sky, hole, t, w=960, h=540, yaw=0, pitch=0,
                             day_angle=90.0, pole=1, ground=True)
        elif scene == 1:    # 北极在天顶（angle=0），抬头 55 度看
            img = sim.render(sky, hole, t, w=960, h=540, yaw=0, pitch=55,
                             day_angle=0.0, pole=2, ground=False)
        else:               # 天顶偏一点（angle=25），正常平视
            img = sim.render(sky, hole, t, w=960, h=540, yaw=0, pitch=15,
                             day_angle=25.0, pole=2, ground=True)
        if scene == 0:
            tiles.append(img[110:430, 240:720])
        elif scene == 1:
            tiles.append(img[70:390, 240:720])
        else:
            tiles.append(img[60:380, 240:720])
        print(u"  θ=%.0f°" % t)
    out = np.concatenate(tiles, axis=0)
    p = os.path.join(OUT, "cmp_theta_s%d.png" % scene)
    write_rgb(p, out)
    print(u"  -> %s  (%dx%d)" % (p, out.shape[1], out.shape[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
