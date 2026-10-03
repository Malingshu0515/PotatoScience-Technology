# -*- coding: utf-8 -*-
u"""_zf84_verify.py —— ZF84 交付校验（常驻，跑在门里）

用户原话：「**汽油的新贴图**」（一张 16×16 JPEG）。本轮换的是汽油**流体**贴图：
`textures/block/gasoline_still.png` 与 `gasoline_flow.png`（ZF78 起两张同图）。

分区：A 贴图（格式 / 确实换过 / 与源图像素一致 / still==flow）
      B 接线（流体类型确实指向这两个文件 —— 换图不接线等于没换）
      C 文档与成品
"""
import hashlib
import io
import json
import os
import struct
import sys
import zipfile
import zlib

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
TEXB = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "textures", "block")
USERART = os.path.join(ROOT, "build", u"用户素材")
TOOLS = os.path.join(ROOT, "build", "zftools")
DOCS = os.path.join(ROOT, "docs")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
OLD_SHA = "30b5e42d66b45acad9f01d212ddbf38671de329c"   # ZF83 成品里那张（=_zf84_pre 留档的）
TARGETS = [u"gasoline_still.png", u"gasoline_flow.png"]

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


def png_px(path):
    b = open(path, "rb").read()
    w, h = struct.unpack(">II", b[16:24])
    idat = b""
    i = 8
    while i < len(b):
        ln = struct.unpack(">I", b[i:i + 4])[0]
        tag = b[i + 4:i + 8]
        if tag == b"IDAT":
            idat += b[i + 8:i + 8 + ln]
        i += 12 + ln
    raw = zlib.decompress(idat)
    px = []
    for y in range(h):
        off = y * (w * 4 + 1)
        if raw[off] != 0:
            return None
        for x in range(w):
            px.append(tuple(raw[off + 1 + x * 4:off + 5 + x * 4]))
    return w, h, b[24], b[25], px


def section_a():
    print(u"\n== A 汽油流体贴图 ==")
    shas = {}
    for name in TARGETS:
        p = os.path.join(TEXB, name)
        info = png_px(p)
        check(u"%s 存在且能解码" % name, info is not None)
        if info is None:
            continue
        w, h, depth, ctype, px = info
        eq(u"%s 16×16" % name, (16, 16), (w, h))
        eq(u"%s 8 位 / RGBA（类型 6）" % name, (8, 6), (depth, ctype))
        check(u"%s 全不透明（流体贴图不该有透明像素）" % name,
              all(a == 255 for (_, _, _, a) in px))
        shas[name] = hashlib.sha1(open(p, "rb").read()).hexdigest()
        check(u"%s **确实换过了**（不再是 ZF83 成品里那张）" % name,
              shas[name] != OLD_SHA)
        cols = set((r, g, b) for (r, g, b, _) in px)
        check(u"%s 的颜色数在合理区间（%d 种）" % (name, len(cols)), 2 <= len(cols) <= 64)
    if len(shas) == 2:
        check(u"still 与 flow 仍是同一张图（ZF78 起的老约定）",
              shas[TARGETS[0]] == shas[TARGETS[1]])

    # 与"当前这张的原图"逐像素比对
    # ⚠ 0.11 ZF89：用户又给了一张新汽油图（`汽油.png` → 留档 `build/用户素材/gasoline.png`），
    #   本轮那张成品**已经被顶掉** ⇒ 这条断言改成"跟**最新**那张留档原图比"（ZF87 改
    #   `_zf73_verify.py` B5 是同一种改法：旧断言被后一轮合法取代时，就把它改成新的真相，
    #   而不是删掉）。ZF84 那张 `gasoline_new.jpg` 的留档与凭据仍然要查 —— 在被顶掉之前它是对的。
    zf89_src = os.path.join(USERART, u"gasoline.png")
    if os.path.exists(zf89_src):
        sys.path.insert(0, TOOLS)
        import _zf66_png
        _, _, _, src_px = _zf66_png.read_png(zf89_src)
        src_px = [p if len(p) == 4 else (p[0], p[1], p[2], 255) for p in src_px]
        got = png_px(os.path.join(TEXB, TARGETS[0]))[4]
        same = sum(1 for a, b in zip(src_px, got) if a == b)
        eq(u"写出的贴图与**最新的**用户原图逐像素一致（ZF89 已顶替 ZF84 那张，%d/256）" % same,
           256, same)
    else:
        dump_p = os.path.join(TOOLS, u"_zf84_pixels.json")
        if os.path.exists(dump_p):
            src = json.loads(read(dump_p))
            src_px = [tuple(int(v) for v in s.split(u",")) + (255,) for s in src]
            got = png_px(os.path.join(TEXB, TARGETS[0]))[4]
            same = sum(1 for a, b in zip(src_px, got) if a == b)
            eq(u"写出的贴图与用户那张**逐像素一致**（%d/256）" % same, 256, same)
        else:
            check(u"源图像素转储在（_zf84_pixels.json）", False)

    prov = json.loads(read(os.path.join(USERART, u"_来源凭据.json")) or u"{}")
    check(u"原图留档 + 凭据（build/用户素材/gasoline_new.jpg，ZF89 起已被 gasoline.png 顶替）",
          os.path.exists(os.path.join(USERART, u"gasoline_new.jpg"))
          and u"gasoline_new.jpg" in prov)


