# -*- coding: utf-8 -*-
u"""_zf140_sim.py —— ZF140 第三步：天空盒的**软件复刻**（不启动游戏就能看见"拉伸点"）

为什么要有这个：用户报的毛病是**画面**上的（「天空盒一个点会看到明显的拉伸现象」），
而这种毛病只靠读代码说不清楚 —— 要么真开客户端截图，要么把渲染器**照抄一遍**在 numpy 里跑。
这里选后者，理由有三条：
  ① 能出图给眼睛看（档案 §6.8）；
  ② 能**先复现**现象再谈修（如果连病都画不出来，凭什么说药有效）；
  ③ 改 `SkyboxRenderer` 的参数（黑洞多大、放几个极点）不用重编译、不用进世界。

复刻的口径 —— **逐条对着 `client/SkyboxRenderer.java` 抄**：
  · 顶点：`lat = π(0.5 - r/RINGS)`、`lon = 2π s/SEGMENTS`，
    位置 `(R cos lat cos lon, R sin lat, R cos lat sin lon)`，UV `(s/SEGMENTS, r/RINGS)`
    ⇒ 反解就是 `v = 0.5 - asin(y)/π`、`u = atan2(z, x)/2π`（u 环绕、v 夹取）；
  · 姿态：`pose = modelview(摄像机旋转) * Rx(A)`，`A = (gameTime%24000)/24000*360`
    ⇒ 世界方向 `w` 对应的**球幕本地**方向是 `Rx(-A) w`；
  · 球幕之后画黑洞盖片：`θ = acos(s * y)`、`φ = atan2(z, x)`、
    `a = tanθ/tanθmax·cosφ`、`b = tanθ/tanθmax·sinφ`、`UV = (0.5+0.5a, 0.5+0.5b)`，
    按 SRC_ALPHA / ONE_MINUS_SRC_ALPHA 混上去。

**为什么黑洞不是"贴进四张星图"而是单独的盖片**：等距圆柱贴图在极点分辨率是塌的 ——
1024x512 的图，极点那一圈（0~11.25°）只占 32 行像素，而这一圈还要摊满 360° 方位角。
真把黑洞烤进这张图，出来的是一团十来个像素高的马赛克。盖片自己的图 + 自己的网格，
分辨率就与星图解耦了，代价只是渲染器里多一次 drawcall。

跑法：
    python build\\zftools\\_zf140_sim.py --sky sky_mystic --angle 90 --yaw 0 --pitch 10
    python build\\zftools\\_zf140_sim.py --before-after --out _zf140_out
"""
import argparse
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _zf140_img import read_png_np, write_rgb  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
SKY_DIR = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "textures", "skybox")
CACHE = os.path.join(ROOT, "build", "zftools", "_zf140_out", "_cache")


# ------------------------------------------------------------------ 贴图装载
def load_sky(name):
    u"""星图是调色板 PNG（colorType 3），_zf140_img 只认 2/6 ⇒ 用 _zf66_png 读，结果缓存成 npy。

    ⚠ 缓存名里带**源文件的 sha1 前 12 位**。ZF142 要反复改星图再看效果，
      第一版按名字缓存 ⇒ 改了图之后模拟器还在拿旧数据，出图是"改了但看不出变化"的假象
      （§4.138 的同款：**替身（文件名）不是证据**）。"""
    import hashlib
    os.makedirs(CACHE, exist_ok=True)
    src = os.path.join(SKY_DIR, name + ".png")
    tag = hashlib.sha1(open(src, "rb").read()).hexdigest()[:12]
    npy = os.path.join(CACHE, "sky_%s_%s.npy" % (name, tag))
    if os.path.exists(npy):
        return np.load(npy)
    from _zf66_png import read_png
    w, h, ctype, px = read_png(src)
    a = np.array(px, dtype=np.uint8).reshape(h, w, 4)[:, :, :3]
    np.save(npy, a)
    print(u"  读入 %s %dx%d colorType=%d sha1 %s" % (name, w, h, ctype, tag))
    return a


def load_hole(path):
    if path is None or not os.path.exists(path):
        return None
    return read_png_np(path)


# ------------------------------------------------------------------ 采样
def sample_bilinear(tex, u, v):
    u"""tex: HxWx3/4；u 环绕 [0,1)、v 夹取 [0,1]；u/v 都是 float 数组（像素中心对齐）"""
    h, w = tex.shape[:2]
    x = u * w - 0.5
    y = v * h - 0.5
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    fx = (x - x0)[..., None]
    fy = (y - y0)[..., None]
    x0m = np.mod(x0, w)
    x1m = np.mod(x0 + 1, w)
    y0m = np.clip(y0, 0, h - 1)
    y1m = np.clip(y0 + 1, 0, h - 1)
    a = tex[y0m, x0m] * (1 - fx) + tex[y0m, x1m] * fx
    b = tex[y1m, x0m] * (1 - fx) + tex[y1m, x1m] * fx
    return a * (1 - fy) + b * fy


# ------------------------------------------------------------------ 摄像机
def camera_rays(w, h, yaw_deg, pitch_deg, fov_deg):
    u"""返回 (h,w,3) 的世界方向单位向量。yaw=0 看 +Z，yaw 顺时针增大；pitch>0 抬头"""
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    fwd = np.array([-math.sin(yaw) * math.cos(pitch), math.sin(pitch),
                    math.cos(yaw) * math.cos(pitch)])
    right = np.array([math.cos(yaw), 0.0, math.sin(yaw)])
    up = np.cross(fwd, right)          # ⚠ 是 cross(fwd, right) 才是 +Y：cross(right, fwd) = -Y，
    #                                    第一版就写反了，出图上下颠倒（地面跑到上半屏）
    t = math.tan(math.radians(fov_deg) * 0.5)
    aspect = w / float(h)
    xs = (np.arange(w) + 0.5) / w * 2.0 - 1.0
    ys = 1.0 - (np.arange(h) + 0.5) / h * 2.0
    gx, gy = np.meshgrid(xs * t * aspect, ys * t)
    d = fwd[None, None, :] + gx[..., None] * right[None, None, :] + gy[..., None] * up[None, None, :]
    return d / np.linalg.norm(d, axis=2, keepdims=True)


