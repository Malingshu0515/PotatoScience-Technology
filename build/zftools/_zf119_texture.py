# -*- coding: utf-8 -*-
r"""_zf119_texture.py —— ZF119：把用户给的「振金锭」长条**重排成 MC 动画贴图**（零重采样）

用户原话：「加个振金锭（目前没配方）这是振金锭贴图 做成动态贴图 3t播放一帧」

收件体检（`_zf119_intake.py`）的结论：
  · 真 PNG / 32×280 / 8 位 RGBA / **零半透明**；
  · 内容是 **10 个锭**，每个 **32×24**，竖直堆着（间距 6,4,7,4,4,4,4,4，最后两个挨着）；
  · MC 的动画贴图**必须**是「宽 × (宽 × 帧数)」的竖直长条 + 同名 `.mcmeta`
    ⇒ 32×280 **不能直接当动画用**（280/32 = 8.75，游戏会按 8 帧截断）。

帧尺寸怎么定的（不靠感觉）：盘上 **`titanium_ingot.png`（ZF60 用户自己画的）= 32×32，
内容 32×24，上下各留 4 行** —— 与本图的内容尺寸**一模一样** ⇒ 照它摆：
每帧 32×32，把 24 行的锭放进 **第 4..27 行**，上下各留 4 行。

⚠ **零重采样**：全程只做"整行搬运"，一个像素都不插值/缩放（本工程的一贯口径）。
   另附一条诊断：这张图是不是"16×16 的整数倍放大"（2×2 块是否全同色）。

产出：
  `src\main\resources\assets\potato_s_t\textures\item\vibranium_ingot.png`  32×320（10 帧）
  `src\main\resources\assets\potato_s_t\textures\item\vibranium_ingot.png.mcmeta`  frametime = 3
"""
import hashlib
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png, write_png  # noqa: E402

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, r"build\用户素材", u"振金锭.png")
TEXI = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
DST = os.path.join(TEXI, u"vibranium_ingot.png")
MCMETA = DST + u".mcmeta"
REF = os.path.join(TEXI, u"titanium_ingot.png")     # 摆位基准（用户 ZF60 自己画的 32×32 锭）
REPORT = os.path.join(ROOT, r"build\zftools\_zf119_texture.txt")

FRAME = 32          # 帧边长（= 宽度）
PAD_TOP = 4         # 上下各留 4 行（照 titanium_ingot.png）
CONTENT = 24        # 每个锭的内容高度
FRAMETIME = 3       # 用户原话「3t播放一帧」

fails, notes = [], []


def rows_of(w, h, buf):
    out = []
    for y in range(h):
        out.append([buf[(y * w + x) * 4:(y * w + x) * 4 + 4] for x in range(w)])
    return out


