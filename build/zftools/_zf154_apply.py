# -*- coding: utf-8 -*-
"""_zf154_apply.py —— ZF154：采油机加顶/底渲染（`cube_all` → `cube_bottom_top`）

用户原话：「采油机的放素材了」
素材 `采油机顶部和底部_001.png`（3059 B / sha1 `64fcb674c2ff` / 16×16 / 8 位 RGBA /
**整张不透明** / 12 色）—— **文件名点明是顶面与底面**。

## 做什么

现状 `models/block/oil_pump.json` 是 `parent: cube_all`
（**六个面都取同一张 `block/oil_pump.png`**，那是 ZF109 的程序生成占位，151 B / 5 色）。

改成 `minecraft:block/cube_bottom_top` —— 与 **ZF130 处理「锂电池构造器 / 柴油发电机控制器」
时同一套做法**（那两台现在就是 `cube_bottom_top`，工程里 `lithium_battery` 也是这个父级）：

| 位置 | 用哪张 |
|---|---|
| 顶 / 底 | `block/oil_pump_top.png`（= 用户新给的素材，**原字节复制**） |
| 四个侧面 | `block/oil_pump.png`（现有那张，**一个字节不动**） |

顶与底**用同一张**（`top` / `bottom` 两个槽指同一个文件）—— 与 `lithium_battery_plant` /
`diesel_generator_controller` 的写法一致。

物品模型不动（它父级到方块模型）；`cube_bottom_top` 的物品图标取的是**顶面**。
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
U = os.path.join(ROOT, "build", u"用户素材")
A = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
TEXB = os.path.join(A, "textures", "block")
MODELB = os.path.join(A, "models", "block")
MODELI = os.path.join(A, "models", "item")
PROV = os.path.join(U, u"_来源凭据.json")
PRE = os.path.join(ROOT, r"build\zftools\zf154_pre")

SRC = os.path.join(U, u"采油机顶部和底部_001.png")
NEWTEX = "oil_pump_top"
SIDETEX = "oil_pump"
EXPECT_NEW_SHA = "64fcb674c2ff"
EXPECT_SIDE_SHA = "df0a36c03eab"      # ZF109 那张占位（151 B）
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    os.makedirs(PRE, exist_ok=True)

    print(u"① 前置断言")
    if not os.path.exists(SRC):
        print(u"  !! 找不到素材 %s" % SRC)
        return 1
    side = os.path.join(TEXB, SIDETEX + ".png")
    if not os.path.exists(side):
        print(u"  !! 找不到现有侧面贴图")
        return 1
    hs = sha1(side)
    print(u"  素材 sha1 %s（期望 %s）" % (sha1(SRC)[:12], EXPECT_NEW_SHA))
    print(u"  现有 %s.png sha1 %s（期望 %s，%d B）"
          % (SIDETEX, hs[:12], EXPECT_SIDE_SHA, os.path.getsize(side)))
    if sha1(SRC)[:12] != EXPECT_NEW_SHA:
        fails.append(u"素材 sha1 与预期不符")
    if hs[:12] != EXPECT_SIDE_SHA:
        fails.append(u"现有侧面贴图不是 ZF109 那张（盘被人动过）")
    if fails:
        for f in fails:
            print(u"  !! " + f)
        return 1

    print(u"\n② 备份将被改的两份（模型 + 凭据）")
    for rel in (r"src\main\resources\assets\potato_s_t\models\block\oil_pump.json",
                r"build\用户素材\_来源凭据.json"):
        p = os.path.join(ROOT, rel)
        dst = os.path.join(PRE, rel.replace("\\", "__"))
        shutil.copyfile(p, dst)
        ok = sha1(p) == sha1(dst)
        print(u"  %s %s" % (u"[OK]" if ok else u"[!!]", os.path.basename(rel)))
        if not ok:
            fails.append(u"%s 备份校验失败" % rel)
    if fails:
        return 1

    print(u"\n③ 新贴图体检 + 原字节上线")
    blob = open(SRC, "rb").read()
    w, h, rgba = read_png(SRC)
    op = sum(1 for i in range(w * h) if rgba[i * 4 + 3] == 255)
    semi = sum(1 for i in range(w * h) if 0 < rgba[i * 4 + 3] < 255)
    print(u"  %dx%d 位深 %d 类型 %d 不透明 %d 半透明 %d  %d B"
          % (w, h, blob[24], blob[25], op, semi, len(blob)))
    if (w, h, blob[24], blob[25]) != (16, 16, 8, 6):
        fails.append(u"规格不是 16x16/8/RGBA")
    if semi:
        fails.append(u"有半透明像素")
    # 方块贴图应当整张不透明（与现有那张一致；有透明会露出洞）
    if op != w * h:
        fails.append(u"方块贴图不是整张不透明（%d/%d）" % (op, w * h))
    if fails:
        for f in fails:
            print(u"  !! " + f)
        return 1
    dst = os.path.join(TEXB, NEWTEX + ".png")
    io.open(dst, "wb").write(blob)
    if open(dst, "rb").read() != blob:
        fails.append(u"%s.png 写出不一致" % NEWTEX)
        return 1
    print(u"  [OK] textures/block/%s.png 写出 sha1 %s" % (NEWTEX, sha1(dst)[:12]))

    print(u"\n④ 模型：cube_all → cube_bottom_top")
    mp = os.path.join(MODELB, "oil_pump.json")
    raw = io.open(mp, encoding="utf-8").read()
    print(u"  改前：%s" % raw.replace(u"\n", u" "))
    if "cube_bottom_top" in raw:
        print(u"  [幂等] 已是 cube_bottom_top")
    elif "cube_all" not in raw:
        fails.append(u"模型父级既不是 cube_all 也不是 cube_bottom_top，停手")
        print(u"  !! 父级认不出，停手")
    else:
        obj = {
            "parent": "minecraft:block/cube_bottom_top",
            "textures": {
                "top": "potato_s_t:block/" + NEWTEX,
                "bottom": "potato_s_t:block/" + NEWTEX,
                "side": "potato_s_t:block/" + SIDETEX,
            },
        }
        io.open(mp, "w", encoding="utf-8", newline="\n").write(
            json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
        back = json.loads(io.open(mp, encoding="utf-8").read())
        ok = (back["parent"] == "minecraft:block/cube_bottom_top"
              and back["textures"]["top"] == "potato_s_t:block/" + NEWTEX
              and back["textures"]["bottom"] == "potato_s_t:block/" + NEWTEX
              and back["textures"]["side"] == "potato_s_t:block/" + SIDETEX)
        print(u"  %s 改后：%s" % (u"[OK]" if ok else u"[!!]",
                                  json.dumps(back, ensure_ascii=False)))
        if not ok:
            fails.append(u"模型改写回读失败")

    print(u"\n⑤ 物品模型（应父级到方块模型，不用改）")
    ip = os.path.join(MODELI, "oil_pump.json")
    im = json.loads(io.open(ip, encoding="utf-8").read())
    ok = im.get("parent") == "potato_s_t:block/oil_pump"
    print(u"  %s %s" % (u"[OK]" if ok else u"[!!]", json.dumps(im, ensure_ascii=False)))
    if not ok:
        fails.append(u"物品模型父级不对")

    print(u"\n⑥ 凭据登记")
    prov = json.loads(io.open(PROV, encoding="utf-8").read())
    prov[NEWTEX + ".png"] = {
        u"原名": u"采油机顶部和底部_001.png",
        "sha1": hashlib.sha1(blob).hexdigest(),
        "bytes": len(blob),
        u"说明": (u"用户 ZF154 给的采油机顶/底贴图（16x16 / 8 位 RGBA / 整张不透明 / 12 色）"
                  u"⇒ 原字节复制成 textures/block/oil_pump_top.png；"
                  u"采油机的模型由 `cube_all` 改成 `cube_bottom_top`（顶/底 = 这张，"
                  u"四个侧面 = ZF109 那张程序生成的 oil_pump.png，一个字节没动）"),
    }
    io.open(PROV, "w", encoding="utf-8", newline="\n").write(
        json.dumps(prov, indent=2, ensure_ascii=False) + "\n")
    print(u"  [OK] 凭据条目 %d 条" % len(prov))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
