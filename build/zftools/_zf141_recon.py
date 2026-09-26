# -*- coding: utf-8 -*-
r"""ZF141 侦察（**只读，一个字节都不改**）：把"原版事实"从盘上的 jar 现抠出来，不靠记忆。

本轮要做的是**星璨钢剩下几把工具**（用户给的四张素材：星璨钢剑 / 星镐子 / 星锄子 / 星璨钢斧子新贴图）。
开工前必须先钉死两件事，否则后面全是"我以为"：

  ① **哪张素材对应哪件工具** —— 素材文件名是中文（剑 / 镐子 / 锄子 / 斧子），
     但"锄"和"锹"、"镐"和"斧"在 16x16 上肉眼并不保险。判据用**形状**：
     把素材的 alpha 掩码与原版五把工具贴图的 alpha 掩码逐个算 **IoU**，
     取最大值那件 —— 形状是"这件东西画的是什么"的客观证据（ZF136 认锭时用的同一招）。
  ② **原版五把工具的属性写法与参数** —— 从 `sources.jar`（NeoForge 反编译产物）现抠
     `createAttributes(...)` 那一行，参数逐字抄，绝不凭记忆写 1.5 / 3.0 这种数。

跑法：python build\zftools\_zf141_recon.py
产出：_zf141_recon.txt（UTF-8，给人看）+ 控制台同一份
"""

import io
import os
import re
import struct
import sys
import zipfile

PROJ = r"E:\PotatoST"
ZFTOOLS = os.path.join(PROJ, "build", "zftools")
USER_ASSETS = os.path.join(PROJ, "build", u"\u7528\u6237\u7d20\u6750")
ITEM_TEX = os.path.join(PROJ, "src", "main", "resources", "assets",
                        "potato_s_t", "textures", "item")

CLIENT_EXTRA = (r"E:\gradle-home\caches\ng_execute"
                r"\b618213606478f4c62e6974e895a173b103a054e4a7be1bf630f2feeb65c5c3b"
                r"\client-extra.jar")
SOURCES_JAR = os.path.join(PROJ, "build", "neoForm",
                           "neoFormJoined1.21.1-20240808.144430", "sources.jar")

OUT = []
OUTF = io.open(os.path.join(ZFTOOLS, "_zf141_recon.txt"), "w",
               encoding="utf-8", newline="\n")


def w(line=u""):
    OUT.append(line)


def flush():
    text = u"\n".join(OUT) + u"\n"
    OUTF.write(text)
    OUTF.close()
    sys.stdout.write(text)


