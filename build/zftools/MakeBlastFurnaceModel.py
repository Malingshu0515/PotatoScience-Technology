# -*- coding: utf-8 -*-
"""ZF39：把用户的 model.obj 烘焙成 4 个朝向变体 + 生成 MTL 与单色贴图。

用户选了「先用单色渲染」⇒ MTL 只给一个漫反射色 + 一张纯色贴图，不指望还原 Blockbench 的材质。

坐标推导（**实测 + 推导，都写在档案 §12.2**）
------------------------------------------------
· 实测 `model.obj`：X −1.5…1.5、Z −1.5…1.5、Y 0…4.9375，第 0 组正好是 3×1×3 底板
  ⇒ **1 单位 = 1 格**，且 NeoForge 的 ObjModel 直接把 OBJ 坐标当"方块角点空间"用
  （源码原话：`// The incoming transform is referenced on the center of the block,
   but our coords are referenced on the corner`）。
· 模型是**居中建模**的（X/Z 都是 ±1.5），原点落在**控制器方块的角点**上；
  而控制器（高炉）在结构**前缘正中**，不是几何中心。
  ⇒ 对齐分两步：**先平移 t 到"以控制器角点为原点的结构坐标"，再绕控制器方块中心 C 旋转**。

    p' = C + R(p + t − C)
    t = (0.5, 0, −0.5)   # 结构 X∈[−1,2] Z∈[−2,1]，模型 X∈[−1.5,1.5] Z∈[−1.5,1.5]
    C = (0.5, 0, 0.5)    # 控制器方块自身的中心
    R = 绕 Y 轴、把模型局部 +Z（= 高炉那一侧 = 正方向）转到 facing 方向

**顺序不能颠倒**：先平移再绕方块中心转，否则控制器自己会被转出自己的格子。
"""
import io
import math
import os
import struct
import sys
import zlib

SRC = r"C:\Users\Administrator\.dsh\attachments\v1\files\4c\4cfdb0359b91bfe97943d66fcb198fd4c80ef0d8e5f3a7a68dc7ff1789fe990a\model.obj"
OUTDIR = r"E:\PotatoST\src\main\resources\assets\potato_s_t\models\block"
TEXDIR = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"

NAME = "electric_blast_furnace"
# facing -> 绕 Y 的旋转角（弧度）。R 把局部 +Z 转到 (sinθ, cosθ)
FACINGS = {"south": 0.0, "east": math.pi / 2, "north": math.pi, "west": -math.pi / 2}

T = (0.5, 0.0, -0.5)
C = (0.5, 0.0, 0.5)


def rot_y(x, z, theta):
    c, s = math.cos(theta), math.sin(theta)
    return x * c + z * s, -x * s + z * c


def bake(lines, theta):
    out = []
    for l in lines:
        t = l.split()
        if not t:
            out.append(l)
            continue
        if t[0] == "v" and len(t) >= 4:
            x, y, z = float(t[1]), float(t[2]), float(t[3])
            x, z = x + T[0], z + T[2]
            x, z = x - C[0], z - C[2]
            x, z = rot_y(x, z, theta)
            x, z = x + C[0], z + C[2]
            out.append("v %.6f %.6f %.6f" % (x, y, z))
        elif t[0] == "vt":
            # Y 轴不参与旋转；V 保持原样（Blockbench 导出的 V 方向与 MC 一致）
            out.append(l)
        elif t[0] == "vn" and len(t) >= 4:
            nx, ny, nz = float(t[1]), float(t[2]), float(t[3])
            nx, nz = rot_y(nx, nz, theta)
            out.append("vn %.6f %.6f %.6f" % (nx, ny, nz))
        elif t[0] == "mtllib":
            out.append("mtllib %s.mtl" % NAME)
        elif t[0] == "usemtl":
            out.append("usemtl %s" % NAME)
        else:
            out.append(l)
    return out


def bounds(lines):
    xs, ys, zs = [], [], []
    for l in lines:
        t = l.split()
        if t and t[0] == "v":
            xs.append(float(t[1])); ys.append(float(t[2])); zs.append(float(t[3]))
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


raw = io.open(SRC, encoding="utf-8").read().split("\n")
if raw and raw[-1] == "":
    raw.pop()

print("=== 4 个朝向变体的包围盒（应当在世界坐标里各自吻合结构）===")
for facing, theta in sorted(FACINGS.items()):
    baked = bake(raw, theta)
    (x0, x1), (y0, y1), (z0, z1) = bounds(baked)
    print("  %-6s X %6.3f..%-6.3f  Y %6.3f..%-6.3f  Z %6.3f..%-6.3f"
          % (facing, x0, x1, y0, y1, z0, z1))
    dst = os.path.join(OUTDIR, "%s_%s.obj" % (NAME, facing))
    io.open(dst, "w", encoding="utf-8", newline="\n").write("\n".join(baked) + "\n")
    print("        -> %s  (%d 字节)" % (os.path.basename(dst), os.path.getsize(dst)))

# ---- MTL：单色 ----
# 铁的漫反射色，比贴图略亮一点，靠 shade_quads 的面明暗把形体读出来
mtl = u"""# ZF39：用户选了「先用单色渲染」⇒ 这里只给一个漫反射色 + 一张纯色贴图
newmtl %s
Ka 0.000 0.000 0.000
Kd 0.620 0.640 0.680
Ks 0.000 0.000 0.000
Ns 0
d 1.0
illum 2
map_Kd potato_s_t:block/%s
""" % (NAME, NAME)
io.open(os.path.join(OUTDIR, NAME + ".mtl"), "w", encoding="utf-8", newline="\n").write(mtl)
print("\nMTL -> %s.mtl" % NAME)

# ---- 单色贴图（16×16，带极轻的噪点，免得纯平一片看不出接缝）----
w = h = 16
base = (150, 154, 162)
flat = bytearray()
for y in range(h):
    for x in range(w):
        n = ((x * 7 + y * 13) % 5) - 2          # -2..+2，确定性噪点
        flat += bytes((max(0, min(255, base[0] + n)),
                       max(0, min(255, base[1] + n)),
                       max(0, min(255, base[2] + n)), 255))


def write_png(path, w, h, rgba):
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + bytes(rgba[y * w * 4:(y + 1) * w * 4]) for y in range(h))
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    io.open(path, "wb").write(png)


tex = os.path.join(TEXDIR, NAME + ".png")
write_png(tex, w, h, flat)
print("贴图 -> %s.png  (%d 字节, %dx%d 单色 %s)" % (NAME, os.path.getsize(tex), w, h, base))
