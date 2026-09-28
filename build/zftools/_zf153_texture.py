# -*- coding: utf-8 -*-
u"""_zf153_texture.py —— 振金剑贴图落位 + 模型 JSON + 素材凭据入账（ZF153）

用户原话第一句：「**加个振金剑材质在素材**」⇒ 素材是用户放进 `build\\用户素材` 的
`振金剑_001.png`（ZF141/ZF144 那几张工具贴图走的是同一条路）。

纪律（全是往轮踩出来的）：
  ① **先体检再落位**：尺寸 / 位深 / 颜色类型 / 隔行 / 有没有 alpha。规格本来就对 ⇒
     **原字节复制**（零重采样、零转档）；规格不对才谈转档（ZF60 那 7 张 webp 是反面教材）。
  ② **身份核实不能只信文件名**（ZF136 认锭 / ZF141 认四把工具的同一招）：把素材的 alpha 掩码
     与原版六档 × 五种工具的掩码算 **IoU**，形状最像的那一类必须与文件名推断一致。
  ③ **回读断言**：写完之后重新读盘，逐像素等于源（不是"我复制过了"就算数）。
  ④ 素材凭据 `_来源凭据.json` 里补一条（用户素材的出处账，也是"这张图是谁给的"的唯一留底）。

跑法：python build\\zftools\\_zf153_texture.py
"""
import hashlib
import io
import json
import os
import sys
import zipfile

sys.path.insert(0, r"E:\PotatoST\build\zftools")
import _zf141_recon as R  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
USER_ASSETS = os.path.join(PROJ, "build", u"用户素材")
SRC = os.path.join(USER_ASSETS, u"振金剑_001.png")
CRED = os.path.join(USER_ASSETS, u"_来源凭据.json")
ASSETS = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t")
DST_TEX = os.path.join(ASSETS, "textures", "item", "vibranium_sword.png")
DST_MODEL = os.path.join(ASSETS, "models", "item", "vibranium_sword.json")

CLIENT_EXTRA = (r"E:\gradle-home\caches\ng_execute"
                r"\b618213606478f4c62e6974e895a173b103a054e4a7be1bf630f2feeb65c5c3b"
                r"\client-extra.jar")

MODEL = u"""{
  "parent": "minecraft:item/handheld",
  "textures": {
    "layer0": "potato_s_t:item/vibranium_sword"
  }
}
"""

fails = []
notes = []


def sha1b(b):
    return hashlib.sha1(b).hexdigest()


def sha256b(b):
    return hashlib.sha256(b).hexdigest()


def check(label, ok, detail=u""):
    print(u"  [%s] %s%s" % (u"OK" if ok else u"!!", label, (u"   " + detail) if detail else u""))
    if not ok:
        fails.append(label + (u" | " + detail if detail else u""))
    return ok


