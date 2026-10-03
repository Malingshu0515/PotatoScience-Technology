# -*- coding: utf-8 -*-
u"""_zf88_verify.py —— ZF88 交付校验：原油 / 柴油的流体贴图换新

（用户又直接放了两张进 textures/block：石油.png / 柴油.png。
 本轮不写代码，只把图转写到 still+flow —— 校验就盯"真换了 / 格式对 / 与源图一致 / still==flow / 成品里有"。）
"""
import hashlib
import io
import json
import os
import struct
import sys
import zipfile
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _zf66_png  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TEXB = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\block")
USERART = os.path.join(ROOT, "build", u"用户素材")
DOCS = os.path.join(ROOT, "docs")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
BK = r"C:\PotatoST救援\zf88_pre\block"
JOBS = [(u"crude_oil", u"crude_oil.png"), (u"diesel", u"diesel.png")]

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


def main():
    print(u"=========== ZF88 校验：石油 / 柴油流体贴图 ===========")
    print(u"\n== A 四张图：格式 + 与源图一致 + 与旧图不同 ==")
    for fluid, src_name in JOBS:
        src_p = os.path.join(USERART, src_name)
        check(u"原图留档在（build/用户素材/%s）" % src_name, os.path.exists(src_p))
        src_px = None
        if os.path.exists(src_p):
            w, h, ctype, px0 = _zf66_png.read_png(src_p)
            src_px = [p if len(p) == 4 else (p[0], p[1], p[2], 255) for p in px0]
            eq(u"%s 是 16×16" % src_name, (16, 16), (w, h))
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
            old = os.path.join(BK, fluid + suffix + u".png")
            if os.path.exists(old):
                check(u"%s%s **确实换过了**（与改前件不同）" % (fluid, suffix),
                      info[4] != hashlib.sha1(open(old, "rb").read()).hexdigest())
            if src_px is not None:
                _, _, _, px = _zf66_png.read_png(p)
                px = [q if len(q) == 4 else (q[0], q[1], q[2], 255) for q in px]
                same = sum(1 for a, b2 in zip(src_px, px) if a == b2)
                eq(u"%s%s 与源图**逐像素一致**（%d/256）" % (fluid, suffix, same), 256, same)
        if len(shas) == 2:
            check(u"%s：still 与 flow 仍是同一张图（本工程惯例）" % fluid, shas[u"_still"] == shas[u"_flow"])

    print(u"\n== B 目录卫生 / 文档 / 成品 ==")
    left = [f for f in os.listdir(TEXB) if any(ord(c) > 127 for c in f) and not f.endswith(u".原名件")]
    check(u"textures/block 下没有中文名（%s）" % (left or u"无"), not left)
    prov = json.loads(read(os.path.join(USERART, u"_来源凭据.json")) or u"{}")
    check(u"来源凭据里记了两张流体原图",
          u"crude_oil.png" in prov and u"diesel.png" in prov)
    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    listing = read(os.path.join(DOCS, u"贴图清单.md")) or u""
    check(u"档案里有 ZF88 那一行", u"| ZF88 |" in arch)
    check(u"贴图清单里有 ZF88 一节", u"## ZF88（0.11）" in listing)
    if not os.path.exists(JAR):
        check(u"成品 jar 存在", False)
        return
    sha = hashlib.sha1(open(JAR, "rb").read()).hexdigest()
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

    print(u"\n------------------------------")
    print(u"通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
