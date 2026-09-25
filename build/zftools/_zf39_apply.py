# -*- coding: utf-8 -*-
"""ZF39 电力高炉：资源落地（模型 JSON / blockstate / 物品图标 / lang / 标签）。

OBJ 与 MTL 由 `MakeBlastFurnaceModel.py` 生成在 `build\\zftools\\_ebf_baked\\`，
这里只负责搬进 src 并写引用它们的 JSON。
"""
import io
import json
import os
import shutil
import struct
import sys
import zlib

ROOT = r"E:\PotatoST"
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
DATA = os.path.join(ROOT, r"src\main\resources\data")
LANG = os.path.join(ASSETS, "lang")
BAKED = os.path.join(ROOT, r"build\zftools\_ebf_baked")

NAME = "electric_blast_furnace"
PART = "electric_blast_furnace_part"
FACINGS = ("south", "north", "east", "west")

NAMES = {
    "zh_cn": u"电力高炉",
    "en_us": u"Electric Blast Furnace",
    "ja_jp": u"電力高炉",
    "ru_ru": u"Электрическая доменная печь",
}
TOOLTIP = {
    "zh_cn": u"用 3×3×3 的结构装配而成。\\n空手 Shift 右键原版高炉即可成型或拆解。\\n12 个输入槽、32 个输出槽，每个槽位 3 秒烧完。\\n储电 320 FE，耗电 = 正在加工的物品数 × 80 FE/t。\\n产物会自动送进紧邻的容器。",
    "en_us": u"Assembled from a 3x3x3 structure.\\nShift-right-click a blast furnace with an empty hand to form or disassemble it.\\n12 input slots and 32 output slots; each slot finishes in 3 seconds.\\nStores 320 FE and draws 80 FE/t per item being processed.\\nOutput is pushed into adjacent containers.",
    "ja_jp": u"3×3×3 の構造物から組み上げます。\\n素手でスニーク+右クリック（溶鉱炉）で組み立て／解体できます。\\n入力 12 スロット、出力 32 スロット。1 スロットは 3 秒で完成します。\\n蓄電 320 FE、消費電力は加工中のアイテム数 × 80 FE/t。\\n産物は隣接するコンテナへ自動搬出されます。",
    "ru_ru": u"Собирается из конструкции 3×3×3.\\nПрисядьте и щёлкните правой кнопкой по доменной печи пустой рукой, чтобы собрать или разобрать.\\n12 входных и 32 выходных слота; каждый слот обрабатывается 3 секунды.\\nХранит 320 FE, расход — 80 FE/т за каждый предмет.\\nПродукция отправляется в соседние контейнеры.",
}
MSG_INVALID = {
    "zh_cn": u"结构不成立：%s",
    "en_us": u"Structure invalid: %s",
    "ja_jp": u"構造が不正です：%s",
    "ru_ru": u"Конструкция неверна: %s",
}
MSG_FORMED = {
    "zh_cn": u"电力高炉已成型",
    "en_us": u"Electric Blast Furnace formed",
    "ja_jp": u"電力高炉を組み上げました",
    "ru_ru": u"Электрическая доменная печь собрана",
}

fail = []


def check(ok, msg):
    print(("  [OK]   " if ok else "  [FAIL] ") + msg)
    if not ok:
        fail.append(msg)


def write_json(path, obj):
    text = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    json.loads(text)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def insert_before_closer(path, new_lines, closer, expect_delta, what):
    with io.open(path, "r", encoding="utf-8") as f:
        text = f.read()
    before = json.loads(text)
    orig = list(before)
    lines = text.split("\n")
    close_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == closer:
            close_idx = i
            break
    if close_idx is None:
        raise SystemExit("找不到收尾符号 %r: %s" % (closer, path))
    j = close_idx - 1
    while lines[j].strip() == "":
        j -= 1
    if not lines[j].rstrip().endswith(","):
        lines[j] = lines[j].rstrip() + ","
    lines[close_idx:close_idx] = new_lines
    out = "\n".join(lines)
    after = json.loads(out)
    check(len(after) - len(orig) == expect_delta,
          "%s 键数 %d → %d（应 +%d）" % (what, len(orig), len(after), expect_delta))
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    return after


print("=" * 72)
print(u"① 搬入 OBJ / MTL / 贴图，并写 4 个朝向的模型 JSON + blockstate")
print("=" * 72)
model_dir = os.path.join(ASSETS, "models", "block")
tex_dir = os.path.join(ASSETS, "textures", "block")
for f in ["%s_%s.obj" % (NAME, d) for d in FACINGS] + ["%s.mtl" % NAME]:
    shutil.copy2(os.path.join(BAKED, f), os.path.join(model_dir, f))
shutil.copy2(os.path.join(BAKED, NAME + ".png"), os.path.join(tex_dir, NAME + ".png"))
check(os.path.exists(os.path.join(tex_dir, NAME + ".png")), "贴图 %s.png" % NAME)

