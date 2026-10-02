# -*- coding: utf-8 -*-
"""_zf135_fluidcheck.py —— 全部流体动画贴图的**常驻复核**（只读）

## 为什么要有它（而不只是看比值）

`_zf132_seam.py` 只报"环绕跳变 ÷ 帧内平均跳变"这个**比值**。对**接近平色**的图
（LPG 的列间基准只有 0.41/255）比值会被放大成 8.27，看着像出了大问题，
而它的**绝对差只有 3.38/255** —— 肉眼根本看不出。
（这正是我自己在档案 §4.114 立的那条："比值要有绝对量兜底"。）

所以这张表把**四条**一起摆：两个方向的比值 + 两个方向的绝对差。

## 判据（接缝）

  · 比值 <= 2.0        —— 接缝不比图内任何一处更突兀；
  · 绝对差 <= 12/255   —— 即使比值高，只要绝对落差小于 ~5% 也看不出。

**一个方向满足其一即可**。两个方向都要过。

## 还要验的（不只是接缝）

  1. 尺寸必须是 16x16xN（竖排帧序列），且有同名 `.png.mcmeta`；
  2. `frametime` 必须能真解析出来 —— **still 必须写 2**（原版 `water_still` 就是 2）、
     **flow 必须缺省**（原版 `water_flow` 的 mcmeta 就是空的 `{}`，缺省 = 1 tick 一帧）；
  3. `_still` 与 `_flow` 两个文件都要在（引擎真的用 flow：
     `IClientFluidTypeExtensions#getFlowingTexture`）。

## 0.13 ZF163 换掉的两条判据（是**换严**，不是放宽）

背景：用户说"流体动画有点怪"。把原版水从真 jar 里量了一遍，才发现**根子在做法的选择上**：

  · 原版 `water_still` 是 **32 帧 / frametime 2**，而且**它不滚动** ——
    相邻帧的"最佳竖向位移"恒为 0 行，它是**原地**的亮暗（逐帧变化密度约 **11%**）；
  · 我们原来（ZF132/ZF135）是**整张下滚 1 行/帧、16 帧、frametime 3** ——
    逐帧变化密度 **49%~98%**，是原版水的 5~9 倍：横条纹像一面墙那样往下走，这就是"怪"。
  · 原版 `water_flow` 是 **32 帧、内容每帧上移 1 行**（32 宽上量到 31 行 = 上移 1 行）。

所以本轮改成：**still = 相干行波涟漪**（每一列整体升降 `round(2*sin(2pi(x/16 - t/32)))` 行、
零净漂移、32 帧闭环），**flow = 每帧上移 1 行**。

于是这两条**老判据被换成更强的**：

  · 老「**首末帧**必须不同」⇒ 新「**逐对相邻帧**都必须有变化」（只看首末帧会漏掉
    "中间有 30 帧不动"这种假动画）；
  · 新增「still **每一列**必须等于底图那一列按公式位移」—— 这一条同时排掉了
    "整体行军"（位移若与列无关就不是行波）与"做了个不动的动画"；
  · 新增「flow 第 t 帧必须**精确**等于底图第 (y+t) 行」—— 方向与步长都钉死。
"""
import io
import json
import math
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

T = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"
RATIO_MAX = 2.0
ABS_MAX = 12.0
FRAMETIME_STILL = 2      # 原版 water_still.png.mcmeta = {"animation": {"frametime": 2}}
FRAMES_STILL = 32        # 原版 water_still 就是 32 帧
FRAMES_FLOW = 16         # 底图 16 高 => 16 帧正好一个周期（原版靠 32 高的底图铺 32 帧）
RIPPLE_A = 2             # 行波振幅（行）

fails = []


