# -*- coding: utf-8 -*-
"""_zf68_obj.py —— 把**用户手绘的合金炉模型**（Blockbench 导出的 model.obj）烘成四份朝向 OBJ

为什么要烘而不是直接用：
  · 游戏里那台机器的模型是挂在**控制器那一格**上的（`neoforge:obj`），坐标必须落在
    "以控制器那格为原点的方块角点空间"（§12.2 实测：1 单位 = 1 格）；用户模型是在 Blockbench
    自己的坐标系里画的（X[-1.5,3.5] Y[0,3.375] Z[-1.5007,2.5007]）；
  · 机器有四个朝向（`facing`），模型几何固定在方块局部空间 ⇒ 得**每个朝向烘一份**
    （和 ZF54 那套占位长方体一样，blockstate 按 facing 挑那一份）。

映射怎么定的（**这是本轮唯一一处"我替用户判断"的地方**，所以要写清楚）：
  · 用户模型的平面是 **5 × 4**（X 方向 5 格、Z 方向 4 格），机器的平面是 **4 列(i) × 5 排(j)**
    ⇒ **模型的 X 轴 → 机器的 j 轴（前后）**，**模型的 Z 轴 → 机器的 i 轴（左右）**；
  · 机器第 2 层的**最前排两端**是两处接线块（成型后就是进电的接线口），而用户模型在
    **-X 那一列**有两根柱子（#2/#3：X[-1.5,-0.5]，正好落在 Z 的两端）⇒ 把 **-X 那一列摆在机器的
    后排 j=0**，两根柱子就精准落在两个接线口格上（`_zf54_verify.py` 里有断言钉死这条）；
  · 竖直方向：模型底面 Y=0 → 机器最底层（控制器在 y=1 ⇒ 局部 Y = -1）⇒ `y' = y - 1`，
    **只平移不缩放**（用户模型高 3.375 格，机器结构是 4 格 ⇒ 顶上留 0.625 格空气）。

跑法：python build/zftools/_zf68_obj.py --write
"""
import argparse
import io
import os
import re
import sys

ASSETS = r"E:\PotatoST\src\main\resources\assets\potato_s_t\models\block"
JAVA = r"E:\PotatoST\src\main\java\com\potatost\mod\AlloySmelterStructure.java"
SRC = r"E:\PotatoST\build\zftools\_zf68_user_model.obj"
NAME = "alloy_smelter"
MAT = "alloy_smelter"
TEX = "potato_s_t:block/heat_resistant_metal_block"      # 用户：「目前没有贴图 先用耐热金属块的吧」

# facing -> (横向 u = getClockWise, 向后 v = getOpposite)，+X=东 +Z=南
FACINGS = {
    "north": ((1, 0), (0, 1)),
    "east": ((0, 1), (-1, 0)),
    "south": ((-1, 0), (0, -1)),
    "west": ((0, -1), (1, 0)),
}


def java_consts():
    text = io.open(JAVA, encoding="utf-8").read()
    def g(name):
        return int(re.search(r"\b%s\s*=\s*(\d+)" % name, text).group(1))
    return g("CTRL_Y"), g("CTRL_J"), g("CTRL_I"), g("HEIGHT")


def read_obj(path):
    """读 v / vt / vn / o / f；面保持四边形，索引按 OBJ 原样（1 基）。"""
    vs, vts, vns = [], [], []
    groups = []           # [(名字, [face, ...])]
    cur = None
    for line in io.open(path, encoding="utf-8", errors="replace"):
        t = line.split()
        if not t:
            continue
        if t[0] == "v":
            vs.append(tuple(float(x) for x in t[1:4]))
        elif t[0] == "vt":
            vts.append(tuple(float(x) for x in t[1:3]))
        elif t[0] == "vn":
            vns.append(tuple(float(x) for x in t[1:4]))
        elif t[0] == "o":
            cur = (t[1] if len(t) > 1 else "mesh", [])
            groups.append(cur)
        elif t[0] == "f":
            if cur is None:
                cur = ("mesh", [])
                groups.append(cur)
            cur[1].append([p.split("/") for p in t[1:]])
    return vs, vts, vns, groups


def rotate(p, u, v, flip):
    """把模型坐标 (mx,my,mz) 转到世界向（控制器局部、单位=格）。

    映射：模型 **-X → +v 方向**（即"模型那一列带柱子的 -X 端 = 机器后排 j=0"）、
    模型 **+Z → +u 方向**。这两个基向量的行列式 = +1（是**旋转**不是镜像；
    取反一个就会把整台机器左右镜像）。
    """
    ux, uz = u
    vx, vz = v
    mx, my, mz = p
    x = mx * (-vx) + mz * ux
    z = mx * (-vz) + mz * uz
    return (x, my, z)


