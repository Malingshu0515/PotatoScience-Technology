# -*- coding: utf-8 -*-
"""_zf54_verify.py —— 盘面复核：合金炉那台**整体模型**必须罩住 4 列 × 5 排的结构，四个朝向都对。

判据（照 §12.15 / ZF39 的实测结论）：
  · OBJ 坐标 = 方块角点空间、1 单位 = 1 格，原点在**控制器那一格的角点**；
  · 结构占：横向 4 格（i）× 向后 5 格（j）× 竖直 4 格（控制器在 y=1 ⇒ 局部 Y ∈ [-1,3]）；
  · **ZF68 起模型换成用户手绘的那份**（原来是 4×5×4 占位长方体）⇒ 判据跟着改：
      - X / Z 包围盒仍必须与"80 格占的方块体积"一致（这条是 ZF58 "模型偏 3 格" 的抓手）；
      - Y **底面必须贴地**（= -1），顶面 = 源模型高度 - 1（**只平移不缩放**，用户模型 3.375 格高
        ⇒ 顶上留 0.625 格空气，这是有意的、写在档案里的）；
      - 网格规模必须与源模型一致（112 顶点 / 84 面）—— 防止哪天又被换回占位盒子；
      - **语义那条**：用户模型 -X 那一列有两根柱子，烘出来必须正好落在机器**后排的两个接线口格**
        （j=0, i=0 与 j=0, i=3）上。这条就是"前后左右到底有没有摆反"的判据。
"""
import io
import json
import os
import re
import sys

PROJ = r"E:\PotatoST"
BLOCK = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t", "models", "block")
BS = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t", "blockstates")
JAVA = os.path.join(PROJ, "src", "main", "java", "com", "potatost", "mod", "AlloySmelterStructure.java")
SRC_OBJ = os.path.join(PROJ, "build", "zftools", "_zf68_user_model.obj")

# facing -> (横向单位向量 = getClockWise, 向后单位向量 = getOpposite)，+X=东 +Z=南
AXES = {
    "north": ((1, 0), (0, 1)),
    "east": ((0, 1), (-1, 0)),
    "south": ((-1, 0), (0, -1)),
    "west": ((0, -1), (1, 0)),
}

fails = []


def check(cond, msg):
    print((u"  [OK]   " if cond else u"  [FAIL] ") + msg)
    if not cond:
        fails.append(msg)


def ctrl():
    """⚠ ZF58：控制器的列号必须**现读 Java**（写死过一次，模型与代码同时错、检查照样全绿）。"""
    text = io.open(JAVA, encoding="utf-8").read()
    return (int(re.search(r"CTRL_Y\s*=\s*(\d+)", text).group(1)),
            int(re.search(r"CTRL_J\s*=\s*(\d+)", text).group(1)),
            int(re.search(r"CTRL_I\s*=\s*(\d+)", text).group(1)),
            int(re.search(r"HEIGHT\s*=\s*(\d+)", text).group(1)))


def cell_box(facing):
    """80 格（4 列 × 5 排 × 4 层）在世界上占的方块体积。"""
    (ux, uz), (vx, vz) = AXES[facing]
    cy, cj, ci, height = ctrl()
    xs, ys, zs = [], [], []
    for y in range(height):
        for i in range(4):
            for j in range(5):
                cx = (i - ci) * ux + (cj - j) * vx
                cz = (i - ci) * uz + (cj - j) * vz
                cw = y - cy
                xs += [cx, cx + 1.0]
                zs += [cz, cz + 1.0]
                ys += [cw, cw + 1.0]
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def one_cell_box(facing, i, j):
    """单格 (i, j) 占的方块体积（底面那一层）。"""
    (ux, uz), (vx, vz) = AXES[facing]
    cy, cj, ci, height = ctrl()
    cx = (i - ci) * ux + (cj - j) * vx
    cz = (i - ci) * uz + (cj - j) * vz
    return cx, cx + 1.0, cz, cz + 1.0


def read_obj_groups(path):
    """读顶点 + 按 o 分组的面（返回 [(名字, [顶点索引...])]）。"""
    vs = []
    groups = []
    cur = None
    for line in io.open(path, encoding="utf-8", errors="replace"):
        t = line.split()
        if not t:
            continue
        if t[0] == "v":
            vs.append(tuple(float(x) for x in t[1:4]))
        elif t[0] == "o":
            cur = [t[1] if len(t) > 1 else "mesh", []]
            groups.append(cur)
        elif t[0] == "f":
            if cur is None:
                cur = ["mesh", []]
                groups.append(cur)
            for part in t[1:]:
                cur[1].append(int(part.split("/")[0]) - 1)
    return vs, groups


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    zs = [p[2] for p in pts]
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


