# -*- coding: utf-8 -*-
"""_zf154_look.py —— 采油机：新素材 vs 现有六面贴图（只读 + 报告）

用户原话：「采油机的放素材了」
素材 `采油机顶部和底部_001.png` —— 文件名点明是**顶面与底面**。

现状：`models/block/oil_pump.json` 是 `parent: cube_all`，
**六个面都取同一张 `block/oil_pump.png`（151 B 的程序生成占位）**。
⇒ 这与 ZF130 处理「锂电池构造器 / 柴油发电机控制器」时**同一个形状的问题**。
"""
import hashlib
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

U = r"E:\PotatoST\build\用户素材"
T = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"
OUT = r"E:\PotatoST\build\zftools\_zf154_look.txt"
RAMP = " .:-=+*#%@"

lines = []


def say(s=u""):
    lines.append(s)
    print(s)


def dump(label, path):
    if not os.path.exists(path):
        say(u"  %s：（不存在）" % label)
        return
    blob = open(path, "rb").read()
    w, h, rgba = read_png(path)
    a = np.array(rgba, dtype=np.uint8).reshape(h, w, 4)
    op = int((a[:, :, 3] == 255).sum())
    tr = int((a[:, :, 3] == 0).sum())
    cols = {}
    for y in range(h):
        for x in range(w):
            if a[y, x, 3] == 0:
                continue
            k = tuple(int(v) for v in a[y, x, :3])
            cols[k] = cols.get(k, 0) + 1
    mean = tuple(int(v) for v in a[a[:, :, 3] == 255][:, :3].mean(axis=0)) if op else (0, 0, 0)
    say(u"  %s" % label)
    say(u"    %s  %d B  sha1 %s" % (os.path.basename(path), len(blob),
                                    hashlib.sha1(blob).hexdigest()[:12]))
    say(u"    %dx%d 位深 %d 类型 %d" % (w, h, blob[24], blob[25]))
    say(u"    alpha：不透明 %d / 全透明 %d / 半透明 %d"
        % (op, tr, w * h - op - tr))
    say(u"    颜色数 %d  平均色 #%02x%02x%02x" % (len(cols), mean[0], mean[1], mean[2]))
    say(u"    主色 top6: " + ", ".join("#%02x%02x%02x x%d" % (k[0], k[1], k[2], v)
                                      for k, v in sorted(cols.items(), key=lambda kv: -kv[1])[:6]))
    say(u"    字符画：")
    lum = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
    for y in range(h):
        row = []
        for x in range(w):
            row.append(u" " if a[y, x, 3] == 0 else
                       RAMP[min(len(RAMP) - 1, int(lum[y, x] / 255.0 * (len(RAMP) - 1)))])
        say(u"      |" + u"".join(row) + u"|")


say(u"=" * 74)
say(u"① 用户给的素材（文件名点明「顶部和底部」）")
dump(u"顶/底素材", os.path.join(U, u"采油机顶部和底部_001.png"))
say()
say(u"=" * 74)
say(u"② 现有六面贴图（cube_all 的 all）")
dump(u"在用 oil_pump.png", os.path.join(T, "oil_pump.png"))

open(OUT, "w", encoding="utf-8").write(u"\n".join(lines))
print(u"\n[报告] %s" % OUT)
