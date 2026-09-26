# -*- coding: utf-8 -*-
r'''_zf144_tex.py —— 上线锹那张贴图（逐字节复制 + 回读核哈希）。

用户原话：「锹现在放用户素材了」⇒ 素材区新增 `星璨铲子.png`（16x16 / 3044 B）。
身份已由 `_zf144_recon.py` 核实：α 掩码与原版六档**锹**的 IoU 均为 **0.9815**
（第二名锄 0.6154、斧 0.6056、镐 0.5250、剑 0.4375）⇒ 就是锹，没有歧义。

跑法：python build\zftools\_zf144_tex.py
'''
import hashlib
import os
import shutil
import struct
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
USER = os.path.join(PROJ, "build", u"用户素材")
ITEM = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t",
                    "textures", "item")

JOBS = [(u"星璨铲子.png", u"star_steel_shovel.png", None)]

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def png_size(data):
    assert data[:8] == b"\x89PNG\r\n\x1a\n", u"不是 PNG"
    assert data[12:16] == b"IHDR", u"不是 IHDR 开头"
    return struct.unpack(">II", data[16:24])


def main():
    for src_name, dst_name, expect_old in JOBS:
        src = os.path.join(USER, src_name)
        dst = os.path.join(ITEM, dst_name)
        if not os.path.isfile(src):
            fails.append(u"素材不在：%s" % src)
            continue
        raw = open(src, "rb").read()
        w, h = png_size(raw)
        s_src = hashlib.sha1(raw).hexdigest()
        if os.path.isfile(dst) and expect_old is None:
            fails.append(u"%s 已经存在（本轮该是新建）" % dst_name)
            continue
        shutil.copy2(src, dst)
        if sha1(dst) != s_src:
            fails.append(u"%s 回读哈希不一致" % dst_name)
            continue
        print(u"  %-26s ← %-20s %dx%d  sha1=%s" % (dst_name, src_name, w, h, s_src[:12]))
        if (w, h) != (16, 16):
            fails.append(u"%s 不是 16x16，是 %dx%d" % (dst_name, w, h))
    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