def main():
    w, h, buf = read_png(SRC)
    notes.append(u"源：%s  %d×%d  sha1 %s"
                 % (os.path.basename(SRC), w, h, hashlib.sha1(open(SRC, "rb").read()).hexdigest()[:12]))
    # ① 摆位基准：titanium_ingot 的内容 bbox
    rw, rh, rbuf = read_png(REF)
    rys = [y for y in range(rh) for x in range(rw) if rbuf[(y * rw + x) * 4 + 3] > 0]
    notes.append(u"基准 titanium_ingot.png：%d×%d，内容 y=%d..%d（上留 %d / 下留 %d）"
                 % (rw, rh, min(rys), max(rys), min(rys), rh - 1 - max(rys)))
    if (rw, rh) != (FRAME, FRAME) or min(rys) != PAD_TOP:
        fails.append(u"基准贴图不是 %d×%d / 上留 %d —— 摆位依据变了，先看清" % (FRAME, FRAME, PAD_TOP))

    src = rows_of(w, h, buf)
    counts = [sum(1 for px in row if px[3] > 0) for row in src]

    # ② 找每个锭的起始行
    starts = []
    for y in range(h):
        prev = counts[y - 1] if y > 0 else 0
        if counts[y] > 0 and prev <= 8:
            if starts and y - starts[-1] < CONTENT:
                continue
            if any(counts[min(h - 1, y + k)] >= 28 for k in range(0, 20)):
                starts.append(y)
    notes.append(u"检出锭的开始行：%s（共 %d 个）" % (starts, len(starts)))
    for k, s in enumerate(starts):
        seg = counts[s:s + CONTENT]
        if len(seg) != CONTENT or min(seg) <= 0:
            fails.append(u"第 %d 个锭（y=%d）后面不足 %d 行有内容" % (k, s, CONTENT))
    if len(starts) != 10:
        fails.append(u"锭的个数 %d ≠ 10 —— 与体检结论不符，先看清" % len(starts))
    if fails:
        print(u"\n".join(u"  [OK] " + n for n in notes))
        print(u"\n失败项 = %d" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1

    # ③ 重排成 32 × (32×10)
    n = len(starts)
    out_h = FRAME * n
    out = bytearray(FRAME * out_h * 4)
    for k, s in enumerate(starts):
        for r in range(CONTENT):
            dst_y = k * FRAME + PAD_TOP + r
            for x in range(w):
                px = src[s + r][x]
                i = (dst_y * FRAME + x) * 4
                out[i:i + 4] = bytes(px)
    write_png(DST, FRAME, out_h, out)
    notes.append(u"写出 %s：%d×%d（%d 帧 × %d）%d B"
                 % (os.path.basename(DST), FRAME, out_h, n, FRAME, os.path.getsize(DST)))

    # ④ mcmeta
    meta = {u"animation": {u"frametime": FRAMETIME}}
    io.open(MCMETA, "w", encoding="utf-8", newline=u"").write(
        json.dumps(meta, ensure_ascii=False, indent=2) + u"\n")
    notes.append(u"写出 %s：%s" % (os.path.basename(MCMETA),
                                 json.dumps(meta, ensure_ascii=False)))

    # ⑤ 回读断言：逐帧逐像素等于源里那 24 行
    bw, bh, bbuf = read_png(DST)
    back = rows_of(bw, bh, bbuf)
    bad = []
    for k, s in enumerate(starts):
        for r in range(CONTENT):
            for x in range(FRAME):
                if back[k * FRAME + PAD_TOP + r][x] != src[s + r][x]:
                    bad.append((k, r, x))
                    break
            if bad:
                break
        # 上下留白必须是全透明
        for r in list(range(0, PAD_TOP)) + list(range(PAD_TOP + CONTENT, FRAME)):
            if any(px[3] != 0 for px in back[k * FRAME + r]):
                bad.append((k, u"留白", r))
    if bad:
        fails.append(u"回读像素不一致：%s" % bad[:5])
    else:
        notes.append(u"回读：%d 帧 × %d×24 内容 **逐像素等于源**，上下留白全透明" % (n, FRAME))
    if (bw, bh) != (FRAME, FRAME * n):
        fails.append(u"回读尺寸 %d×%d ≠ %d×%d" % (bw, bh, FRAME, FRAME * n))

    # ⑥ 诊断：这张图是不是"整数倍放大"（2×2 块全同色）
    same = tot = 0
    for y in range(0, h - 1, 2):
        for x in range(0, w - 1, 2):
            tot += 1
            a = src[y][x]
            if a == src[y][x + 1] == src[y + 1][x] == src[y + 1][x + 1]:
                same += 1
    notes.append(u"诊断：2×2 同色块 %d/%d（%.1f%%）——%s"
                 % (same, tot, 100.0 * same / tot,
                    u"像是整数倍放大出来的" if same / tot > 0.95 else u"有原生细节，不是简单放大"))

    # ⑦ 帧数/时长账
    notes.append(u"时长账：%d 帧 × %d tick = **%d tick**（= %.2f 秒一轮），与用户原话「3t播放一帧」一致"
                 % (n, FRAMETIME, n * FRAMETIME, n * FRAMETIME / 20.0))

    print(u"\n".join(u"  [OK] " + n2 for n2 in notes))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    io.open(REPORT, "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(notes) + u"\n\n失败项 = %d\n" % len(fails)
        + u"\n".join(u"  !! " + f for f in fails) + u"\n")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
