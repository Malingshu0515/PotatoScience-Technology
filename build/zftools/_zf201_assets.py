# -*- coding: utf-8 -*-
"""_zf201_assets.py —— 0.16 ZF201 钢套 / 钢工具的**贴图与模型**（两个工程一起做）

用户原话：「做钢的全套盔甲 钢镐 钢剑 钢斧 全部套用铁套就可以 … 贴图在工作区的 材质 文件夹里」。

做的事：
  ① 从 `E:\\PotatoST\\材质\\` 把 7 张钢贴图复制成两侧的 `textures/item/steel_*.png`
     （**原字节复制**：那 7 张已经是 16×16 RGBA，脚本会先验尺寸，不转档）；
  ② 写 7 个模型 JSON：盔甲 4 件 → `minecraft:item/generated`；
     工具 3 把 → `minecraft:item/handheld`（与 star_steel_* 同一套写法）。

跑法：
    python build/zftools/_zf201_assets.py            # 只体检
    python build/zftools/_zf201_assets.py --write
"""
import io
import json
import os
import struct
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SRC = r"E:\PotatoST\材质"
PROJECTS = [
    r"E:\PotatoST\PotatoSTneoforge1.21.1",
    r"E:\PotatoST\PotatoSTforge1.20.1",
]

# (中文原名, 注册 id, 模型父级)
FILES = [
    (u"钢头盔_1.png", u"steel_helmet", u"minecraft:item/generated"),
    (u"钢胸甲_3.png", u"steel_chestplate", u"minecraft:item/generated"),
    (u"钢护腿1.png", u"steel_leggings", u"minecraft:item/generated"),
    (u"钢靴子_2.png", u"steel_boots", u"minecraft:item/generated"),
    (u"钢镐_4.png", u"steel_pickaxe", u"minecraft:item/handheld"),
    (u"钢剑_1.png", u"steel_sword", u"minecraft:item/handheld"),
    (u"钢斧_1.png", u"steel_axe", u"minecraft:item/handheld"),
]

fails = []


def png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def main(argv):
    write = u"--write" in argv
    print(u"源目录：%s" % SRC)
    for cn, rid, parent in FILES:
        src = os.path.join(SRC, cn)
        if not os.path.isfile(src):
            fails.append(u"贴图不存在：%s" % src)
            continue
        size = png_size(src)
        ok16 = size == (16, 16)
        if not ok16:
            fails.append(u"%s 不是 16×16：%s" % (cn, size))
        print(u"  [%s] %-16s → textures/item/%-18s %s %s"
              % (u"OK" if ok16 else u"FAIL", cn, rid + u".png", size, parent))

    for proj in PROJECTS:
        tex = os.path.join(proj, "src", "main", "resources", "assets", "potato_s_t",
                           "textures", "item")
        mod = os.path.join(proj, "src", "main", "resources", "assets", "potato_s_t",
                           "models", "item")
        if not os.path.isdir(tex) or not os.path.isdir(mod):
            fails.append(u"工程目录不对：%s" % proj)
            continue
        for cn, rid, parent in FILES:
            src = os.path.join(SRC, cn)
            if not os.path.isfile(src):
                continue
            dst = os.path.join(tex, rid + u".png")
            if write:
                io.open(dst, "wb").write(io.open(src, "rb").read())
            model = {
                "parent": parent,
                "textures": {"layer0": u"potato_s_t:item/%s" % rid},
            }
            mpath = os.path.join(mod, rid + u".json")
            text = json.dumps(model, ensure_ascii=False, indent=2) + u"\n"
            if write:
                io.open(mpath, "w", encoding="utf-8", newline=u"\n").write(text)
            if not write:
                continue
            # 复核：贴图字节一致、模型能解析且父级对
            if io.open(dst, "rb").read() != io.open(src, "rb").read():
                fails.append(u"%s 复制后字节不一致" % dst)
            back = json.loads(io.open(mpath, encoding="utf-8").read())
            if back.get("parent") != parent or \
                    back.get("textures", {}).get("layer0") != u"potato_s_t:item/%s" % rid:
                fails.append(u"%s 模型内容不对：%s" % (mpath, back))
        print(u"  [%s] %s：贴图 7 张 + 模型 7 个"
              % (u"写出" if write else u"将写", os.path.basename(proj)))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