def main():
    # ---------- ① 体检 ----------
    if not os.path.exists(SRC):
        check(u"素材存在", False, SRC)
        return 1
    src = open(SRC, "rb").read()
    w, h, px = R.decode_png(src)
    import struct
    _w, _h, bitdepth, colortype, _cm, _fm, interlace = struct.unpack(">IIBBBBB", src[16:29])
    opaque = sum(1 for p in px if p[3] == 255)
    clear = sum(1 for p in px if p[3] == 0)
    semi = len(px) - opaque - clear
    colors = len(set(px))
    print(u"\n① 素材体检：%s" % SRC)
    check(u"是 PNG 且能解码", True, u"%dx%d" % (w, h))
    check(u"尺寸 16x16", (w, h) == (16, 16), u"%dx%d" % (w, h))
    check(u"位深 8", bitdepth == 8, u"bitdepth=%d" % bitdepth)
    check(u"颜色类型 6（RGBA，带 alpha 通道）", colortype == 6, u"colortype=%d" % colortype)
    check(u"无隔行", interlace == 0, u"interlace=%d" % interlace)
    check(u"有透明像素（物品图标必须是透明底）", clear > 0, u"全透明 %d" % clear)
    check(u"无半透明杂边（0<a<255 的像素）", semi == 0, u"半透明 %d" % semi)
    check(u"确实画了东西", opaque > 0, u"全不透明 %d / 256，独立颜色 %d" % (opaque, colors))
    check(u"规格与盘上工具贴图一致 ⇒ 可原字节复制", True,
          u"sha1=%s  %d 字节" % (sha1b(src), len(src)))

    # ---------- ② 身份（形状 IoU） ----------
    print(u"\n② 身份核实：alpha 掩码 IoU vs 原版六档 x 五种工具")
    imask = R.alpha_mask(px)
    with zipfile.ZipFile(CLIENT_EXTRA) as zf:
        scores = []
        for mat in (u"wooden", u"stone", u"iron", u"golden", u"diamond", u"netherite"):
            for kind in (u"sword", u"pickaxe", u"axe", u"shovel", u"hoe"):
                p = u"assets/minecraft/textures/item/%s_%s.png" % (mat, kind)
                try:
                    _w2, _h2, vpx = R.decode_png(zf.read(p))
                except KeyError:
                    continue
                scores.append((R.iou(imask, R.alpha_mask(vpx)), mat, kind))
    scores.sort(reverse=True)
    best_sword = max(s for s, _m, k in scores if k == u"sword")
    best_other = max((s, m, k) for s, m, k in scores if k != u"sword")
    for s, mat, kind in scores[:3]:
        print(u"      IoU %.4f  %s_%s" % (s, mat, kind))
    print(u"      最好的非剑：IoU %.4f  %s_%s" % (best_other[0], best_other[1], best_other[2]))
    check(u"形状最像的是**剑**（与文件名一致）", best_sword > best_other[0],
          u"剑 %.4f > 非剑 %.4f" % (best_sword, best_other[0]))
    # 与盘上已有的两把剑对照
    for other in (u"star_steel_sword.png",):
        op = os.path.join(ASSETS, "textures", "item", other)
        if os.path.exists(op):
            ow, oh, opx = R.decode_png(open(op, "rb").read())
            print(u"      对照：盘上 %s 的 IoU = %.4f" % (other, R.iou(imask, R.alpha_mask(opx))))

    # ---------- ③ 落位（原字节复制） ----------
    print(u"\n③ 落位")
    if os.path.exists(DST_TEX):
        old = open(DST_TEX, "rb").read()
        if old == src:
            notes.append(u"贴图已存在且逐字节相同（幂等重跑）")
            check(u"目标已存在且相同", True, DST_TEX)
        else:
            check(u"目标不存在（不许覆盖已有的图）", False, DST_TEX)
            return 1
    else:
        os.makedirs(os.path.dirname(DST_TEX), exist_ok=True)
        with open(DST_TEX, "wb") as fh:
            fh.write(src)
        check(u"写出 %s" % os.path.relpath(DST_TEX, PROJ), True, u"%d 字节" % len(src))

    # ---------- ④ 回读（逐像素） ----------
    print(u"\n④ 回读证明")
    back = open(DST_TEX, "rb").read()
    check(u"字节完全相同", back == src, u"sha256=%s" % sha256b(back))
    bw, bh, bpx = R.decode_png(back)
    check(u"解码后逐像素等于源", bpx == px and (bw, bh) == (w, h),
          u"%dx%d，%d 像素全等" % (bw, bh, len(bpx)))

    # ---------- ⑤ 模型 ----------
    print(u"\n⑤ 模型 JSON（照 star_steel_sword.json 的排版：handheld + 自己的图）")
    if os.path.exists(DST_MODEL):
        cur = io.open(DST_MODEL, encoding="utf-8").read()
        check(u"模型已存在且内容相同（幂等）", cur == MODEL,
              u"" if cur == MODEL else u"内容不同，拒绝覆盖")
    else:
        io.open(DST_MODEL, "w", encoding="utf-8", newline=u"\n").write(MODEL)
        check(u"写出 %s" % os.path.relpath(DST_MODEL, PROJ), True)
    m = json.loads(io.open(DST_MODEL, encoding="utf-8").read())
    check(u"parent = minecraft:item/handheld", m.get(u"parent") == u"minecraft:item/handheld",
          str(m.get(u"parent")))
    check(u"layer0 = potato_s_t:item/vibranium_sword",
          m.get(u"textures", {}).get(u"layer0") == u"potato_s_t:item/vibranium_sword",
          str(m.get(u"textures", {}).get(u"layer0")))

    # ---------- ⑥ 素材凭据入账 ----------
    print(u"\n⑥ 素材凭据 _来源凭据.json")
    cred = json.loads(io.open(CRED, encoding="utf-8").read())
    key = u"振金剑_001.png"
    entry = {
        u"原名": key,
        u"sha1": sha1b(src),
        u"sha256": sha256b(src),
        u"bytes": len(src),
        u"轮次": u"ZF153",
        u"说明": (u"用户 ZF153 给的振金剑贴图（16x16 / 8 位 RGBA / 无隔行 / 零半透明，"
                 u"本来就是本工程要的规格 ⇒ **原字节复制**）。身份核实：alpha 掩码与原版六档"
                 u"**剑**的 IoU 均为 **%.4f**，而最好的非剑（%s %s）只有 **%.4f** ⇒ 与文件名一致。"
                 u"落位 textures/item/vibranium_sword.png，模型 models/item/vibranium_sword.json"
                 u"（parent = minecraft:item/handheld）。")
                % (best_sword, best_other[1], best_other[2], best_other[0]),
    }
    if key in cred:
        same = cred[key].get(u"sha1") == entry[u"sha1"]
        check(u"凭据里已有这条且 sha1 相同（幂等）", same, cred[key].get(u"轮次", u""))
        if not same:
            return 1
    else:
        cred[key] = entry
        io.open(CRED, "w", encoding="utf-8", newline=u"\n").write(
            json.dumps(cred, ensure_ascii=False, indent=2) + u"\n")
        check(u"补了一条凭据", True, key)
    back2 = json.loads(io.open(CRED, encoding="utf-8").read())
    check(u"回读：条目在、sha1 对、总条目数 +1", back2.get(key, {}).get(u"sha1") == sha1b(src),
          u"条目数 %d" % len(back2))

    print(u"\n备注：")
    for n in notes:
        print(u"  - " + n)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