def section_b():
    print(u"\n== B 接线：流体类型确实指向这两个文件 ==")
    fluids = read(os.path.join(SRC, "ModFluids.java")) or u""
    # ⚠ 汽油不是手写贴图路径，而是走 liquidType(...) 工厂：路径由**流体名拼出来**
    #   （"block/" + name + "_still"）。第一版直接搜 `block/gasoline_still` 搜不到 ⇒ 误报。
    # ⚠ 0.11 ZF85 起，那套"按名字拼贴图"的客户端注册**搬到了 PotatoSTClient**
    #   （ModFluids 里不能再出现客户端类）⇒ 这里改成到新落点核对同一件事。
    client = read(os.path.join(SRC, "PotatoSTClient.java")) or u""
    check(u"汽油的流体类型由 liquidType( 工厂建（贴图路径按名字拼）",
          u'liquidType("gasoline"' in fluids)
    check(u"客户端注册里有汽油这一种", u'textures("gasoline")' in client)
    check(u"工厂拼的是 block/<名字>_still", u'"block/" + name + "_still"' in client)
    check(u"工厂拼的是 block/<名字>_flow", u'"block/" + name + "_flow"' in client)
    check(u"汽油方块/桶走的是同一套流体注册（没另写死贴图路径）",
          u"ModBlocks.GASOLINE" in fluids and u"ModItems.GASOLINE_BUCKET" in fluids)


def section_c():
    print(u"\n== C 文档与成品 ==")
    tex = read(os.path.join(DOCS, u"贴图清单.md")) or u""
    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    check(u"贴图清单里有 ZF84 那一节", u"## ZF84（0.11）" in tex)
    check(u"贴图清单写了新图来源（gasoline_new.jpg）", u"gasoline_new.jpg" in tex)
    check(u"档案里有 ZF84 那一行", u"| ZF84 |" in arch)
    check(u"档案里写了「先抄后动手」（与 ZF83 的对比）",
          u"先抄后动手" in arch)
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
        for name in TARGETS:
            entry = u"assets/potato_s_t/textures/block/" + name
            inside = zf.read(entry) if entry in names else None
            check(u"成品里的 %s 与盘上一致" % name,
                  inside == open(os.path.join(TEXB, name), "rb").read())
            if inside is not None:
                check(u"成品里的 %s **不再是**旧图" % name,
                      hashlib.sha1(inside).hexdigest() != OLD_SHA)


def main():
    print(u"=========== ZF84 校验：汽油流体贴图换新 ===========")
    section_a()
    section_b()
    section_c()
    print(u"\n------------------------------")
    print(u"通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
