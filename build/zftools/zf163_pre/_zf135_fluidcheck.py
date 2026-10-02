# -*- coding: utf-8 -*-
"""_zf135_fluidcheck.py —— 全部流体动画贴图的**常驻复核**（只读）

## 为什么要有它（而不只是看比值）

`_zf132_seam.py` 只报"环绕跳变 ÷ 帧内平均跳变"这个**比值**。对**接近平色**的图
（LPG 的列间基准只有 0.41/255）比值会被放大成 8.27，看着像出了大问题，
而它的**绝对差只有 3.38/255** —— 肉眼根本看不出。
（这正是我自己在档案 §4.114 立的那条："比值要有绝对量兜底"，本轮又差点栽在上面。）

所以这张表把**四条**一起摆：两个方向的比值 + 两个方向的绝对差。

## 判据

  · 比值 ≤ 2.0        —— 接缝不比图内任何一处更突兀；
  · 绝对差 ≤ 12/255   —— 即使比值高，只要绝对落差小于 ~5% 也看不出。

**一个方向满足其一即可**。两个方向都要过。

## 还要验的（不只是接缝）

  1. 尺寸必须是 16×16×N（竖排帧序列），且有同名 `.png.mcmeta`；
  2. `frametime` 必须能真解析出来；
  3. **首末帧必须不同**（防"做了个不动的动画"这种最常见的假成功）；
  4. `_still` 与 `_flow` 两个文件都要在（引擎真的用 flow：
     `IClientFluidTypeExtensions#getFlowingTexture`）。
"""
import io
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

T = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"
RATIO_MAX = 2.0
ABS_MAX = 12.0
FRAMETIME_EXPECT = 3

fails = []


def wrap_stats(a, fh, w, nf):
    lr_r, lr_a, tb_r, tb_a = [], [], [], []
    for f in range(nf):
        fr = a[f * fh:(f + 1) * fh].astype(int)
        wl = float(np.abs(fr[:, -1] - fr[:, 0]).mean())
        ca = float(np.abs(np.diff(fr, axis=1)).mean())
        wt = float(np.abs(fr[-1] - fr[0]).mean())
        ra = float(np.abs(np.diff(fr, axis=0)).mean())
        lr_r.append(wl / max(1e-6, ca)); lr_a.append(wl)
        tb_r.append(wt / max(1e-6, ra)); tb_a.append(wt)
    return (float(np.mean(lr_r)), float(np.mean(lr_a)),
            float(np.mean(tb_r)), float(np.mean(tb_a)))


def main():
    all_png = sorted(f[:-4] for f in os.listdir(T) if f.endswith(".png"))
    anim = [n for n in all_png if os.path.exists(os.path.join(T, n + ".png.mcmeta"))]
    fluids = sorted(set(n.rsplit("_", 1)[0] for n in all_png
                        if n.endswith("_still") or n.endswith("_flow")))

    print(u"方块贴图目录：%d 张 PNG，其中带 .mcmeta 的 %d 张" % (len(all_png), len(anim)))
    print(u"流体 %d 种\n" % len(fluids))

    print(u"== ① 每种流体的 still / flow 都要在、都要动画 ==")
    for fl in fluids:
        for sfx in ("_still", "_flow"):
            n = fl + sfx
            p = os.path.join(T, n + ".png")
            if not os.path.exists(p):
                fails.append(u"缺 %s.png" % n)
                print(u"  !! 缺 %s.png" % n)
                continue
            if not os.path.exists(p + ".mcmeta"):
                fails.append(u"%s 没有 .mcmeta（不是动画）" % n)
                print(u"  !! %s 没有 .mcmeta" % n)
    if not fails:
        print(u"  [OK] %d 种 × 2 张 = %d 张，全部在位且都有 .mcmeta"
              % (len(fluids), len(fluids) * 2))

    print(u"\n== ② 尺寸 / frametime / 首末帧 ==")
    print(u"%-26s %9s %6s %8s %9s" % (u"贴图", u"尺寸", u"帧数", u"frametime", u"首末帧差"))
    for n in anim:
        p = os.path.join(T, n + ".png")
        w, h, rgba = read_png(p)
        fh = 16
        if w != 16 or h % fh:
            fails.append(u"%s 尺寸 %dx%d 不是 16 的竖排" % (n, w, h))
        nf = h // fh
        meta = json.loads(io.open(p + ".mcmeta", encoding="utf-8").read())
        ft = meta.get("animation", {}).get("frametime")
        if ft != FRAMETIME_EXPECT:
            fails.append(u"%s frametime = %s（期望 %d）" % (n, ft, FRAMETIME_EXPECT))
        f0 = bytes(rgba[0:16 * 16 * 4])
        fN = bytes(rgba[((nf - 1) * 16 * 16) * 4:(nf * 16 * 16) * 4])
        d = sum(1 for i in range(0, len(f0), 4) if f0[i:i + 4] != fN[i:i + 4])
        if d == 0:
            fails.append(u"%s 首末帧一模一样（没动）" % n)
        print(u"%-26s %9s %6d %8s %9d"
              % (n, u"%dx%d" % (w, h), nf, ft, d))

    print(u"\n== ③ 环绕接缝（比值 + 绝对差，两条都看）==")
    print(u"%-26s %7s %7s %7s %7s  %s" %
          (u"贴图", u"左右比", u"左右abs", u"上下比", u"上下abs", u"判定"))
    worst = 0.0
    for n in anim:
        w, h, rgba = read_png(os.path.join(T, n + ".png"))
        a = np.array(rgba, dtype=np.int16).reshape(h, w, 4)[:, :, :3]
        lr_r, lr_a, tb_r, tb_a = wrap_stats(a, 16, w, h // 16)
        ok = ((lr_r <= RATIO_MAX or lr_a <= ABS_MAX)
              and (tb_r <= RATIO_MAX or tb_a <= ABS_MAX))
        if not ok:
            fails.append(u"%s 环绕接缝不合格（左右 %.2f/%.2f，上下 %.2f/%.2f）"
                         % (n, lr_r, lr_a, tb_r, tb_a))
        worst = max(worst, lr_r, tb_r)
        print(u"%-26s %7.2f %7.2f %7.2f %7.2f  %s"
              % (n, lr_r, lr_a, tb_r, tb_a, u"OK" if ok else u"!! 不合格"))

    print(u"\n最大比值 %.2f（阈值 %.1f；比值超了就看绝对差 ≤ %.0f/255）"
          % (worst, RATIO_MAX, ABS_MAX))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