def rot_x(vec, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    out = vec.copy()
    out[..., 1] = vec[..., 1] * c - vec[..., 2] * s
    out[..., 2] = vec[..., 1] * s + vec[..., 2] * c
    return out


# ------------------------------------------------------------------ 渲染
def render(sky, hole, theta_max, w=960, h=540, yaw=0.0, pitch=10.0, fov=70.0,
           day_angle=0.0, pole=0, ground=True, clip_theta=0.0):
    u"""pole: 0=不画黑洞，1=只画北极，-1=只画南极，2=两极都画
       clip_theta>0 时把"离极点 theta_max 以内"画成洋红（诊断用）"""
    rays = camera_rays(w, h, yaw, pitch, fov)
    local = rot_x(rays, -day_angle)

    v = 0.5 - np.arcsin(np.clip(local[..., 1], -1, 1)) / math.pi
    u = np.mod(np.arctan2(local[..., 2], local[..., 0]) / (2 * math.pi), 1.0)
    img = sample_bilinear(sky.astype(np.float32), u, v)

    if ground:
        g = rays[..., 1] < 0.0
        img[g] = img[g] * 0.25 + np.array([18.0, 34.0, 16.0]) * 0.75

    if clip_theta > 0.0:
        for s in (1, -1):
            th = np.degrees(np.arccos(np.clip(s * local[..., 1], -1, 1)))
            img[th < clip_theta] = (255.0, 0.0, 255.0)

    if hole is not None and pole != 0:
        N = hole.shape[0]
        poles = (1, -1) if pole == 2 else (pole,)
        tmax = math.tan(math.radians(theta_max))
        for s in poles:
            cy = np.clip(s * local[..., 1], -1.0, 1.0)
            theta = np.arccos(cy)                       # 0..π
            r = np.tan(theta) / tmax                    # 归一化的 gnomonic 半径
            phi = np.arctan2(local[..., 2], local[..., 0])
            a = r * np.cos(phi)
            b = r * np.sin(phi)
            inside = (np.abs(a) <= 1.0) & (np.abs(b) <= 1.0) & (r <= math.sqrt(2.0))
            # 前半球才画（背面那半张盖片不会出现在屏幕上）
            inside &= (cy > 0.0)
            uu = 0.5 + 0.5 * a
            # ⚠ V 取 +：正对极点看过去必须**和源图一模一样**（含上下）。
            #   第一版写的 0.5-0.5b，正对极点时上下颠倒 —— 实测"正对极点的渲染 vs 源裁剪"
            #   平均绝对差 61.4/255；改成 + 之后 0.79/255（`_zf140_mapping.py` 常驻守着这条）。
            vv = 0.5 + 0.5 * b
            tex = sample_bilinear(hole.astype(np.float32), np.clip(uu, 0, 1), np.clip(vv, 0, 1))
            al = (tex[..., 3:4] / 255.0) * inside[..., None]
            img = tex[..., :3] * al + img * (1.0 - al)
    return np.clip(img, 0, 255).astype(np.uint8)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sky", default="sky_mystic")
    ap.add_argument("--hole", default=os.path.join(ROOT, "build", "zftools", "_zf140_out", "black_hole.png"))
    ap.add_argument("--theta", type=float, default=20.0, help=u"盖片角半径（度）")
    ap.add_argument("--pole", type=int, default=2, help=u"0=不画 1=北极 -1=南极 2=两极")
    ap.add_argument("--angle", type=float, default=90.0, help=u"天球自转角（0=北极在天顶，90=北极在地平线）")
    ap.add_argument("--yaw", type=float, default=0.0)
    ap.add_argument("--pitch", type=float, default=10.0)
    ap.add_argument("--fov", type=float, default=70.0)
    ap.add_argument("--w", type=int, default=960)
    ap.add_argument("--h", type=int, default=540)
    ap.add_argument("--out", default=os.path.join(ROOT, "build", "zftools", "_zf140_out"))
    ap.add_argument("--name", default=None)
    ap.add_argument("--clip-theta", type=float, default=0.0)
    ap.add_argument("--no-ground", action="store_true")
    a = ap.parse_args(argv)

    os.makedirs(a.out, exist_ok=True)
    load_sky(a.sky)                       # 先确保缓存里有（并打印一次原始规格）
    sky = load_sky(a.sky)
    hole = load_hole(a.hole) if a.pole != 0 else None
    if hole is not None:
        print(u"  盖片 %s %dx%d" % (os.path.basename(a.hole), hole.shape[1], hole.shape[0]))
    img = render(sky, hole, a.theta, w=a.w, h=a.h, yaw=a.yaw, pitch=a.pitch, fov=a.fov,
                 day_angle=a.angle, pole=a.pole, ground=not a.no_ground,
                 clip_theta=a.clip_theta)
    name = a.name or ("%s_a%03d_y%03d_p%03d_hole%d_t%02d.png"
                      % (a.sky, int(a.angle), int(a.yaw), int(a.pitch), a.pole, int(a.theta)))
    p = os.path.join(a.out, name)
    write_rgb(p, img)
    print(u"  -> %s" % p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
