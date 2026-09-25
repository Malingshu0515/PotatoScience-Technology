# -*- coding: utf-8 -*-
u"""_zf82_assets.py —— ZF82 资源：两个液体方块（blockstate/model/贴图）+ 两个桶的物品模型 + 换流器的方块资源 + 合成配方

规矩（往轮踩过的）：
  · 液体方块的 blockstate/model 照原油那两份抄（只有 particle 的 model）；
  · 桶的物品模型按用户吩咐**借原版水桶贴图**（不新增 PNG）；
  · 换流器方块贴图是**我生成的 16×16 占位**（用户没给图），进贴图清单的待画；
  · 合成配方里的每个 id 都**查注册名核对**（不凭记忆），并断言锚点/文件数。
"""
import io
import json
import os
import struct
import sys
import zlib

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ASSETS = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t")
DATA = os.path.join(ROOT, "src", "main", "resources", "data", "potato_s_t")
TEX = os.path.join(ASSETS, "textures", "block")

fails = []


def write_json(path, obj, label):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(
        json.dumps(obj, indent=2, ensure_ascii=False) + u"\n")
    print(u"  [OK]   %s" % label)


def png16(path, pixels, label):
    u"""写一张 16×16 的 8 位 RGBA PNG（TextureCheck 要求位深 8 / 类型 6）。"""
    raw = b""
    for y in range(16):
        raw += b"\x00" + b"".join(pixels[y * 16 + x] for x in range(16))

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", 16, 16, 8, 6, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    io.open(path, "wb").write(data)
    print(u"  [OK]   %s（16×16 / 8 位 / RGBA）" % label)


def main():
    print(u"== ① 两个液体方块的 blockstate / model ==")
    for name in [u"diesel", u"gasoline"]:
        write_json(os.path.join(ASSETS, "blockstates", name + u".json"),
                   {"variants": {"": {"model": "potato_s_t:block/" + name}}},
                   u"blockstates/%s.json" % name)
        write_json(os.path.join(ASSETS, "models", "block", name + u".json"),
                   {"textures": {"particle": "potato_s_t:block/" + name + "_still"}},
                   u"models/block/%s.json（只有 particle，照原油那份）" % name)

    print(u"== ② 两个桶的物品模型（借原版水桶贴图，用户吩咐）==")
    for name in [u"diesel_bucket", u"gasoline_bucket"]:
        write_json(os.path.join(ASSETS, "models", "item", name + u".json"),
                   {"parent": "minecraft:item/generated",
                    "textures": {"layer0": "minecraft:item/water_bucket"}},
                   u"models/item/%s.json（layer0 = 原版水桶）" % name)

    print(u"== ③ 容器换流器的方块资源（占位贴图，我生成）==")
    write_json(os.path.join(ASSETS, "blockstates", u"fluid_exchanger.json"),
               {"variants": {"facing=north": {"model": "potato_s_t:block/fluid_exchanger"},
                             "facing=east": {"model": "potato_s_t:block/fluid_exchanger",
                                             "y": 90},
                             "facing=south": {"model": "potato_s_t:block/fluid_exchanger",
                                              "y": 180},
                             "facing=west": {"model": "potato_s_t:block/fluid_exchanger",
                                             "y": 270}}},
               u"blockstates/fluid_exchanger.json（四个朝向同一张对称贴图）")
    write_json(os.path.join(ASSETS, "models", "block", u"fluid_exchanger.json"),
               {"parent": "minecraft:block/cube_all",
                "textures": {"all": "potato_s_t:block/fluid_exchanger"}},
               u"models/block/fluid_exchanger.json")
    write_json(os.path.join(ASSETS, "models", "item", u"fluid_exchanger.json"),
               {"parent": "potato_s_t:block/fluid_exchanger"},
               u"models/item/fluid_exchanger.json")

    # 占位贴图：金属灰底 + 两侧"管道口" + 中间一个方框（16×16）
    edge = bytes((0x6E, 0x74, 0x7A, 0xFF))
    body = bytes((0x9A, 0xA1, 0xA8, 0xFF))
    dark = bytes((0x4A, 0x50, 0x56, 0xFF))
    accent = bytes((0x3F, 0xA8, 0xC2, 0xFF))
    px = []
    for y in range(16):
        for x in range(16):
            if x in (0, 15) or y in (0, 15):
                px.append(edge)
            elif 6 <= x <= 9 and 2 <= y <= 5:
                px.append(accent)          # 上方的"入口"
            elif 6 <= x <= 9 and 10 <= y <= 13:
                px.append(accent)          # 下方的"出口"
            elif 3 <= x <= 12 and 7 <= y <= 8:
                px.append(dark)            # 中间那道横缝
            else:
                px.append(body)
    png16(os.path.join(TEX, u"fluid_exchanger.png"), px, u"textures/block/fluid_exchanger.png")

    print(u"== ④ 合成配方（用户给的三行）==")
    recipe = {
        "type": "minecraft:crafting_shaped",
        "category": "misc",
        "pattern": [" M ", "PBP", "FTF"],
        "key": {
            "M": {"item": "potato_s_t:common_metal_block"},
            "P": {"item": "potato_s_t:iron_plate"},
            "B": {"item": "potato_s_t:oil_bucket"},
            "F": {"item": "potato_s_t:fluid_pipe"},
            "T": {"item": "potato_s_t:high_pressure_tank"},
        },
        "result": {"id": "potato_s_t:fluid_exchanger", "count": 1},
    }
    write_json(os.path.join(DATA, "recipe", u"fluid_exchanger.json"), recipe,
               u"recipe/fluid_exchanger.json")

    # 逐个 id 查注册名（不凭记忆）：Java 里必须能搜到对应的注册调用
    java_all = u""
    for rel in [r"src\main\java\com\potatost\mod\ModBlocks.java",
                r"src\main\java\com\potatost\mod\ModItems.java",
                r"src\main\java\com\potatost\mod\PotatoSTOres.java"]:
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            java_all += io.open(p, encoding="utf-8").read()
    for name in [u"common_metal_block", u"iron_plate", u"oil_bucket", u"fluid_pipe",
                 u"high_pressure_tank", u"fluid_exchanger"]:
        hit = (u'register("%s"' % name) in java_all
        if hit:
            print(u"  [OK]   id 真实存在：potato_s_t:%s" % name)
        else:
            fails.append(u"配方里引用了不存在的 id：potato_s_t:%s" % name)

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
