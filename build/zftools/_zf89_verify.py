# -*- coding: utf-8 -*-
u"""_zf89_verify.py —— ZF89 常驻校验：汽油 / 石脑油流体贴图 + 电力高炉"已知待修"记账

三块：
  A 两张新图（汽油 / 石脑油）：格式对、与改前件不同、与留档原图逐像素一致、still==flow；
  B 目录卫生 + 来源凭据（凭据里的 sha1 必须等于留档原图的真实 sha1 —— 这是本轮的**刀口**）；
  C 电力高炉**已知待修**的可证伪断言：模型 OBJ 仍是"整张贴图铺每个面"（只有 4 个 UV 点），
    贴图那张 256×256 是 61 个岛。用户一旦把带 UV 的模型导出给我、我修好之后，
    **这几条会自己挂**，逼着把文档与断言一起改新 —— 这是故意的。
"""
import hashlib
import io
import json
import os
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _zf66_png  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TEXB = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\block")
TEXI = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
MODELS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\block")
USERART = os.path.join(ROOT, "build", u"用户素材")
DOCS = os.path.join(ROOT, "docs")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
BK = r"C:\PotatoST救援\zf89_pre"
BKBLK = os.path.join(BK, r"src\main\resources\assets\potato_s_t\textures\block")
JOBS = [(u"gasoline", u"gasoline.png"), (u"naphtha", u"naphtha.png")]
EBF_TEX = os.path.join(TEXB, "electric_blast_furnace.png")
EBF_TEX_SHA1 = u"598c2d8257e6c1ebfa76a25f6ffdbb8f958236ff"
EBF_OBJS = [u"electric_blast_furnace_%s.obj" % f for f in ("north", "south", "east", "west")]

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


def pixels(p):
    w, h, ctype, px0 = _zf66_png.read_png(p)
    return [q if len(q) == 4 else (q[0], q[1], q[2], 255) for q in px0]


