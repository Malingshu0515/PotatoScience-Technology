# -*- coding: utf-8 -*-
"""_zf116_intake.py —— ZF116 收件体检：三件星璨钢盔甲（只读 + 写报告）

用户第二次说「又放了」。本轮候选 3 件（都在 build/用户素材/）：
  星璨钢胸甲.png / 星璨钢护腿.png / 星璨钢靴子.png
与上一轮同规格，走同一套体检：真实格式 / 尺寸 / 位深 / alpha 分布 / 主色 / 字符画。
"""
import hashlib
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

USERART = r"E:\PotatoST\build\用户素材"
TOOLS = r"E:\PotatoST\build\zftools"
TEXI = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item"
OUT = os.path.join(TOOLS, "_zf116_intake.txt")

CANDIDATES = ["星璨钢胸甲.png", "星璨钢护腿.png", "星璨钢靴子.png"]
RAMP = " .:-=+*#%@"


def ascii_art(w, h, rgba):
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
    lines = ["# ZF116 收件体检（三件星璨钢盔甲）", ""]
    for name in CANDIDATES:
        p = os.path.join(USERART, name)
        lines.append("=" * 74)
        lines.append("文件 : %s" % name)
        if not os.path.exists(p):
            lines.append("  !! 不存在")
            lines.append("")
            continue
        blob = open(p, "rb").read()
        real_png = blob[:8] == b"\x89PNG\r\n\x1a\n"
        lines.append("  字节 %d   sha1 %s   **真 PNG = %s**"
                     % (len(blob), hashlib.sha1(blob).hexdigest(), real_png))
        if not real_png:
            lines.append("  !! 不是 PNG（扩展名骗人，§4.23）")
            lines.append("")
            continue
        w, h, rgba = read_png(p)
        n = w * h
        opaque = sum(1 for i in range(n) if rgba[i * 4 + 3] == 255)
        trans = sum(1 for i in range(n) if rgba[i * 4 + 3] == 0)
        semi = n - opaque - trans
        colors = {}
        sr = sg = sb = 0
        for i in range(n):
            if rgba[i * 4 + 3] == 0:
                continue
            k = (rgba[i * 4], rgba[i * 4 + 1], rgba[i * 4 + 2])
            colors[k] = colors.get(k, 0) + 1
            sr += k[0]; sg += k[1]; sb += k[2]
        c = max(1, sum(colors.values()))
        mean = (sr // c, sg // c, sb // c)
        top = sorted(colors.items(), key=lambda kv: -kv[1])[:6]
        lines.append("  位深 %d  色彩类型 %d  尺寸 %dx%d" % (blob[24], blob[25], w, h))
        lines.append("  alpha：不透明 %d / 全透明 %d / **半透明 %d**" % (opaque, trans, semi))
        lines.append("  颜色数 %d   平均色 RGB%s #%02x%02x%02x"
                     % (len(colors), mean, mean[0], mean[1], mean[2]))
        lines.append("  主色 top6 " + ", ".join("#%02x%02x%02x x%d" % (k[0], k[1], k[2], v)
                                             for k, v in top))
        lines.append("  字符画：")
        for row in ascii_art(w, h, rgba):
            lines.append("    |" + row + "|")
        lines.append("")

    lines.append("=" * 74)
    lines.append("## 对照：上一轮已上线的星璨钢头盔")
    hp = os.path.join(TEXI, "star_steel_helmet.png")
    if os.path.exists(hp):
        b = open(hp, "rb").read()
        w, h, rgba = read_png(hp)
        op = sum(1 for i in range(w * h) if rgba[i * 4 + 3] == 255)
        lines.append("  star_steel_helmet.png  %d B  %dx%d  不透明 %d  sha1 %s"
                     % (len(b), w, h, op, hashlib.sha1(b).hexdigest()[:12]))

    text = "\n".join(lines)
    open(OUT, "w", encoding="utf-8").write(text)
    print(text)
    print("\n[报告] %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
