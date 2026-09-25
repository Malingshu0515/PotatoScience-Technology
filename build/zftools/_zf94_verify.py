# -*- coding: utf-8 -*-
r"""_zf94_verify.py —— ZF94 常驻校验：电力高炉两根接线柱**六个面逐面同画**

用户第 3 条：「电力高炉 接线方块还是对称一致一下吧」。ZF92 之后两根柱子只剩**东/西**不一致
（一根格栅、一根素板），本轮把第二根的东/西也换成格栅那对瓦片。

判据（都不靠下标）：
  A 在四份 OBJ 里按几何找出那两根 y 1..2 的 1×1×1，再用面法线认方向，然后**逐面比画**：
    同一个 UV 矩形，或两个矩形在贴图上**逐像素相同**（艺术家给每面各留了副本）—— 六面都必须成立；
  B 其余不动：152 顶点 / 456 vt / 114 面、贴图 sha1、MTL、model JSON；
    以及 ZF92 定下的三面（顶=素板 / 南=金框 / 下=盖板）仍然是那三个**矩形原点**；
  C 补丁工程链在（ZF92 与 ZF94 两份）；
  D 文档；E 成品 jar。
"""
import hashlib
import io
import json
import math
import os
import re
import sys
import zipfile

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
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
TEX_SHA1 = "598c2d8257e6c1ebfa76a25f6ffdbb8f958236ff"
DOWNS = [u"北", u"南", u"东", u"西"]
NAMES = {(147, 100): u"素板", (147, 83): u"金框", (147, 66): u"盖板",
         (154, 151): u"素板", (154, 117): u"金框", (154, 134): u"盖板",
         (149, 0): u"深灰", (47, 161): u"深灰", (47, 144): u"格栅A", (64, 144): u"格栅B"}
# 朝向 → 世界法线 → **工程里的面名**。烘焙是绕 Y 转的，所以"东/西"在四份 OBJ 里落在不同的世界方向；
# ⚠ 第一版直接按世界方向比"东/西用同一个矩形"，四个朝向里有三个必然假 FAIL（数据自己把这张表印出来了：
#   north 的 南=深灰/北=金框/东=格栅B/西=格栅A ⇒ 正好是工程面名转一圈的结果）。
BACK = {
    "south": {(0, 0, 1): u"南", (0, 0, -1): u"北", (1, 0, 0): u"东", (-1, 0, 0): u"西"},
    "east": {(-1, 0, 0): u"北", (1, 0, 0): u"南", (0, 0, -1): u"东", (0, 0, 1): u"西"},
    "north": {(0, 0, -1): u"南", (0, 0, 1): u"北", (-1, 0, 0): u"东", (1, 0, 0): u"西"},
    "west": {(0, 0, -1): u"东", (0, 0, 1): u"西", (1, 0, 0): u"北", (-1, 0, 0): u"南"},
}
EXPECT_ART = {u"上": u"素板", u"下": u"盖板", u"南": u"金框", u"北": u"深灰",
              u"东": u"格栅", u"西": u"格栅"}


def art_name(rect_, tex, w):
    # ⚠ 第一版把字典方向搞反了（`{v: k for k, v in NAMES.items()}` 建出来还是"名字→矩形"，
    #   再用矩形去查当然查不到 ⇒ 全打印成 ?(x,y)、六条断言全假 FAIL）。NAMES 本来就是"矩形→名字"。
    return NAMES.get(rect_[:2], u"?(%d,%d)" % rect_[:2])
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


def normal(vs, f):
    a, b, c = vs[f[0][0]], vs[f[1][0]], vs[f[2][0]]
    u1 = [b[i] - a[i] for i in range(3)]
    u2 = [c[i] - a[i] for i in range(3)]
    n = [u1[1] * u2[2] - u1[2] * u2[1], u1[2] * u2[0] - u1[0] * u2[2], u1[0] * u2[1] - u1[1] * u2[0]]
    ln = math.sqrt(sum(q * q for q in n)) or 1.0
    return [q / ln for q in n]


def rect(vts, f):
    us = [vts[t][0] for _, t in f]
    vs2 = [vts[t][1] for _, t in f]
    return (int(round(min(us) * 256)), int(round(min(vs2) * 256)),
            int(round((max(us) - min(us)) * 256)), int(round((max(vs2) - min(vs2)) * 256)))


