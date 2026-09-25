# -*- coding: utf-8 -*-
u"""_zf83_verify.py —— ZF83 交付校验（常驻，跑在门里）

用户原话：「钢板和铁（银 铝...）板 铜板贴图放item文件夹了 **换一下** 然后**删除原来的贴图**」。

分区：
  A 三张板子贴图（格式 / 板状轮廓 / 确实换过）      B 物品模型指向（含"引用的贴图必须存在"的全量扫描）
  C 原图留档（§4.24）                                D 文档（贴图清单 + 档案两条雷）
  E 成品
"""
import hashlib
import io
import json
import os
import re
import struct
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ASSETS = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t")
TEX = os.path.join(ASSETS, "textures", "item")
MODELS = os.path.join(ASSETS, "models", "item")
USERART = os.path.join(ROOT, "build", u"用户素材")
DOCS = os.path.join(ROOT, "docs")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
OLD_JAR_ART = {           # ZF82 成品 jar 里那三张（=_zf83_pre 里留档的）——用来证明"真的换过"
    u"steel_plate.png": u"82c5879f",
    u"copper_plate.png": u"99cc2674",
    u"plate.png": u"a28b0654",
}
PLATES_THREE = [u"steel_plate", u"iron_plate", u"copper_plate"]
OTHERS = [u"aluminum_plate", u"cobalt_plate", u"nickel_plate", u"silver_plate"]

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


def png_info(path):
    u"""返回 (w, h, depth, colorType, sha1)。"""
    if not os.path.exists(path):
        return None
    b = open(path, "rb").read()
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", b[16:24])
    return (w, h, b[24], b[25], hashlib.sha1(b).hexdigest())


def opaque_count(path):
    u"""数 alpha=255 的像素（自带解码器：只处理 filter 0，本工程贴图都是 0）。"""
    import zlib
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
    n = 0
    for y in range(h):
        row = raw[y * (w * 4 + 1):(y + 1) * (w * 4 + 1)]
        if row[0] != 0:
            return None
        for x in range(w):
            if row[1 + x * 4 + 3] == 255:
                n += 1
    return n


# ================= A 贴图 =================

def section_a():
    print(u"\n== A 三张板子贴图 ==")
    for name in PLATES_THREE:
        info = png_info(os.path.join(TEX, name + u".png"))
        check(u"%s.png 存在且是真 PNG" % name, info is not None)
        if info is None:
            continue
        eq(u"%s.png 16×16" % name, (16, 16), (info[0], info[1]))
        eq(u"%s.png 8 位色深" % name, 8, info[2])
        eq(u"%s.png RGBA（类型 6）" % name, 6, info[3])
        n = opaque_count(os.path.join(TEX, name + u".png"))
        check(u"%s.png 是「一块板」的轮廓（不透明像素 %s 个，期望 60~220）" % (name, n),
              n is not None and 60 <= n <= 220)
        if name + u".png" in OLD_JAR_ART:
            check(u"%s.png **确实换过了**（与 ZF82 成品里那张不同）" % name,
                  not info[4].startswith(OLD_JAR_ART[name + u".png"]))
    # ⚠ 0.11 ZF90：用户「其它锭板子贴图都换成铁板的」⇒ 银/铝/镍/钴四件改指 iron_plate，
    #   通用 plate.png 因此**已被删除**。下面这几条原本断言「plate.png 仍在、一个字节没动」，
    #   现在断言的是新真相（ZF87 改 `_zf73_verify.py` B5、ZF89 改本脚本前面那条，都是同一改法）。
    info = png_info(os.path.join(TEX, u"plate.png"))
    check(u"通用 plate.png 已按 ZF90 删除（银/铝/镍/钴四件改指 iron_plate 之后没人用了）",
          info is None)
    if info is not None:
        print(u"  [WARN] plate.png 又出现了（%s），ZF90 之后它应当是删掉的" % (info[4][:8],))
    left = [f for f in os.listdir(TEX) if any(ord(c) > 127 for c in f)]
    check(u"textures/item 下没有中文文件名（%s）" % (left or u"无"), not left)


# ================= B 模型 =================

