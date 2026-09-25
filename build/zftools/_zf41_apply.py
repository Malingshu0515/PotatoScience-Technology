# -*- coding: utf-8 -*-
"""ZF41 资源：扳手的贴图/模型 + 两条 lang（扳手名、部件格的 Jade 名字）。"""
import io
import json
import os
import struct
import sys
import zlib

ROOT = r"E:\PotatoST"
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
LANG = os.path.join(ASSETS, "lang")

# 部件格的显示名**故意与控制器同名** —— Jade 里那些格子就都念"电力高炉"，
# 而不是甩出一大串 block.potato_s_t.electric_blast_furnace_part（用户报的问题）。
BLOCK_NAMES = {
    "zh_cn": u"电力高炉",
    "en_us": u"Electric Blast Furnace",
    "ja_jp": u"電力高炉",
    "ru_ru": u"Электрическая доменная печь",
}
WRENCH_NAMES = {
    "zh_cn": u"扳手",
    "en_us": u"Wrench",
    "ja_jp": u"レンチ",
    "ru_ru": u"Гаечный ключ",
}

fail = []


def check(ok, msg):
    print(("  [OK]   " if ok else "  [FAIL] ") + msg)
    if not ok:
        fail.append(msg)


# 16×16 开口扳手：开口在右上、手柄斜到左下。'#' = 金属
ART = [
    "................",
    "...........##...",
    "..........#..#..",
    "..........#..#..",
    "...........#.#..",
    "..........##....",
    ".........##.....",
    "........##......",
    ".......##.......",
    "......##........",
    ".....##.........",
    "....##..........",
    "...###..........",
    "..####..........",
    "..###...........",
    "................",
]
LIGHT = (186, 188, 196, 255)
DARK = (104, 106, 114, 255)


def build():
    solid = [[ART[y][x] == '#' for x in range(16)] for y in range(16)]
    px = []
    for y in range(16):
        for x in range(16):
            if not solid[y][x]:
                px.append((0, 0, 0, 0))
                continue
            # 简单倒角：右/下挨着空白的像素涂暗色
            right = x + 1 < 16 and solid[y][x + 1]
            down = y + 1 < 16 and solid[y + 1][x]
            px.append(DARK if (not right or not down) else LIGHT)
    return px


def write_png(path, w, h, rgba):
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    flat = bytearray()
    for c in rgba:
        flat += bytes(c)
    raw = b"".join(b"\x00" + bytes(flat[y * w * 4:(y + 1) * w * 4]) for y in range(h))
    io.open(path, "wb").write(b"\x89PNG\r\n\x1a\n"
                              + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                              + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


print("== ① 扳手贴图 + 物品模型 ==")
tex = os.path.join(ASSETS, "textures", "item", "wrench.png")
write_png(tex, 16, 16, build())
check(os.path.getsize(tex) > 0, "textures/item/wrench.png（%d 字节）" % os.path.getsize(tex))

model = os.path.join(ASSETS, "models", "item", "wrench.json")
with io.open(model, "w", encoding="utf-8", newline="\n") as f:
    f.write(json.dumps({"parent": "minecraft:item/generated",
                        "textures": {"layer0": "potato_s_t:item/wrench"}}, indent=2, ensure_ascii=False) + "\n")
check(json.loads(io.open(model, encoding="utf-8").read())["textures"]["layer0"] == "potato_s_t:item/wrench",
      "models/item/wrench.json")

print()
print("== ② lang ×4：+2 键（扳手 + 部件格的 Jade 名字）==")
for code in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
    path = os.path.join(LANG, code + ".json")
    with io.open(path, "r", encoding="utf-8") as f:
        text = f.read()
    before = json.loads(text)
    lines = text.split("\n")
    close = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "}":
            close = i
            break
    j = close - 1
    while lines[j].strip() == "":
        j -= 1
    if not lines[j].rstrip().endswith(","):
        lines[j] = lines[j].rstrip() + ","
    lines[close:close] = [
        u'    "item.potato_s_t.wrench":  "%s",' % WRENCH_NAMES[code],
        u'    "block.potato_s_t.electric_blast_furnace_part":  "%s"' % BLOCK_NAMES[code],
    ]
    out = "\n".join(lines)
    after = json.loads(out)          # 先校验再写
    check(len(after) - len(before) == 2,
          "%s 键数 %d → %d" % (code, len(before), len(after)))
    check(after.get("item.potato_s_t.wrench") == WRENCH_NAMES[code], "%s 扳手名" % code)
    check(after.get("block.potato_s_t.electric_blast_furnace_part") == BLOCK_NAMES[code],
          "%s 部件格名（Jade 用）" % code)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)

print()
if fail:
    print("有 %d 项失败" % len(fail))
    for m in fail:
        print("   - " + m)
    sys.exit(1)
print("全部通过。")
