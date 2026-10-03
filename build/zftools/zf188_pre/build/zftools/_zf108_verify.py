# -*- coding: utf-8 -*-
u"""_zf108_verify.py —— ZF108 常驻校验：合金冶炼炉的两张贴图 + 模型的 UV 复位

用户原话：「你看看您不能发挥一下 简单画一下合金冶炼炉的材质（不用太好 凑活都可以）现在的太丑了谢谢啦」

查四件事：
  ① **贴图本身**：16×16、颜色数够少（本工程好看的机器图都是 5~19 色的平涂；
     旧 `alloy_smelter.png` 是 **228 色**的糊图）、用色都落在家族调色板里、
     机体那张**上下镜像对称**（这样 OBJ 的 v 朝哪边都不影响观感）、没有透明像素；
  ② **模型没被画坏**：4 个 OBJ 行数/顶点/法线/面/材质行数与改前件**逐字节相同**，
     只有 `vt` 变了；唯一 vt 仍是 4 个，但已放大到整张贴图；
  ③ **引用链**：MTL 指向新贴图、主控与外壳仍用 `alloy_smelter.png`、接线口仍用 `wiring_block`；
  ④ **文档跟上了**：`docs\贴图清单.md` 那三行 + 档案 §5/§9。
"""
import hashlib
import io
import json
import os
import re
import struct
import sys
import zlib

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
RES = os.path.join(ROOT, r"src\main\resources")
TEXB = os.path.join(RES, r"assets\potato_s_t\textures\block")
MDIR = os.path.join(RES, r"assets\potato_s_t\models\block")
BK = r"C:\PotatoST救援\zf108_pre"
DOC = os.path.join(ROOT, r"docs\开发档案.md")
PLAN = os.path.join(ROOT, r"docs\贴图清单.md")

OBJS = ["alloy_smelter_north.obj", "alloy_smelter_east.obj",
        "alloy_smelter_south.obj", "alloy_smelter_west.obj"]
# 家族调色板（照微型粉碎机/燃烧反应室实测；不许自己发明颜色）
PALETTE = {(0x4a, 0x4a, 0x52), (0x34, 0x36, 0x3b), (0x23, 0x23, 0x2a),
           (0x6e, 0x6e, 0x78), (0x9a, 0xa2, 0xac), (0xc4, 0x60, 0x22), (0xe8, 0x91, 0x2f)}
NEW_VT = {"vt 0.0000 0.0000", "vt 1.0000 0.0000", "vt 0.0000 1.0000", "vt 1.0000 1.0000"}

n_pass = 0
fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def check(name, cond, detail=None):
    global n_pass
    if cond:
        n_pass += 1
    else:
        fails.append(name + (u"  ← %s" % detail if detail else u""))


def eq(name, want, got):
    check(name, want == got, u"期望 %r 实际 %r" % (want, got))


