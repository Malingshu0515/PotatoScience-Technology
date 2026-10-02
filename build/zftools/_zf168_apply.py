# -*- coding: utf-8 -*-
u"""_zf168_apply.py —— ZF168：应用用户放的铝罐/可乐贴图 + 补上机器漏掉的创造页那一行

用户原话：「饮料罐装机创造模式物品栏好像没有 然后我item里放铝罐和可乐的贴图了 应用一下」。

两件事：
  ① **创造页漏行**（§4.82 那个经典漏项）：`ModBlocks.BEVERAGE_CANNING_MACHINE_ITEM` 没进
     `ModItems` 的创造页 accept ⇒ 玩家在物品栏里找不到它（用户实测发现）；
  ② 用户把两张图**直接放进了 `textures/item/`**，而且是 **`.jpg`**：
       `铝罐.jpg`（795 B）/ `可乐.jpg`（831 B）
     Minecraft 的贴图只认 PNG，且这两件物品现在借的是原版玻璃瓶/蜂蜜瓶 ⇒ 本轮：
     体检 → 转成 16×16 RGBA PNG（**整像素最近邻**，不做插值/缩放）→ 落位 → 改模型指自己的图。

⚠ 转档纪律（ZF60 那 7 张 webp 的教训）：**先体检再谈转档**；尺寸不是 16×16 就停下问人，
   不自己缩；JPG 没有 alpha 通道 ⇒ "透明底"这件事要**现算**（见下）。
"""
import glob
import hashlib
import io
import json
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
BK = r"C:\PotatoST救援\zf168_pre"
TEX = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
MODELS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\item")
MOD = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
ITEMS = os.path.join(MOD, "ModItems.java")
CRED = os.path.join(ROOT, r"build\用户素材\_来源凭据.json")
TEXL = os.path.join(ROOT, r"docs\贴图清单.md")

# (用户放的 jpg, 落位的 png 名, 模型 json, 模型里原来自带的 layer0)
PAIRS = [(u"铝罐.jpg", u"empty_aluminum_can.png", u"empty_aluminum_can.json", u"minecraft:item/glass_bottle"),
         (u"可乐.jpg", u"cola.png", u"cola.json", u"minecraft:item/honey_bottle")]

fails = []


def check(label, ok, detail=u""):
    print(u"  [%s] %s%s" % (u"OK" if ok else u"!!", label, (u"   " + detail) if detail else u""))
    if not ok:
        fails.append(label)
    return ok