# 源模型（用户手绘）的规格：顶点/面/高度 —— 全都现读，不写死
src_vs, src_groups = read_obj_groups(SRC_OBJ)
src_h = max(p[1] for p in src_vs) - min(p[1] for p in src_vs)
src_faces = sum(len(g[1]) // 4 for g in src_groups)
print(u"源模型（用户手绘）: 顶点 %d 组 %d 面 %d 高 %.4f 格" % (len(src_vs), len(src_groups), src_faces, src_h))

print(u"\n== ① 四个朝向的 OBJ：网格规模 / X Z 罩住结构 / 底面贴地 / 顶面不超高 ==")
for facing in AXES:
    p = os.path.join(BLOCK, "alloy_smelter_{0}.obj".format(facing))
    if not os.path.isfile(p):
        check(False, u"%s 存在" % os.path.basename(p))
        continue
    text = io.open(p, encoding="utf-8").read()
    vs, groups = read_obj_groups(p)
    faces = sum(len(g[1]) // 4 for g in groups)
    check(len(vs) == len(src_vs) and faces == src_faces and len(groups) == len(src_groups),
          u"%s：还是用户那份网格（顶点 %d/%d 面 %d/%d 组 %d/%d）"
          % (facing, len(vs), len(src_vs), faces, src_faces, len(groups), len(src_groups)))
    b = bbox(vs)
    ex0, ex1, ey0, ey1, ez0, ez1 = cell_box(facing)
    check(abs(b[0] - ex0) <= 0.01 and abs(b[1] - ex1) <= 0.01,
          u"%s：X 范围 (%.4f, %.4f) ≈ 结构预期 (%.1f, %.1f)" % (facing, b[0], b[1], ex0, ex1))
    check(abs(b[4] - ez0) <= 0.01 and abs(b[5] - ez1) <= 0.01,
          u"%s：Z 范围 (%.4f, %.4f) ≈ 结构预期 (%.1f, %.1f)" % (facing, b[4], b[5], ez0, ez1))
    check(abs(b[2] - ey0) <= 0.001,
          u"%s：底面贴地 Y0 = %.4f（结构底面 %.1f）" % (facing, b[2], ey0))
    check(abs(b[3] - (ey0 + src_h)) <= 0.001,
          u"%s：顶面 = 底面 + 源模型高度 = %.4f（读到 %.4f，**只平移没缩放**）"
          % (facing, ey0 + src_h, b[3]))
    check(b[3] <= ey1 + 0.001, u"%s：没有戳出结构顶面（%.4f ≤ %.1f）" % (facing, b[3], ey1))
    check(u"map_Kd" not in text and u"mtllib alloy_smelter.mtl" in text, u"%s：引用 alloy_smelter.mtl" % facing)

print(u"\n== ② 语义：两根柱子必须落在后排的两个接线口格上（前后摆反了这条会挂）==")
for facing in AXES:
    p = os.path.join(BLOCK, "alloy_smelter_{0}.obj".format(facing))
    vs, groups = read_obj_groups(p)
    if len(groups) < 4:
        check(False, u"%s：组数不足" % facing)
        continue
    ports = {(0, 0): one_cell_box(facing, 0, 0), (3, 0): one_cell_box(facing, 3, 0)}
    for gi in (2, 3):                                  # 源模型里第 3、4 组就是那两根柱子
        pts = [vs[k] for k in set(groups[gi][1])]
        b = bbox(pts)
        hit = None
        for key, (cx0, cx1, cz0, cz1) in ports.items():
            if (abs(b[0] - cx0) <= 0.01 and abs(b[1] - cx1) <= 0.01
                    and abs(b[4] - cz0) <= 0.01 and abs(b[5] - cz1) <= 0.01):
                hit = key
        check(hit is not None,
              u"%s：柱 #%d 落在接线口格上（实际 X[%.3f,%.3f] Z[%.3f,%.3f]）"
              % (facing, gi, b[0], b[1], b[4], b[5]))

print(u"\n== ③ MTL 指向耐热金属块（用户：目前没有贴图，先用耐热金属块的）==")
mtl = io.open(os.path.join(BLOCK, "alloy_smelter.mtl"), encoding="utf-8").read()
check(u"map_Kd potato_s_t:block/heat_resistant_metal_block" in mtl,
      u"map_Kd = potato_s_t:block/heat_resistant_metal_block")
check(u"newmtl alloy_smelter" in mtl, u"材质名与 OBJ 的 usemtl 一致")

print(u"\n== ④ 模型 JSON 与 blockstate ==")
for facing in AXES:
    p = os.path.join(BLOCK, "alloy_smelter_{0}.json".format(facing))
    d = json.loads(io.open(p, encoding="utf-8").read())
    check(d.get("loader") == "neoforge:obj", u"%s：loader = neoforge:obj" % facing)
    check(d.get("model") == "potato_s_t:models/block/alloy_smelter_{0}.obj".format(facing),
          u"%s：model 路径（要写全路径）" % facing)
    check(d.get("mtl_override") == "potato_s_t:models/block/alloy_smelter.mtl",
          u"%s：mtl_override 指向 alloy_smelter.mtl" % facing)
bs = json.loads(io.open(os.path.join(BS, "alloy_smelter.json"), encoding="utf-8").read())
for facing in AXES:
    # ZF56 起：OBJ 只挂在 formed=true 上（未成型时主控是那个 1×1×1 小方块）
    check(bs["variants"]["facing=" + facing + ",formed=true"]["model"]
          == "potato_s_t:block/alloy_smelter_" + facing,
          u"blockstate facing=%s,formed=true -> 对应那一份 OBJ" % facing)
check(bs["variants"]["formed=false"]["model"] == "potato_s_t:block/alloy_smelter",
      u"blockstate formed=false -> 主控小方块（不是 OBJ 大盒子）")
part_bs = json.loads(io.open(os.path.join(BS, "alloy_smelter_part.json"), encoding="utf-8").read())
check(part_bs["variants"][""]["model"] == "potato_s_t:block/alloy_smelter_part", u"部件格 blockstate 正常")

print(u"\n== ⑤ 摆放图仍要对得上（ZF52 回归）==")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import subprocess
r = subprocess.call([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_zf52_verify.py")],
                    stdout=subprocess.DEVNULL)
check(r == 0, u"_zf52_verify.py 退出码 0（介绍里的摆放图与结构代码一致）")

print(u"\n------------------------------")
print(u"失败项 = %d" % len(fails))
print(u"结论: " + (u"通过" if not fails else u"有失败项"))
sys.exit(1 if fails else 0)
