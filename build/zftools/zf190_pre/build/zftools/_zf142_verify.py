# -*- coding: utf-8 -*-
u"""_zf142_verify.py —— ZF142 的**常驻校验**（四张星图的极带横向模糊）

用户原话：「可以尝试加一点点模糊」

本轮的判据只有一条主心骨：**盘上那四张图 = 留底那张 + 极滤波(96,16,1.0)**，一个字节都不许差。
它一口气钉住三件事：① 改的**只有**极带；② 改的**正好**是这条滤波（没有手改、没有多糊一块）；
③ 留底（`zf142_pre`）没被动过 —— 否则"重算对得上"就无从谈起。

另外量两条**屏幕上的**疗效：极区细条纹必须明显变少、赤道带必须一个像素没动。

跑法：python build\\zftools\\_zf142_verify.py
"""
import hashlib
import io
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _zf140_sim as sim  # noqa: E402
import _zf142_look as LOOK  # noqa: E402
import _zf142_poleblur as PB  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
SKY = PB.SKY
PRE = r"C:\PotatoST救援\zf142_pre\src\main\resources\assets\potato_s_t\textures\skybox"
PARAMS = (96, 16.0, 1.0)         # 本轮实际用的：y0=96 行（33.8°）、极点半径 16 px、线性衰减
HOLE_SHA1 = "61c1032e3a73a1409fa0e920793bae97ec413f9b"

fails, warns, notes = [], [], []


def check(ok, msg):
    (notes if ok else fails).append(msg)
    return ok


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    print(u"== A 盘上 = 留底 + 极滤波%s ==" % (PARAMS,))
    if not os.path.isdir(PRE):
        warns.append(u"没有 zf142_pre 留底，A 组整组跳过（新克隆的仓库会这样）")
    for name in PB.NAMES:
        p = os.path.join(SKY, name + ".png")
        q = os.path.join(PRE, name + ".png")
        w, h, idx, plte = PB.read_pal_png(p)
        check((w, h) == (1024, 512) and len(plte) == 256,
              u"A1 %-14s 结构：%dx%d colorType3 调色板 %d 色" % (name, w, h, len(plte)))
        if not os.path.exists(q):
            continue
        w0, h0, idx0, plte0 = PB.read_pal_png(q)
        check(w == w0 and h == h0 and np.array_equal(plte, plte0),
              u"A2 %-14s 调色板与留底逐字节相同（%d 色）" % (name, len(plte0)))
        rad = PB.polar_radius(h0, PARAMS[0], PARAMS[1], PARAMS[2])
        band = rad >= 0.5
        same_out = bool((idx[~band] == idx0[~band]).all())
        moved = int((idx[band] != idx0[band]).sum())
        check(same_out and moved > 1000,
              u"A3 %-14s 只有极带被动过：带外 %d 行逐字节相同、带内改 %d 像素"
              % (name, int((~band).sum()), moved))
        # —— 主心骨：现滤一遍，必须与盘上逐字节相同
        again, band2, _ = PB.filter_sky(idx0, plte0, PARAMS[0], PARAMS[1], PARAMS[2])
        check(np.array_equal(again, idx),
              u"A4 %-14s 重算：留底 + 极滤波%s ⇒ 与盘上**逐字节相同**（差 %d 像素）"
              % (name, PARAMS, int((again != idx).sum())))
        check(os.path.getsize(p) < os.path.getsize(q),
              u"A5 %-14s 体积 %d → %d B（糊过之后调色板图压得更小）"
              % (name, os.path.getsize(q), os.path.getsize(p)))

    print(u"\n== B 屏幕上的疗效 ==")
    f = 520 / 2.0 / math.tan(math.radians(35.0))
    r_in, r_out = math.tan(math.radians(3.0)), math.tan(math.radians(20.0))
    for name in PB.NAMES:
        q = os.path.join(PRE, name + ".png")
        if not os.path.exists(q):
            continue
        _, _, idx0, plte0 = PB.read_pal_png(q)
        before = plte0[idx0].astype(np.float32)
        after = sim.load_sky(name).astype(np.float32)
        v0, _ = LOOK.pole_view(before, 520)
        v1, _ = LOOK.pole_view(after, 520)
        hf0, _ = LOOK.ring_hf(v0, f * r_in, f * r_out)
        hf1, _ = LOOK.ring_hf(v1, f * r_in, f * r_out)
        # ⚠ 阈值定 15%：实测 24 / 20 / 60 / 20%（mystic 那张原本最"散"，糊掉的比例最小）。
        #   这条量的是**疗效**（"确实糊了、细条纹确实少了"），"是不是正好这条滤波"由 A4 逐字节钉死；
        #   为了凑一个好看的百分比去加糊，是本末倒置 —— 用户要的就是"一点点"。
        check(hf1 <= hf0 * 0.85,
              u"B1 %-14s 极区细条纹 %5.2f → %5.2f（降 %.0f%%，要求 ≥15%%）"
              % (name, hf0, hf1, 100.0 * (1 - hf1 / max(hf0, 1e-9))))
        # 赤道带（行 200~312）一个像素都不许动
        eq = int((idx0[200:312] != PB.read_pal_png(os.path.join(SKY, name + ".png"))[2][200:312]).sum())
        check(eq == 0, u"B2 %-14s 赤道带（第 200~311 行）逐字节未动（差 %d 像素）" % (name, eq))

    print(u"\n== C 回归 ==")
    hole = os.path.join(SKY, "black_hole.png")
    check(sha1(hole) == HOLE_SHA1,
          u"C1 黑洞盖片贴图本轮一个字节没动（sha1 %s…）" % sha1(hole)[:12])
    for name in PB.NAMES:
        a = sim.load_sky(name)
        check(float(a.std()) > 5.0 and float(a.std()) < 100.0,
              u"C2 %-14s 没被糊死：整图 std %.2f（5~100）" % (name, float(a.std())))

    print(u"\n---- 汇总 ----")
    for n in notes:
        print(u"  [OK] " + n)
    for w in warns:
        print(u"  [WARN] " + w)
    print(u"通过 %d   失败 %d   提示 %d" % (len(notes), len(fails), len(warns)))
    for x in fails:
        print(u"  [FAIL] " + x)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
