# -*- coding: utf-8 -*-
r"""_zf119_texture.py —— ZF119：把用户给的「振金锭」长条重排成 MC 动画贴图（零重采样）

用户原话（第一次）：「加个振金锭（目前没配方）这是振金锭贴图 做成动态贴图 3t播放一帧」
用户原话（实测反馈，本版就是改这个）：
    「最后一帧会猛地向下弹一下 **锭本体保持一致 不要以闪光为基准**」

⚠ **第一版错在哪**（值得记）：我按"**哪一行有不透明像素**"分帧 —— 而闪光会跑到本体**上方**
（第 10 帧就是：闪光在 253..255、本体其实在 256..279）⇒ 那一帧的窗口被抬高了 3 行，
重排后本体落在 y=7..27 而不是 4..27 ⇒ **播放时最后一帧往下弹 3 像素**，正是用户看到的现象。
（分析见 `_zf119_align.py` / `_zf119_bodybands.py`。）

**这一版的口径**：**只按本体分行**（本体 = 低饱和的灰白像素；闪光 = 高饱和的黄）。
判定后本体是干净的 **10 段 × 24 行**：

    本体行段 = 0..23, 30..53, 58..81, 89..112, 117..140, 145..168, 173..196, 201..224, 229..252, **256..279**

重排规则（每帧 32×32）：

    dst 第 y 行  ←  源图第 (本体顶行 - 4 + y) 行      （越界 = 透明）

⇒ 10 帧的**本体**都落在 y=4..27（与盘上 `titanium_ingot.png` 的摆位一致），
   闪光仍旧在动（可以跑进上下那 4 行留白 —— 那本来就是留给它的），**本体一动不动**。

产出：
  `textures\item\vibranium_ingot.png`  32×320（10 帧）
  `textures\item\vibranium_ingot.png.mcmeta`  frametime = 3
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
REF = os.path.join(TEXI, u"titanium_ingot.png")
REPORT = os.path.join(ROOT, r"build\zftools\_zf119_texture.txt")

FRAME = 32
PAD_TOP = 4
CONTENT = 24
FRAMETIME = 3
N = 10

fails, notes = [], []


def is_shine(px):
    u"""闪光 = 高饱和的黄（本体是灰白，饱和度低）"""
    r, g, b, a = px
    if a == 0:
        return False
    mx, mn = max(r, g, b), min(r, g, b)
    return (mx - mn) >= 60 and r >= 120 and g >= 100 and b <= 160


def body_bands(w, h, buf):
    u"""**只按本体分行**（不算闪光）"""
    rows = [[buf[(y * w + x) * 4:(y * w + x) * 4 + 4] for x in range(w)] for y in range(h)]
    nbody = [sum(1 for px in row if px[3] > 0 and not is_shine(px)) for row in rows]
    bands, cur = [], None
    for y in range(h):
        if nbody[y] > 0 and cur is None:
            cur = y
        elif nbody[y] == 0 and cur is not None:
            bands.append((cur, y - 1))
            cur = None
    if cur is not None:
        bands.append((cur, h - 1))
    return bands, rows


def main():
    w, h, buf = read_png(SRC)
    notes.append(u"源：%s  %d×%d  sha1 %s"
                 % (os.path.basename(SRC), w, h,
                    hashlib.sha1(open(SRC, "rb").read()).hexdigest()[:12]))
    rw, rh, rbuf = read_png(REF)
    rrows = [[rbuf[(y * rw + x) * 4:(y * rw + x) * 4 + 4] for x in range(rw)] for y in range(rh)]
    rys = [y for y in range(rh) if any(px[3] > 0 for px in rrows[y])]
    notes.append(u"基准 titanium_ingot.png：%d×%d，内容 y=%d..%d（上留 %d / 下留 %d）"
                 % (rw, rh, min(rys), max(rys), min(rys), rh - 1 - max(rys)))
    if (rw, rh) != (FRAME, FRAME) or min(rys) != PAD_TOP:
        fails.append(u"基准贴图不是 %d×%d / 上留 %d —— 摆位依据变了" % (FRAME, FRAME, PAD_TOP))

    bands, rows = body_bands(w, h, buf)
    notes.append(u"本体行段（%d 段）：%s" % (len(bands), [u"%d..%d" % b for b in bands]))
    heights = [b - a + 1 for a, b in bands]
    if len(bands) != N:
        fails.append(u"本体段数 %d ≠ %d" % (len(bands), N))
    if set(heights) != {CONTENT}:
        fails.append(u"本体段高不全是 %d：%s" % (CONTENT, heights))
    if fails:
        print(u"\n".join(u"  [OK] " + n for n in notes))
        print(u"\n失败项 = %d" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1

    # 覆盖性检查：源图里**每一行的内容**都必须至少进到一帧的窗口里（不许丢内容）
    # ⚠ 两帧的本体可以只隔 3 行（第 8 帧 229..252 / 第 9 帧 256..279）⇒ 它们的 32 行窗口会**重叠**，
    #   于是同一行会进到两帧里 —— 这是**有意的**（重叠处正是闪光跨帧的那几行，剪掉反而会跳）。
    #   所以这里不检查"某帧的闪光有没有跑出自己的 32 行"，只检查"源图内容一行都没漏"。
    covered = set()
    for k, (a, b) in enumerate(bands):
        covered.update(range(max(0, a - PAD_TOP), min(h, b + 1 + PAD_TOP)))
    missed = [y for y in range(h)
              if any(px[3] > 0 for px in rows[y]) and y not in covered]
    if missed:
        print(u"\n".join(u"  [OK] " + n for n in notes))
        print(u"\n失败项 = 1")
        print(u"  !! 源图里有 %d 行内容没进任何一帧的窗口：%s" % (len(missed), missed[:8]))
        return 1

    # ---------- 重排 ----------
    # ⚠ 相邻两帧的本体可以只隔 3 行（229..252 与 256..279）⇒ 32 行窗口会互相"咬"进对方的**本体**一行。
    #   所以每帧的窗口要**夹在本帧本体与邻居本体之间**：
    #       lo = max(本体顶 - 4,  上一帧本体底 + 1)
    #       hi = min(本体底 + 4,  下一帧本体顶 - 1)
    #   夹完之后：本体永远落在 y=4..27（对齐！），而闪光跨帧的那几行仍旧进得来。
    out_h = FRAME * N
    out = bytearray(FRAME * out_h * 4)
    clip = []
    for k, (a, b) in enumerate(bands):
        lo = max(a - PAD_TOP, bands[k - 1][1] + 1 if k > 0 else 0)
        hi = min(b + PAD_TOP, bands[k + 1][0] - 1 if k + 1 < N else h - 1)
        clip.append((lo, hi))
        for y in range(FRAME):
            sy = a - PAD_TOP + y
            if sy < lo or sy > hi:
                continue
            for x in range(w):
                px = rows[sy][x]
                i = ((k * FRAME + y) * FRAME + x) * 4
                out[i:i + 4] = bytes(px)
    notes.append(u"每帧窗口（源图行）夹在邻居本体之间：%s"
                 % [u"%d..%d" % c for c in clip])
    write_png(DST, FRAME, out_h, out)
    notes.append(u"写出 %s：%d×%d（%d 帧 × %d）%d B"
                 % (os.path.basename(DST), FRAME, out_h, N, FRAME, os.path.getsize(DST)))
    meta = {u"animation": {u"frametime": FRAMETIME}}
    io.open(MCMETA, "w", encoding="utf-8", newline=u"").write(
        json.dumps(meta, ensure_ascii=False, indent=2) + u"\n")
    notes.append(u"写出 %s：%s" % (os.path.basename(MCMETA), json.dumps(meta, ensure_ascii=False)))

    # ---------- 回读断言 ----------
    bw, bh, bbuf = read_png(DST)
    brows = [[bbuf[(y * bw + x) * 4:(y * bw + x) * 4 + 4] for x in range(bw)] for y in range(bh)]
    if (bw, bh) != (FRAME, out_h):
        fails.append(u"回读尺寸 %d×%d 不对" % (bw, bh))
        return 1
    # ① 每帧逐像素 == 源图对应行（窗口外的行 = 透明）
    diff = []
    for k, (a, b) in enumerate(bands):
        lo, hi = clip[k]
        for y in range(FRAME):
            sy = a - PAD_TOP + y
            if 0 <= sy < h and lo <= sy <= hi:
                want = rows[sy]
            else:
                want = [b"\0\0\0\0"] * w
            if brows[k * FRAME + y] != want:
                diff.append((k, y))
                break
    if diff:
        fails.append(u"回读像素与源图不一致：%s" % diff[:5])
    else:
        notes.append(u"回读：%d 帧 × %d 行 **逐像素等于源图对应行**（窗口外 = 透明）" % (N, FRAME))
    # ② 每帧的**本体** bbox 必须完全一致（用户的要求：锭本体保持一致）
    tops, cols, spans = [], [], []
    for k in range(N):
        pts = [(y, x) for y in range(FRAME) for x in range(FRAME)
               if brows[k * FRAME + y][x][3] > 0 and not is_shine(brows[k * FRAME + y][x])]
        tops.append(min(p[0] for p in pts))
        cols.append((min(p[1] for p in pts), max(p[1] for p in pts)))
        spans.append((min(p[0] for p in pts), max(p[0] for p in pts)))
    if len(set(tops)) != 1 or len(set(spans)) != 1:
        fails.append(u"10 帧的本体**没有**对齐：顶行 %s / 行范围 %s" % (tops, spans))
    else:
        notes.append(u"本体对齐：%d 帧全部落在 y=%d..%d（顶行 %s），列 %s"
                     % (N, spans[0][0], spans[0][1], tops[0], cols[0]))
    eqd = (spans[0] == (PAD_TOP, PAD_TOP + CONTENT - 1))
    if not eqd:
        fails.append(u"本体不在 y=%d..%d（实际 %s）" % (PAD_TOP, PAD_TOP + CONTENT - 1, spans[0]))
    else:
        notes.append(u"本体与基准摆位一致：y=%d..%d（照 titanium_ingot）" % (PAD_TOP, PAD_TOP + CONTENT - 1))
    # ③ 闪光仍要动
    shinetops = []
    for k in range(N):
        pts = [y for y in range(FRAME) for x in range(FRAME)
               if is_shine(brows[k * FRAME + y][x])]
        shinetops.append(min(pts) if pts else None)
    uniq = len(set(shinetops))
    if uniq < 3:
        fails.append(u"闪光几乎没动（顶行只有 %d 种）—— 动画看着会像静止" % uniq)
    else:
        notes.append(u"闪光位移：顶行 %s（%d 种 ⇒ 确实在动）" % (shinetops, uniq))
    # ④ 帧与帧不同（整体）
    same_pairs = sum(1 for k in range(N - 1)
                     if all(brows[k * FRAME + y] == brows[(k + 1) * FRAME + y] for y in range(FRAME)))
    if same_pairs > 2:
        fails.append(u"相邻帧完全相同的对数 %d > 2" % same_pairs)
    notes.append(u"时长账：%d 帧 × %d tick = %d tick = %.2f 秒一轮"
                 % (N, FRAMETIME, N * FRAMETIME, N * FRAMETIME / 20.0))

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    io.open(REPORT, "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(notes) + u"\n\n失败项 = %d\n" % len(fails)
        + u"\n".join(u"  !! " + f for f in fails) + u"\n")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
