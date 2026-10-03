# -*- coding: utf-8 -*-
u"""_zf140_verify.py —— ZF140 的**常驻校验**（每轮都跑，改了什么都要它还是 0 失败）

用户原话：「因为图片问题 天空盒一个点会看到明显的拉伸现象 解决不了 那正好在那个地方
（四张星图都需要）补个黑洞 图给你了 估计得抠一下 只剩黑洞本体 然后放到拉伸的地方」

四组判据，都落在**能失败**的东西上：
  A 源码：盖片怎么建、什么时候画、画在哪一层（重点是"原版星空不受影响"与
    "buildOrThrow 只有 2 处" —— ZF133 那次崩客户端就是它）；
  B 贴图：尺寸/alpha 分布/中心必须不透明/角落必须全透明/**与用户素材逐字节对得上**；
  C 几何：顶点位置与 UV 必须构成"正对极点看过去不变形"的恒等（算式**从 Java 源码里读**，
    见 `_zf140_mapping.py`），分格误差 ≤1 px；
  D 疗效：把盖片按渲染器的规矩贴上去，正对极点看过去**与原图逐像素相同**，
    并且极点 4° 以内**处处被不透明的黑洞本体盖住**（这正是"拉伸现象"发生的地方）。

跑法：python build\\zftools\\_zf140_verify.py
"""
import hashlib
import io
import math
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _zf140_mapping as MAP  # noqa: E402
from _zf140_img import read_png_np, resize_bilinear, write_rgb  # noqa: E402
from _zf66_png import read_png  # noqa: E402          # 独立解码器交叉复核

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA_DIR = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
JAVA = os.path.join(JAVA_DIR, "client", "SkyboxRenderer.java")
ASSETS = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t")
SKY_DIR = os.path.join(ASSETS, "textures", "skybox")
HOLE = os.path.join(SKY_DIR, "black_hole.png")
OUT = os.path.join(ROOT, "build", "zftools", "_zf140_out")
PRE = r"C:\PotatoST救援\zf140_pre"
PRE2 = r"C:\PotatoST救援\zf142_pre"
RAW = os.path.join(ROOT, "build", "zftools", "_zf140_hole.bgra")
SKIES = ["sky_verdant", "sky_mystic", "sky_ember", "sky_tarantula"]

fails, warns, notes = [], [], []


def check(ok, msg):
    if ok:
        notes.append(msg)
    else:
        fails.append(msg)
    return ok


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


GIT = r"C:\Users\Administrator\AppData\Local\GitHubDesktop\app-3.6.5\resources\app\git\cmd\git.exe"


