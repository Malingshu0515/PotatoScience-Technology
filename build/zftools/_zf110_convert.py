# -*- coding: utf-8 -*-
"""_zf110_convert.py —— ZF110：用户新放的 5 件素材上线

用户这轮丢进来的（全部 16×16）：
  1. build/用户素材/星璨钢头盔.png   -> textures/item/star_steel_helmet.png   （新物品图标；模型原先借原版铁头盔）
  2. build/用户素材/碳酸锂.png       -> textures/item/lithium_carbonate.png    （顶掉 ZF86 我生成的占位）
  3. build/用户素材/氯化钠.png       -> textures/item/sodium_chloride.png      （顶掉 ZF86 我生成的占位）
  4. E:/硫_001.png                   -> textures/item/sulfur.png               （顶掉 ZF96 我生成的占位）
  5. build/用户素材/油桶.jpg         -> textures/item/oil_bucket.png           （真 JPEG，要转档）

转档口径：
  * 1/2/3/4 是**已经合规**的 16×16 / 8 位 RGBA / 零半透明 —— 原字节复制，一个像素都不重编码；
  * 5 是 JPEG，无 alpha ⇒ 走 ZF87 那套：**.NET System.Drawing 解像素**（_zf110_jpeg_dump.ps1）
    → 四边泛洪去背景 + 只留最大连通域 → 写成 16×16 / 8 位 / RGBA。

留档：四张 PNG 逐字节进 build/用户素材/（ASCII 名），哈希写进 _来源凭据.json；
      E:/硫_001.png 就地归档后从 E 盘根删掉（不散落）。

写盘前先断言"预备件哈希 == 我预期的原值"，防止在别人已经改过的盘上盲写（§4.76）。
"""
import hashlib
import io
import json
import os
import shutil
import struct
import sys
import zlib

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
USERART = os.path.join(ROOT, "build", "用户素材")
TEX = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
MODELS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\item")

TOL = 26
fails = []
notes = []

# 可接受的原值（跑之前盘上应该长这样；对不上就停手）
# 每项给「改造前」与「本轮成品」两档 —— 脚本要能重复跑（§4.64 幂等），
# 但两档之外的第三态 = 盘被别人动过 ⇒ 停手（§4.76）。
EXPECT = {
    "lithium_carbonate.png": ("c61e5c40b048", "c2b73d18a4d4"),
    "sodium_chloride.png": ("6ed1658c7d4d", "47b795f7fca1"),
    "sulfur.png": ("b8621e694531", "1a6ef7d514cb"),
    "oil_bucket.png": ("750c80745a14", None),          # 成品待第 ④ 步算出
    "star_steel_helmet.json": ("28679e2ce40b", "871552005c22"),
}

# 要上线的四张 PNG：源名 -> (目标名, 存档名)
PNG_JOBS = [
    ("星璨钢头盔.png", "star_steel_helmet.png", "star_steel_helmet.png"),
    ("碳酸锂.png", "lithium_carbonate.png", "lithium_carbonate.png"),
    ("氯化钠.png", "sodium_chloride.png", "sodium_chloride.png"),
]
# 硫在 E 盘根，单独处理
SULFUR_SRC = os.path.join("E:\\", "硫_001.png")
SULFUR_DST = "sulfur.png"
SULFUR_ARCHIVE = "sulfur.png"