def section_b():
    print(u"\n== B 物品模型指向 ==")
    for name in PLATES_THREE:
        p = os.path.join(MODELS, name + u".json")
        t = read(p) or u""
        check(u"%s.json 指向自己的贴图 potato_s_t:item/%s" % (name, name),
              u'"potato_s_t:item/%s"' % name in t)
    for name in OTHERS:
        t = read(os.path.join(MODELS, name + u".json")) or u""
        # ⚠ 0.11 ZF90：用户「其它锭板子贴图都换成铁板的」⇒ 这四件改成指向 iron_plate。
        check(u"%s.json 已按 ZF90 改指 iron_plate" % name,
              u'"potato_s_t:item/iron_plate"' in t)

    # 全量扫描：每个 item 模型引用的 potato_s_t:item/* 贴图必须真的存在（孤儿引用=紫黑块）
    missing = []
    for n in sorted(os.listdir(MODELS)):
        if not n.endswith(u".json"):
            continue
        t = read(os.path.join(MODELS, n)) or u""
        for ref in re.findall(r'"potato_s_t:item/([a-z0-9_]+)"', t):
            if not os.path.exists(os.path.join(TEX, ref + u".png")):
                missing.append(u"%s → %s.png" % (n, ref))
    check(u"所有 item 模型引用的贴图都存在（缺 %s）" % (missing or u"无"), not missing)

    # 反向：每个 textures/item/*.png 至少被一个模型引用（孤兒贴图=白占体积，也可能是漏接线）
    used = set()
    for n in sorted(os.listdir(MODELS)):
        if n.endswith(u".json"):
            used |= set(re.findall(r'"potato_s_t:item/([a-z0-9_]+)"',
                                   read(os.path.join(MODELS, n)) or u""))
    orphans = [f[:-4] for f in sorted(os.listdir(TEX))
               if f.endswith(u".png") and f[:-4] not in used]
    # 只报出来（不判 FAIL）：有些贴图可能被方块模型/其它地方用（本工程目前没有）
    print(u"  —— 没被任何物品模型引用的贴图：%s" % (orphans or u"无"))


# ================= C 原图留档 =================

def section_c():
    print(u"\n== C 原图留档（§4.24）==")
    prov_p = os.path.join(USERART, u"_来源凭据.json")
    prov = json.loads(read(prov_p)) if os.path.exists(prov_p) else {}
    check(u"来源凭据还在（build/用户素材/_来源凭据.json）", bool(prov))
    for key, jpg in [(u"steel", u"steel_plate.jpg"), (u"iron", u"iron_plate.jpg"),
                     (u"copper", u"copper_plate.jpg")]:
        p = os.path.join(USERART, jpg)
        ok = os.path.exists(p)
        check(u"原图留档在：%s" % jpg, ok)
        if ok and jpg in prov:
            eq(u"%s 与凭据里的哈希一致" % jpg, prov[jpg][u"sha1"],
               hashlib.sha1(open(p, "rb").read()).hexdigest())


# ================= D 文档 =================

def section_d():
    print(u"\n== D 文档 ==")
    listing = read(os.path.join(DOCS, u"贴图清单.md")) or u""
    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    check(u"贴图清单里有 ZF83 那一节", u"ZF83" in listing)
    check(u"贴图清单写清「铁板换掉了通用贴图」",
          u"iron_plate" in listing and u"plate.png" in listing)
    check(u"档案里有 §4.56（白底贴图去背景要从四边泛洪）", u"### 4.56" in arch)
    check(u"档案里**如实记了**本轮「先动手后抄」",
          u"先动手后抄" in arch and u"zf83_pre" in arch)
    check(u"档案里有 ZF83 那一行", u"| ZF83 |" in arch)
    check(u"档案里写了与成品 jar 的对比证据（换过图）", u"82c5879f" in arch or u"与 ZF82" in arch)


# ================= E 成品 =================

def section_e():
    print(u"\n== E 成品 ==")
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
        for name in PLATES_THREE:
            entry = u"assets/potato_s_t/textures/item/%s.png" % name
            inside = zf.read(entry) if entry in names else None
            local = open(os.path.join(TEX, name + u".png"), "rb").read()
            check(u"成品里的 %s.png 与盘上一致" % name, inside == local)
            if inside is not None and name + u".png" in OLD_JAR_ART:
                check(u"成品里的 %s.png **不再是** ZF82 那一张" % name,
                      not hashlib.sha1(inside).hexdigest().startswith(
                          OLD_JAR_ART[name + u".png"]))
        check(u"成品里 item 模型指向新贴图",
              json.loads(zf.read(u"assets/potato_s_t/models/item/iron_plate.json")
                         .decode(u"utf-8"))[u"textures"][u"layer0"] == u"potato_s_t:item/iron_plate")


def main():
    print(u"=========== ZF83 校验：三张板子贴图换新 ===========")
    section_a()
    section_b()
    section_c()
    section_d()
    section_e()
    print(u"\n------------------------------")
    print(u"通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
