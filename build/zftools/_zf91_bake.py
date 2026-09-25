# -*- coding: utf-8 -*-
r"""_zf91_bake.py —— 拿用户的 `.bbmodel`（Free/mesh 模型）烘出四个朝向的 OBJ（**贴图一个字节不碰**）

这份工程与 ZF39 那份的来源不同，必须先说清三件事（都是实测出来的）：

  ① **它是 Free / mesh 模型**（`meta.model_format = "free"`）：19 个 `type:"mesh"` 元素，
     每个 8 顶点 / 6 面 = **114 个面**；**顶点是"相对该元素 origin 的局部坐标"**，
     世界坐标 = `origin + R(rotation) · v`（rotation 是角度制欧拉角）。
     判据：mesh#05 的局部 Y 是 −13..29（局部读会出现"沉到地板以下"），加上 origin[15,45,0] 才是 32..74
     —— 正好等于旧模型那两根立柱的 Y 2..4.625 格。
  ② **UV 是逐顶点给的真 UV**（456 个不同取值 / 114 个不同矩形）⇒ 这次不需要"猜"面的角点顺序，
     照 Blockbench 给的顶点顺序与 UV 原样写进 OBJ 就行。
  ③ 工程里**内嵌的贴图是 UV 模板**（sha256 `139264fb…`），不是用户的画；
     用户的画 = 我们成品里在用的那张（与用户发的图一**逐字节相同**）⇒ **贴图不动**。

烘焙与 ZF39/ZF89 同一套坐标约定（照 §12.2/§12.6）：
    p' = C + R_y(θ) · (p + t − C)，  t = (0.5 − 模型中心X, 0, −0.5 − 模型中心Z)，  C = (0.5, 0, 0.5)
四个朝向：south θ=0 / east θ=π/2 / north θ=π / west θ=−π/2。

用法：
    python _zf91_bake.py            # 预演（只报告，不写盘）
    python _zf91_bake.py --write    # 真的写四份 OBJ
"""
import io
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _zf66_png  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
HERE = os.path.dirname(os.path.abspath(__file__))
BB = r"C:\Users\Administrator\.dsh\attachments\v1\files\15\15028bf3d0dc6e7234ea03ec6a697b72858bc12ff7383c401b7c394fd2aab366\电力高炉.bbmodel"
OUTDIR = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\block")
TEX = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png")
NAME = "electric_blast_furnace"
FACINGS = {"south": 0.0, "east": math.pi / 2, "north": math.pi, "west": -math.pi / 2}
C = (0.5, 0.0, 0.5)
STRUCT_CX, STRUCT_CZ = 0.5, -0.5
EXPECT_H = 4.9375          # 旧模型的高度（格）—— 新模型应当一样
fails = []


def rot_mat(rx, ry, rz, order):
    u"""角度制欧拉角 → 3x3 旋转矩阵。order 为 'XYZ' 或 'ZYX'（THREE 的写法：
    'XYZ' = 先绕 X 再绕 Y 再绕 Z 的**内旋**，即 R = Rx·Ry·Rz）。"""
    def ax(a, i):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        if i == 0:
            return [[1, 0, 0], [0, c, -s], [0, s, c]]
        if i == 1:
            return [[c, 0, s], [0, 1, 0], [-s, 0, c]]
        return [[c, -s, 0], [s, c, 0], [0, 0, 1]]

    def mul(a, b):
        return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

    Rx, Ry, Rz = ax(rx, 0), ax(ry, 1), ax(rz, 2)
    return mul(mul(Rx, Ry), Rz) if order == "XYZ" else mul(mul(Rz, Ry), Rx)