def git_head(rel):
    u"""取 HEAD 里那份文件的内容（用来证明"这张星图本轮一个字节没动"）"""
    import subprocess
    if not os.path.exists(GIT):
        return None
    r = subprocess.run([GIT, "-C", ROOT, "show", "HEAD:" + rel],
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return r.stdout if r.returncode == 0 else None


def body(text, header):
    i = text.index(header)
    j = text.index("{", i)
    d = 0
    for k in range(j, len(text)):
        if text[k] == "{":
            d += 1
        elif text[k] == "}":
            d -= 1
            if d == 0:
                return text[j:k + 1]
    raise AssertionError(u"切不出 %s" % header)


# ------------------------------------------------------------------ A 源码
def part_a():
    u"""A 组第一半：**只读源码文本**的判据（不依赖任何解析，所以注入把解析打坏时它们照样跑）"""
    print(u"\n== A 源码（SkyboxRenderer.java）==")
    text = io.open(JAVA, "r", encoding="utf-8", newline="").read()

    init = body(text, "public static void init()")
    check(init.count("caps = buildCaps();") == 1 and
          init.index("caps = buildCaps();") < init.index("addListener"),
          u"A6 网格在 init() 里建一次，且在挂监听之前（不在渲染线程里现算）")

    draw = body(text, "private static void onRenderLevelStage(RenderLevelStageEvent event)")
    n_call = draw.count("drawBlackHoles(matrix);")
    check(n_call == 1, u"A7 渲染里恰好调用一次 drawBlackHoles（读到 %d 次）" % n_call)
    if n_call == 1:
        i_call = draw.index("drawBlackHoles(matrix);")
        i_dome = draw.index("BufferUploader.drawWithShader(buffer.buildOrThrow());")
        i_cull = draw.index("RenderSystem.enableCull();")
        i_depth = draw.index("RenderSystem.depthMask(true);")
        check(i_dome < i_call < i_cull and i_call < i_depth,
              u"A8 盖片画在**球幕之后、恢复状态之前**（同一个「关雾 / 不写深度」的窗口里）")
        i_guard = draw.find("index <= 0 || index >= SKIES.length")
        check(i_guard >= 0 and i_guard < i_call,
              u"A9 盖片在 `index <= 0` 的提前 return **之后** ⇒ 原版星空那一档不受影响")
        check("pose.popPose();" in draw[i_call:],
              u"A10 盖片用的是同一个 pose（跟着天球一起转）")

    dh = body(text, "private static void drawBlackHoles(Matrix4f matrix)")
    check("RenderSystem.enableBlend();" in dh and "RenderSystem.defaultBlendFunc();" in dh,
          u"A11 盖片开混合且用 SRC_ALPHA / ONE_MINUS_SRC_ALPHA")
    check(dh.count("disableBlend") == 1, u"A12 画完把混合恢复回去")
    check("setShaderTexture(0, BLACK_HOLE)" in dh, u"A13 绑的是盖片自己的贴图")
    check("new float[" not in dh and "buildCaps" not in dh,
          u"A14 drawBlackHoles 里不新建数组、不重建网格（每帧只搬顶点）")

    check(text.count("buildOrThrow()") == 2,
          u"A15 全文件 buildOrThrow() 恰好 2 处（ZF133 崩客户端就是因为多出来一个空 buffer 的调用）")
    pc = body(text, "private static int putCap(")
    check(pc.count("out[n++]") == 5, u"A16 putCap 恰好写 5 个 float（x,y,z,u,v）")
    check("Math.atan(g * tmax)" in pc, u"A17 顶点角度走 atan(g·tanθmax)（透视的逆）")
    check(not re.search(r"0\.5D\s*-\s*0\.5D\s*\*\s*b", pc),
          u"A18 putCap 里没有把 V 的 UV 写成减号（减号 = 正对极点时上下颠倒）")

    # A19：编译产物里必须**真的**带着新代码的痕迹。
    #   ⚠ 第一版比的是 mtime（.class 不比 .java 旧），结果反证脚本"注入→还原"一跑就假红：
    #     还原写盘会刷新 .java 的 mtime，而 .class 一个字节都没变。**时间戳是替身，不是证据**，
    #     改成查 class 常量池里的字面量 —— 它只有在真的编译过之后才会出现。
    cls = os.path.join(ROOT, "build", "classes", "java", "main", "com", "potatost", "mod",
                       "client", "SkyboxRenderer.class")
    blob = open(cls, "rb").read() if os.path.exists(cls) else b""
    for lit in (b"textures/skybox/black_hole.png", b"drawBlackHoles", b"putCap", b"HOLE_GRID"):
        check(lit in blob, u"A19 编译产物里带着 %s（说明改动真的编译过了）"
              % lit.decode("ascii", "replace"))

    # A20：开机自检 —— 源码判据管不到"编译出来跑起来算什么"，这一步把真顶点数组量一遍打进日志，
    #      runClient 那一路就有了**正面证据**（日志里必须出现 OK 那一行）。
    check(init.count("verifyCaps();") == 1, u"A20 init() 里调用一次 verifyCaps 自检")
    vc = body(text, "private static void verifyCaps()")
    check("LOGGER.info(\"SkyboxRenderer: black-hole caps OK" in vc and
          "LOGGER.error(\"SkyboxRenderer: black-hole cap geometry BROKEN" in vc,
          u"A20b 自检两条路都写了日志（OK 与 BROKEN 各一条，日志检查才咬得住）")
    check("throw " not in vc,
          u"A20c 自检**不抛异常**（玩家的客户端不该因为一行自检挂掉）")


def part_a2():
    u"""A 组第二半：常量（经由 `_zf140_mapping` 从源码里读出来）"""
    cap = MAP.JavaCap(JAVA)
    check(cap.tex == "black_hole.png",
          u"A1 盖片贴图指向 textures/skybox/%s" % cap.tex)
    check(5.0 <= cap.degrees <= 45.0,
          u"A2 θmax = %.1f°（5~45 之间：太小盖不住第一环 11.25°，太大独占天空）" % cap.degrees)
    check(cap.grid >= 8, u"A3 网格 %d×%d（≥8 才够密，见 C3）" % (cap.grid, cap.grid))
    check(0.90 <= cap.radius_factor < 1.0,
          u"A4 盖片半径 = 球幕 × %.3f（略小一圈，压在球幕之上）" % cap.radius_factor)
    check(abs(cap.tmax - math.tan(math.radians(cap.degrees))) < 1e-5,
          u"A5 tmax 由 θmax 现算：tan(%.1f°) = %.6f" % (cap.degrees, cap.tmax))


# ------------------------------------------------------------------ B 贴图
def part_b():
    print(u"\n== B 贴图（skybox/black_hole.png）==")
    w, h, ctype, px = read_png(HOLE)
    check((w, h) == (640, 640), u"B1 尺寸 %dx%d（源图不缩放直接裁，640 是抠图时的正方形边长）" % (w, h))
    check(ctype == 6, u"B2 colorType=%d（必须是 6=RGBA，才带得动透明边）" % ctype)

    rgba = np.array(px, dtype=np.uint8).reshape(h, w, 4)
    a = rgba[:, :, 3]
    op = float((a == 255).mean())
    check(0.08 <= op <= 0.25, u"B3 不透明像素占 %.1f%%（8~25%%：是「一个黑洞」，不是整张图也不是几个点）"
          % (100.0 * op))
    check(int((a == 0).mean() * 100) >= 60,
          u"B4 全透明像素占 %.1f%%（背景抠干净了）" % (100.0 * (a == 0).mean()))

    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.sqrt((xx - w / 2.0) ** 2 + (yy - h / 2.0) ** 2)
    core = rr <= 40
    check(int(a[core].min()) == 255,
          u"B5 正中 40 px 半径**全不透明**（极点就落在这里；最小 alpha = %d）" % a[core].min())
    corners = a[[0, 0, h - 1, h - 1], [0, w - 1, 0, w - 1]]
    check((corners == 0).all(), u"B6 四角全透明（alpha=%s）" % list(corners))
    check(int(rgba[a == 0][:, :3].max()) == 0,
          u"B7 全透明处的 RGB 全是 0（不把没用的颜色留在文件里）")

    # B8：与"从用户素材现抠一遍"的结果逐字节相同 —— 这是"这张图确实是那张素材抠出来的"的硬证据
    sys.path.insert(0, os.path.join(ROOT, "build", "zftools"))
    import _zf140_cutout as CUT  # noqa: E402
    if not os.path.exists(RAW):
        # 裸像素是**可再生的中间产物**（3.4 MB），不进仓库；要用先跑一次解码
        warns.append(u"B8 跳过：缺 %s（跑 build\\zftools\\_zf140_jpeg_dump.ps1 可再生）"
                     % os.path.relpath(RAW, ROOT))
    else:
        rgb = CUT.load_rgb()
        _, alpha, cx, cy = CUT.cutout(rgb, 35.0, 1)
        half = CUT.SIDE / 2.0
        ix0, iy0 = int(round(cx - half)), int(round(cy - half))
        ref = np.zeros_like(rgba)
        ref[:, :, :3] = rgb[iy0:iy0 + CUT.SIDE, ix0:ix0 + CUT.SIDE]
        refa = (alpha[iy0:iy0 + CUT.SIDE, ix0:ix0 + CUT.SIDE] * 255.0 + 0.5).astype(np.uint8)
        ref[:, :, 3] = refa
        ref[refa == 0, :3] = 0
        check(np.array_equal(ref, rgba),
              u"B8 盘上这张图与「从 build/用户素材/黑洞.jpg 现抠一遍」逐字节相同（差 %d 个像素）"
              % int((ref != rgba).any(axis=2).sum()))

    # B9：四张星图（0.11 ZF142 起极带被极滤波动过）——
    #   ⚠ 原来这条是"相对上次提交一个字节没动"，ZF142 之后**按设计不再成立**。
    #   换成两条更硬的：① 结构没坏；② 与 zf142_pre 的留底相比，**带外逐字节相同、带内确实变过**。
    import _zf142_poleblur as PB
    pre = os.path.join(PRE2, "src", "main", "resources", "assets", "potato_s_t",
                       "textures", "skybox")
    for name in SKIES:
        p = os.path.join(SKY_DIR, name + ".png")
        try:
            w, h, idx, plte = PB.read_pal_png(p)
            check((w, h) == (1024, 512) and len(plte) == 256,
                  u"B9 %s.png 结构没坏：%dx%d / 调色板 %d 色" % (name, w, h, len(plte)))
        except Exception as exc:                      # noqa: BLE001
            check(False, u"B9 %s.png 解不开：%r" % (name, exc))
            continue
        q = os.path.join(pre, name + ".png")
        if not os.path.exists(q):
            warns.append(u"B9 %s.png：没有 zf142_pre 留底，跳过「只动极带」比对" % name)
            continue
        w0, h0, idx0, plte0 = PB.read_pal_png(q)
        rad = PB.polar_radius(h0, 96, 16.0, 1.0)
        band = rad >= 0.5
        same_out = int((idx[~band] == idx0[~band]).all())
        moved_in = int((idx[band] != idx0[band]).sum())
        check(np.array_equal(plte, plte0) and same_out == 1 and moved_in > 0,
              u"B9 %s.png 只动了极带：调色板未变、带外 %d 行逐字节相同、带内改了 %d 像素"
              % (name, int((~band).sum()), moved_in))


# ------------------------------------------------------------------ C 几何
def part_c():
    print(u"\n== C 几何（算式从 Java 源码读出来）==")
    cap = MAP.JavaCap(JAVA)
    err, s, uv = MAP.identity_error(cap, 1.0)
    check(err < 1e-6, u"C1 恒等：顶点 gnomonic 坐标 vs (2u-1,2v-1)·tmax 的最大偏差 %.2e"
          % err)
    err2, _, _ = MAP.identity_error(cap, -1.0)
    check(err2 < 1e-6, u"C2 南极那一份同样成立（偏差 %.2e）" % err2)

    for g, limit in ((cap.grid, 1.0), (8, 3.0), (4, 8.0)):
        e = MAP.facet_error_px(cap, grid=g)
        check(e <= limit, u"C3 分格误差 %d×%d = %.3f px（阈值 %.1f px，400 px 半径屏）"
              % (g, g, e, limit))

    for (aa, bb) in ((0.0, 0.0), (0.5, -0.5), (-0.75, 0.25), (1.0, 1.0)):
        _, one = cap.sample(np.array([aa]), np.array([bb]), 1.0)
        check(abs(one[0, 0] - (0.5 + 0.5 * aa)) < 1e-6 and abs(one[0, 1] - (0.5 + 0.5 * bb)) < 1e-6,
              u"C4 UV(%+.2f,%+.2f) = (%.3f, %.3f) 正是 0.5+0.5·(a,b)"
              % (aa, bb, one[0, 0], one[0, 1]))

    # C5：极点 4° 以内**处处**被不透明像素盖住（把纹理按 C1 的映射反查一遍）
    hole = read_png_np(HOLE).astype(np.float32)
    rng = np.random.default_rng(140)
    th = np.radians(4.0) * np.sqrt(rng.random(4000))
    ph = rng.random(4000) * 2 * math.pi
    g = np.tan(th) / cap.tmax
    aa, bb = g * np.cos(ph), g * np.sin(ph)
    _, one = cap.sample(aa, bb, 1.0)
    uu = np.clip(one[:, 0], 0, 1) * hole.shape[1] - 0.5
    vv = np.clip(one[:, 1], 0, 1) * hole.shape[0] - 0.5
    x0 = np.floor(uu).astype(int)
    y0 = np.clip(np.floor(vv).astype(int), 0, hole.shape[0] - 1)
    al = hole[y0, np.mod(x0, hole.shape[1]), 3]
    check(al.min() >= 250, u"C5 极点 4° 以内 4000 个方向取样，最小 alpha = %d（必须全不透明）"
          % al.min())


# ------------------------------------------------------------------ D 疗效
def part_d():
    print(u"\n== D 疗效（照渲染器的规矩贴上去看）==")
    # 正对极点的视图：屏幕坐标就是 gnomonic 坐标。
    # ⚠ 两个容易搞错的地方（第一版全踩了，量出来 61/255，看着像"方向反了"，其实是量错了）：
    #   ① 屏幕**上半**对应盖片的 **b<0**：把渲染器的姿态摊开算一遍 ——
    #      A=90°、yaw=0、pitch=0 时 世界(0,1,0) ↦ 球幕本地(0,0,-1)，而 b 取的是本地的 z 分量；
    #   ② 盖片正方形在屏幕上只有 2·f·tanθmax 像素宽，**不是整个视口** ——
    #      拿整屏去比会差一个 f·tanθmax/(H/2) 的比例，那是比例错，不是朝向错。
    cap = MAP.JavaCap(JAVA)
    hole = read_png_np(HOLE)
    H = 400
    f = H / 2.0 / math.tan(math.radians(70.0) / 2.0)
    n = int(round(2.0 * f * cap.tmax))
    ys, xs = np.mgrid[0:H, 0:H]
    gx = (xs + 0.5 - H / 2.0) / f
    gy = (H / 2.0 - (ys + 0.5)) / f
    aa = gx / cap.tmax
    bb = -gy / cap.tmax
    inside = (np.abs(aa) <= 1) & (np.abs(bb) <= 1)
    _, one = cap.sample(aa.ravel(), bb.ravel(), 1.0)
    uu = np.clip(one[:, 0], 0, 1).reshape(H, H)
    vv = np.clip(one[:, 1], 0, 1).reshape(H, H)

    def bil(u, v, img):
        u"""双线性取样（u 环绕、v 夹取），与渲染器的采样口径一致"""
        hh, ww = img.shape[:2]
        x = np.clip(u, 0, 1) * ww - 0.5
        y = np.clip(v, 0, 1) * hh - 0.5
        x0, y0 = np.floor(x).astype(int), np.clip(np.floor(y).astype(int), 0, hh - 1)
        x1, y1 = x0 + 1, np.clip(y0 + 1, 0, hh - 1)
        fx, fy = (x - x0)[..., None], (y - y0)[..., None]
        a = img[y0, np.mod(x0, ww)] * (1 - fx) + img[y0, np.mod(x1, ww)] * fx
        b = img[y1, np.mod(x0, ww)] * (1 - fx) + img[y1, np.mod(x1, ww)] * fx
        return (a * (1 - fy) + b * fy).astype(np.float32)

    got = bil(uu, vv, hole)                     # 按源码算式取色 = 屏幕上该看到的样子
    sub = got[H // 2 - n // 2:H // 2 + n // 2, H // 2 - n // 2:H // 2 + n // 2]
    # 参照：把屏幕那一块**按"正对极点就该是原图"的朴素定义**取一遍 ——
    # 两个走的是不同的路（一个过 Java 的算式，一个是朴素恒等映射），对不上就是映射歪了。
    jj, ii = np.mgrid[0:n, 0:n]
    ref = bil((ii + 0.5) / n, (jj + 0.5) / n, hole)
    m = (ref[:, :, 3] / 255.0) > 0.5
    diff = float(np.abs(sub[:, :, :3].mean(2) - ref[:, :, :3].mean(2))[m].mean())
    check(diff <= 2.0,
          u"D1 正对极点看到的就是原图：不透明处平均绝对差 %.2f/255（阈值 2.0；盖片在屏幕上 %d px 见方）"
          % (diff, n))

    rr = np.sqrt(gx ** 2 + gy ** 2)
    core2 = rr < math.tan(math.radians(2.0))
    luma = sub_luma = got[:, :, :3].mean(2)
    check(float(luma[H // 2, H // 2]) < 60.0 and float(luma[core2].mean()) < 60.0,
          u"D2 极点（拉伸奇点所在）画出来是**暗的**：正中心 %.1f、2° 内均值 %.1f（都须 <60）"
          % (luma[H // 2, H // 2], luma[core2].mean()))

    prev = os.path.join(OUT, "pole_check.png")
    ring = np.clip(255 - got[:, :, :3], 0, 255).astype(np.uint8)
    write_rgb(prev, np.concatenate(
        [ring, got[:, :, :3].astype(np.uint8),
         np.repeat((got[:, :, 3]).astype(np.uint8)[:, :, None], 3, axis=2)], axis=1))
    notes.append(u"D3 出图：%s（左=反色看轮廓 / 中=贴上去的样子 / 右=alpha）" % prev)


# ------------------------------------------------------------------ E 病根
def part_e():
    print(u"\n== E 病根（「极点拉伸」确实存在，才谈得上补）==")
    for name in SKIES:
        w, h, ctype, px = read_png(os.path.join(SKY_DIR, name + ".png"))
        a = np.array(px, dtype=np.uint8).reshape(h, w, 4)[:, :, :3].astype(np.float32)
        band = a[:16]                       # 极点那一圈：整行要摊满 360° 方位角
        mid = a[h // 2 - 8:h // 2 + 8]      # 对照：赤道
        s_band = float(band.std())
        s_mid = float(mid.std())
        check(s_band >= 4.0,
              u"E1 %-14s 极带横std %5.2f / 赤道 %5.2f ⇒ 极点是「有内容的」，绕成一点就是放射条纹"
              % (name, s_band, s_mid))


def main():
    # ⚠ 每个 part 都包一层：**校验器自己抛异常也算失败**。
    #   否则"把锚点删掉"这类注入会让校验器崩掉，而崩掉在只看退出码的调用方眼里
    #   和"通过"没区别 —— 那就是一条永远咬不住的判据（§4.126 的同款坑）。
    for name, fn in ((u"A 源码", part_a), (u"A 常量", part_a2), (u"B 贴图", part_b),
                     (u"C 几何", part_c), (u"D 疗效", part_d), (u"E 病根", part_e)):
        try:
            fn()
        except Exception as exc:                      # noqa: BLE001
            import traceback
            fails.append(u"%s 这一段抛异常：%r（%s）"
                         % (name, exc, traceback.format_exc().strip().splitlines()[-1]))
    print(u"\n---- 汇总 ----")
    if "--brief" not in sys.argv:
        for n in notes:
            print(u"  [OK] " + n)
    print(u"通过 %d   失败 %d   提示 %d" % (len(notes), len(fails), len(warns)))
    for f in fails:
        print(u"  [FAIL] " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
