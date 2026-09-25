# -*- coding: utf-8 -*-
u"""_zf89_ebf_bake.py —— 把用户**新导出**的电力高炉 OBJ 烘成四个朝向（贴图一个字节都不碰）

背景（§4.58）：手里这份模型每个面都在采样整张 0..1 贴图（114 个面只有 4 个 UV 点），
而 ZF79 换上的 256×256 是**给模型展开的 UV 图集** ⇒ 每个面铺整张图集。
用户拍了「我重新导出模型」⇒ 本脚本负责把新模型接进来。

用法：
    python _zf89_ebf_bake.py <新模型.obj>            # 只看不写（预演）
    python _zf89_ebf_bake.py <新模型.obj> --write    # 真的写四份朝向

它做五件事，每件都要打印结论，**任何一条不过就不写盘**（除非 --force）：
  ① **UV 检查**：不同 `vt` 取值必须 > 4（= 真的带 UV，不是"整张贴图铺每个面"）；
  ② **几何检查**：新的 `v` 顶点集合必须与手里那份**逐点一致**（用户只是补了 UV）；
     若不一致 → 打印差多少、并提示"对齐常数可能要重算"，不静默；
  ③ **逐面可视检查**：把每个面的 UV 矩形在 256×256 贴图上圈出来，数里面有**多少透明像素**；
     `flip_v` 两种取法都算一遍，哪边透明像素少就报哪边（并在需要时提醒改 model JSON 的 flip_v）；
  ④ 用 `t`（按模型自身包围盒**算出来**，不再写死 ±1.5）与 `C` 烘四份朝向，打印各自包围盒；
  ⑤ 只写 `electric_blast_furnace_{north,south,east,west}.obj`；**MTL 与贴图一律不动**。
     （`MakeBlastFurnaceModel.py` 会把贴图盖回单色，已列为禁跑，本脚本不复制那一段。）
"""
import io
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _zf66_png  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
OUTDIR = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\block")
TEX = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png")
NAME = "electric_blast_furnace"
FACINGS = {"south": 0.0, "east": math.pi / 2, "north": math.pi, "west": -math.pi / 2}
C = (0.5, 0.0, 0.5)          # 控制器方块自身的中心（结构坐标）
# 结构在 X 方向占 [-1, 2]、Z 方向占 [-2, 1] ⇒ 中心 (0.5, -0.5)
STRUCT_CX, STRUCT_CZ = 0.5, -0.5
fails = []


def rot_y(x, z, theta):
    c, s = math.cos(theta), math.sin(theta)
    return x * c + z * s, -x * s + z * c


