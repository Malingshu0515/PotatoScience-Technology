# -*- coding: utf-8 -*-
"""_zf54_obj.py —— 给合金冶炼炉生成"整台机器一个模型"的 OBJ（先用 4×5×4 长方体占位）

用户：「改成像电力高炉那样的建模 先用4*5*4的长方体」⇒ 照 ZF39 那套：
  · OBJ 坐标 = **方块角点空间、1 单位 = 1 格**（§12.2 实测的结论）
  · 四个朝向各烘焙一份（模型几何固定在方块局部空间，由 blockstate 挑那一份）
  · 盒子相对**控制器那一格**画：控制器在最前排最左格 ⇒
      横向 u ∈ [0,4]（4 格宽）、向后 v ∈ [0,5]（5 格深）、竖直 w ∈ [-1,3]（控制器上下各留）
  · UV 每个面都给 0..1（**故意不铺砖**：OBJ 走方块图集，UV 超出 0..1 会采到隔壁贴图 ⇒ 花屏）

跑法：python build/zftools/_zf54_obj.py --write
"""
import argparse
import io
import os
import re
import sys

ASSETS = r"E:\PotatoST\src\main\resources\assets\potato_s_t\models\block"
JAVA = r"E:\PotatoST\src\main\java\com\potatost\mod\AlloySmelterStructure.java"
NAME = "alloy_smelter"
TEX = "potato_s_t:block/alloy_smelter"
# 相对控制器那格的盒子（u=横向、v=向机器背后、w=向上）
U0, U1 = 0.0, 4.0
V0, V1 = 0.0, 5.0
W0, W1 = -1.0, 3.0

# facing -> (横向单位向量 = facing.getClockWise(), 向后单位向量 = facing.getOpposite())
# MC 里 +X=东 +Z=南。⚠ 第一版把"向后"写成了 facing 本身，南/北两个朝向整个反了 ——
#    这一版直接用 getOpposite()，并且**由 80 格算包围盒**（不再手写 U0/U1）。
FACINGS = {
    "north": ((1, 0), (0, 1)),     # 面朝北：右=东(+X)，背后=南(+Z)
    "east": ((0, 1), (-1, 0)),
    "south": ((-1, 0), (0, -1)),   # 面朝南：右=西(-X)，背后=北(-Z)
    "west": ((0, -1), (1, 0)),
}
W0, W1 = -1.0, 3.0                 # 竖直：由 CTRL_Y 与 HEIGHT 现算（见 extent()），这里只是占位


def ctrl():
    """从 AlloySmelterStructure.java 里读控制器的位置（CTRL_Y/J/I）。

    ⚠ ZF58 的教训：这个脚本原来写死了"控制器在最前排最左格"（等于 `i * u`），
    用户把主控挪到**最右列**（CTRL_I 0 → 3）之后，**模型整套偏了 3 格**（截图上"模型在左边、
    机器方块在右边"）。所以现在一律**现读 Java 里的常量**，读什么摆什么，不再自己假设。
    """
    text = io.open(JAVA, encoding="utf-8").read()
    return (int(re.search(r"CTRL_Y\s*=\s*(\d+)", text).group(1)),
            int(re.search(r"CTRL_J\s*=\s*(\d+)", text).group(1)),
            int(re.search(r"CTRL_I\s*=\s*(\d+)", text).group(1)))


def extent(facing):
    """由 4 列 × 5 排算出世界向包围盒（每格占角点起 1×1×1）。

    格子相对控制器的偏移 = (i − CTRL_I) × u + (CTRL_J − j) × v（u = getClockWise，v = getOpposite），
    竖直同理 (y − CTRL_Y)：y 取 0..3 ⇒ w ∈ [−CTRL_Y, HEIGHT − CTRL_Y]。
    """
    (ux, uz), (vx, vz) = FACINGS[facing]
    cy, cj, ci = ctrl()
    text = io.open(JAVA, encoding="utf-8").read()
    height = int(re.search(r"HEIGHT\s*=\s*(\d+)", text).group(1))
    w0, w1 = -float(cy), float(height - cy)
    xs, zs = [], []
    for i in range(4):
        for j in range(5):
            cx = (i - ci) * ux + (cj - j) * vx
            cz = (i - ci) * uz + (cj - j) * vz
            xs += [cx, cx + 1.0]
            zs += [cz, cz + 1.0]
    return min(xs), max(xs), w0, w1, min(zs), max(zs)


