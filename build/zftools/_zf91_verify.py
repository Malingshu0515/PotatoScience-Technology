# -*- coding: utf-8 -*-
r"""_zf91_verify.py —— ZF91 常驻校验：电力高炉换成用户 `.bbmodel` 烘出来的四份 OBJ（真 UV）

关键几条（都是"换了必须成立、换错必然挂"的）：
  A 四份 OBJ：152 顶点 / 456 vt / 114 面；**vt 不同取值远多于 4**（不再是"整张贴图铺每个面"）；
    **每个面的 UV 矩形在贴图上没有透明像素**；UV 矩形尺寸与面的世界尺寸（×16）对得上；
    包围盒仍罩住 3×3×4.9375（四朝向逐个核）。
  B 贴图与 model JSON **一个字节没动**（本轮只换模型）。
  C `.bbmodel` 原件留档在 `zf91_pre\user\`（sha256 对得上）。
  D 文档；E 成品 jar；F 文档与产物一致性（沿用 ZF90 的 H 段）。
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
MI = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\item")
TEX = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png")
DOCS = os.path.join(ROOT, "docs")
TOOLS = os.path.join(ROOT, "build", "zftools")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
BK = r"C:\PotatoST救援\zf91_pre"
BB_KEEP = os.path.join(BK, "user", "electric_blast_furnace.bbmodel")
BB_SHA256 = "15028bf3d0dc6e7234ea03ec6a697b72858bc12ff7383c401b7c394fd2aab366"
TEX_SHA1 = "598c2d8257e6c1ebfa76a25f6ffdbb8f958236ff"
FACINGS = {"south": ((-1, 2), (-2, 1)), "north": ((-1, 2), (0, 3)),
           "east": ((-2, 1), (-1, 2)), "west": ((0, 3), (-1, 2))}
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
            faces.append([(int(a.split("/")[0]) - 1,
                           int(a.split("/")[1]) - 1 if len(a.split("/")) > 1 and a.split("/")[1] else None)
                          for a in t[1:]])
    return vs, vts, faces


def main():
    print(u"=========== ZF91 校验：电力高炉 ===== 用户 .bbmodel 烘出的四份 OBJ ===========")
    w, h, ct, tex = _zf66_png.read_png(TEX)
    print(u"\n== A 四份 OBJ ==")
    for facing, (ex, ez) in sorted(FACINGS.items()):
        p = os.path.join(MB, "%s_%s.obj" % ("electric_blast_furnace", facing))
        check(u"%s.obj 在" % facing, os.path.exists(p))
        if not os.path.exists(p):
            continue
        vs, vts, faces = parse_obj(p)
        eq(u"%s 顶点数" % facing, 152, len(vs))
        eq(u"%s vt 数" % facing, 456, len(vts))
        eq(u"%s 面数" % facing, 114, len(faces))
        uvs = set(vts)
        check(u"%s 的 vt 不同取值 %d 个（**远多于 4** = 真 UV，不再是整张贴图铺每个面）"
              % (facing, len(uvs)), len(uvs) > 4)
        body = read(p) or u""
        check(u"%s 的 mtllib / usemtl 都对" % facing,
              u"mtllib electric_blast_furnace.mtl" in body
              and u"usemtl electric_blast_furnace" in body)
        # UV 矩形：不透明 + 尺寸与面的世界尺寸对得上
        bad = 0
        size_bad = 0
        for f in faces:
            uvl = [vts[t] for _, t in f if t is not None]
            us = [q[0] for q in uvl]; vv = [q[1] for q in uvl]
            x0, x1 = int(round(min(us) * w)), int(round(max(us) * w))
            y0, y1 = int(round(min(vv) * h)), int(round(max(vv) * h))
            for y in range(y0, y1):
                for x in range(x0, x1):
                    if tex[y * w + x][3] == 0:
                        bad += 1
            # 面的世界尺寸（两条边）×16 应当等于 UV 矩形的两边
            pts = [vs[i] for i, _ in f]
            e1 = math.dist(pts[0], pts[1]) * 16.0
            e2 = math.dist(pts[1], pts[2]) * 16.0
            rw, rh = x1 - x0, y1 - y0
            if sorted((round(e1), round(e2))) != sorted((rw, rh)):
                size_bad += 1
        eq(u"%s 每个面的 UV 矩形都落在画好的地方（透明像素总数）" % facing, 0, bad)
        eq(u"%s 每个面的 UV 矩形尺寸 = 面的世界尺寸（不符的面数）" % facing, 0, size_bad)
        xs = [q[0] for q in vs]; ys = [q[1] for q in vs]; zs = [q[2] for q in vs]
        eq(u"%s 包围盒 X（%s）" % (facing, ex), (float(ex[0]), float(ex[1])),
           (round(min(xs), 4), round(max(xs), 4)))
        eq(u"%s 包围盒 Z（%s）" % (facing, ez), (float(ez[0]), float(ez[1])),
           (round(min(zs), 4), round(max(zs), 4)))
        eq(u"%s 高仍是 4.9375 格" % facing, 4.9375, round(max(ys) - min(ys), 4))

    print(u"\n== B 贴图与 model JSON 一个字节没动 ==")
    eq(u"贴图 sha1 未变（%s…）" % TEX_SHA1[:8], TEX_SHA1, sha1f(TEX))
    eq(u"贴图仍是 256×256 / RGBA", (256, 256, 6), (w, h, ct))
    mj = json.loads(read(os.path.join(MB, "electric_blast_furnace_north.json")) or u"{}")
    check(u"model JSON 仍指同一份 OBJ / MTL / flip_v=false / automatic_culling=false",
          mj.get("loader") == "neoforge:obj"
          and mj.get("flip_v") is False and mj.get("automatic_culling") is False
          and mj.get("mtl_override") == "potato_s_t:models/block/electric_blast_furnace.mtl")
    mtl = read(os.path.join(MB, "electric_blast_furnace.mtl")) or u""
    check(u"MTL 仍指向 block/electric_blast_furnace",
          u"map_Kd potato_s_t:block/electric_blast_furnace" in mtl)

    print(u"\n== C 用户工程原件留档 ==")
    check(u"`zf91_pre\\user\\electric_blast_furnace.bbmodel` 在", os.path.exists(BB_KEEP))
    if os.path.exists(BB_KEEP):
        eq(u"原件 sha256 与收到的那个一致", BB_SHA256,
           hashlib.sha256(open(BB_KEEP, "rb").read()).hexdigest())

    print(u"\n== D 文档 ==")
    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    listing = read(os.path.join(DOCS, u"贴图清单.md")) or u""
    check(u"档案里有 ZF91 那一行", u"| ZF91 |" in arch)
    check(u"档案 §4.58 已改成「已修」的新真相（不再写「待修」）",
          u"已修" in arch and u"4 个 UV 点" in arch)
    check(u"贴图清单里有 ZF91 一节", u"## ZF91（0.11）" in listing)

    print(u"\n== E 成品 jar ==")
    if not os.path.exists(JAR):
        check(u"成品 jar 存在", False)
    else:
        rec = read(JAR + u".sha1")
        check(u".sha1 与 jar 一致（%s…）" % sha1f(JAR)[:8],
              rec is not None and rec.strip().lower() == sha1f(JAR))
        with zipfile.ZipFile(JAR) as zf:
            names = zf.namelist()
            bad = [n for n in names if u"Check" in n.split(u"/")[-1] and n.endswith(u".class")]
            check(u"成品里没有探针 class（%s）" % (bad or u"0 个"), not bad)
            for facing in sorted(FACINGS):
                e = u"assets/potato_s_t/models/block/electric_blast_furnace_%s.obj" % facing
                check(u"成品里的 %s.obj 与盘上一致" % facing,
                      e in names and zf.read(e) == open(
                          os.path.join(MB, u"electric_blast_furnace_%s.obj" % facing), "rb").read())
            e = u"assets/potato_s_t/textures/block/electric_blast_furnace.png"
            check(u"成品里的贴图与盘上一致",
                  e in names and zf.read(e) == open(TEX, "rb").read())

    print(u"\n== F 文档与产物一致性 ==")
    rel_sha = (read(JAR + u".sha1") or u"").strip().lower()
    last = None
    for l in arch.split(u"\n"):
        if l.startswith(u"**成品**：") and u"PotatoST-0.11.jar" in l:
            last = l
    check(u"§9 里有「**成品**」那一行", last is not None)
    if last:
        m = re.search(r"`([0-9a-f]{40})`", last)
        got = m.group(1) if m else u"(没读到)"
        eq(u"最新「**成品**」行的哈希 == release\\.sha1（%s…）" % got[:8], rel_sha, got)
        check(u"最新那行不是「当时的成品」", not last.startswith(u"**当时的成品**"))

    print(u"\n------------------------------")
    print(u"通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
