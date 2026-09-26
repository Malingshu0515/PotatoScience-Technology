# -*- coding: utf-8 -*-
u"""_zf125_assets.py —— ZF125 的资源：贴图 / 方块模型 / 标签 / 配方

七件事，每件都自检：
  ① `textures/block/diesel_generator_controller.png` —— **程序化生成**的 16×16 占位贴图
     （用户没给控制器贴图；写法照本工程的老路：`PngRecolor.write_png` 零依赖写 PNG，
     写完**回读**逐像素核几条关键点，不合格就 sys.exit(1)）
  ② `blockstates/diesel_generator_controller.json` —— 方块有 FACING ⇒ 四个朝向都得列
  ③ `models/block/diesel_generator_controller.json` + `models/item/…json`
  ④ `blockstates/diesel_generator_port.json` + `models/block/diesel_generator_port.json`
     —— 接线口贴图**直接用接线块那张**（`potato_s_t:block/wiring_block`），玩家看不出被换过
  ⑤ `data/minecraft/tags/block/mineable/pickaxe.json` —— 加两个方块（不然挖下去什么都不掉，§4.25）
  ⑥ `data/minecraft/tags/block/needs_stone_tool.json` —— 同上（木镐不够）
  ⑦ `data/potato_s_t/recipe/diesel_generator_controller.json`（用户给的配方）
     + `data/potato_s_t/tags/item/copper_blocks.json`（8 种铜块，用户说"无论氧化/涂蜡程度都可以"）

跑法：
    python build\\zftools\\_zf125_assets.py
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png, write_png   # noqa: E402

ROOT = r"E:\PotatoST"
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
DATA = os.path.join(ROOT, r"src\main\resources\data")

CTRL_TEX = os.path.join(ASSETS, r"textures\block\diesel_generator_controller.png")

notes, fails = [], []

# ===================== ① 贴图 =====================

BASE = (124, 127, 133)
DARK = (66, 68, 74)
LIGHT = (156, 159, 165)
BOLT = (176, 178, 184)
GLASS = (30, 32, 38)
DIESEL = (206, 124, 32)
DIESEL_TOP = (232, 152, 52)


def build_texture():
    u"""16×16 的占位贴图：金属面板 + 一颗铆钉四角 + 中间一扇能看到柴油液位的观察窗。"""
    px = bytearray(16 * 16 * 4)
    for y in range(16):
        for x in range(16):
            r, g, b, a = BASE[0], BASE[1], BASE[2], 255
            if x in (0, 15) or y in (0, 15):
                r, g, b = DARK
            elif 1 <= x <= 14 and 1 <= y <= 14:
                # 两格一档的明暗交替 —— 让 16×16 看起来像有厚度的金属板，不是纯色块
                if (x + y) % 4 < 2:
                    r, g, b = LIGHT
            px[(y * 16 + x) * 4:(y * 16 + x) * 4 + 4] = bytes((r, g, b, a))
    # 观察窗：外框 1 圈深色，里面是暗腔，下半截是柴油
    for y in range(4, 13):
        for x in range(5, 11):
            color = GLASS
            if y == 4 or y == 12 or x == 5 or x == 10:
                color = DARK
            elif y >= 8:
                color = DIESEL_TOP if y == 8 else DIESEL
            px[(y * 16 + x) * 4:(y * 16 + x) * 4 + 4] = bytes(
                (color[0], color[1], color[2], 255))
    # 四角铆钉
    for (x, y) in ((2, 2), (13, 2), (2, 13), (13, 13)):
        px[(y * 16 + x) * 4:(y * 16 + x) * 4 + 4] = bytes((BOLT[0], BOLT[1], BOLT[2], 255))
    # 顶上两根排气管
    for x in (6, 9):
        px[(1 * 16 + x) * 4:(1 * 16 + x) * 4 + 4] = bytes((DARK[0], DARK[1], DARK[2], 255))
    return px


def pixel(rgba, x, y):
    i = (y * 16 + x) * 4
    return tuple(rgba[i:i + 4])


def step_texture():
    write_png(CTRL_TEX, 16, 16, build_texture())
    w, h, back = read_png(CTRL_TEX)
    if (w, h) != (16, 16):
        fails.append(u"贴图尺寸 %dx%d（要 16x16）" % (w, h))
        return
    checks = [
        (u"左上角是深色边框", pixel(back, 0, 0)[:3] == DARK),
        (u"四角铆钉是亮色", pixel(back, 2, 2)[:3] == BOLT),
        (u"观察窗下沿是柴油色（R>G>B 且 R>150）",
         pixel(back, 7, 10)[0] > 150 and pixel(back, 7, 10)[0] > pixel(back, 7, 10)[1] > pixel(back, 7, 10)[2]),
        (u"观察窗里没有透明像素", pixel(back, 7, 6)[3] == 255),
    ]
    bad = [name for name, ok in checks if not ok]
    if bad:
        fails.append(u"贴图回读自检失败：%s" % u"、".join(bad))
        return
    notes.append(u"① 贴图 %d B（16×16，4 条回读自检全过）" % os.path.getsize(CTRL_TEX))


# ===================== JSON 小工具 =====================

def write_json(rel, obj):
    path = os.path.join(ROOT, rel)
    if os.path.exists(path):
        fails.append(u"%s 已经存在了 —— 本轮它是新增件，别覆盖" % rel)
        return
    text = json.dumps(obj, ensure_ascii=False, indent=2) + u"\n"
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)
    back = json.loads(io.open(path, encoding="utf-8").read())
    if back != obj:
        fails.append(u"%s 回读不相等" % rel)
        return
    notes.append(u"新增 %s（%d B，回读通过）" % (rel.replace(u"\\", u"/"), len(text.encode(u"utf-8"))))


def patch(rel, old, new):
    path = os.path.join(ROOT, rel)
    text = io.open(path, encoding="utf-8", newline=u"").read()
    nl = u"\r\n" if u"\r\n" in text else u"\n"
    o, n = old.replace(u"\n", nl), new.replace(u"\n", nl)
    cnt = text.count(o)
    if cnt != 1:
        fails.append(u"%s：锚点命中 %d 次（要 1 次）" % (rel, cnt))
        return
    io.open(path, "w", encoding="utf-8", newline=u"").write(text.replace(o, n, 1))
    json.loads(io.open(path, encoding="utf-8").read())     # 改完必须是合法 JSON
    notes.append(u"追加 %s（锚点 1 次命中，改后仍是合法 JSON）" % rel.replace(u"\\", u"/"))


# ===================== ②③ 控制器 =====================

def step_controller_assets():
    write_json(r"src\main\resources\assets\potato_s_t\blockstates\diesel_generator_controller.json", {
        u"variants": {
            u"facing=north": {u"model": u"potato_s_t:block/diesel_generator_controller"},
            u"facing=east": {u"model": u"potato_s_t:block/diesel_generator_controller"},
            u"facing=south": {u"model": u"potato_s_t:block/diesel_generator_controller"},
            u"facing=west": {u"model": u"potato_s_t:block/diesel_generator_controller"},
        }
    })
    write_json(r"src\main\resources\assets\potato_s_t\models\block\diesel_generator_controller.json", {
        u"parent": u"minecraft:block/cube_all",
        u"textures": {u"all": u"potato_s_t:block/diesel_generator_controller"},
    })
    write_json(r"src\main\resources\assets\potato_s_t\models\item\diesel_generator_controller.json", {
        u"parent": u"potato_s_t:block/diesel_generator_controller",
    })


# ===================== ④ 接线口 =====================

def step_port_assets():
    write_json(r"src\main\resources\assets\potato_s_t\blockstates\diesel_generator_port.json", {
        u"variants": {u"": {u"model": u"potato_s_t:block/diesel_generator_port"}}
    })
    write_json(r"src\main\resources\assets\potato_s_t\models\block\diesel_generator_port.json", {
        u"parent": u"minecraft:block/cube_all",
        u"textures": {u"all": u"potato_s_t:block/wiring_block"},
    })


# ===================== ⑤⑥ 挖掘标签 =====================

def step_tags():
    patch(r"src\main\resources\data\minecraft\tags\block\mineable\pickaxe.json",
          u"    \"potato_s_t:lithium_battery_plant\"\n  ]\n",
          u"    \"potato_s_t:lithium_battery_plant\",\n"
          u"    \"potato_s_t:diesel_generator_controller\",\n"
          u"    \"potato_s_t:diesel_generator_port\"\n  ]\n")
    patch(r"src\main\resources\data\minecraft\tags\block\needs_stone_tool.json",
          u"    \"potato_s_t:alloy_smelter_port\"\n  ]\n",
          u"    \"potato_s_t:alloy_smelter_port\",\n"
          u"    \"potato_s_t:diesel_generator_controller\",\n"
          u"    \"potato_s_t:diesel_generator_port\"\n  ]\n")


# ===================== ⑦ 配方 + 铜块标签 =====================

def step_recipe():
    # 用户原话：「柴油发电机控制器配方;【】【流体管道】【】，【铜块】【熔炉】【铜块】，【】【钢板】【】」
    write_json(r"src\main\resources\data\potato_s_t\recipe\diesel_generator_controller.json", {
        u"type": u"minecraft:crafting_shaped",
        u"category": u"misc",
        u"pattern": [u" P ", u"CBC", u" S "],
        u"key": {
            u"P": {u"item": u"potato_s_t:fluid_pipe"},
            u"C": {u"tag": u"potato_s_t:copper_blocks"},
            u"B": {u"item": u"minecraft:furnace"},
            u"S": {u"item": u"potato_s_t:steel_plate"},
        },
        u"result": {u"id": u"potato_s_t:diesel_generator_controller", u"count": 1},
    })
    # 用户原话「（铜无论氧化/涂蜡程度都可以）」⇒ 配方里的铜块也照这条放宽（8 种全收）
    write_json(r"src\main\resources\data\potato_s_t\tags\item\copper_blocks.json", {
        u"values": [
            u"minecraft:copper_block",
            u"minecraft:exposed_copper",
            u"minecraft:weathered_copper",
            u"minecraft:oxidized_copper",
            u"minecraft:waxed_copper_block",
            u"minecraft:waxed_exposed_copper",
            u"minecraft:waxed_weathered_copper",
            u"minecraft:waxed_oxidized_copper",
        ]
    })


def main():
    step_texture()
    step_controller_assets()
    step_port_assets()
    step_tags()
    step_recipe()
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"完成 %d 项" % len(notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