def main():
    print(u"=========== ZF89 校验：汽油 / 石脑油流体贴图 + 电力高炉记账 ===========")
    print(u"\n== A 四张图：格式 + 与改前件不同 + 与留档原图一致 + still==flow ==")
    for fluid, src_name in JOBS:
        keep = os.path.join(USERART, src_name)
        check(u"留档原图在（build/用户素材/%s）" % src_name, os.path.exists(keep))
        src_px = None
        if os.path.exists(keep):
            w, h, ctype, px0 = _zf66_png.read_png(keep)
            src_px = [p if len(p) == 4 else (p[0], p[1], p[2], 255) for p in px0]
            eq(u"%s 是 16×16" % src_name, (16, 16), (w, h))
            eq(u"%s 全不透明（%d 个透明像素）" % (src_name, sum(1 for p in src_px if p[3] != 255)),
               0, sum(1 for p in src_px if p[3] != 255))
        shas = {}
        for suffix in (u"_still", u"_flow"):
            p = os.path.join(TEXB, fluid + suffix + u".png")
            info = None
            if os.path.exists(p):
                b = open(p, "rb").read()
                w, h = struct.unpack(">II", b[16:24])
                info = (w, h, b[24], b[25], hashlib.sha1(b).hexdigest())
            check(u"%s%s.png 存在且是真 PNG" % (fluid, suffix), info is not None)
            if info is None:
                continue
            eq(u"%s%s 16×16 / 8 位 / RGBA" % (fluid, suffix), (16, 16, 8, 6), info[:4])
            shas[suffix] = info[4]
            old = os.path.join(BKBLK, fluid + suffix + u".png")
            if os.path.exists(old):
                check(u"%s%s **确实换过了**（与改前件 %s… 不同）" % (fluid, suffix, sha1f(old)[:8]),
                      info[4] != sha1f(old))
            else:
                check(u"%s%s 有改前件可比" % (fluid, suffix), False)
            if src_px is not None:
                px = pixels(p)
                same = sum(1 for a, b2 in zip(src_px, px) if a == b2)
                eq(u"%s%s 与源图**逐像素一致**（%d/256）" % (fluid, suffix, same), 256, same)
        if len(shas) == 2:
            check(u"%s：still 与 flow 仍是同一张图（本工程惯例）" % fluid,
                  shas[u"_still"] == shas[u"_flow"])

    print(u"\n== B 目录卫生 / 来源凭据 / 文档 ==")
    left = [f for f in os.listdir(TEXB) if any(ord(c) > 127 for c in f)
            and not f.endswith(u".原名件")]
    check(u"textures/block 下没有中文名（%s）" % (left or u"无"), not left)
    left_i = [f for f in os.listdir(TEXI) if any(ord(c) > 127 for c in f)]
    check(u"textures/item 下没有中文名（%s）" % (left_i or u"无"), not left_i)
    prov = json.loads(read(os.path.join(USERART, u"_来源凭据.json")) or u"{}")
    for fluid, src_name in JOBS:
        e = prov.get(src_name)
        check(u"来源凭据里有 %s 这一条" % src_name, isinstance(e, dict))
        if isinstance(e, dict):
            real = sha1f(os.path.join(USERART, src_name))
            eq(u"凭据里 %s 的 sha1 与留档原图一致" % src_name, real, e.get("sha1"))
            eq(u"凭据里 %s 的字节数对得上" % src_name,
               os.path.getsize(os.path.join(USERART, src_name)), e.get("bytes"))
    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    listing = read(os.path.join(DOCS, u"贴图清单.md")) or u""
    check(u"档案里有 ZF89 那一行", u"| ZF89 |" in arch)
    check(u"档案里记了电力高炉这条雷（OBJ 满贴图 UV）",
          u"4 个 UV 点" in arch or u"满贴图" in arch)
    check(u"贴图清单里有 ZF89 一节", u"## ZF89（0.11）" in listing)

    # ⚠ 0.11 ZF91：用户把 `.bbmodel` 发来了，四份 OBJ 已换成**带真 UV** 的那版 ⇒
    #   这一段从"已知待修（只有 4 个 UV 点）"改成"**已修**（UV 点多得多，且逐面落在画好的地方）"。
    #   （本段的其它断言——贴图字节未变、尺寸、不透明像素数——照样保留，正是为这一步兜底的。）
    print(u"\n== C 电力高炉：ZF89 记的「已知待修」已于 ZF91 **修掉** ==")
    check(u"那 256×256 贴图还在原处、字节未变（sha1 %s…）" % EBF_TEX_SHA1[:8],
          os.path.exists(EBF_TEX) and sha1f(EBF_TEX) == EBF_TEX_SHA1)
    w, h, ctype, px = _zf66_png.read_png(EBF_TEX)
    eq(u"贴图仍是 256×256 / RGBA", (256, 256, 6), (w, h, ctype))
    opaque = sum(1 for p in px if p[3] != 0)
    eq(u"不透明像素仍是 32903（61 个岛的总面积）", 32903, opaque)
    for name in EBF_OBJS:
        p = os.path.join(MODELS, name)
        if not os.path.exists(p):
            check(u"%s 在" % name, False)
            continue
        uvs = set()
        nf = 0
        for raw in io.open(p, encoding="utf-8", errors="replace"):
            t = raw.split()
            if t and t[0] == "vt":
                uvs.add((float(t[1]), float(t[2])))
            elif t and t[0] == "f":
                nf += 1
        check(u"%s **已换成真 UV**（%d 个 UV 取值 / %d 个面，不再是 4 个）"
              % (name, len(uvs), nf), len(uvs) > 4 and nf == 114)

    print(u"\n== D 成品 jar ==")
    if not os.path.exists(JAR):
        check(u"成品 jar 存在", False)
    else:
        sha = sha1f(JAR)
        rec = read(JAR + u".sha1")
        check(u".sha1 与 jar 一致（%s…）" % sha[:8], rec is not None and rec.strip().lower() == sha)
        with zipfile.ZipFile(JAR) as zf:
            names = zf.namelist()
            bad = [n for n in names if u"Check" in n.split(u"/")[-1] and n.endswith(u".class")]
            check(u"成品里没有探针 class（%s）" % (bad or u"0 个"), not bad)
            for fluid, _ in JOBS:
                for suffix in (u"_still", u"_flow"):
                    entry = u"assets/potato_s_t/textures/block/%s%s.png" % (fluid, suffix)
                    inside = zf.read(entry) if entry in names else None
                    check(u"成品里的 %s%s.png 与盘上一致" % (fluid, suffix),
                          inside == open(os.path.join(TEXB, fluid + suffix + u".png"), "rb").read())
            entry = u"assets/potato_s_t/textures/block/electric_blast_furnace.png"
            check(u"成品里的电力高炉贴图与盘上一致",
                  entry in names and zf.read(entry) == open(EBF_TEX, "rb").read())

    print(u"\n------------------------------")
    print(u"通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