def bake(source, facing, consts):
    """把源模型按 facing 烘成目标 OBJ 文本 + 诊断信息。"""
    vs, vts, vns, groups = source
    cy, cj, ci, height = consts
    u, v = FACINGS[facing]

    # ① 源包围盒 → 旋转后的包围盒
    xs = [rotate(p, u, v, False)[0] for p in vs]
    zs = [rotate(p, u, v, False)[2] for p in vs]
    ys = [p[1] for p in vs]
    rx0, rx1 = min(xs), max(xs)
    rz0, rz1 = min(zs), max(zs)
    ry0, ry1 = min(ys), max(ys)

    # ② 目标包围盒 = 机器 80 格占的方块体积（与 _zf54_verify.py 同一套算法）
    (ux, uz), (vx, vz) = u, v
    txs, tzs = [], []
    for i in range(4):
        for j in range(5):
            cx = (i - ci) * ux + (cj - j) * vx
            cz = (i - ci) * uz + (cj - j) * vz
            txs += [cx, cx + 1.0]
            tzs += [cz, cz + 1.0]
    tx0, tx1 = min(txs), max(txs)
    tz0, tz1 = min(tzs), max(tzs)
    ty0, ty1 = -float(cy), float(height - cy)

    # ③ 只平移（不缩放）：把旋转后的包围盒对齐到目标包围盒
    dx = tx0 - rx0
    dz = tz0 - rz0
    dy = ty0 - ry0

    out_v = []
    for p in vs:
        x, y, z = rotate(p, u, v, False)
        out_v.append((x + dx, y + dy, z + dz))
    out_n = []
    for n in vns:
        nx, ny, nz = rotate(n, u, v, False)
        out_n.append((nx, ny, nz))

    lines = [
        "# ZF68：用户手绘模型（Blockbench 导出）烘成 facing={0} 的那一份。**不要手改**，".format(facing),
        "#        改请改 build/zftools/_zf68_obj.py 再重跑（映射规则见脚本头部注释）。",
        "# 源模型包围盒  X[{0:.4f},{1:.4f}] Y[{2:.4f},{3:.4f}] Z[{4:.4f},{5:.4f}]".format(
            min(p[0] for p in vs), max(p[0] for p in vs), ry0, ry1,
            min(p[2] for p in vs), max(p[2] for p in vs)),
        "# 平移量 dx={0:.4f} dy={1:.4f} dz={2:.4f}（只平移，不缩放）".format(dx, dy, dz),
        "mtllib {0}.mtl".format(NAME),
    ]
    for x, y, z in out_v:
        lines.append("v {0:.4f} {1:.4f} {2:.4f}".format(x, y, z))
    for a, b in vts:
        lines.append("vt {0:.4f} {1:.4f}".format(a, b))
    for x, y, z in out_n:
        lines.append("vn {0:.4f} {1:.4f} {2:.4f}".format(x, y, z))
    for gname, faces in groups:
        lines.append("o {0}".format(gname))
        lines.append("usemtl {0}".format(MAT))
        for f in faces:
            parts = []
            for p in f:
                vi = p[0]
                ti = p[1] if len(p) > 1 and p[1] else None
                ni = p[2] if len(p) > 2 and p[2] else None
                parts.append("{0}/{1}/{2}".format(vi, ti if ti else "", ni if ni else ""))
            lines.append("f " + " ".join(parts))

    info = dict(bbox=(min(p[0] for p in out_v), max(p[0] for p in out_v),
                      min(p[1] for p in out_v), max(p[1] for p in out_v),
                      min(p[2] for p in out_v), max(p[2] for p in out_v)),
                target=(tx0, tx1, ty0, ty1, tz0, tz1),
                verts=len(out_v), faces=sum(len(f) for _, f in groups), groups=len(groups))
    return "\n".join(lines) + "\n", info


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--src", default=SRC)
    args = ap.parse_args(argv)

    if not os.path.isfile(args.src):
        print(u"源模型不存在: %s" % args.src)
        return 2
    source = read_obj(args.src)
    consts = java_consts()
    print(u"源模型: %s  v=%d vt=%d vn=%d 组=%d 面=%d" % (
        os.path.basename(args.src), len(source[0]), len(source[1]), len(source[2]),
        len(source[3]), sum(len(f) for _, f in source[3])))
    print(u"Java 常量: CTRL_Y={0} CTRL_J={1} CTRL_I={2} HEIGHT={3}".format(*consts))

    mtl = (u"# ZF68：用户模型暂时没有贴图，按用户要求先用**耐热金属块**那张（Kd 拉满，免得被漫反射色压暗）\n"
           u"newmtl {0}\n"
           u"Ka 0.000 0.000 0.000\n"
           u"Kd 1.000 1.000 1.000\n"
           u"Ks 0.000 0.000 0.000\n"
           u"Ns 0\n"
           u"d 1.0\n"
           u"illum 2\n"
           u"map_Kd {1}\n").format(MAT, TEX)

    for facing in FACINGS:
        text, info = bake(source, facing, consts)
        b, t = info["bbox"], info["target"]
        print(u"== {0}_{1}.obj  顶点 {2} 面 {3} 组 {4}".format(NAME, facing, info["verts"], info["faces"], info["groups"]))
        print(u"   输出包围盒 X[{0:.4f},{1:.4f}] Y[{2:.4f},{3:.4f}] Z[{4:.4f},{5:.4f}]".format(*b))
        print(u"   目标包围盒 X[{0:.1f},{1:.1f}] Y[{2:.1f},{3:.1f}] Z[{4:.1f},{5:.1f}]".format(*t))
        for k, name in ((0, "X0"), (1, "X1"), (4, "Z0"), (5, "Z1")):
            if abs(b[k] - t[k]) > 0.01:
                print(u"   !! {0} 差 {1:.4f}（超过 0.01）".format(name, abs(b[k] - t[k])))
        if args.write:
            p = os.path.join(ASSETS, "{0}_{1}.obj".format(NAME, facing))
            io.open(p, "w", encoding="utf-8", newline="\n").write(text)
            print(u"   已写出 {0}（{1} 字节）".format(os.path.basename(p), os.path.getsize(p)))
    if args.write:
        p = os.path.join(ASSETS, NAME + ".mtl")
        io.open(p, "w", encoding="utf-8", newline="\n").write(mtl)
        print(u"已写出 {0}.mtl（map_Kd {1}）".format(NAME, TEX))
    else:
        print(u"（加 --write 才落盘）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