def main():
    from PIL import Image
    print(u"① 轮号检查")
    # ⚠ 自己这份脚本要排除掉：第一版 `glob("_zf168_*")` 把**本文件**也算上 ⇒ 永远"不空闲"。
    others = [p for p in glob.glob(os.path.join(ROOT, r"build\zftools\_zf168_*"))
              if os.path.basename(p) != u"_zf168_apply.py"]
    if others or os.path.isdir(BK):
        check(u"ZF168 空闲", False, u"已有 %s 或备份根" % [os.path.basename(p) for p in others])
        return 1
    check(u"ZF168 空闲", True)

    print(u"\n② 备份（要动的四份）")
    for rel in (ITEMS, CRED, TEXL, os.path.join(MODELS, u"empty_aluminum_can.json"),
                os.path.join(MODELS, u"cola.json")):
        dst = os.path.join(BK, os.path.relpath(rel, ROOT))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(rel, dst)
        ok = hashlib.sha1(open(rel, "rb").read()).hexdigest() == \
            hashlib.sha1(open(dst, "rb").read()).hexdigest()
        check(u"%s 备份 + 回读" % os.path.relpath(rel, ROOT), ok)

    print(u"\n③ 两张图体检 + 转 PNG（JPEG 没有 alpha ⇒ 透明底要**现算**）")
    for src_name, png_name, model_name, old_layer in PAIRS:
        src = os.path.join(TEX, src_name)
        if not os.path.exists(src):
            check(u"%s 在盘上" % src_name, False)
            continue
        im = Image.open(src)
        print(u"      %s：%s %dx%d" % (src_name, im.format, im.width, im.height))
        check(u"%s 尺寸 16x16（不对就停下问人，不自己缩）" % src_name,
              (im.width, im.height) == (16, 16), u"%dx%d" % (im.width, im.height))
        rgba = im.convert("RGBA")
        px = rgba.load()
        # JPG 的"透明底"其实是一块纯色（多半是白或黑）：把与四角同色的像素当背景抠掉
        corners = [px[0, 0], px[15, 0], px[0, 15], px[15, 15]]
        bg = max(set(corners), key=corners.count)
        print(u"      四角 = %s ⇒ 判定背景色 %s" % (corners, bg))
        cleared = 0
        for y in range(16):
            for x in range(16):
                r, g, b, a = px[x, y]
                if (r, g, b) == bg[:3]:
                    px[x, y] = (r, g, b, 0)
                    cleared += 1
        check(u"%s 抠掉背景像素（JPG 没 alpha ⇒ 按四角纯色判）" % src_name, cleared > 0,
              u"抠掉 %d / 256" % cleared)
        dst = os.path.join(TEX, png_name)
        rgba.save(dst, "PNG")
        back = Image.open(dst)
        check(u"落位 %s（%d 字节，读回 %s %dx%d）"
              % (png_name, os.path.getsize(dst), back.format, back.width, back.height),
              back.format == "PNG" and (back.width, back.height) == (16, 16))
        # 模型改成指自己的图
        mp = os.path.join(MODELS, model_name)
        text = io.open(mp, encoding="utf-8").read()
        new = text.replace(u'"layer0": "%s"' % old_layer, u'"layer0": "potato_s_t:item/%s"' % png_name[:-4])
        check(u"%s 原本确实借的是 %s" % (model_name, old_layer), new != text)
        io.open(mp, "w", encoding="utf-8", newline=u"\n").write(new)
        d = json.loads(io.open(mp, encoding="utf-8").read())
        check(u"%s 现在指自己的图" % model_name,
              d.get(u"textures", {}).get(u"layer0") == u"potato_s_t:item/%s" % png_name[:-4],
              str(d.get(u"textures")))
        # 源 jpg 归档进用户素材（原字节）
        arch = os.path.join(ROOT, r"build\用户素材", png_name.replace(u".png", u".jpg"))
        shutil.copy2(src, arch)
        cred = json.loads(io.open(CRED, encoding="utf-8").read())
        cred[src_name] = {u"原名": src_name, u"sha1": hashlib.sha1(open(arch, "rb").read()).hexdigest(),
                          u"bytes": os.path.getsize(arch), u"轮次": u"ZF168",
                          u"说明": (u"用户 ZF168 直接把图放进了 textures/item（**JPEG**，%d 字节，16x16）。"
                                   u"Minecraft 只认 PNG ⇒ 转成 8 位 RGBA：**不缩放**（像素一一对应），"
                                   u"只把与四角同色的背景像素抠成透明（JPEG 没有 alpha 通道）。"
                                   u"落位 textures/item/%s，模型 %s 改成指它自己。"
                                   % (os.path.getsize(arch), png_name, model_name))}
        io.open(CRED, "w", encoding="utf-8", newline=u"\n").write(
            json.dumps(cred, ensure_ascii=False, indent=2) + u"\n")
        check(u"凭据登记 %s" % src_name, src_name in json.loads(io.open(CRED, encoding="utf-8").read()))

    print(u"\n④ 补上创造页漏掉的那一行（§4.82）")
    t = io.open(ITEMS, encoding="utf-8").read()
    anchor = u'                        output.accept(COLA.get());// ← 新增（0.13 ZF167 可乐）\n'
    add = u'                        output.accept(ModBlocks.BEVERAGE_CANNING_MACHINE_ITEM.get());// ← 新增（0.13 ZF167 饮料罐装机；ZF168 补：用户实测物品栏里找不到）\n'
    if u"BEVERAGE_CANNING_MACHINE_ITEM.get()" in t:
        print(u"  [幂等] 已经在创造页里了")
    elif t.count(anchor) == 1:
        io.open(ITEMS, "w", encoding="utf-8", newline=u"\n").write(t.replace(anchor, anchor + add, 1))
        check(u"创造页补上机器那一行", u"BEVERAGE_CANNING_MACHINE_ITEM.get()" in
              io.open(ITEMS, encoding="utf-8").read())
    else:
        check(u"锚点（可乐那一行）唯一", False, u"%d 次" % t.count(anchor))

    print(u"\n⑤ 贴图清单：把这两件从「待画」里挪到「已画」")
    tex = io.open(TEXL, encoding="utf-8").read()
    row = (u"\n### ZF168 追记：空铝罐 / 可乐 换上手绘图（用户直接放的就是最终图）\n\n"
           u"| 项 | 值 |\n|---|---|\n"
           u"| 空铝罐 | `textures/item/empty_aluminum_can.png`（用户给的 `铝罐.jpg` 转档：16×16、"
           u"不缩放、按四角纯色抠背景） |\n"
           u"| 可乐 | `textures/item/cola.png`（同上，源 `可乐.jpg`） |\n"
           u"| 机器两张 | ⚠ **仍是占位**（`micro_crusher_*` 的逐字节副本），待画 |\n")
    if u"ZF168 追记" in tex:
        print(u"  [幂等] 已在")
    else:
        io.open(TEXL, "w", encoding="utf-8", newline=u"\n").write(tex + row)
        check(u"贴图清单追记一段", True)

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