for d in FACINGS:
    write_json(os.path.join(model_dir, "%s_%s.json" % (NAME, d)), {
        "loader": "neoforge:obj",
        "model": "potato_s_t:models/block/%s_%s.obj" % (NAME, d),
        "mtl_override": "potato_s_t:models/block/%s.mtl" % NAME,
        # 部件格是 INVISIBLE，靠自动剔除会把整块模型的内部面剃掉
        "automatic_culling": False,
        "shade_quads": True,
        "flip_v": False,
        "emissive_ambient": False,
    })
    check(True, "models/block/%s_%s.json" % (NAME, d))

write_json(os.path.join(ASSETS, "blockstates", NAME + ".json"), {
    "variants": {("facing=" + d): {"model": "potato_s_t:block/%s_%s" % (NAME, d)} for d in FACINGS}
})
check(True, "blockstates/%s.json（4 个朝向）" % NAME)

# 部件格：不可见，所以给一个空模型
write_json(os.path.join(model_dir, PART + ".json"), {"textures": {}})
write_json(os.path.join(ASSETS, "blockstates", PART + ".json"),
           {"variants": {"": {"model": "potato_s_t:block/" + PART}}})
check(True, "部件格 blank 模型 + blockstate")

print()
print("=" * 72)
print(u"② 物品图标（模型是整块 3×3×3，直接拿它当图标会糊，所以单独画一个 16×16 图标）")
print("=" * 72)
item_dir = os.path.join(ASSETS, "textures", "item")
FRAME_D = (44, 46, 50, 255)
FRAME = (86, 90, 98, 255)
FRAME_L = (132, 136, 146, 255)
GLOW = (236, 152, 34, 255)
GLOW_L = (252, 208, 104, 255)
px = [(0, 0, 0, 0)] * 256
for y in range(16):
    for x in range(16):
        px[y * 16 + x] = FRAME
for x in range(16):
    px[x] = FRAME_L
    px[15 * 16 + x] = FRAME_D
for y in range(16):
    px[y * 16] = FRAME_L
    px[y * 16 + 15] = FRAME_D
for y in range(5, 11):                      # 炉口
    for x in range(4, 12):
        px[y * 16 + x] = FRAME_D
for x in range(4, 12):                      # 炉火带
    px[9 * 16 + x] = GLOW
for x in (5, 7, 9, 11):
    px[9 * 16 + x] = GLOW_L
for (bx, by) in ((1, 1), (14, 1), (1, 14), (14, 14)):
    px[by * 16 + bx] = FRAME_L


def write_png(path, w, h, rgba):
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    raw = b"".join(b"\x00" + bytes(rgba[y * w * 4:(y + 1) * w * 4]) for y in range(h))
    io.open(path, "wb").write(b"\x89PNG\r\n\x1a\n"
                              + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                              + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


icon = os.path.join(item_dir, NAME + ".png")
write_png(icon, 16, 16, b"".join(bytes(c) for c in px))
check(os.path.getsize(icon) > 0, "物品图标 item/%s.png（%d 字节）" % (NAME, os.path.getsize(icon)))

write_json(os.path.join(ASSETS, "models", "item", NAME + ".json"),
           {"parent": "minecraft:item/generated",
            "textures": {"layer0": "potato_s_t:item/" + NAME}})
check(True, "models/item/%s.json" % NAME)

print()
print("=" * 72)
print(u"③ lang ×4（block 名 + Shift 说明 + 2 条装配提示）")
print("=" * 72)
for code in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
    path = os.path.join(LANG, code + ".json")
    lines = [
        u'    "block.potato_s_t.%s":  "%s",' % (NAME, NAMES[code]),
        u'    "tooltip.potato_s_t.%s":  "%s",' % (NAME, TOOLTIP[code]),
        u'    "gui.potato_s_t.ebf.invalid":  "%s",' % MSG_INVALID[code],
        u'    "gui.potato_s_t.ebf.formed":  "%s"' % MSG_FORMED[code],
    ]
    after = insert_before_closer(path, lines, "}", 4, code + ".json")
    check(after.get("block.potato_s_t." + NAME) == NAMES[code],
          "%s block 名 = %s" % (code, after.get("block.potato_s_t." + NAME)))

print()
print("=" * 72)
print(u"④ 原版标签：控制器进 mineable/pickaxe + needs_stone_tool")
print("=" * 72)
for rel, label in ((r"minecraft\tags\block\mineable\pickaxe.json", "mineable/pickaxe"),
                   (r"minecraft\tags\block\needs_stone_tool.json", "needs_stone_tool")):
    path = os.path.join(DATA, rel)
    after = insert_before_closer(path, [u'    "potato_s_t:%s"' % NAME], "]", 1, label)
    check("potato_s_t:" + NAME in after["values"], "%s 含 %s" % (label, NAME))

print()
if fail:
    print("有 %d 项失败：" % len(fail))
    for m in fail:
        print("   - " + m)
    sys.exit(1)
print(u"全部通过。")
