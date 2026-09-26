# -*- coding: utf-8 -*-
r"""_zf141_tex.py —— 上线四张贴图（三新一换），**逐字节**复制 + 回读核哈希。

用户原话：「贴图在用户素材 刚才忘说了」。素材区现有四张跟本轮有关的图：
  星璨钢剑.png            → textures/item/star_steel_sword.png     （新）
  星镐子_001.png          → textures/item/star_steel_pickaxe.png   （新）
  星锄子_001.png          → textures/item/star_steel_hoe.png       （新）
  星璨钢斧子新贴图.png    → textures/item/star_steel_axe.png        （**顶掉 ZF133 那张**）

⚠ 第四张是"换皮"不是"新增"：用户素材区里的 `星璨钢斧.png`（ZF133 的源件、sha1 8f5de358…）
  **已经不在了**，取而代之的是 `星璨钢斧子新贴图.png` —— 用户是拿它来**换**斧子那张图的。
  这是本轮唯一一处"改已在用产物"，所以：
    ① 先核"我要顶掉的那张"到底是不是 ZF133 上线的那张（sha1 对不上就停手）；
    ② 被顶掉那份在 `zf141_pre` 里有逐字节备份（`_zf141_backup.py` 已存）。

跑法：python build\zftools\_zf141_tex.py
"""
import hashlib
import io
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

# (素材名, 落盘名, 期望的旧 sha1（None = 新文件不该存在）)
JOBS = [
    (u"星璨钢剑.png", u"star_steel_sword.png", None),
    (u"星镐子_001.png", u"star_steel_pickaxe.png", None),
    (u"星锄子_001.png", u"star_steel_hoe.png", None),
    (u"星璨钢斧子新贴图.png", u"star_steel_axe.png",
     u"8f5de358857e6fc2e5a0886503308b030d667455"),
]

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def png_size(data):
    u"""从 IHDR 现读宽高（第 16..24 字节）—— 只做"是不是 16x16"这一条断言。"""
    assert data[:8] == b"\x89PNG\r\n\x1a\n", u"不是 PNG"
    assert data[12:16] == b"IHDR", u"不是 IHDR 开头"
    w, h = struct.unpack(">II", data[16:24])
    return w, h


def main():
    lines = []
    for src_name, dst_name, expect_old in JOBS:
        src = os.path.join(USER, src_name)
        dst = os.path.join(ITEM, dst_name)
        if not os.path.isfile(src):
            fails.append(u"素材不在：%s" % src)
            continue
        raw = open(src, "rb").read()
        w, h = png_size(raw)
        s_src = hashlib.sha1(raw).hexdigest()

        old_note = u"（新文件）"
        if os.path.isfile(dst):
            s_old = sha1(dst)
            if expect_old is None:
                fails.append(u"%s 已经存在（本轮该是新建）sha1=%s" % (dst_name, s_old))
                continue
            if s_old != expect_old:
                fails.append(u"%s 盘上那份不是 ZF133 上线的那张：期望 %s，实际 %s "
                             u"⇒ 停手，不敢顶" % (dst_name, expect_old, s_old))
                continue
            old_note = u"（顶掉 %s）" % s_old[:12]
        elif expect_old is not None:
            fails.append(u"%s 不在盘上，但本轮期望顶掉 %s" % (dst_name, expect_old[:12]))
            continue

        shutil.copy2(src, dst)
        s_dst = sha1(dst)
        if s_dst != s_src:
            fails.append(u"%s 回读哈希不一致" % dst_name)
            continue
        lines.append(u"  %-26s ← %-24s %dx%d  sha1=%s  %s"
                     % (dst_name, src_name, w, h, s_dst[:12], old_note))
        if (w, h) != (16, 16):
            fails.append(u"%s 不是 16x16，是 %dx%d" % (dst_name, w, h))

    print(u"贴图上线：")
    for l in lines:
        print(l)
    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