# ---------------------------------------------------------------- PNG 解码
def decode_png(data):
    u"""极简 PNG 解码：认 8 位 RGBA/RGB 与 1/2/4/8 位调色板、无隔行。

    ⚠ **第一版只写了 8 位**，跑起来当场死在原版贴图上（`AssertionError: 位深 4 不支持`）
    —— 原版 `diamond_sword.png` 那种是 **4 位调色板**。这条正是"别凭印象写解码器"：
    规格按 IHDR 现读，读不懂就抛，**绝不猜**。

    返回 (w, h, pixels)，pixels 是 [(r,g,b,a), ...] 行优先。
    """
    assert data[:8] == b"\x89PNG\r\n\x1a\n", u"不是 PNG"
    pos = 8
    w = h = None
    bitdepth = colortype = None
    idat = b""
    plte = None
    trns = None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            w, h, bitdepth, colortype, comp, filt, interlace = struct.unpack(">IIBBBBB", body)
            assert interlace == 0, u"隔行 PNG 不支持"
        elif ctype == b"PLTE":
            plte = body
        elif ctype == b"tRNS":
            trns = body
        elif ctype == b"IDAT":
            idat += body
        elif ctype == b"IEND":
            break
    if colortype == 6:
        nch = 4
    elif colortype == 2:
        nch = 3
    elif colortype == 3:
        nch = 1
    else:
        raise AssertionError(u"颜色类型 %d 不支持" % colortype)
    if bitdepth not in (1, 2, 4, 8):
        raise AssertionError(u"位深 %d 不支持" % bitdepth)

    raw = zlib_decompress(idat)
    # 滤波是按**扫描线的字节**做的，所以位深 < 8 时"每像素字节数"是 1（打包）
    bpp = max(1, (nch * bitdepth) // 8)
    rowbytes = (w * nch * bitdepth + 7) // 8
    out = []
    prev = bytearray(rowbytes)
    p = 0
    for _y in range(h):
        f = raw[p]
        p += 1
        line = bytearray(raw[p:p + rowbytes])
        p += rowbytes
        if f == 1:
            for i in range(bpp, rowbytes):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif f == 2:
            for i in range(rowbytes):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(rowbytes):
                a = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(rowbytes):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                pa = abs(b - c)
                pb = abs(a - c)
                pc = abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        elif f != 0:
            raise AssertionError(u"滤波类型 %d" % f)
        prev = line

        # 解包成"每像素一个下标/一组通道"
        vals = []
        if bitdepth == 8:
            vals = list(line[:w * nch])
        else:
            per = 8 // bitdepth
            mask = (1 << bitdepth) - 1
            for byte in line:
                for k in range(per):
                    vals.append((byte >> (8 - bitdepth * (k + 1))) & mask)
            vals = vals[:w * nch]

        if colortype == 6:
            for i in range(0, w * 4, 4):
                out.append((vals[i], vals[i + 1], vals[i + 2], vals[i + 3]))
        elif colortype == 2:
            for i in range(0, w * 3, 3):
                out.append((vals[i], vals[i + 1], vals[i + 2], 255))
        else:
            assert plte is not None, u"调色板图没有 PLTE"
            for i in range(w):
                idx = vals[i]
                r, g, b = plte[idx * 3], plte[idx * 3 + 1], plte[idx * 3 + 2]
                a = trns[idx] if (trns and idx < len(trns)) else 255
                out.append((r, g, b, a))
    return w, h, out


def zlib_decompress(data):
    import zlib
    return zlib.decompress(data)


def alpha_mask(px):
    return [1 if p[3] > 0 else 0 for p in px]


def iou(a, b):
    inter = sum(1 for x, y in zip(a, b) if x and y)
    union = sum(1 for x, y in zip(a, b) if x or y)
    return (inter / union) if union else 0.0


# ---------------------------------------------------------------- ① 素材身份
VANILLA_TOOLS = [u"wooden", u"stone", u"iron", u"golden", u"diamond",
                 u"netherite"]
TOOL_KINDS = [u"sword", u"pickaxe", u"axe", u"shovel", u"hoe"]

USER_FILES = [
    (u"星璨钢剑.png", u"sword"),          # 星璨钢剑
    (u"星镐子_001.png", u"pickaxe"),      # 星镐子
    (u"星锄子_001.png", u"hoe"),          # 星锄子
    (u"星璨钢斧子新贴图.png", u"axe"),    # 星璨钢斧子新贴图
]


def read_zip_png(zf, name):
    return decode_png(zf.read(name))


def section1():
    w(u"=" * 78)
    w(u"① 素材身份：形状 IoU（vs 原版六档 \u00d7 五种工具）")
    w(u"=" * 78)
    with zipfile.ZipFile(CLIENT_EXTRA) as zf:
        van = {}
        for mat in VANILLA_TOOLS:
            for kind in TOOL_KINDS:
                p = u"assets/minecraft/textures/item/%s_%s.png" % (mat, kind)
                try:
                    _w, _h, px = read_zip_png(zf, p)
                except KeyError:
                    continue
                van[(mat, kind)] = alpha_mask(px)
        w(u"原版贴图取到 %d 张（client-extra.jar）" % len(van))

        for fname, guess in USER_FILES:
            path = os.path.join(USER_ASSETS, fname)
            with open(path, "rb") as fh:
                data = fh.read()
            iw, ih, ipx = decode_png(data)
            imask = alpha_mask(ipx)
            scores = []
            for (mat, kind), mask in van.items():
                if len(mask) != len(imask):
                    continue
                scores.append((iou(imask, mask), mat, kind))
            scores.sort(reverse=True)
            nonempty = sum(imask)
            w(u"")
            w(u"【%s】 %dx%d  非空像素 %d  文件名猜=%s"
              % (fname, iw, ih, nonempty, guess))
            for s, mat, kind in scores[:5]:
                mark = u"  <== 文件名猜的" if kind == guess else u""
                w(u"    IoU %.4f  原版 %-9s %-8s%s" % (s, mat, kind, mark))
            best = scores[0]
            agree = (best[2] == guess)
            w(u"    ⇒ 形状最像：%s_%s（IoU %.4f）；与文件名推断 %s"
              % (best[1], best[2], best[0],
                 u"**一致**" if agree else u"**不一致，要问用户**"))
    return


# ---------------------------------------------------------------- ② 原版属性
WANT = [u"net/minecraft/world/item/SwordItem.java",
        u"net/minecraft/world/item/PickaxeItem.java",
        u"net/minecraft/world/item/ShovelItem.java",
        u"net/minecraft/world/item/HoeItem.java",
        u"net/minecraft/world/item/AxeItem.java",
        u"net/minecraft/world/item/DiggerItem.java",
        u"net/minecraft/world/item/TieredItem.java",
        u"net/minecraft/world/item/Items.java",
        u"net/minecraft/world/item/Tiers.java",
]

TOOL_CTORS = [u"new SwordItem(", u"new PickaxeItem(", u"new AxeItem(",
              u"new ShovelItem(", u"new HoeItem("]


def section2():
    w(u"")
    w(u"=" * 78)
    w(u"② 原版五把工具：属性怎么写、参数是多少（sources.jar 现抠，逐字）")
    w(u"=" * 78)
    if not os.path.exists(SOURCES_JAR):
        w(u"!! 找不到 sources.jar：%s" % SOURCES_JAR)
        return
    with zipfile.ZipFile(SOURCES_JAR) as zf:
        names = set(zf.namelist())
        for want in WANT:
            hit = [n for n in names if n.endswith(want)]
            if not hit:
                w(u"!! sources.jar 里没有 %s" % want)
                continue
            src = zf.read(hit[0]).decode("utf-8", "replace")
            lines = src.split(u"\n")
            w(u"")
            w(u"---- %s ----" % want.split(u"/")[-1])
            if want.endswith(u"Tiers.java"):
                # 档位实体：六个枚举常量的 (耐久, 速度, 伤害加成, 附魔权重, 挖不动的标签)
                for i, line in enumerate(lines, 1):
                    if u"new Tier(" in line or u"Tier(" in line and u"=" in line:
                        w(u"  %5d | %s" % (i, line.strip()))
            elif want.endswith(u"Items.java"):
                # **全部档位**都打（不只钻石）：锄头那种"负伤害 + 0 攻速"的写法
                # 只有把六档摆在一起才看得出规律，只看一档会误读。
                for i, line in enumerate(lines, 1):
                    if any(c in line for c in TOOL_CTORS):
                        w(u"  %5d | %s" % (i, line.strip()))
            else:
                # 把 createAttributes 的**整个方法体**打出来（含它调用的那个重载）
                for i, line in enumerate(lines, 1):
                    if u"createAttributes" not in line:
                        continue
                    w(u"  %5d | %s" % (i, line.strip()))
                    if u"{" in line:
                        depth = line.count(u"{") - line.count(u"}")
                        j = i
                        while depth > 0 and j < len(lines):
                            j += 1
                            if j - 1 >= len(lines):
                                break
                            w(u"  %5d | %s" % (j, lines[j - 1].rstrip()))
                            depth += lines[j - 1].count(u"{") - lines[j - 1].count(u"}")
    return


def section_recipe():
    w(u"")
    w(u"=" * 78)
    w(u"④ 原版五把工具的**配方 JSON**（client-extra.jar 现抠，逐字）")
    w(u"=" * 78)
    with zipfile.ZipFile(CLIENT_EXTRA) as zf:
        for kind in TOOL_KINDS:
            p = u"data/minecraft/recipe/diamond_%s.json" % kind
            w(u"")
            w(u"---- %s ----" % p)
            try:
                txt = zf.read(p).decode("utf-8")
            except KeyError:
                w(u"  !! jar 里没有这个路径")
                continue
            for line in txt.split(u"\n"):
                w(u"  " + line)
    return


def section3():
    w(u"")
    w(u"=" * 78)
    w(u"③ 盘上现状：星璨钢斧的贴图与模型（对照用）")
    w(u"=" * 78)
    for p in [os.path.join(ITEM_TEX, u"star_steel_axe.png")]:
        if os.path.exists(p):
            with open(p, "rb") as fh:
                _w, _h, px = decode_png(fh.read())
            import hashlib
            h = hashlib.sha1(open(p, "rb").read()).hexdigest()
            w(u"%s  sha1=%s  非空像素 %d"
              % (os.path.basename(p), h, sum(alpha_mask(px))))
    model_dir = os.path.join(PROJ, "src", "main", "resources", "assets",
                             "potato_s_t", "models", "item")
    for n in sorted(os.listdir(model_dir)):
        if n.startswith(u"star_steel") or n.startswith(u"titanium_alloy_"):
            with io.open(os.path.join(model_dir, n), encoding="utf-8") as fh:
                w(u"models/item/%-32s %s" % (n, fh.read().replace(u"\n", u"")))
    return


def section5():
    w(u"")
    w(u"=" * 78)
    w(u"⑤ 继承关系与 mineBlock 的原版实现（决定「覆写挂点」到底在哪一层）")
    w(u"=" * 78)
    with zipfile.ZipFile(SOURCES_JAR) as zf:
        names = set(zf.namelist())
        for want in [u"net/minecraft/world/item/SwordItem.java",
                     u"net/minecraft/world/item/PickaxeItem.java",
                     u"net/minecraft/world/item/HoeItem.java",
                     u"net/minecraft/world/item/ShovelItem.java",
                     u"net/minecraft/world/item/AxeItem.java",
                     u"net/minecraft/world/item/DiggerItem.java"]:
            hit = [n for n in names if n.endswith(want)]
            if not hit:
                continue
            src = zf.read(hit[0]).decode("utf-8", "replace")
            lines = src.split(u"\n")
            w(u"")
            w(u"---- %s ----" % want.split(u"/")[-1])
            for i, line in enumerate(lines, 1):
                s = line.strip()
                if s.startswith(u"public class") or s.startswith(u"public interface") \
                        or s.startswith(u"public abstract class"):
                    w(u"  %5d | %s" % (i, s))
                if u"mineBlock" in line or u"hurtEnemy" in line:
                    w(u"  %5d | %s" % (i, s))
                    depth = line.count(u"{") - line.count(u"}")
                    j = i
                    while depth > 0 and j < len(lines):
                        j += 1
                        if j - 1 >= len(lines):
                            break
                        w(u"  %5d | %s" % (j, lines[j - 1].rstrip()))
                        depth += lines[j - 1].count(u"{") - lines[j - 1].count(u"}")
    return


if __name__ == u"__main__":
    section1()
    section2()
    section_recipe()
    section3()
    section5()
    flush()
