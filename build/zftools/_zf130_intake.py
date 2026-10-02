# -*- coding: utf-8 -*-
"""_zf117_intake.py —— ZF117 收件体检（只读 + 写报告）

本轮 5 件：
  银线_001.png / 银线轴_001.png                    -> 物品（silver_wire / silver_wire_spool）
  锂电池构造器上和下面_001.png                      -> 方块顶+底
  柴油发电机控制器顶部&底部_001.png                  -> 方块顶+底
"""
import hashlib
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

USERART = r"E:\PotatoST\build\用户素材"
TOOLS = r"E:\PotatoST\build\zftools"
OUT = os.path.join(TOOLS, "_zf117_intake.txt")
RAMP = " .:-=+*#%@"

CANDIDATES = [
    "银线_001.png",
    "银线轴_001.png",
    "锂电池构造器上和下面_001.png",
    "柴油发电机控制器顶部&底部_001.png",
    "振金锭.png",
]


def art(w, h, rgba):
    rows = []
    for y in range(h):
        line = []
        for x in range(w):
            i = (y * w + x) * 4
            a = rgba[i + 3]
            if a == 0:
                line.append(" ")
                continue
            lum = (0.299 * rgba[i] + 0.587 * rgba[i + 1] + 0.114 * rgba[i + 2]) / 255.0
            line.append(RAMP[min(len(RAMP) - 1, int(lum * (len(RAMP) - 1)))])
        rows.append("".join(line))
    return rows


def main():
    L = [u"# ZF117 收件体检", u""]
    for name in CANDIDATES:
        p = os.path.join(USERART, name)
        L.append("=" * 74)
        L.append(u"文件 : %s" % name)
        if not os.path.exists(p):
            L.append(u"  !! 不存在")
            L.append("")
            continue
        blob = open(p, "rb").read()
        if blob[:8] != b"\x89PNG\r\n\x1a\n":
            L.append(u"  !! 不是 PNG（%d B，头 %s）—— 扩展名骗人（§4.23）"
                     % (len(blob), blob[:8].hex()))
            L.append("")
            continue
        w, h, rgba = read_png(p)
        n = w * h
        op = sum(1 for i in range(n) if rgba[i * 4 + 3] == 255)
        tr = sum(1 for i in range(n) if rgba[i * 4 + 3] == 0)
        sem = n - op - tr
        cols = {}
        sr = sg = sb = 0
        for i in range(n):
            if rgba[i * 4 + 3] == 0:
                continue
            k = (rgba[i * 4], rgba[i * 4 + 1], rgba[i * 4 + 2])
            cols[k] = cols.get(k, 0) + 1
            sr += k[0]; sg += k[1]; sb += k[2]
        c = max(1, sum(cols.values()))
        mean = (sr // c, sg // c, sb // c)
        top = sorted(cols.items(), key=lambda kv: -kv[1])[:5]
        L.append(u"  %d B   sha1 %s" % (len(blob), hashlib.sha1(blob).hexdigest()))
        L.append(u"  %dx%d  位深 %d  色彩类型 %d" % (w, h, blob[24], blob[25]))
        L.append(u"  alpha：不透明 %d / 全透明 %d / 半透明 %d" % (op, tr, sem))
        L.append(u"  颜色数 %d   平均色 #%02x%02x%02x" % (len(cols), mean[0], mean[1], mean[2]))
        L.append(u"  主色 " + ", ".join("#%02x%02x%02x x%d" % (k[0], k[1], k[2], v)
                                       for k, v in top))
        L.append(u"  字符画：")
        for r in art(w, h, rgba):
            L.append(u"    |" + r + u"|")
        L.append("")

    L.append("=" * 74)
    L.append(u"## 对照：这两个方块现在盘上的贴图")
    TEXB = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"
    for f in ["lithium_battery_plant.png", "diesel_generator_controller.png",
              "lithium_battery_top.png", "lithium_battery_side.png",
              "low_generator_top.png", "low_generator_side.png"]:
        fp = os.path.join(TEXB, f)
        if os.path.exists(fp):
            b = open(fp, "rb").read()
            try:
                w, h, _ = read_png(fp)
                spec = "%dx%d" % (w, h)
            except Exception:
                spec = "?"
            L.append(u"  %-34s %6d B  %s" % (f, len(b), spec))
        else:
            L.append(u"  %-34s （不存在）" % f)

    text = "\n".join(L)
    open(OUT, "w", encoding="utf-8").write(text)
    print(text)
    print("\n[报告] %s" % OUT)


if __name__ == "__main__":
    sys.exit(main() or 0)
