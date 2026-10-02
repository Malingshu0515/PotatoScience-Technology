# -*- coding: utf-8 -*-
"""_zf132_anim.py —— ZF132：给**柴油 / 汽油 / 原油**做流体动态贴图

用户原话：「现在流体都没有动态贴图 你看看能不能做 只做柴油 汽油 原油 就可以啦」

## 规则（从 client-extra.jar 现抠，不是记忆）

| 项 | 原版做法（实测） |
|---|---|
| 动画格式 | `<贴图>.png.mcmeta`，`{"animation": {...}}`；贴图本身是**竖排帧序列**（高 = 帧宽 × 帧数） |
| 水 `water_still` | 32 帧、`"frametime": 2` |
| 岩浆 `lava_still` | 20 帧 + **ping-pong `frames` 数组**、`"frametime": 2` |
| 本工程已有样板 | `textures/item/vibranium_ingot.png` = **32×320 / 10 帧** + `{"frametime": 3}` |

## ⚠ 动法：试过"每行错位"（剪切），对**原油**不适用

第一版用的是每行横向错位 `shift(y,t) = A·sin(2π(y/H + t/N))`：
横向着色完美（环绕跳变 ÷ 帧内平均跳变 ≈ 1.0），但**原油的上下比值 2.7~2.8**
（判据见 `_zf132_seam.py`：环绕跳变 ≤ 帧内平均跳变才叫无缝）。
根因：原油源图**行间自相关是负的**（`_zf132_look.py` 实测 -0.343），
再叠上剪切造成的行间疏密不均 ⇒ "第 15 行 ↔ 第 0 行"这一对比帧内平均明显突兀。

**改用整体竖向滚动**：每一帧把整幅往下平移 `k` 行（环绕）。纯粹平移的好处是
**环绕处就是一对普通相邻行**，不需要任何额外论证 —— 它天然与图内其它行等价。
`k=1` 给 `_still`（16 帧，慢），`k=2` 给 `_flow`（16 帧、周期 8，快一倍）。
"""
import io
import json
import os
import struct
import sys
import zlib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

T = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"
FRAMES = 16
FRAMETIME = 3

# (名字, 每帧下移几行)
JOBS = [
    ("diesel_still", 1),
    ("diesel_flow", 2),
    ("gasoline_still", 1),
    ("gasoline_flow", 2),
    ("crude_oil_still", 1),
    ("crude_oil_flow", 2),
]

fails = []


def png_encode(w, h, rows):
    raw = b"".join(b"\x00" + r for r in rows)

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    # 第 7 字节 interlace = 0（不隔行）—— PngRecolor 只读不隔行的
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def main():
    print(u"帧数 %d / frametime %d（一轮 %.1f s）—— 整体竖向滚动" %
          (FRAMES, FRAMETIME, FRAMES * FRAMETIME / 20.0))
    for name, k in JOBS:
        src = os.path.join(T, name + ".png")
        if not os.path.exists(src):
            fails.append(u"缺 %s" % src)
            print(u"  !! 缺 %s" % src)
            continue
        w, h, rgba = read_png(src)
        before = open(src, "rb").read()
        if (w, h) != (16, 16):
            fails.append(u"%s 源不是 16x16（%dx%d）" % (name, w, h))
            continue
        if any(rgba[i * 4 + 3] != 255 for i in range(w * h)):
            fails.append(u"%s 源里有非不透明像素" % name)

        base = [bytes(rgba[(y * w) * 4:(y * w + w) * 4]) for y in range(h)]
        rows = []
        for f in range(FRAMES):
            for y in range(h):
                rows.append(base[(y - f * k) % h])      # 整体下移 f*k 行（环绕）
        out = png_encode(w, h * FRAMES, rows)
        dst = os.path.join(T, name + ".png")
        io.open(dst, "wb").write(out)
        meta = os.path.join(T, name + ".png.mcmeta")
        io.open(meta, "w", encoding="utf-8", newline="\n").write(
            json.dumps({"animation": {"frametime": FRAMETIME}}, indent=2) + "\n")

        # ---------- 回读自证 ----------
        w2, h2, back = read_png(dst)
        if (w2, h2) != (16, 16 * FRAMES):
            fails.append(u"%s 回读尺寸 %dx%d" % (name, w2, h2))
        bad = 0
        for f in range(FRAMES):
            for y in range(16):
                got = bytes(back[((f * 16 + y) * 16) * 4:((f * 16 + y) * 16 + 16) * 4])
                want = base[(y - f * k) % 16]
                if got != want:
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
            fails.append(u"%s 的 mcmeta frametime 不对" % name)

        print(u"  %-18s 每帧下移 %d 行  %d B -> %d B + mcmeta %d B  回读 %dx%d  "
              u"逐行验算差 %d  首末帧差 %d px"
              % (name, k, len(before), len(out), os.path.getsize(meta), w2, h2, bad, diff))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