def apply(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def parse_bbmodel(order):
    d = json.loads(io.open(BB, encoding="utf-8").read())
    W = d["resolution"]["width"]; H = d["resolution"]["height"]
    meshes = []
    for e in d.get("elements", []):
        if e.get("type") != "mesh":
            continue
        o = e.get("origin", [0, 0, 0])
        rot = e.get("rotation", [0, 0, 0])
        m = rot_mat(rot[0], rot[1], rot[2], order)
        lv = {k: tuple(v) for k, v in e.get("vertices", {}).items()}
        wv = {}
        for k, v in lv.items():
            p = apply(m, v)
            wv[k] = (o[0] + p[0], o[1] + p[1], o[2] + p[2])
        faces = []
        for fid, fc in e.get("faces", {}).items():
            vids = fc.get("vertices", [])
            uvd = fc.get("uv", {})
            faces.append((vids, uvd))
        meshes.append({"name": e.get("name"), "origin": list(o), "rotation": list(rot),
                       "local": lv, "world": wv, "faces": faces})
    return W, H, meshes


def all_points(meshes):
    return [p for m in meshes for p in m["world"].values()]


def _pair(meshes):
    u"""按 **origin 关于 Z=0 镜像、且 rotation 的 X 分量相反** 找那一对元素
    （本工程即 origin [0,58,−13] rot [10,−90,0] 与 origin [0,58,13] rot [−10,−90,0]）。"""
    for a in meshes:
        for b in meshes:
            oa, ob = a["origin"], b["origin"]
            ra, rb = a["rotation"], b["rotation"]
            if abs(oa[0] - ob[0]) < 1e-9 and abs(oa[1] - ob[1]) < 1e-9 \
                    and abs(oa[2] + ob[2]) < 1e-9 and abs(oa[2]) > 1e-9 \
                    and abs(ra[0] + rb[0]) < 1e-9 and abs(ra[0]) > 1e-9 \
                    and abs(ra[1] - rb[1]) < 1e-9 and abs(ra[2] - rb[2]) < 1e-9:
                return a, b
    return None, None


def mirror_err(meshes, order):
    u"""用上面那对镜像元素给欧拉角顺序定案：把 A 的世界顶点按 z→−z 镜像后与 B 逐点比，
    **误差为 0 的那个顺序才是对的**（实测：XYZ = 0.000000，ZYX = 252.11 ⇒ 本工程用 XYZ）。
    ⚠ 第一版"随便挑一对"定不了案（两个顺序误差一模一样），这里改成按 origin+rotation 精确配对。"""
    a, b = _pair(meshes)
    if a is None:
        return None
    oa, ob = a["origin"], b["origin"]
    ma, mb = a["local"], b["local"]
    Ra = rot_mat(a["rotation"][0], a["rotation"][1], a["rotation"][2], order)
    Rb = rot_mat(b["rotation"][0], b["rotation"][1], b["rotation"][2], order)
    def w(pt, o, R):
        p = apply(R, pt)
        return (o[0] + p[0], o[1] + p[1], o[2] + p[2])

    pa = sorted(tuple(round(x, 4) for x in (w(v, oa, Ra)[0], w(v, oa, Ra)[1], -w(v, oa, Ra)[2]))
                for v in ma.values())
    pb = sorted(tuple(round(x, 4) for x in w(v, ob, Rb)) for v in mb.values())
    if len(pa) != len(pb):
        return None
    return sum(max(abs(x - y) for x, y in zip(p, q)) for p, q in zip(pa, pb))


def main(argv):
    write = "--write" in argv
    print(u"== ① 读工程，两个欧拉顺序各算一遍，用镜像对定案 ==")
    W, H, m_xyz = parse_bbmodel("XYZ")
    _, _, m_zyx = parse_bbmodel("ZYX")
    e_xyz, e_zyx = mirror_err(m_xyz, "XYZ"), mirror_err(m_zyx, "ZYX")
    print(u"  XYZ 顺序的镜像误差 = %s" % e_xyz)
    print(u"  ZYX 顺序的镜像误差 = %s" % e_zyx)
    if e_xyz is None or e_zyx is None:
        fails.append(u"找不到那对指定的镜像元素，无法给欧拉顺序定案")
        order = "XYZ"
    else:
        order = "XYZ" if e_xyz <= e_zyx else "ZYX"
        best = min(e_xyz, e_zyx)
        if best > 1.0:
            fails.append(u"两个顺序的镜像误差都很大（XYZ %.4f / ZYX %.4f）⇒ 定不了案"
                         % (e_xyz, e_zyx))
    print(u"  ⇒ 采用 **%s** 顺序（Blockbench 的 ZYX 默认在本工程不成立；按镜像误差取小的）" % order)
    W, H, meshes = parse_bbmodel(order)
    nfaces = sum(len(m["faces"]) for m in meshes)
    print(u"  分辨率 %dx%d；mesh %d 个；面 %d 个" % (W, H, len(meshes), nfaces))
    if nfaces != 114:
        fails.append(u"面数不是 114（%d）" % nfaces)

    print(u"\n== ② 世界坐标包围盒（工程单位与格）==")
    pts = all_points(meshes)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; zs = [p[2] for p in pts]
    print(u"  X %8.3f..%-8.3f Y %8.3f..%-8.3f Z %8.3f..%-8.3f（工程单位）"
          % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    print(u"  X %8.4f..%-8.4f Y %8.4f..%-8.4f Z %8.4f..%-8.4f（格）"
          % (min(xs) / 16, max(xs) / 16, min(ys) / 16, max(ys) / 16, min(zs) / 16, max(zs) / 16))
    h = (max(ys) - min(ys)) / 16.0
    print(u"  高 %.4f 格（旧模型 %.4f）" % (h, EXPECT_H))
    if abs(h - EXPECT_H) > 0.02:
        fails.append(u"高度与旧模型对不上（%.4f vs %.4f）" % (h, EXPECT_H))
    if abs((max(xs) - min(xs)) / 16.0 - 3.0) > 0.02 or abs((max(zs) - min(zs)) / 16.0 - 3.0) > 0.02:
        fails.append(u"平面不是 3×3 格")

    print(u"\n== ③ 逐面 UV 矩形在成品贴图上是否全不透明 ==")
    w, hh, ct, px = _zf66_png.read_png(TEX)
    print(u"  贴图 %dx%d，不透明 %d 像素" % (w, hh, sum(1 for p in px if p[3] != 0)))
    bad = []
    rects = []
    for m in meshes:
        name, wv, faces = m["name"], m["world"], m["faces"]
        for vids, uvd in faces:
            us = [uvd[k][0] for k in vids if k in uvd]
            vs = [uvd[k][1] for k in vids if k in uvd]
            if not us:
                continue
            x0, x1 = int(min(us)), int(max(us))
            y0, y1 = int(min(vs)), int(max(vs))
            rects.append((x0, y0, x1, y1))
            t = n = 0
            for y in range(max(0, y0), min(hh, y1)):
                for x in range(max(0, x0), min(w, x1)):
                    n += 1
                    if px[y * w + x][3] == 0:
                        t += 1
            if t:
                bad.append((name, (x0, y0, x1, y1), t, n))
    print(u"  UV 矩形 %d 个（去重 %d 个）；压到透明像素的 %d 个"
          % (len(rects), len(set(rects)), len(bad)))
    for nm, r, t, n in bad:
        print(u"     %-6s (%3d,%3d)-(%3d,%3d)  %3dx%-3d  %d/%d 像素透明"
              % (nm, r[0], r[1], r[2], r[3], r[2] - r[0], r[3] - r[1], t, n))
    if bad:
        print(u"  ⚠ 这些面在游戏里会是「没画到」的地方 —— 报给用户，不静默发版（但**不阻止烘焙**：")
        print(u"     先按用户的 UV 原样上线，缺口清单单独列出来）")

    print(u"\n== ④ 烘四个朝向 ==")
    t = (STRUCT_CX - (min(xs) + max(xs)) / 32.0, 0.0, STRUCT_CZ - (min(zs) + max(zs)) / 32.0)
    print(u"  平移 t = (%.4f, 0, %.4f) 格（模型中心 → 结构中心）" % (t[0], t[2]))
    baked = {}
    for facing, theta in sorted(FACINGS.items()):
        co, si = math.cos(theta), math.sin(theta)
        lines = [u"# Made in Blockbench 5.1.6（ZF91：由 %s.bbmodel 烘出，%s 顺序欧拉角）" % (u"电力高炉", order),
                 u"mtllib %s.mtl" % NAME, u"", u"o mesh"]
        vt_lines, vn_lines, f_lines = [], [], []
        nv = 0
        for m in meshes:
            name, wv, faces = m["name"], m["world"], m["faces"]
            idx = {}
            for k, p in wv.items():
                nv += 1
                idx[k] = nv
                x, y, z = p[0] / 16.0 + t[0], p[1] / 16.0, p[2] / 16.0 + t[2]
                x, z = x - C[0], z - C[2]
                x, z = x * co + z * si, -x * si + z * co
                lines.append(u"v %.6f %.6f %.6f" % (x + C[0], y, z + C[2]))
            for vids, uvd in faces:
                base = len(vt_lines)
                for k in vids:
                    u, v = uvd[k]
                    vt_lines.append(u"vt %.6f %.6f" % (u / float(W), v / float(H)))
                # 面法线（用变换后的顶点算，右手系）
                p0 = wv[vids[0]]
                def tf(p):
                    x, y, z = p[0] / 16.0 + t[0], p[1] / 16.0, p[2] / 16.0 + t[2]
                    x, z = x - C[0], z - C[2]
                    x, z = x * co + z * si, -x * si + z * co
                    return (x + C[0], y, z + C[2])
                a, b, c = tf(p0), tf(wv[vids[1]]), tf(wv[vids[2]])
                u1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
                u2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
                nx = u1[1] * u2[2] - u1[2] * u2[1]
                ny = u1[2] * u2[0] - u1[0] * u2[2]
                nz = u1[0] * u2[1] - u1[1] * u2[0]
                ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
                vn_lines.append(u"vn %.6f %.6f %.6f" % (nx / ln, ny / ln, nz / ln))
                ni = len(vn_lines)
                f_lines.append(u"f " + u" ".join(
                    u"%d/%d/%d" % (idx[k], base + i + 1, ni) for i, k in enumerate(vids)))
        body = lines + vt_lines + vn_lines + [u"usemtl %s" % NAME] + f_lines
        vv = [tuple(float(x) for x in l.split()[1:4]) for l in body if l.startswith(u"v ")]
        bx = (min(p[0] for p in vv), max(p[0] for p in vv))
        by = (min(p[1] for p in vv), max(p[1] for p in vv))
        bz = (min(p[2] for p in vv), max(p[2] for p in vv))
        print(u"  %-6s X %7.4f..%-7.4f Y %7.4f..%-7.4f Z %7.4f..%-7.4f   v=%d f=%d"
              % (facing, bx[0], bx[1], by[0], by[1], bz[0], bz[1], len(vv), len(f_lines)))
        exp = {u"south": ((-1, 2), (-2, 1)), u"north": ((-1, 2), (0, 3)),
               u"east": ((-2, 1), (-1, 2)), u"west": ((0, 3), (-1, 2))}[facing]
        if abs(bx[0] - exp[0][0]) > 1e-3 or abs(bx[1] - exp[0][1]) > 1e-3 \
                or abs(bz[0] - exp[1][0]) > 1e-3 or abs(bz[1] - exp[1][1]) > 1e-3:
            fails.append(u"%s 的包围盒与结构对不上：X %.3f..%.3f Z %.3f..%.3f（期望 X %s Z %s）"
                         % (facing, bx[0], bx[1], bz[0], bz[1], exp[0], exp[1]))
        baked[facing] = body

    print(u"\n== ⑤ 写盘 ==")
    if fails:
        print(u"  [STOP] 上面 %d 条不过 ⇒ 不写任何文件" % len(fails))
    elif not write:
        print(u"  预演：没加 --write，未写盘")
    else:
        for facing, body in baked.items():
            dst = os.path.join(OUTDIR, "%s_%s.obj" % (NAME, facing))
            io.open(dst, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(body) + u"\n")
            print(u"  [OK]   %s（%d 字节）" % (os.path.basename(dst), os.path.getsize(dst)))
        print(u"  ⚠ MTL 与贴图**一个字节都没碰**")
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
