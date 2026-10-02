# -*- coding: utf-8 -*-
"""_zf117_apply.py —— ZF117：给两个方块加顶/底渲染 + 上线银线两件

用户原话：「东西放用户素材了 有些方块6个面用的都是一个贴图 你加个顶面底面渲染
然后再用相应的贴图」

## 方块（本轮主体）

两个方块现在是 `parent: minecraft:block/cube_all` ——
**六个面都取同一张 `all` 贴图**（这就是用户说的"6 个面用的都是一个贴图"）。
改成 `minecraft:block/cube_bottom_top`（**与本工程既有的 `lithium_battery` 同一个父级、同一套写法**）：

| 方块 | top / bottom（你给的新图） | side（现有那张，不动） |
|---|---|---|
| `lithium_battery_plant`（锂电池构造器） | `锂电池构造器上和下面_001.png` | `lithium_battery_plant.png` |
| `diesel_generator_controller`（柴油发电机控制器） | `柴油发电机控制器顶部&底部_001.png` | `diesel_generator_controller.png` |

**凭什么断定"现有那张就是侧面"**（不是猜的）：
① 你这两张文件名分别叫「上和下面」「顶部&底部」⇒ 明说了是顶/底；
② `lithium_battery_plant.png` 下半截是绿/蓝**竖条纹**（电芯柱面的样子），
   `diesel_generator_controller.png` 是灰格栅 —— 都是侧面的画法；
③ `diesel_generator_controller` 的 blockstate **有 facing**（这台机器认朝向），
   侧面本来就该是"转过去看的那一面"。

⚠ 顶/底用**同一张**（`cube_bottom_top` 的 `top`/`bottom` 两个槽指同一个文件）——
既有 `lithium_battery` 就是这么写的（`bottom` 指 `_side`、`top` 指 `_top`），保持一致。

## 物品（顺带）

`银线_001.png` / `银线轴_001.png` —— 这两个物品**现在还在借原版贴图**
（`silver_wire` → `minecraft:item/iron_nugget`、`silver_wire_spool` → `minecraft:item/iron_ingot`）
⇒ 上线后模型改指自己。借原版贴图的模型 **9 → 7**（三处活体数字一起改）。

`振金锭.png`（32×280 = **8 帧竖排**）本轮**不动**：形状可疑（原版锭贴图是 16×16），
而且 ZF114 刚给 `raw_vibranium` 做过 16×16 贴图 —— 等用户说明这是什么再收。
"""
import hashlib
import io
import json
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
USERART = os.path.join(ROOT, "build", "用户素材")
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
TEXB = os.path.join(ASSETS, "textures", "block")
TEXI = os.path.join(ASSETS, "textures", "item")
MODELB = os.path.join(ASSETS, "models", "block")
MODELI = os.path.join(ASSETS, "models", "item")
DOCS = os.path.join(ROOT, "docs")

fails = []

# 方块：{方块名: (用户顶底图, 上线后的顶底贴图名, 现有侧面贴图名, 期望现有贴图 sha1 前12)}
BLOCKS = {
    "lithium_battery_plant": (u"锂电池构造器上和下面_001.png",
                              "lithium_battery_plant_top", "lithium_battery_plant",
                              "3b3f6d1a"),   # 占位，下面动态读
    "diesel_generator_controller": (u"柴油发电机控制器顶部&底部_001.png",
                                    "diesel_generator_controller_top",
                                    "diesel_generator_controller", None),
}

# 物品：{物品id: (用户图, 上线贴图名, 原本借的原版贴图)}
ITEMS = {
    "silver_wire": (u"银线_001.png", "silver_wire", "minecraft:item/iron_nugget"),
    "silver_wire_spool": (u"银线轴_001.png", "silver_wire_spool", "minecraft:item/iron_ingot"),
}

OLD_N, NEW_N = 9, 7


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def check_png(p, label):
    b = open(p, "rb").read()
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        fails.append(u"%s 不是真 PNG" % label)
        return None
    w, h, rgba = read_png(p)
    op = sum(1 for i in range(w * h) if rgba[i * 4 + 3] == 255)
    sem = sum(1 for i in range(w * h) if 0 < rgba[i * 4 + 3] < 255)
    print(u"    %s：%d B  %dx%d 位深%d 类型%d 不透明 %d 半透明 %d"
          % (label, len(b), w, h, b[24], b[25], op, sem))
    if (w, h, b[24], b[25]) != (16, 16, 8, 6):
        fails.append(u"%s 规格不是 16x16/8/RGBA" % label)
    if sem:
        fails.append(u"%s 有半透明像素 %d 个" % (label, sem))
    return b


