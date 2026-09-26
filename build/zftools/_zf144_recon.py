# -*- coding: utf-8 -*-
r'''_zf144_recon.py —— 只读：锹那张素材的身份 + 原版锹的写法（不靠文件名、不靠记忆）

用户原话：「锹现在放用户素材了」⇒ 素材区新出现 `星璨铲子.png`。
要钉两件事：
  ① 它是不是**锹**（α 掩码与原版六档 × 五种工具算 IoU，取最大）；
  ② 原版**锹**的属性写法与参数（`Items.java` 里那一行 + `DiggerItem.createAttributes`），
     并把它与镐并排摆出来（原版锹 = 镐 + 0.5 点伤害，本轮要决定是否沿用这个相对关系）。

跑法：python build\zftools\_zf144_recon.py
'''
import io
import os
import struct
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJ = r"E:\PotatoST"
USER = os.path.join(PROJ, "build", u"用户素材")
CLIENT_EXTRA = (r"E:\gradle-home\caches\ng_execute"
                r"\b618213606478f4c62e6974e895a173b103a054e4a7be1bf630f2feeb65c5c3b"
                r"\client-extra.jar")
SOURCES = os.path.join(PROJ, "build", "neoForm",
                       "neoFormJoined1.21.1-20240808.144430", "sources.jar")
OUT = os.path.join(PROJ, "build", "zftools", "_zf144_recon.txt")

sys.path.insert(0, os.path.join(PROJ, "build", "zftools"))
import _zf141_recon as R  # 复用那一份 PNG 解码 + IoU（它只有 __main__ 才写文件）

lines = []


def w(s=u""):
    lines.append(s)


def main():
    # ---------------- ① 身份 ----------------
    w(u"=" * 78)
    w(u"① 新素材的身份：形状 IoU（vs 原版六档 × 五种工具，共 30 张）")
    w(u"=" * 78)
    with zipfile.ZipFile(CLIENT_EXTRA) as zf:
        van = {}
        for mat in R.VANILLA_TOOLS:
            for kind in R.TOOL_KINDS:
                p = u"assets/minecraft/textures/item/%s_%s.png" % (mat, kind)
                try:
                    _w, _h, px = R.read_zip_png(zf, p)
                except KeyError:
                    continue
                van[(mat, kind)] = R.alpha_mask(px)
        for fname, guess in ((u"星璨铲子.png", u"shovel"),):
            path = os.path.join(USER, fname)
            if not os.path.isfile(path):
                w(u"!! 素材不在：%s" % path)
                continue
            raw = open(path, "rb").read()
            iw, ih, ipx = R.decode_png(raw)
            mask = R.alpha_mask(ipx)
            scores = sorted(((R.iou(mask, m), k[0], k[1]) for k, m in van.items()
                             if len(m) == len(mask)), reverse=True)
            w(u"【%s】 %dx%d  非空像素 %d  字节 %d  文件名猜=%s"
              % (fname, iw, ih, sum(mask), len(raw), guess))
            for s, mat, kind in scores[:5]:
                mark = u"  <== 文件名猜的" if kind == guess else u""
                w(u"    IoU %.4f  原版 %-9s %-8s%s" % (s, mat, kind, mark))
            w(u"    ⇒ 形状最像：%s_%s（IoU %.4f）" % (scores[0][1], scores[0][2], scores[0][0]))
            # 顺手把"最像的类别"的分布也打出来（防"第一第二就差一点点"）
            best = {}
            for s, mat, kind in scores:
                best.setdefault(kind, s)
            w(u"    各类别的最好成绩：%s"
              % u"  ".join(u"%s=%.4f" % (k, v) for k, v in sorted(best.items(),
                                                                  key=lambda kv: -kv[1])))

    # ---------------- ② 原版锹 ----------------
    w(u"")
    w(u"=" * 78)
    w(u"② 原版锹：属性那一行 + 与镐的相对关系（sources.jar 现抠）")
    w(u"=" * 78)
    with zipfile.ZipFile(SOURCES) as zf:
        names = set(zf.namelist())
        src = zf.read([n for n in names if n.endswith(u"net/minecraft/world/item/Items.java")][0]
                      ).decode(u"utf-8", u"replace")
        for i, line in enumerate(src.split(u"\n"), 1):
            s = line.strip()
            if (u"new ShovelItem(" in s or u"new PickaxeItem(" in s) and u"DIAMOND" in s:
                w(u"  Items.java %5d | %s" % (i, s))
        tier = zf.read([n for n in names if n.endswith(u"net/minecraft/world/item/Tiers.java")][0]
                       ).decode(u"utf-8", u"replace")
        for line in tier.split(u"\n"):
            if u"DIAMOND(" in line:
                w(u"  Tiers.java        | %s" % line.strip())

    # ---------------- ③ 盘上现状 ----------------
    w(u"")
    w(u"=" * 78)
    w(u"③ 盘上现状：星璨钢这一档现有的四个数（本轮只加不变量）")
    w(u"=" * 78)
    t = io.open(os.path.join(PROJ, r"src\main\java\com\potatost\mod\ModTiers.java"),
                encoding="utf-8").read()
    for line in t.split(u"\n"):
        if u"STAR_STEEL_" in line and u"public static final" in line:
            w(u"  " + line.strip())

    io.open(OUT, "w", encoding="utf-8", newline="\n").write(u"\n".join(lines) + u"\n")
    sys.stdout.write(u"\n".join(lines) + u"\n")
    print(u"\n（已写 %s）" % OUT)


main()