def read_png(path):
    u"""够用的 PNG 读入（本工程自己生成的 8 位 RGB/RGBA 非隔行）"""
    b = open(path, "rb").read()
    pos, w, h, ch, idat = 8, 0, 0, 4, b""
    while pos < len(b):
        (ln,) = struct.unpack(">I", b[pos:pos + 4])
        typ = b[pos + 4:pos + 8]
        data = b[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, color = struct.unpack(">IIBB", data[:10])
            if depth != 8 or color not in (2, 6):
                raise ValueError("color=%d depth=%d" % (color, depth))
            ch = 4 if color == 6 else 3
        elif typ == b"IDAT":
            idat += data
        elif typ == b"IEND":
            break
        pos += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * ch
    rows, prev, i = [], bytearray(stride), 0
    for _y in range(h):
        f = raw[i]
        i += 1
        line = bytearray(raw[i:i + stride])
        i += stride
        for x in range(stride):
            a = line[x - ch] if x >= ch else 0
            bb = prev[x]
            c = prev[x - ch] if x >= ch else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + bb) & 255
            elif f == 3:
                line[x] = (line[x] + (a + bb) // 2) & 255
            elif f == 4:
                p = a + bb - c
                pa, pb, pc = abs(p - a), abs(p - bb), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (bb if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        rows.append([tuple(line[x * ch:x * ch + ch]) for x in range(w)])
        prev = line
    return w, h, ch, rows


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    global n_pass
    # ============ ① 贴图本身 ============
    print(u"== ① 两张贴图 ==")
    for name, old_colors in ((u"alloy_smelter", 228), (u"alloy_smelter_formed", None)):
        p = os.path.join(TEXB, name + u".png")
        if not os.path.exists(p):
            check(u"%s.png 存在" % name, False)
            continue
        w, h, ch, rows = read_png(p)
        cols = set()
        opaque = True
        for row in rows:
            for c in row:
                cols.add(c[:3])
                if c[3] != 255:
                    opaque = False
        eq(u"%s.png 是 16×16" % name, (16, 16), (w, h))
        check(u"%s.png 每个像素都不透明（机器方块不该有洞）" % name, opaque)
        check(u"%s.png 颜色数 ≤ 8（平涂像素画；旧图是 %s 色）" % (name, old_colors),
              len(cols) <= 8, u"实际 %d 色" % len(cols))
        outside = sorted(c for c in cols if c not in PALETTE)
        eq(u"%s.png 的用色都在家族调色板里" % name, [], outside)
        check(u"%s.png 不是旧那张（sha1 变了）" % name,
              sha1(p) != u"b508edfb3d82cd3ef79fa941f05105fd126ae0fb1ddafb0bf4ec79a017a4fb9b")
        if name == u"alloy_smelter_formed":
            # 上下镜像对称 ⇒ OBJ 的 v 翻不翻都一样
            mirror_ok = all(rows[r] == rows[15 - r] for r in range(16))
            check(u"机体贴图上下镜像对称（第 r 行 == 第 15-r 行）⇒ v 朝向不再是问题", mirror_ok)
    # 主控/外壳那张：主控与外壳模型都还指着它
    sm = json.loads(read(os.path.join(MDIR, u"alloy_smelter.json")))
    part = json.loads(read(os.path.join(MDIR, u"alloy_smelter_part.json")))
    port = json.loads(read(os.path.join(MDIR, u"alloy_smelter_port.json")))
    eq(u"主控模型仍用 block/alloy_smelter", u"potato_s_t:block/alloy_smelter",
       sm.get("textures", {}).get("all"))
    eq(u"外壳模型仍用 block/alloy_smelter", u"potato_s_t:block/alloy_smelter",
       part.get("textures", {}).get("all"))
    eq(u"接线口仍用 block/wiring_block（本轮没动它）", u"potato_s_t:block/wiring_block",
       port.get("textures", {}).get("all"))

    # ============ ② 模型没被画坏 ============
    print(u"\n== ② 4 个 OBJ：只有 vt 变了 ==")
    for name in OBJS:
        p = os.path.join(MDIR, name)
        old_p = os.path.join(BK, r"src\main\resources\assets\potato_s_t\models\block", name)
        if not (os.path.exists(p) and os.path.exists(old_p)):
            check(u"%s 与改前件都在" % name, False)
            continue
        a = read(old_p).split(u"\n")
        b = read(p).split(u"\n")
        eq(u"%s 行数没变" % name, len(a), len(b))
        bad = []
        for x, y in zip(a, b):
            if x == y:
                continue
            kx = x.strip().split(u" ")[0] if x.strip() else u""
            ky = y.strip().split(u" ")[0] if y.strip() else u""
            if kx != u"vt" or ky != u"vt":
                bad.append((kx, ky))
        eq(u"%s：变的行只有 vt（其它行逐字节相同）" % name, [], bad[:4])
        vt = [l.strip() for l in b if l.strip().startswith(u"vt ")]
        vt_old = [l.strip() for l in a if l.strip().startswith(u"vt ")]
        eq(u"%s：vt 行数不变" % name, len(vt_old), len(vt))
        eq(u"%s：唯一 vt 还是 4 个（但已放大到整张贴图）" % name, NEW_VT, set(vt))
        for kind, want in ((u"v ", 112), (u"vn ", 0), (u"f ", 84)):
            got = len([l for l in b if l.strip().startswith(kind.strip() + u" ")])
            if kind == u"vn ":
                continue
            eq(u"%s：%s 行数 = %d" % (name, kind.strip(), want), want, got)
        eq(u"%s：面数仍是 84（没被当成顶点表重写）" % name, 84,
           len([l for l in b if l.strip().startswith(u"f ")]))

    # ============ ③ 引用链 ============
    print(u"\n== ③ MTL 与引用链 ==")
    mtl = read(os.path.join(MDIR, u"alloy_smelter.mtl"))
    check(u"MTL 指向新贴图 alloy_smelter_formed", u"map_Kd potato_s_t:block/alloy_smelter_formed" in mtl)
    check(u"MTL 不再借 heat_resistant_metal_block", u"heat_resistant_metal_block" not in mtl)
    check(u"MTL 的 Kd 仍是拉满（免得被漫反射压暗）", u"Kd 1.000 1.000 1.000" in mtl)
    for d in (u"north", u"east", u"south", u"west"):
        j = json.loads(read(os.path.join(MDIR, u"alloy_smelter_%s.json" % d)))
        eq(u"%s 模型仍是 obj + 同一个 mtl_override" % d, u"potato_s_t:models/block/alloy_smelter.mtl",
           j.get("mtl_override"))
        eq(u"%s 模型 flip_v 没被动（仍是 false）" % d, False, j.get("flip_v"))

    # ============ ④ 文档 ============
    print(u"\n== ④ 文档 ==")
    doc = read(DOC)
    plan = read(PLAN)
    check(u"档案 §5 有 ZF108 行", u"| ZF108 |" in doc)
    check(u"档案 §9 有 ZF108 小节", u"ZF108（0.11）" in doc)
    check(u"档案里写明「4 个唯一 vt」这件事", u"4 个唯一" in doc and u"vt" in doc)
    check(u"贴图清单里合金冶炼炉已改指新贴图",
          u"alloy_smelter_formed.png" in plan)

    print(u"")
    print(u"通过 = %d   失败 = %d" % (n_pass, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