def main():
    print("=" * 74)
    print(u"① 方块：顶/底贴图上线")
    for name, (srcname, texname, sidename, _) in BLOCKS.items():
        src = os.path.join(USERART, srcname)
        if not os.path.exists(src):
            fails.append(u"找不到 %s" % srcname)
            print(u"  !! 找不到 %s" % srcname)
            continue
        print(u"  %s（%s）" % (name, srcname))
        b = check_png(src, srcname)
        if b is None:
            continue
        # 原字节复制成 block/<texname>.png
        dst = os.path.join(TEXB, texname + ".png")
        io.open(dst, "wb").write(b)
        if open(dst, "rb").read() != b:
            fails.append(u"%s.png 写出不一致" % texname)
        else:
            print(u"    [OK] textures/block/%s.png  sha1 %s" % (texname, sha1(dst)[:12]))
        # 侧面必须已经在
        side = os.path.join(TEXB, sidename + ".png")
        if not os.path.exists(side):
            fails.append(u"侧面贴图 %s.png 不存在" % sidename)
        else:
            print(u"    侧面 textures/block/%s.png 在（sha1 %s，不动）"
                  % (sidename, sha1(side)[:12]))

        # 模型：cube_all -> cube_bottom_top
        mp = os.path.join(MODELB, name + ".json")
        raw = io.open(mp, encoding="utf-8").read()
        if "cube_bottom_top" in raw:
            print(u"    [幂等] 模型已是 cube_bottom_top")
            continue
        if "cube_all" not in raw:
            fails.append(u"%s 的模型既不是 cube_all 也不是 cube_bottom_top，停手" % name)
            print(u"    !! %s 的模型父级不是 cube_all，停手" % name)
            continue
        model = {
            "parent": "minecraft:block/cube_bottom_top",
            "textures": {
                "top": "potato_s_t:block/" + texname,
                "bottom": "potato_s_t:block/" + texname,
                "side": "potato_s_t:block/" + sidename,
            },
        }
        io.open(mp, "w", encoding="utf-8", newline="\n").write(
            json.dumps(model, indent=2, ensure_ascii=False) + "\n")
        back = json.loads(io.open(mp, encoding="utf-8").read())
        ok = (back["parent"] == "minecraft:block/cube_bottom_top"
              and back["textures"]["top"] == "potato_s_t:block/" + texname
              and back["textures"]["bottom"] == "potato_s_t:block/" + texname
              and back["textures"]["side"] == "potato_s_t:block/" + sidename)
        print(u"    %s 模型 cube_all -> cube_bottom_top（顶/底=%s，侧面=%s）"
              % (u"[OK]" if ok else u"[!!]", texname, sidename))
        if not ok:
            fails.append(u"%s 模型改写回读失败" % name)

    print("\n" + "=" * 74)
    print(u"② 物品：银线 / 银线轴 上线（原先借原版贴图）")
    for item, (srcname, texname, borrowed) in ITEMS.items():
        src = os.path.join(USERART, srcname)
        if not os.path.exists(src):
            fails.append(u"找不到 %s" % srcname)
            print(u"  !! 找不到 %s" % srcname)
            continue
        print(u"  %s（%s，原先借 %s）" % (item, srcname, borrowed))
        b = check_png(src, srcname)
        if b is None:
            continue
        dst = os.path.join(TEXI, texname + ".png")
        io.open(dst, "wb").write(b)
        if open(dst, "rb").read() != b:
            fails.append(u"%s.png 写出不一致" % texname)
        else:
            print(u"    [OK] textures/item/%s.png  sha1 %s" % (texname, sha1(dst)[:12]))
        mp = os.path.join(MODELI, item + ".json")
        raw = io.open(mp, encoding="utf-8").read()
        if "potato_s_t:item/" + texname in raw:
            print(u"    [幂等] 模型已指向自己")
            continue
        if borrowed not in raw:
            fails.append(u"%s 模型里没有预期的原版引用 %s，停手" % (item, borrowed))
            print(u"    !! 模型里找不到 %s，停手" % borrowed)
            continue
        raw2 = raw.replace(borrowed, "potato_s_t:item/" + texname)
        io.open(mp, "w", encoding="utf-8", newline="\n").write(raw2)
        back = json.loads(io.open(mp, encoding="utf-8").read())
        ok = back["textures"]["layer0"] == "potato_s_t:item/" + texname
        print(u"    %s 模型 layer0：%s -> %s" % (u"[OK]" if ok else u"[!!]",
                                                 borrowed, back["textures"]["layer0"]))
        if not ok:
            fails.append(u"%s 模型改写回读失败" % item)

    print("\n" + "=" * 74)
    print(u"③ 活体数字 %d -> %d（三处一起改）" % (OLD_N, NEW_N))

    def patch(path, old, new, label):
        t = io.open(path, encoding="utf-8").read()
        n = t.count(old)
        if n != 1:
            fails.append(u"%s：锚点出现 %d 次（期望 1）—— 停手" % (label, n))
            print(u"    !! %s 锚点 %d 次，停手" % (label, n))
            return
        io.open(path, "w", encoding="utf-8", newline="\n").write(t.replace(old, new))
        b = io.open(path, encoding="utf-8").read()
        if new not in b or old in b:
            fails.append(u"%s 回读失败" % label)
            print(u"    !! %s 回读失败" % label)
        else:
            print(u"    [OK] %s" % label)

    ann = os.path.join(DOCS, "UpdateAnnouncement_EN.md")
    t = io.open(ann, encoding="utf-8").read()
    if u"%d models still do this" % NEW_N in t:
        print(u"    [幂等] 公告已是 %d" % NEW_N)
    else:
        patch(ann, u"%d models still do this" % OLD_N, u"%d models still do this" % NEW_N,
              u"公告 %d -> %d" % (OLD_N, NEW_N))
    z71 = os.path.join(TOOLS, "_zf71_verify.py")
    t = io.open(z71, encoding="utf-8").read()
    if u"n_draw == %d" % NEW_N in t:
        print(u"    [幂等] _zf71 已是 %d" % NEW_N)
    else:
        patch(z71, u"n_draw == %d" % OLD_N, u"n_draw == %d" % NEW_N,
              u"_zf71 n_draw %d -> %d" % (OLD_N, NEW_N))
        patch(z71, u'u"%d models still do this"' % OLD_N, u'u"%d models still do this"' % NEW_N,
              u"_zf71 文案 %d -> %d" % (OLD_N, NEW_N))
        patch(z71, u"（公告写 %d）" % OLD_N, u"（公告写 %d）" % NEW_N,
              u"_zf71 中文标签 -> %d" % NEW_N)
    z90 = os.path.join(TOOLS, "_zf90_verify.py")
    t = io.open(z90, encoding="utf-8").read()
    if u"u\"%d models still do this\" in ann" % NEW_N in t:
        print(u"    [幂等] _zf90 已是 %d" % NEW_N)
    else:
        patch(z90, u'u"英文公告已改成 %d models still do this"' % OLD_N,
              u'u"英文公告已改成 %d models still do this"' % NEW_N, u"_zf90 公告标签")
        patch(z90, u'u"%d models still do this" in ann' % OLD_N,
              u'u"%d models still do this" in ann' % NEW_N, u"_zf90 公告断言")
        patch(z90, u"for n in (5, 6, 7, 13, 12)", u"for n in (5, 6, 7, 13, 12, 9)",
              u"_zf90 旧数字黑名单加 9")
        patch(z90, u"u\"英文公告里不再写 5/6/7/13/12 models\"",
              u"u\"英文公告里不再写 5/6/7/13/12/9 models\"", u"_zf90 标签补 9")
        patch(z90, u'u"`_zf71_verify.py` 的期望值同步成 %d"' % OLD_N,
              u'u"`_zf71_verify.py` 的期望值同步成 %d"' % NEW_N, u"_zf90 z71 标签")
        patch(z90, u'u"n_draw == %d" in z71' % OLD_N,
              u'u"n_draw == %d" in z71' % NEW_N, u"_zf90 z71 断言")

    print("\n" + "=" * 74)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