def main():
    print(u"=========== ZF94 校验：两根接线柱六个面逐面同画 ===========")
    w, h, _ct, tex = _zf66_png.read_png(TEX)

    def art(r):
        return [tex[(r[1] + y) * w + r[0] + x] for y in range(16) for x in range(16)]

    print(u"\n== A 四份 OBJ：两根柱子逐面同画 ==")
    for facing in ["north", "south", "east", "west"]:
        p = os.path.join(MB, "electric_blast_furnace_%s.obj" % facing)
        if not os.path.exists(p):
            check(u"%s.obj 在" % facing, False)
            continue
        vs, vts, faces = parse_obj(p)
        eq(u"%s 顶点/vt/面" % facing, (152, 456, 114), (len(vs), len(vts), len(faces)))
        posts = []
        for k in range(len(faces) // 6):
            grp = faces[k * 6:(k + 1) * 6]
            pts = [vs[i] for f in grp for i, _ in f]
            xs = [q[0] for q in pts]; ys = [q[1] for q in pts]; zs = [q[2] for q in pts]
            if (abs(max(xs) - min(xs) - 1) < 1e-6 and abs(max(ys) - min(ys) - 1) < 1e-6
                    and abs(max(zs) - min(zs) - 1) < 1e-6 and abs(min(ys) - 1) < 1e-6):
                posts.append(grp)
        eq(u"%s 找到两根柱子" % facing, 2, len(posts))
        if len(posts) != 2:
            continue
        by_dir = []
        for grp in posts:
            d = {}
            for f in grp:
                n = normal(vs, f)
                if abs(n[1] - 1) < 1e-6:
                    d[u"上"] = rect(vts, f)
                elif abs(n[1] + 1) < 1e-6:
                    d[u"下"] = rect(vts, f)
                else:
                    for vec, lab in BACK[facing].items():
                        if all(abs(n[i] - vec[i]) < 1e-6 for i in range(3)):
                            d[lab] = rect(vts, f)
            by_dir.append(d)
        eq(u"%s 每根柱子认全六面" % facing, 6, len(by_dir[0]))
        ok_art, detail = True, []
        for lab in (u"上", u"下", u"南", u"北", u"东", u"西"):
            a, b = by_dir[0][lab], by_dir[1][lab]
            same = (a == b) or (art(a) == art(b))
            if not same:
                ok_art = False
            detail.append(u"%s %s/%s" % (lab, art_name(a, tex, w), art_name(b, tex, w)))
        check(u"%s：两根柱子**六面逐面同画**（%s）" % (facing, u" ".join(detail)), ok_art)
        # 本轮的正题：那对"格栅"面（工程里的 东/西）两根必须用**同一个矩形**
        for lab in (u"东", u"西"):
            eq(u"%s：%s 两根柱子用同一个矩形" % (facing, lab), by_dir[0][lab], by_dir[1][lab])
        # 六面的画各自对不对
        for lab, want in EXPECT_ART.items():
            got = art_name(by_dir[0][lab], tex, w).rstrip(u"AB")
            got2 = art_name(by_dir[1][lab], tex, w).rstrip(u"AB")
            check(u"%s：两根柱子的%s 都是「%s」（实际 %s / %s）" % (facing, lab, want, got, got2),
                  got == want and got2 == want)

    print(u"\n== B 其余不动 ==")
    eq(u"贴图 sha1 未变（%s…）" % TEX_SHA1[:8], TEX_SHA1, sha1f(TEX))
    mtl = read(os.path.join(MB, "electric_blast_furnace.mtl")) or u""
    check(u"MTL 仍指向 block/electric_blast_furnace",
          u"map_Kd potato_s_t:block/electric_blast_furnace" in mtl)
    mj = json.loads(read(os.path.join(MB, "electric_blast_furnace_north.json")) or u"{}")
    check(u"model JSON 仍 flip_v=false / automatic_culling=false",
          mj.get("loader") == "neoforge:obj" and mj.get("flip_v") is False
          and mj.get("automatic_culling") is False)

    print(u"\n== C 补丁工程链 ==")
    for nm in ("_zf92_ebf_fixed.bbmodel", "_zf94_ebf_fixed.bbmodel"):
        check(u"%s 在（改法可复现）" % nm, os.path.exists(os.path.join(TOOLS, nm)))
    check(u"用户原件仍在 zf91_pre\\user\\（未被覆盖）",
          os.path.exists(r"C:\PotatoST救援\zf91_pre\user\electric_blast_furnace.bbmodel"))
    check(u"ZF94 改前件目录在", os.path.isdir(r"C:\PotatoST救援\zf94_pre"))

    print(u"\n== D 文档 ==")
    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    listing = read(os.path.join(DOCS, u"贴图清单.md")) or u""
    check(u"档案里有 ZF94 那一行", u"| ZF94 |" in arch)
    check(u"贴图清单里有 ZF94 一节", u"## ZF94" in listing)

    print(u"\n== E 成品 jar ==")
    if not os.path.exists(JAR):
        check(u"成品 jar 在", False)
    else:
        sha = sha1f(JAR)
        check(u".sha1 与 jar 一致（%s…）" % sha[:8], (read(JAR + u".sha1") or u"").strip() == sha)
        with zipfile.ZipFile(JAR) as zf:
            names = zf.namelist()
            check(u"成品里 assets/ 与 data/ 条目名全合法",
                  not [n for n in names if (n.startswith(u"assets/") or n.startswith(u"data/"))
                       and not re.fullmatch(u"[a-z0-9/._-]+", n)])
            same = 0
            for f in ("north", "south", "east", "west"):
                rel = u"assets/potato_s_t/models/block/electric_blast_furnace_%s.obj" % f
                disk = os.path.join(MB, u"electric_blast_furnace_%s.obj" % f)
                if rel in names and zf.read(rel) == open(disk, "rb").read():
                    same += 1
            eq(u"成品里四份 OBJ 与盘上逐字节一致", 4, same)

    print(u"\n通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