def parse(lines):
    vs, vts, faces = [], [], []
    for l in lines:
        t = l.split()
        if not t:
            continue
        if t[0] == "v":
            vs.append(tuple(float(x) for x in t[1:4]))
        elif t[0] == "vt":
            vts.append(tuple(float(x) for x in t[1:3]))
        elif t[0] == "f":
            ids = []
            for a in t[1:]:
                parts = a.split("/")
                vi = int(parts[0]) - 1                       # OBJ 下标是 1 起
                ti = (int(parts[1]) - 1
                      if len(parts) > 1 and parts[1] else None)
                ids.append((vi, ti))
            faces.append(ids)
    return vs, vts, faces


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    src = argv[1]
    write = "--write" in argv
    force = "--force" in argv
    lines = io.open(src, encoding="utf-8", errors="replace").read().split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    vs, vts, faces = parse(lines)
    print(u"新模型：%s（%d 字节）" % (os.path.basename(src), os.path.getsize(src)))
    print(u"  v=%d  vt=%d  面=%d" % (len(vs), len(vts), len(faces)))

    print(u"\n== ① UV 检查 ==")
    uvs = sorted(set(vts))
    print(u"  不同 UV 点：%d 个" % len(uvs))
    if len(uvs) <= 4:
        fails.append(u"新模型仍然只有 %d 个 UV 点 ⇒ 还是「整张贴图铺每个面」，换了没用" % len(uvs))
    else:
        print(u"  [OK]   带真 UV（前 6 个：%s）" % (uvs[:6],))

    print(u"\n== ② 几何检查（与手里那份成品比）==")
    # 只跟 **south** 比：那个朝向的烘焙是"纯平移、零旋转"（theta=0），
    # 所以两边各自归一化（减掉最小角）之后应当逐点相同。
    old = set()
    p = os.path.join(OUTDIR, "%s_south.obj" % NAME)
    if os.path.exists(p):
        ovs, _, _ = parse(io.open(p, encoding="utf-8", errors="replace").read().split("\n"))
        old = set(tuple(round(c, 6) for c in v) for v in ovs)
    oldr = set()
    for v in vs:                       # 先把新模型的包围盒中心算出来（后面烘制要用）
        oldr.add(tuple(round(c, 6) for c in v))
    xs = [v[0] for v in vs]; ys = [v[1] for v in vs]; zs = [v[2] for v in vs]
    print(u"  新模型包围盒：X %.4f..%.4f  Y %.4f..%.4f  Z %.4f..%.4f"
          % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    print(u"  平面尺寸：X 跨 %.4f 格，Z 跨 %.4f 格，高 %.4f 格"
          % (max(xs) - min(xs), max(zs) - min(zs), max(ys) - min(ys)))
    # 手里那份的"原始（未平移）"顶点 = 去掉平移 t 再转回来太绕；直接比**相对形状**：
    # 把两边的顶点集合各自平移成"以最小角为原点"，再比。
    def normalize(pts):
        mx = min(p[0] for p in pts); my = min(p[1] for p in pts); mz = min(p[2] for p in pts)
        return set((round(p[0] - mx, 4), round(p[1] - my, 4), round(p[2] - mz, 4)) for p in pts)
    if old:
        a, b = normalize(oldr), normalize(old)
        only_new = sorted(a - b)[:4]
        only_old = sorted(b - a)[:4]
        print(u"  归一化后：新 %d 个点 / 旧 %d 个点；只在新的 %d 个，只在旧的 %d 个"
              % (len(a), len(b), len(a - b), len(b - a)))
        if only_new or only_old:
            print(u"    只在新的（前 4）：%s" % (only_new,))
            print(u"    只在旧的（前 4）：%s" % (only_old,))
            fails.append(u"几何与手里那份**不一致**（用户可能改了模型）⇒ 对齐要重算，别硬套")
        else:
            print(u"  [OK]   几何逐点一致（用户只是补了 UV）")
    else:
        print(u"  [WARN] 找不到旧的成品 OBJ，跳过对比")

    print(u"\n== ③ 逐面可视检查（UV 矩形里有多少透明像素）==")
    w, h, ctype, px = _zf66_png.read_png(TEX)
    print(u"  贴图 %dx%d，不透明 %d 像素"
          % (w, h, sum(1 for p in px if p[3] != 0)))

    def transparent_faces(flip):
        bad = 0
        worst = []
        for fi, f in enumerate(faces):
            uv = [vts[t] for _, t in f if t is not None]
            if not uv:
                continue
            us = [p[0] for p in uv]; vv = [p[1] for p in uv]
            x0 = max(0, min(w - 1, int(math.floor(min(us) * w))))
            x1 = max(0, min(w - 1, int(math.ceil(max(us) * w)) - 1))
            vm = [(1 - v) if flip else v for v in vv]
            y0 = max(0, min(h - 1, int(math.floor(min(vm) * h))))
            y1 = max(0, min(h - 1, int(math.ceil(max(vm) * h)) - 1))
            n = t = 0
            for yy in range(y0, y1 + 1):
                for xx in range(x0, x1 + 1):
                    n += 1
                    if px[yy * w + xx][3] == 0:
                        t += 1
            if t:
                bad += 1
                worst.append((fi + 1, (x0, y0, x1, y1), t, n))
        return bad, worst

    bad_a, wa = transparent_faces(False)
    bad_b, wb = transparent_faces(True)
    print(u"  flip_v=false（OBJ 的 v 直接用）：%d/%d 个面碰到透明像素" % (bad_a, len(faces)))
    print(u"  flip_v=true （v 取 1-v）      ：%d/%d 个面碰到透明像素" % (bad_b, len(faces)))
    pick = False if bad_a <= bad_b else True
    print(u"  ⇒ 少的那边是 flip_v=%s（model JSON 现在写的是 false）" % (u"true" if pick else u"false"))
    worst = (wa if not pick else wb)[:6]
    for it in worst:
        print(u"    面%03d UV 矩形 %s：%d/%d 像素透明" % it)
    if min(bad_a, bad_b) > 0:
        fails.append(u"最好的取法下仍有 %d 个面压在透明像素上 ⇒ UV 与贴图没对上"
                     % min(bad_a, bad_b))

    print(u"\n== ④ 烘四个朝向 ==")
    t = (STRUCT_CX - (min(xs) + max(xs)) / 2.0, 0.0, STRUCT_CZ - (min(zs) + max(zs)) / 2.0)
    print(u"  平移 t = (%.4f, 0, %.4f)（由模型包围盒算出来）" % (t[0], t[2]))
    baked = {}
    for facing, theta in sorted(FACINGS.items()):
        out = []
        for l in lines:
            p = l.split()
            if not p:
                out.append(l)
                continue
            if p[0] == "v" and len(p) >= 4:
                x, y, z = float(p[1]), float(p[2]), float(p[3])
                x, z = x + t[0], z + t[2]
                x, z = x - C[0], z - C[2]
                x, z = rot_y(x, z, theta)
                out.append("v %.6f %.6f %.6f" % (x + C[0], y, z + C[2]))
            elif p[0] == "vn" and len(p) >= 4:
                nx, nz = rot_y(float(p[1]), float(p[3]), theta)
                out.append("vn %.6f %.6f %.6f" % (nx, float(p[2]), nz))
            elif p[0] == "mtllib":
                out.append("mtllib %s.mtl" % NAME)
            elif p[0] == "usemtl":
                out.append("usemtl %s" % NAME)
            else:
                out.append(l)
        b = [tuple(float(x) for x in l.split()[1:4]) for l in out if l.split() and l.split()[0] == "v"]
        bx = (min(v[0] for v in b), max(v[0] for v in b))
        by = (min(v[1] for v in b), max(v[1] for v in b))
        bz = (min(v[2] for v in b), max(v[2] for v in b))
        print(u"  %-6s X %7.4f..%-7.4f Y %7.4f..%-7.4f Z %7.4f..%-7.4f"
              % (facing, bx[0], bx[1], by[0], by[1], bz[0], bz[1]))
        if abs((bx[1] - bx[0]) - 3.0) > 1e-4 or abs((bz[1] - bz[0]) - 3.0) > 1e-4:
            fails.append(u"%s 朝向的平面不是 3×3（X 跨 %.4f，Z 跨 %.4f）"
                         % (facing, bx[1] - bx[0], bz[1] - bz[0]))
        baked[facing] = out

    print(u"\n== ⑤ 写盘 ==")
    if fails and not force:
        print(u"  [STOP] 有 %d 条不过，**没有写任何文件**（要硬来加 --force）" % len(fails))
    elif not write:
        print(u"  预演：没有 --write，未写盘")
    else:
        for facing, out in baked.items():
            dst = os.path.join(OUTDIR, "%s_%s.obj" % (NAME, facing))
            io.open(dst, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
            print(u"  [OK]   %s  (%d 字节)" % (os.path.basename(dst), os.path.getsize(dst)))
        print(u"  ⚠ MTL 与贴图**一个字节都没碰**（本脚本不生成贴图）")
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