def sha1_file(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def png_px(path):
    """读 16×16 RGBA PNG 的像素。

    ⚠ 不自己写解码器：用户给的图带**真压缩过滤**（星璨钢头盔那张第 3 行是 filter=1 Sub），
    而本工程自带 `PngRecolor.read_png` 的 `_unfilter` 支持 0..4 全部过滤器 —— 复用它
    （§11.4 复用优先；我第一版手写的简易解码器只认 filter=0，当场被这张图打回）。
    """
    sys.path.insert(0, TOOLS)
    from PngRecolor import read_png
    w, h, rgba = read_png(path)
    b = io.open(path, "rb").read()
    bitdepth, colortype = b[24], b[25]
    px = [tuple(rgba[i * 4:i * 4 + 4]) for i in range(w * h)]
    return w, h, bitdepth, colortype, px


def write_png16(path, px, w=16, h=16):
    raw = b""
    for y in range(h):
        raw += b"\x00" + b"".join(bytes(px[y * w + x]) for x in range(w))

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    io.open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                              + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def strip_background(px, w=16, h=16):
    """ZF83/ZF86/ZF87 那套：四边泛洪去背景 + 只留最大连通域。"""
    n = w * h
    alpha = [255] * n
    corners = [px[0], px[w - 1], px[(h - 1) * w], px[n - 1]]
    bg = tuple(sorted(c[i] for c in corners)[1] for i in range(3))
    stack = [i for i in range(n)
             if (i // w in (0, h - 1) or i % w in (0, w - 1))
             and all(abs(px[i][c] - bg[c]) <= TOL for c in range(3))]
    seen = set(stack)
    while stack:
        i = stack.pop()
        alpha[i] = 0
        y, x = divmod(i, w)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w:
                j = ny * w + nx
                if j not in seen and all(abs(px[j][c] - bg[c]) <= TOL for c in range(3)):
                    seen.add(j)
                    stack.append(j)
    visited, comps = set(), []
    for i in range(n):
        if alpha[i] == 0 or i in visited:
            continue
        comp, st = set(), [i]
        while st:
            k = st.pop()
            if k in comp:
                continue
            comp.add(k)
            ky, kx = divmod(k, w)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = ky + dy, kx + dx
                    if 0 <= ny < h and 0 <= nx < w:
                        j = ny * w + nx
                        if alpha[j] != 0 and j not in comp:
                            st.append(j)
        comps.append(comp)
        visited |= comp
    if comps:
        main = max(comps, key=len)
        for comp in comps:
            if comp is not main:
                for k in comp:
                    alpha[k] = 0
    return [(px[i][0], px[i][1], px[i][2], alpha[i]) for i in range(n)], bg, len(comps)


def ascii_alpha(px, w=16, h=16):
    return ["     " + "".join("#" if px[y * w + x][3] == 255 else
                            ("+" if px[y * w + x][3] else ".") for x in range(w))
            for y in range(h)]


def load_prov():
    p = os.path.join(USERART, "_来源凭据.json")
    return json.loads(io.open(p, encoding="utf-8").read()) if os.path.exists(p) else {}


def save_prov(prov):
    p = os.path.join(USERART, "_来源凭据.json")
    io.open(p, "w", encoding="utf-8", newline="\n").write(
        json.dumps(prov, indent=2, ensure_ascii=False) + "\n")


def main():
    print("=" * 74)
    print("⓪ 幂等/恢复：把被覆盖的留档、已移走的原件还原回已知状态")
    # (a) 旧的 oil_bucket.jpg 留档被本轮覆盖过（779 B 顶掉 824 B）—— 从 zf110_pre 还原成品
    pre_old = os.path.join(ROOT, r"build\zftools\zf110_pre",
                           "src__main__resources__assets__potato_s_t__textures__item__oil_bucket.png")
    dst_old = os.path.join(TEX, "oil_bucket.png")
    if os.path.exists(pre_old):
        want = sha1_file(pre_old)
        cur = sha1_file(dst_old) if os.path.exists(dst_old) else ""
        if cur != want:
            shutil.copyfile(pre_old, dst_old)
            print("  [恢复] oil_bucket.png <- zf110_pre（%s -> %s）" % (cur[:12], want[:12]))
        else:
            print("  [OK]   oil_bucket.png 已是预备件版本 %s" % want[:12])
    # (b) 硫的原件已从 E 盘根移走、留在 用户素材/sulfur.png；再次运行时别重复要求源文件
    #     ⚠ 用独立的局部变量：在 main() 里给 SULFUR_SRC 赋值会把它变成局部名，
    #       于是上面那行读取就 UnboundLocalError（Python 作用域规则，不是笔误）。
    sulfur_arch = os.path.join(USERART, SULFUR_ARCHIVE)
    sulfur_src = SULFUR_SRC
    if not os.path.exists(sulfur_src) and os.path.exists(sulfur_arch):
        sulfur_src = sulfur_arch
        print("  [幂等] 硫原件已归档，改用 %s 作为源" % SULFUR_ARCHIVE)

    print("\n" + "=" * 74)
    print("① 前置断言：盘上现状 ∈ {改造前, 本轮成品}（第三态 = 别人动过 ⇒ 停手）")
    for name, (want, done) in EXPECT.items():
        p = os.path.join(TEX, name) if name.endswith(".png") else os.path.join(MODELS, name)
        if not os.path.exists(p):
            fails.append("缺少 %s" % name)
            print("  !! 缺 %s" % name)
            continue
        got = sha1_file(p)[:12]
        if got == want:
            state = "改造前"
        elif done and got == done:
            state = "已是本轮成品"
        else:
            state = None
        ok = state is not None
        print("  %s  %-26s sha1 %s（%s）"
              % ("OK " if ok else "!! ", name, got,
                 state or ("期望 %s 或 %s" % (want, done))))
        if not ok:
            fails.append("%s 是第三态（%s），盘被别人动过" % (name, got))
    if fails:
        print("\n前置断言失败，停手。")
        return 1

    print("\n" + "=" * 74)
    print("② 四张 PNG：原字节上线（不重编码一个像素）")
    prov = load_prov()
    for srcname, dstname, archname in PNG_JOBS:
        src = os.path.join(USERART, srcname)
        if not os.path.exists(src):
            fails.append("找不到素材 %s" % srcname)
            print("  !! 找不到 %s" % srcname)
            continue
        raw = open(src, "rb").read()
        w, h, bd, ct, px = png_px(src)
        opaque = sum(1 for p in px if p[3] == 255)
        semi = sum(1 for p in px if 0 < p[3] < 255)
        print("\n  %s -> textures/item/%s" % (srcname, dstname))
        print("     源: %dx%d 位深 %d 色彩类型 %d  不透明 %d / 半透明 %d  字节 %d"
              % (w, h, bd, ct, opaque, semi, len(raw)))
        if (w, h, bd, ct) != (16, 16, 8, 6):
            fails.append("%s 规格不是 16x16/8/RGBA" % srcname)
        if semi:
            fails.append("%s 有半透明像素（%d 个）" % (srcname, semi))
        dst = os.path.join(TEX, dstname)
        io.open(dst, "wb").write(raw)
        back = open(dst, "rb").read()
        if back != raw:
            fails.append("%s 写出后逐字节不一致" % dstname)
        else:
            print("     [OK] 逐字节写出 sha1 %s" % hashlib.sha1(back).hexdigest()[:12])
        # 留档
        arch = os.path.join(USERART, archname)
        io.open(arch, "wb").write(raw)
        prov[archname] = {
            "原名": srcname,
            "sha1": hashlib.sha1(raw).hexdigest(),
            "bytes": len(raw),
            "说明": "用户 ZF110 放的素材（%s）⇒ 原字节复制成 textures/item/%s（16x16/8位/RGBA，零半透明）"
                    % (srcname, dstname),
        }

    print("\n" + "=" * 74)
    print("③ 硫：E 盘根 -> textures/item/sulfur.png")
    if not os.path.exists(sulfur_src):
        fails.append("找不到 %s" % sulfur_src)
        print("  !! 找不到 %s" % sulfur_src)
    else:
        raw = open(sulfur_src, "rb").read()
        w, h, bd, ct, px = png_px(sulfur_src)
        opaque = sum(1 for p in px if p[3] == 255)
        semi = sum(1 for p in px if 0 < p[3] < 255)
        print("     源: %dx%d 位深 %d 色彩类型 %d  不透明 %d / 半透明 %d  字节 %d"
              % (w, h, bd, ct, opaque, semi, len(raw)))
        if (w, h, bd, ct) != (16, 16, 8, 6):
            fails.append("硫_001.png 规格不是 16x16/8/RGBA")
        if semi:
            fails.append("硫_001.png 有半透明像素")
        dst = os.path.join(TEX, SULFUR_DST)
        io.open(dst, "wb").write(raw)
        if open(dst, "rb").read() != raw:
            fails.append("sulfur.png 写出后逐字节不一致")
        else:
            print("     [OK] 逐字节写出 sha1 %s" % hashlib.sha1(raw).hexdigest()[:12])
        arch = os.path.join(USERART, SULFUR_ARCHIVE)
        io.open(arch, "wb").write(raw)
        prov[SULFUR_ARCHIVE] = {
            "原名": "硫_001.png（原放在 E:\\ 根目录）",
            "sha1": hashlib.sha1(raw).hexdigest(),
            "bytes": len(raw),
            "说明": "用户 ZF110 放的硫素材 ⇒ 原字节复制成 textures/item/sulfur.png"
                    "（顶掉 ZF96 的程序生成占位 136 B）；原件从 E 盘根归档到这里",
        }
        if os.path.exists(SULFUR_SRC):      # 已在归档时不再删（幂等）
            os.remove(SULFUR_SRC)
            print("     [OK] 原件已从 E:\\硫_001.png 归档并移除")
        else:
            print("     [幂等] 原件已归档，E 盘根无需再删")

    print("\n" + "=" * 74)
    print("④ 油桶：JPEG 转档（暗底包边 ⇒ 只掏最外圈）")
    dump_p = os.path.join(TOOLS, "_zf110_oil_pixels.json")
    src_jpg = os.path.join(USERART, "油桶.jpg")
    if not os.path.exists(dump_p) or not os.path.exists(src_jpg):
        fails.append("缺像素 dump 或源 jpg")
        print("  !! 缺 %s 或 %s" % (dump_p, src_jpg))
    else:
        d = json.loads(io.open(dump_p, encoding="utf-8").read())
        if d["w"] != 16 or d["h"] != 16 or len(d["px"]) != 256:
            fails.append("油桶源图不是 16x16（%sx%s/%d）" % (d["w"], d["h"], len(d["px"])))
        else:
            src_px = [tuple(int(v) for v in s.split(",")) for s in d["px"]]

            # ---------------------------------------------------------------
            # ⚠ 这一张**不能**照 ZF83/ZF86/ZF87 的「四边泛洪去背景」做。
            #
            # 实测（_zf110_oil_look.py）：最外圈 60 个像素**全是暗色**（亮 0 / 暗 60），
            # 四角 ≈ RGB(5,3,0)，而桶身的暗部与背景同色系 ⇒ 泛洪会顺着暗部把桶吃掉。
            # 第一版照抄泛洪，结果只剩 137 个实心像素（桶没了），而"40..230"那条断言
            # 照样放行 —— 是"检查能过 ≠ 结果对"的又一例。
            #
            # 用户这张就是**暗底 + 桶占满画面**的画法（与 ZF87 那张留白底的不是同一种）。
            # 因此改成**只掏掉最外圈一圈**，桶身一个像素不动：最小干预、可复现、
            # 且与 ZF87 成品同样是"1 格宽透明边"的口径。
            # ---------------------------------------------------------------
            out = list(src_px)
            ring = 0
            for y in range(16):
                for x in range(16):
                    if y in (0, 15) or x in (0, 15):
                        p = out[y * 16 + x]
                        out[y * 16 + x] = (p[0], p[1], p[2], 0)
                        ring += 1
            opaque = sum(1 for p in out if p[3] == 255)
            print("     画法：暗底包边（最外圈 60 像素全暗，无亮底可抠）⇒ 只掏掉最外圈 %d 个" % ring)
            print("     留下桶身 %d 个像素" % opaque)
            for line in ascii_alpha(out):
                print(line)
            if opaque < 150:
                fails.append("油桶只留下 %d 个像素，太少" % opaque)

            dst = os.path.join(TEX, "oil_bucket.png")
            write_png16(dst, out)
            b = open(dst, "rb").read()
            w2, h2 = struct.unpack(">II", b[16:24])
            print("     [OK] oil_bucket.png 写出：%dx%d 位深 %d 类型 %d sha1 %s（%d B）"
                  % (w2, h2, b[24], b[25], hashlib.sha1(b).hexdigest()[:12], len(b)))
            if (w2, h2, b[24], b[25]) != (16, 16, 8, 6):
                fails.append("oil_bucket.png 写出的格式不对")

            # 留档：这一次**先看旧的还在不在**，在就改名保住（上一版直接覆盖，教训记进 §9）
            arch = os.path.join(USERART, "oil_bucket.jpg")
            raw = open(src_jpg, "rb").read()
            if os.path.exists(arch):
                old_raw = open(arch, "rb").read()
                if old_raw != raw:
                    keep = os.path.join(USERART, "oil_bucket_prev.jpg")
                    io.open(keep, "wb").write(old_raw)
                    print("     [保档] 旧 oil_bucket.jpg（%d B）另存为 oil_bucket_prev.jpg" % len(old_raw))
                    prov["oil_bucket_prev.jpg"] = {
                        "sha1": hashlib.sha1(old_raw).hexdigest(),
                        "bytes": len(old_raw),
                        "说明": "ZF87 那位用户给的旧油桶素材（原名 油桶.jpg，824 B）⇒ 成品是当时的 "
                                "textures/item/oil_bucket.png（824 B / sha1 750c80745a14）。"
                                "⚠ 本轮（ZF110）收新素材时先被覆盖、随后从 build/zftools/zf110_pre 恢复成品，"
                                "但**这一个 jpg 留档的原字节已丢失**，此处只保留名称与哈希记录",
                    }
            io.open(arch, "wb").write(raw)
            prov["oil_bucket.jpg"] = {
                "原名": "油桶.jpg",
                "sha1": hashlib.sha1(raw).hexdigest(),
                "bytes": len(raw),
                "说明": "用户 ZF110 新放的油桶素材（16x16 真 JPEG 基线 JFIF，无 ICC/无 Adobe 标记，"
                        "无 alpha，779 B）⇒ .NET System.Drawing 解像素后**只掏掉最外圈**，"
                        "转档成 textures/item/oil_bucket.png，顶掉 ZF87 那版（824 B）",
            }

    print("\n" + "=" * 74)
    print("⑤ 星璨钢头盔模型改指向自己")
    mp = os.path.join(MODELS, "star_steel_helmet.json")
    before = io.open(mp, encoding="utf-8").read()
    data = json.loads(before)
    old = data["textures"]["layer0"]
    data["textures"]["layer0"] = "potato_s_t:item/star_steel_helmet"
    io.open(mp, "w", encoding="utf-8", newline="\n").write(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    after = io.open(mp, encoding="utf-8").read()
    print("     layer0: %s -> %s" % (old, data["textures"]["layer0"]))
    if "minecraft:item/iron_helmet" in after:
        fails.append("star_steel_helmet.json 里还残留原版引用")
    else:
        print("     [OK] 不再引用原版铁头盔")

    save_prov(prov)
    print("\n     [OK] _来源凭据.json 已更新")

    print("\n" + "=" * 74)
    print("⑥ 资源目录卫生检查：不许有非 ASCII 文件名")
    left = [f for f in os.listdir(TEX) if any(ord(c) > 127 for c in f)]
    if left:
        fails.append("textures/item 下还有非 ASCII 名：%s" % left)
    else:
        print("     [OK] textures/item 下无中文名")

    print("\n失败项 = %d" % len(fails))
    for f in fails:
        print("  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
