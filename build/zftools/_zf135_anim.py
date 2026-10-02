# -*- coding: utf-8 -*-
"""_zf135_anim.py —— ZF135：给**其余 12 种流体**补动态贴图

用户原话：「都加上动态吧吧 不过在此之前把用户素材里没有的可以都删一下」

动法与 ZF132 完全一致（**整体竖向滚动**，理由见 `_zf132_anim.py` 的模块注释）：
  · `_still` 每帧下移 1 行、`_flow` 每帧下移 2 行；
  · 各 16 帧、`frametime 3`；
  · 纯平移 ⇒ 环绕处就是一对普通相邻行，天然无缝。

同时补齐 ZF132 漏做的一件事：**`_flow` 是独立文件**（引擎真的会用它，
`IClientFluidTypeExtensions#getFlowingTexture` 指的就是它）。
ZF132 那三种的 flow 与 still 内容相同，所以当时两套都做了；
这一批里 **carbon_dioxide 的 flow 与 still 本来就不同**（209 B vs 121 B，ZF100 特意画了流动版）
⇒ 必须**各自以自己为源**，不能拿 still 去覆盖 flow。
"""
import io
import json
import os
import sys
import zlib
import struct

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

T = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"
FRAMES = 16
FRAMETIME = 3

# 其余 12 种（ZF132 已做 diesel / gasoline / crude_oil）
FLUIDS = ["oxygen", "hydrogen", "chlorine", "nitrogen", "ammonia", "carbon_dioxide",
          "lpg", "naphtha", "carbonic_acid", "nitric_acid", "sulfuric_acid",
          "hydrochloric_acid"]

fails = []


def png_encode(w, h, rows):
    raw = b"".join(b"\x00" + r for r in rows)

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def animate(name, k):
    """把 <name>.png 就地变成 16 帧动画（k = 每帧下移行数）"""
    src = os.path.join(T, name + ".png")
    w, h, rgba = read_png(src)
    if (w, h) != (16, 16):
        fails.append(u"%s 不是 16x16（%dx%d）—— 可能已经动画过" % (name, w, h))
        return None
    if any(rgba[i * 4 + 3] != 255 for i in range(w * h)):
        fails.append(u"%s 有非不透明像素" % name)
    before = open(src, "rb").read()
    base = [bytes(rgba[(y * w) * 4:(y * w + w) * 4]) for y in range(h)]
    rows = []
    for f in range(FRAMES):
        for y in range(h):
            rows.append(base[(y - f * k) % h])
    out = png_encode(w, h * FRAMES, rows)
    io.open(src, "wb").write(out)
    meta = src + ".mcmeta"
    io.open(meta, "w", encoding="utf-8", newline="\n").write(
        json.dumps({"animation": {"frametime": FRAMETIME}}, indent=2) + "\n")

    # 回读自证
    w2, h2, back = read_png(src)
    bad = 0
    if (w2, h2) != (16, 16 * FRAMES):
        fails.append(u"%s 回读尺寸 %dx%d" % (name, w2, h2))
    for f in range(FRAMES):
        for y in range(16):
            got = bytes(back[((f * 16 + y) * 16) * 4:((f * 16 + y) * 16 + 16) * 4])
            if got != base[(y - f * k) % 16]:
                bad += 1
    if bad:
        fails.append(u"%s 有 %d 行与预期位移不符" % (name, bad))
    f0 = bytes(back[0:16 * 16 * 4])
    fN = bytes(back[(FRAMES - 1) * 16 * 16 * 4:FRAMES * 16 * 16 * 4])
    diff = sum(1 for i in range(0, len(f0), 4) if f0[i:i + 4] != fN[i:i + 4])
    if diff == 0:
        fails.append(u"%s 首末帧一模一样（没动）" % name)
    m = json.loads(io.open(meta, encoding="utf-8").read())
    if m.get("animation", {}).get("frametime") != FRAMETIME:
        fails.append(u"%s 的 mcmeta 不对" % name)
    return len(before), len(out), bad, diff


def main():
    print(u"其余 %d 种流体 × 2 张（still/flow）= %d 张" % (len(FLUIDS), len(FLUIDS) * 2))
    print(u"帧数 %d / frametime %d\n" % (FRAMES, FRAMETIME))
    print(u"  %-22s %-6s %10s %10s %6s %7s" %
          (u"贴图", u"下移", u"源", u"成品", u"验算差", u"首末帧差"))
    for fl in FLUIDS:
        for suffix, k in (("_still", 1), ("_flow", 2)):
            name = fl + suffix
            p = os.path.join(T, name + ".png")
            if not os.path.exists(p):
                fails.append(u"缺 %s" % name)
                print(u"  %-22s !! 缺文件" % name)
                continue
            r = animate(name, k)
            if r is None:
                print(u"  %-22s !! 跳过（见失败项）" % name)
                continue
            b, a, bad, diff = r
            print(u"  %-22s %-6d %9dB %9dB %6d %7d" % (name, k, b, a, bad, diff))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
