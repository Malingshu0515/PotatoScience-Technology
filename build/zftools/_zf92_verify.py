# -*- coding: utf-8 -*-
r"""_zf92_verify.py —— ZF92 常驻校验：电力高炉两根「接线柱」的 UV 归属（用户选的 A 方案）

事实（改完之后应当永远成立）：
  两根柱子（塔的 ±X 两侧、y 1..2 格的 1×1×1）六面用图变成
      顶面 = 素板(浅灰横纹)   正面(结构南面) = 金框方块   底面 = 带铆钉盖板
  其余各面（北=深灰、#01 的东/西=格栅、#02 的东/西=素板）不动。

判据刻意**不按下标**：先在 OBJ 里按几何找出那两根 1×1×1 的柱子，再用面法线认方向。
四个朝向的 OBJ 里"正面"的法线分别是 +Z/+X/−Z/−X（烘焙是绕 Y 转的），所以逐个核。
"""
import hashlib
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
MB = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\block")
TEX = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png")
DOCS = os.path.join(ROOT, "docs")
TOOLS = os.path.join(ROOT, "build", "zftools")
USERART = os.path.join(ROOT, "build", u"用户素材")
BK = r"C:\PotatoST救援\zf92_pre"
BB_KEEP = r"C:\PotatoST救援\zf91_pre\user\electric_blast_furnace.bbmodel"
BB_FIXED = os.path.join(TOOLS, "_zf92_ebf_fixed.bbmodel")
BB_SHA256 = "15028bf3d0dc6e7234ea03ec6a697b72858bc12ff7383c401b7c394fd2aab366"
TEX_SHA1 = "598c2d8257e6c1ebfa76a25f6ffdbb8f958236ff"
# 瓦片（贴图像素原点）→ 名字
PLAIN1, GOLD1, LID1 = (147, 100), (147, 83), (147, 66)
PLAIN2, GOLD2, LID2 = (154, 151), (154, 117), (154, 134)
POST_TRIPLES = [{"上": PLAIN1, "南": GOLD1, "下": LID1},
                {"上": PLAIN2, "南": GOLD2, "下": LID2}]
# 朝向 → 结构"正面"在 OBJ 里的法线
FRONT_N = {"south": (0, 0, 1), "east": (1, 0, 0), "north": (0, 0, -1), "west": (-1, 0, 0)}
passed = 0
failed = 0
fails = []


def check(label, cond):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label)
        print(u"  [FAIL] " + label)


def eq(label, want, got):
    check(u"%s（期望 %r，实际 %r）" % (label, want, got), want == got)


def read(p):
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else None


