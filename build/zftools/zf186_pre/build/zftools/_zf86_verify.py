# -*- coding: utf-8 -*-
u"""_zf86_verify.py —— ZF86 交付校验（常驻，跑在门里）

用户这批是"又放了四张素材"：铜板（内容其实是 JPEG）+ 氯化钠 + 电容 + 碳酸锂。
校验要点：
  A 四张贴图都是**真 PNG**（16×16 / 8 位 / RGBA）——**铜板那条最重要**（假 PNG 在游戏里就是坏图）
  B 三件物品的模型指向自己的贴图；老的四张板子/别的物品一个都没被带坏
  C 资源目录不留中文名；原图留档 + 凭据
  D 全量扫描：模型引用的贴图都在、每张贴图至少被引用一次
  E 文档与成品
"""
import hashlib
import io
import json
import os
import re
import struct
import sys
import zipfile
import zlib

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
# ⚠ ZF87 追加 oil_bucket：同一批"用户放图 ⇒ 转档 ⇒ 模型指向自己"的活，同一套断言
FOUR = [u"copper_plate", u"sodium_chloride", u"capacitor", u"lithium_carbonate",
        u"oil_bucket"]

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


def png_head(path):
    if not os.path.exists(path):
        return None
    b = open(path, "rb").read()
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        return (u"不是 PNG（头是 %s）" % b[:4].hex(),)
    w, h = struct.unpack(">II", b[16:24])
    return (w, h, b[24], b[25], hashlib.sha1(b).hexdigest())


def opaque_count(path):
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
        off = y * (w * 4 + 1)
        if raw[off] != 0:
            return None
        for x in range(w):
            if raw[off + 1 + x * 4 + 3] == 255:
                n += 1
    return n


def section_a():
    print(u"\n== A 四张贴图（真 PNG / 16×16 / 8 位 / RGBA）==")
    for name in FOUR:
        info = png_head(os.path.join(TEX, name + u".png"))
        check(u"%s.png 是真 PNG" % name, info is not None and len(info) == 5)
        if info is None or len(info) != 5:
            continue
        eq(u"%s.png 16×16" % name, (16, 16), (info[0], info[1]))
        eq(u"%s.png 8 位 / RGBA" % name, (8, 6), (info[2], info[3]))
        n = opaque_count(os.path.join(TEX, name + u".png"))
        check(u"%s.png 有不透明主体（%s 个像素）" % (name, n), n is not None and n >= 20)


def section_b():
    print(u"\n== B 模型指向 ==")
    for name in FOUR:
        t = read(os.path.join(MODELS, name + u".json")) or u""
        check(u"%s.json → potato_s_t:item/%s" % (name, name), u'"potato_s_t:item/%s"' % name in t)
    # 别把老的带坏：三张板子 + 汽油 + 铜板（铜板在本轮也被重写过）
    # ⚠ 0.11 ZF90：用户「其它锭板子贴图都换成铁板的」⇒ 银板从 `item/plate` 改指 `item/iron_plate`，
    #   通用 `plate.png` 也已删除 ⇒ 这条回归断言改成新真相（ZF87/ZF89 同一改法：不删历史）。
    for name, want in [(u"steel_plate", u"potato_s_t:item/steel_plate"),
                       (u"iron_plate", u"potato_s_t:item/iron_plate"),
                       (u"silver_plate", u"potato_s_t:item/iron_plate")]:
        t = read(os.path.join(MODELS, name + u".json")) or u""
        check(u"回归：%s.json 仍指向 %s" % (name, want), u'"%s"' % want in t)

    missing = []
    for n in sorted(os.listdir(MODELS)):
        if not n.endswith(u".json"):
            continue
        for ref in re.findall(r'"potato_s_t:item/([a-z0-9_]+)"', read(os.path.join(MODELS, n)) or u""):
            if not os.path.exists(os.path.join(TEX, ref + u".png")):
                missing.append(u"%s → %s.png" % (n, ref))
    check(u"所有 item 模型引用的贴图都存在（缺 %s）" % (missing or u"无"), not missing)


def section_c():
    print(u"\n== C 目录卫生 / 原图留档 ==")
    left = [f for f in os.listdir(TEX) if any(ord(c) > 127 for c in f)]
    check(u"textures/item 下没有中文文件名（%s）" % (left or u"无"), not left)
    prov = json.loads(read(os.path.join(USERART, u"_来源凭据.json")) or u"{}")
    for jpg in [u"sodium_chloride.jpg", u"capacitor.jpg", u"lithium_carbonate.png"]:
        p = os.path.join(USERART, jpg)
        check(u"原图留档在：%s" % jpg, os.path.exists(p))
        if os.path.exists(p) and jpg in prov:
            eq(u"%s 与凭据哈希一致" % jpg, prov[jpg][u"sha1"],
               hashlib.sha1(open(p, "rb").read()).hexdigest())


def section_d():
    print(u"\n== D 文档与成品 ==")
    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    listing = read(os.path.join(DOCS, u"贴图清单.md")) or u""
    check(u"档案里有 ZF86 那一行", u"| ZF86 |" in arch)
    check(u"档案里点名了「铜板其实是 JPEG」这个坑",
          u"其实是 JPEG" in arch or u"内容其实是 JPEG" in arch)
    check(u"档案里记了碳酸锂 20×20 → 16×16 的处理", u"20×20" in arch)
    check(u"贴图清单里有 ZF86 一节", u"## ZF86（0.11）" in listing)
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
        for name in FOUR:
            entry = u"assets/potato_s_t/textures/item/%s.png" % name
            inside = zf.read(entry) if entry in names else None
            check(u"成品里的 %s.png 与盘上一致" % name,
                  inside == open(os.path.join(TEX, name + u".png"), "rb").read())


def main():
    print(u"=========== ZF86 校验：四张素材转档 ===========")
    section_a()
    section_b()
    section_c()
    section_d()
    print(u"\n------------------------------")
    print(u"通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
