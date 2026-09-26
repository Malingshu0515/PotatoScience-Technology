# -*- coding: utf-8 -*-
u"""_zf122_tex2.py —— ZF122 贴图第二版：消接缝 + 减抖动

用户实测反馈 #2（2026-09-25）：「这些分界线略微有点明显 可以优化一下下嘛」。

两处改动：
  ① **环形接缝融合**：源图不是 360° 全景 ⇒ 左右边缘内容对不上，贴到球幕上就是一条竖线。
     做法是标准的"偏移 + 融合"：最左边一小段从右边缘内容渐变进来
     （`out[:, :band] = right*(1-a) + left*a`），于是首列 ≈ 末列，跨接缝连续。
     脚本里带**判据**：融合前后各量一次"首列与末列的平均绝对差"。
  ② **抖动减半**：Floyd–Steinberg 的误差只传播 50% —— 上一版噪点偏重（截图里像一层沙）。

跑法：python build\\zftools\\_zf122_tex2.py [--write]
"""
import io
import os
import sys

import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import _zf122_textures as T   # noqa: E402


def mirror_tile(img):
    u"""镜像拼接：左半原图 + 右半镜像 ⇒ **接缝处首列与末列逐像素相同**，数学上必然无缝。

    第一版我试的是"向内渐变融合"（标准 tileable 做法），接缝指标**反而变差**
    （verdant 41.15 → 41.36）：因为源图不是 360° 全景，边缘内容对不上，
    渐变只是把"跳变"挪了个位置，并没有消除它。
    镜像拼接的代价是横向有效分辨率减半（1024 宽里其实是 512 的内容），
    对星云这种软图完全看不出来，换来的是**零接缝**。
    """
    w2 = img.shape[1] // 2
    half = img[:, :w2]
    return np.concatenate([half, half[:, ::-1]], axis=1)


def make_seamless(img, frac=0.125):
    h, w = img.shape[:2]
    band = max(1, int(w * frac))
    a = np.linspace(0.0, 1.0, band, dtype=np.float32)[None, :, None]
    out = img.copy()
    out[:, :band] = img[:, -band:] * (1.0 - a) + img[:, :band] * a
    return out


def seam_metric(img):
    return float(np.abs(img[:, 0] - img[:, -1]).mean())


def dither_half(img, pal, strength=0.5):
    u"""与 _zf122_textures.dither_fs 同一套，只把误差传播乘了 strength"""
    h, w = img.shape[:2]
    buf = img.astype(np.float32).copy()
    idx = np.zeros((h, w), dtype=np.uint8)
    pl = pal.astype(np.float32)
    for y in range(h):
        row = buf[y]
        for x in range(w):
            old = row[x]
            k = int(((pl - old) ** 2).sum(axis=1).argmin())
            idx[y, x] = k
            err = (old - pl[k]) * strength
            if x + 1 < w:
                row[x + 1] += err * (7.0 / 16.0)
            if y + 1 < h:
                if x > 0:
                    buf[y + 1, x - 1] += err * (3.0 / 16.0)
                buf[y + 1, x] += err * (5.0 / 16.0)
                if x + 1 < w:
                    buf[y + 1, x + 1] += err * (1.0 / 16.0)
    return idx


def main(argv):
    write = "--write" in argv
    os.makedirs(T.OUT, exist_ok=True)
    if write:
        os.makedirs(T.DEST, exist_ok=True)
    total = 0
    for name in T.SOURCES:
        # 先裁成 1:1 再缩到一半宽度：镜像拼接后仍是 1024×512（横向有效分辨率 512）
        # ⚠ mirror_tile 内部会把宽度砍一半再镜像 ⇒ 这里必须缩到**全宽** T.W
        img = T.resize(T.center_crop_2to1(T.load(name)), T.W, T.H)
        before = seam_metric(img)
        img = mirror_tile(img)
        after = seam_metric(img)
        pal = T.median_cut(img[::4, ::4].reshape(-1, 3), 256)
        idx = dither_half(img, pal, 0.5)
        pal_rgb = pal[idx.astype(np.int64)]
        path = os.path.join(T.OUT, name + u"_pal2.png")
        T.write_png_palette(path, T.W, T.H, idx, pal)
        T.write_preview(os.path.join(T.OUT, name + u"_preview2.png"), pal_rgb)
        size = os.path.getsize(path)
        # ⚠ **真解码**校验：只查文件头会被"IDAT 长度只有一半"这种坏文件骗过去（本轮就是这么交付了一版黑紫天空）
        from _zf66_png import read_png
        w3, h3, ctype3, px3 = read_png(path)
        assert (w3, h3) == (T.W, T.H), u"%s: 解码出 %dx%d" % (name, w3, h3)
        assert len(px3) == T.W * T.H, u"%s: 像素数 %d" % (name, len(px3))
        assert px3[0][3] == 255, u"%s: 首像素不是不透明" % name
        total += size
        print(u"   %-14s 接缝 %.2f → %.2f（越小越好）  抖动 50%%  %6.0f KB  量化误差 %.2f"
              % (name, before, after, size / 1024.0,
                 float(np.abs(pal_rgb.astype(np.float32) - img).mean())))
        if write:
            import shutil
            shutil.copyfile(path, os.path.join(T.DEST, name + u".png"))
    print(u"   合计 %.1f MB%s" % (total / 1048576.0, u"；已写进 textures/skybox/" if write else u"（体检模式）"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
