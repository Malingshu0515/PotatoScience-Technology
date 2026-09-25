# -*- coding: utf-8 -*-
"""_zf60_verify.py —— 这 7 张贴图装对了没有（常驻检查）

用户按顺序给的：磁铁 铁粉 钛矿石 深层钛矿石 粗钛 钛粉 钛锭（文件名他自己说可能打错）。
这条检查把三件事钉住：
  ① 7 张贴图都在资源树里、是 **8 位 RGBA PNG**、尺寸对；
  ② 物品贴图**必须有透明底**（没有的话游戏里就是个花屏/白方块套着图案 —— ZF60 真踩过：
     WPF 的 BitmapDecoder 读 webp 会把 alpha 丢掉，透明区底下是花屏）；
     方块贴图（两张矿）整张不透明；
  ③ 7 个模型都指向**自己的**贴图，不许再借原版 iron_ingot / gunpowder / raw_iron / iron_ore。
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _zf60_install import read_png, stats  # noqa: E402

PROJ = r"E:\PotatoST"
ASSETS = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t")

# (贴图相对路径, 尺寸, 模式, 引用它的模型, 模型里必须出现的贴图串)
ITEMS = [
    ("textures/item/magnet.png", (32, 32), "alpha", "models/item/magnet.json",
     "potato_s_t:item/magnet"),
    ("textures/item/iron_powder.png", (16, 16), "alpha", "models/item/iron_powder.json",
     "potato_s_t:item/iron_powder"),
    ("textures/item/raw_titanium.png", (32, 32), "alpha", "models/item/raw_titanium.json",
     "potato_s_t:item/raw_titanium"),
    ("textures/item/titanium_powder.png", (32, 32), "alpha", "models/item/titanium_powder.json",
     "potato_s_t:item/titanium_powder"),
    ("textures/item/titanium_ingot.png", (32, 32), "alpha", "models/item/titanium_ingot.json",
     "potato_s_t:item/titanium_ingot"),
    ("textures/block/titanium_ore.png", (16, 16), "opaque", "models/block/titanium_ore.json",
     "potato_s_t:block/titanium_ore"),
    ("textures/block/deepslate_titanium_ore.png", (16, 16), "opaque",
     "models/block/deepslate_titanium_ore.json", "potato_s_t:block/deepslate_titanium_ore"),
]

# 这几条**不许**再出现在这些模型里（都是原来借的原版贴图）
BANNED = ["minecraft:item/iron_ingot", "minecraft:item/gunpowder", "minecraft:item/raw_iron",
          "minecraft:block/iron_ore", "minecraft:block/deepslate_iron_ore"]

fails = []


def check(cond, msg):
    print((u"  [OK]   " if cond else u"  [FAIL] ") + msg)
    if not cond:
        fails.append(msg)
    return cond


def main():
    print(u"① 贴图本体")
    for rel, want, mode, model, ref in ITEMS:
        path = os.path.join(ASSETS, rel.replace("/", os.sep))
        if not os.path.isfile(path):
            check(False, u"%s 存在" % rel)
            continue
        w, h, depth, color, ch, px = read_png(path)
        opaque, ncolors, _top = stats(w, h, ch, px, b"")
        ratio = 100.0 * opaque / (w * h)
        ok = check((w, h) == want and depth == 8 and color == 6,
                   u"%s: %dx%d 8 位 RGBA（读到 %dx%d 深度%d 色型%d）" % (rel, want[0], want[1], w, h, depth, color))
        ok &= check(ncolors >= 4, u"%s: 真实内容（%d 色）" % (rel, ncolors))
        if mode == "alpha":
            ok &= check(5.0 <= ratio <= 99.5,
                        u"%s: 物品贴图有透明底（不透明 %.1f%%）" % (rel, ratio))
        else:
            ok &= check(ratio >= 99.9, u"%s: 方块贴图整张不透明（%.1f%%）" % (rel, ratio))

    print(u"\n② 模型指向自己的贴图")
    for rel, want, mode, model, ref in ITEMS:
        path = os.path.join(ASSETS, model.replace("/", os.sep))
        if not os.path.isfile(path):
            check(False, u"%s 存在" % model)
            continue
        text = io.open(path, encoding="utf-8").read()
        json.loads(text)                      # 语法
        check(ref in text, u"%s 指向 %s" % (model, ref))

    print(u"\n③ 原版占位贴图已经全部换掉")
    offenders = []
    for _rel, _want, _mode, model, _ref in ITEMS:
        text = io.open(os.path.join(ASSETS, model.replace("/", os.sep)), encoding="utf-8").read()
        for bad in BANNED:
            if bad in text:
                offenders.append(u"%s 里还有 %s" % (model, bad))
    check(not offenders, u"7 个模型里没有残留的原版贴图引用（%s）" % (offenders or u"无"))

    print(u"\n④ 矿石物品模型跟着方块模型")
    for rel, parent in (("models/item/titanium_ore.json", "potato_s_t:block/titanium_ore"),
                        ("models/item/deepslate_titanium_ore.json",
                         "potato_s_t:block/deepslate_titanium_ore")):
        path = os.path.join(ASSETS, rel.replace("/", os.sep))
        text = io.open(path, encoding="utf-8").read() if os.path.isfile(path) else u""
        check(parent in text, u"%s -> %s" % (rel, parent))

    print(u"\n------------------------------")
    print(u"失败项 = %d" % len(fails))
    print(u"结论: " + (u"通过" if not fails else u"有失败项"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