def sha1f(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def parse_obj(p):
    vs, vts, faces = [], [], []
    for raw in io.open(p, encoding="utf-8", errors="replace"):
        t = raw.split()
        if not t:
            continue
        if t[0] == "v":
            vs.append(tuple(float(x) for x in t[1:4]))
        elif t[0] == "vt":
            vts.append(tuple(float(x) for x in t[1:3]))
        elif t[0] == "f":
            faces.append([(int(a.split("/")[0]) - 1, int(a.split("/")[1]) - 1) for a in t[1:]])
    return vs, vts, faces


def face_normal(vs, f):
    a, b, c = vs[f[0][0]], vs[f[1][0]], vs[f[2][0]]
    u1 = [b[i] - a[i] for i in range(3)]
    u2 = [c[i] - a[i] for i in range(3)]
    n = [u1[1] * u2[2] - u1[2] * u2[1], u1[2] * u2[0] - u1[0] * u2[2],
         u1[0] * u2[1] - u1[1] * u2[0]]
    ln = math.sqrt(sum(q * q for q in n)) or 1.0
    return [q / ln for q in n]


def tile_of(vts, f):
    us = [vts[t][0] for _, t in f]
    vs2 = [vts[t][1] for _, t in f]
    return (int(round(min(us) * 256)), int(round(min(vs2) * 256)),
            int(round((max(us) - min(us)) * 256)), int(round((max(vs2) - min(vs2)) * 256)))


def main():
    print(u"=========== ZF92 校验：电力高炉两根接线柱的 UV 归属（A 方案）===========")

    print(u"\n== A 四份 OBJ：几何定位两根柱子 + 三面归属 ==")
    for facing in ["north", "south", "east", "west"]:
        p = os.path.join(MB, "electric_blast_furnace_%s.obj" % facing)
        if not os.path.exists(p):
            check(u"%s.obj 在" % facing, False)
            continue
        vs, vts, faces = parse_obj(p)
        eq(u"%s 面数" % facing, 114, len(faces))
        posts = []
        for k in range(len(faces) // 6):
            grp = faces[k * 6:(k + 1) * 6]
            pts = [vs[i] for f in grp for i, _ in f]
            xs = [q[0] for q in pts]
            ys = [q[1] for q in pts]
            zs = [q[2] for q in pts]
            if (abs(max(xs) - min(xs) - 1.0) < 1e-6 and abs(max(ys) - min(ys) - 1.0) < 1e-6
                    and abs(max(zs) - min(zs) - 1.0) < 1e-6 and abs(min(ys) - 1.0) < 1e-6):
                posts.append((k, grp))
        eq(u"%s 里 y 1..2 格的 1×1×1 柱子数" % facing, 2, len(posts))
        if len(posts) != 2:
            continue
        got = []
        for k, grp in posts:
            triple = {}
            for f in grp:
                n = face_normal(vs, f)
                t = tile_of(vts, f)
                if abs(n[1] - 1.0) < 1e-6:
                    triple[u"上"] = t
                elif abs(n[1] + 1.0) < 1e-6:
                    triple[u"下"] = t
                elif all(abs(n[i] - FRONT_N[facing][i]) < 1e-6 for i in range(3)):
                    triple[u"南"] = t
            got.append(triple)
            print(u"    面组 #%02d：上=%s 南(正面)=%s 下=%s"
                  % (k, triple.get(u"上"), triple.get(u"南"), triple.get(u"下")))
        for want in POST_TRIPLES:
            hit = [g for g in got if g.get(u"上", ())[:2] == want[u"上"]
                   and g.get(u"南", ())[:2] == want[u"南"] and g.get(u"下", ())[:2] == want[u"下"]]
            check(u"%s：有一根柱子是 上=素板%s 南=金框%s 下=盖板%s"
                  % (facing, want[u"上"], want[u"南"], want[u"下"]), len(hit) == 1)
        for g in got:
            for lab in (u"上", u"南", u"下"):
                eq(u"%s 面组尺寸仍是 16×16（%s）" % (facing, lab), (16, 16), g[lab][2:])

    print(u"\n== B 补丁工程与用户原件 ==")
    check(u"补丁后的工程留档在（%s）" % os.path.basename(BB_FIXED), os.path.exists(BB_FIXED))
    if os.path.exists(BB_FIXED):
        d = json.loads(io.open(BB_FIXED, encoding="utf-8").read())
        posts = []
        for e in d["elements"]:
            t = [len(e["vertices"]), len(e["faces"])]
            if t != [8, 6]:
                continue
            # 找 16×16 的顶面 + 16×16 的南面 + 16×16 的底面，且三张画正好是那套
            home = {}
            for fk, f in e["faces"].items():
                uu = [f["uv"][k][0] for k in f["vertices"]]
                vv = [f["uv"][k][1] for k in f["vertices"]]
                if int(max(uu)) - int(min(uu)) == 16 and int(max(vv)) - int(min(vv)) == 16:
                    home[(int(min(uu)), int(min(vv)))] = fk
            if PLAIN1 in home and GOLD1 in home and LID1 in home:
                posts.append((e.get("origin"), home))
            if PLAIN2 in home and GOLD2 in home and LID2 in home:
                posts.append((e.get("origin"), home))
        eq(u"补丁工程里两根柱子各自同时出现「素板+金框+盖板」", 2, len(posts))
        eq(u"用户原件 sha256 未变", BB_SHA256,
           hashlib.sha256(open(BB_KEEP, "rb").read()).hexdigest())
    check(u"改前件目录 zf92_pre 在", os.path.isdir(BK))
    if os.path.isdir(BK):
        for rel in [r"src\main\resources\assets\potato_s_t\models\block\electric_blast_furnace_north.obj"]:
            check(u"改前件里有 %s" % rel.split("\\")[-1], os.path.exists(os.path.join(BK, rel)))

    print(u"\n== C 贴图 / MTL / model JSON 一个字节没动 ==")
    eq(u"贴图 sha1 未变（%s…）" % TEX_SHA1[:8], TEX_SHA1, sha1f(TEX))
    w, h, ct, _px = _zf66_png.read_png(TEX)
    eq(u"贴图仍是 256×256 / RGBA", (256, 256, 6), (w, h, ct))
    mtl = read(os.path.join(MB, "electric_blast_furnace.mtl")) or u""
    check(u"MTL 仍指向 block/electric_blast_furnace",
          u"map_Kd potato_s_t:block/electric_blast_furnace" in mtl)
    mj = json.loads(read(os.path.join(MB, "electric_blast_furnace_north.json")) or u"{}")
    check(u"model JSON 仍 flip_v=false / automatic_culling=false / 同一份 OBJ+MTL",
          mj.get("loader") == "neoforge:obj" and mj.get("flip_v") is False
          and mj.get("automatic_culling") is False
          and mj.get("mtl_override") == "potato_s_t:models/block/electric_blast_furnace.mtl")

    print(u"\n== D 文档 ==")
    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    listing = read(os.path.join(DOCS, u"贴图清单.md")) or u""
    check(u"档案里有 ZF92 那一行", u"| ZF92 |" in arch)
    check(u"档案里写清了「顶=素板 / 正面=金框 / 底=盖板」",
          u"素板" in arch and u"金框" in arch and u"ZF92" in arch)
    check(u"贴图清单里有 ZF92 一节", u"## ZF92" in listing)

    print(u"\n== E 用户中途丢进来的那张唱片素材（§4.24 处理过了）==")
    # 用户 2026-09-25 00:07 把 `音乐唱片茉莉花.png` 放进 textures/item ⇒ 资源目录里不能留中文名，
    # 本轮既不建物品也不该让它进 jar：原件留档 + 记凭据 + 从资源目录移走。
    item_dir = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
    block_dir = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\block")
    bad = []
    for d in (item_dir, block_dir):
        if os.path.isdir(d):
            bad += [n for n in os.listdir(d) if not n.isascii()]
    eq(u"两个贴图目录里没有非 ASCII 文件名", [], sorted(bad))
    disc = os.path.join(USERART, "music_disc_jasmine_flower.png")
    check(u"那张唱片素材已留档到 build/用户素材/music_disc_jasmine_flower.png", os.path.exists(disc))
    if os.path.exists(disc):
        cred = json.loads(read(os.path.join(USERART, u"_来源凭据.json")) or u"{}")
        e = cred.get("music_disc_jasmine_flower.png") or {}
        eq(u"留档件 sha1 与凭据一致", sha1f(disc), e.get("sha1"))
        eq(u"凭据里记着原名", u"音乐唱片茉莉花.png", e.get(u"原名"))
    check(u"资源目录里已无原名件", not os.path.exists(os.path.join(item_dir, u"音乐唱片茉莉花.png")))

    print(u"\n通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