def box_obj(facing):
    """按 facing 把盒子烘成世界向的 8 顶点 + 6 面。"""
    x0, x1, y0, y1, z0, z1 = extent(facing)
    print(u"   包围盒 X [{0:.0f},{1:.0f}] Y [{2:.0f},{3:.0f}] Z [{4:.0f},{5:.0f}]".format(x0, x1, y0, y1, z0, z1))

    corners = {
        "000": (x0, y0, z0), "100": (x1, y0, z0), "110": (x1, y0, z1), "010": (x0, y0, z1),
        "001": (x0, y1, z0), "101": (x1, y1, z0), "111": (x1, y1, z1), "011": (x0, y1, z1),
    }
    order = ["000", "100", "110", "010", "001", "101", "111", "011"]
    idx = {k: i + 1 for i, k in enumerate(order)}
    # 面：外法线朝外（逆时针）
    faces = [
        (("000", "010", "110", "100"), (0, -1, 0)),     # 下
        (("001", "101", "111", "011"), (0, 1, 0)),      # 上
        (("000", "100", "101", "001"), (0, 0, -1)),     # 一面
        (("110", "010", "011", "111"), (0, 0, 1)),      # 对面
        (("100", "110", "111", "101"), (1, 0, 0)),
        (("010", "000", "001", "011"), (-1, 0, 0)),
    ]
    lines = ["# ZF54 合金冶炼炉占位模型（4x5x4 长方体），facing={0}".format(facing),
             "mtllib {0}.mtl".format(NAME),
             "usemtl {0}".format(NAME)]
    for k in order:
        x, y, z = corners[k]
        lines.append("v {0:.4f} {1:.4f} {2:.4f}".format(x, y, z))
    lines.append("vt 0.0000 0.0000")
    lines.append("vt 1.0000 0.0000")
    lines.append("vt 1.0000 1.0000")
    lines.append("vt 0.0000 1.0000")
    normals = {}
    for _, n in faces:
        if n not in normals:
            normals[n] = len(normals) + 1
            lines.append("vn {0} {1} {2}".format(*n))
    for quad, n in faces:
        a, b, c, d = (idx[k] for k in quad)
        ni = normals[n]
        lines.append("f {0}/1/{4} {1}/2/{4} {2}/3/{4} {3}/4/{4}".format(a, b, c, d, ni))
    return "\n".join(lines) + "\n"


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)

    mtl = ("# ZF54：占位长方体用控制器那张贴图（Kd 拉满，免得被 MTL 的漫反射色压暗）\n"
           "newmtl {0}\n"
           "Ka 0.000 0.000 0.000\n"
           "Kd 1.000 1.000 1.000\n"
           "Ks 0.000 0.000 0.000\n"
           "Ns 0\n"
           "d 1.0\n"
           "illum 2\n"
           "map_Kd {1}\n").format(NAME, TEX)

    for facing in FACINGS:
        obj = box_obj(facing)
        print(u"== {0}_{1}.obj".format(NAME, facing))
        print(u"   顶点 8 / 面 6 / 行 {0}".format(len(obj.strip().split("\n"))))
        if args.write:
            p = os.path.join(ASSETS, "{0}_{1}.obj".format(NAME, facing))
            io.open(p, "w", encoding="utf-8", newline="\n").write(obj)
            print(u"   已写出 {0}（{1} 字节）".format(os.path.basename(p), os.path.getsize(p)))
    if args.write:
        p = os.path.join(ASSETS, NAME + ".mtl")
        io.open(p, "w", encoding="utf-8", newline="\n").write(mtl)
        print(u"已写出 {0}.mtl".format(NAME))
    else:
        print(u"（加 --write 才落盘）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