def col_of(rgba, fr, x):
    return [bytes(rgba[((fr * 16) + y) * 64 + x * 4: ((fr * 16) + y) * 64 + x * 4 + 4]) for y in range(16)]


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

    print(u"== (1) 每种流体的 still / flow 都要在、都要动画 ==")
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
        print(u"  [OK] %d 种 x 2 张 = %d 张，全部在位且都有 .mcmeta"
              % (len(fluids), len(fluids) * 2))

    print(u"\n== (2) 尺寸 / 帧数 / frametime ==")
    print(u"%-26s %9s %6s %10s" % (u"贴图", u"尺寸", u"帧数", u"frametime"))
    for n in anim:
        p = os.path.join(T, n + ".png")
        w, h, rgba = read_png(p)
        if w != 16 or h % 16:
            fails.append(u"%s 尺寸 %dx%d 不是 16 的竖排" % (n, w, h))
        nf = h // 16
        meta = json.loads(io.open(p + ".mcmeta", encoding="utf-8").read())
        ft = meta.get("animation", {}).get("frametime")
        want_nf = FRAMES_STILL if n.endswith("_still") else FRAMES_FLOW
        want_ft = FRAMETIME_STILL if n.endswith("_still") else None
        if nf != want_nf:
            fails.append(u"%s 帧数 %d（期望 %d）" % (n, nf, want_nf))
        if ft != want_ft:
            fails.append(u"%s frametime = %s（期望 %s）" % (n, ft, want_ft))
        print(u"%-26s %9s %6d %10s" % (n, u"%dx%d" % (w, h), nf, ft))

    print(u"\n== (3) 逐对相邻帧都必须有变化（比只看首末帧严）==")
    quiet = []
    for n in anim:
        w, h, rgba = read_png(os.path.join(T, n + ".png"))
        nf = h // 16
        for t in range(1, nf):
            if bytes(rgba[(t - 1) * 1024:t * 1024]) == bytes(rgba[t * 1024:(t + 1) * 1024]):
                quiet.append(u"%s 第 %d 帧与上一帧一模一样" % (n, t))
    if quiet:
        fails.extend(quiet)
        for q in quiet[:6]:
            print(u"  !! " + q)
    else:
        print(u"  [OK] %d 张 x 每一对相邻帧都有变化" % len(anim))

    print(u"\n== (4) still：每一列必须 == 底图那一列按公式位移（『不再行军』的硬证据）==")
    bad = 0
    for fl in fluids:
        w, h, rgba = read_png(os.path.join(T, fl + "_still.png"))
        base = [col_of(rgba, 0, x) for x in range(16)]
        for t in range(h // 16):
            for x in range(16):
                dy = int(round(RIPPLE_A * math.sin(2 * math.pi * (x / 16.0 - t / float(FRAMES_STILL)))))
                if col_of(rgba, t, x) != [base[x][(y - dy) % 16] for y in range(16)]:
                    bad += 1
    if bad:
        fails.append(u"still 有 %d 列不符合行波公式" % bad)
    print(u"  %s 15 种 x %d 帧 x 16 列 全部符合 round(%d*sin(2pi(x/16 - t/%d)))"
          % (u"[OK]" if not bad else u"!!", FRAMES_STILL, RIPPLE_A, FRAMES_STILL))

    print(u"\n== (5) flow：第 t 帧必须精确等于底图第 (y+t) 行（上移 1 行/帧）==")
    bad2 = 0
    for fl in fluids:
        w, h, rgba = read_png(os.path.join(T, fl + "_flow.png"))
        rows = [[bytes(rgba[(fr * 16 + y) * 64:(fr * 16 + y) * 64 + 64]) for y in range(16)]
                for fr in range(16)]
        for t in range(16):
            if rows[t] != [rows[0][(y + t) % 16] for y in range(16)]:
                bad2 += 1
    if bad2:
        fails.append(u"flow 有 %d 帧不是 1 行上移" % bad2)
    print(u"  %s 15 种 x 16 帧 全部是 1 行/帧上移" % (u"[OK]" if not bad2 else u"!!"))

    print(u"\n== (6) 环绕接缝（比值 + 绝对差，两条都看）==")
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

    print(u"\n最大比值 %.2f（阈值 %.1f；比值超了就看绝对差 <= %.0f/255）"
          % (worst, RATIO_MAX, ABS_MAX))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
