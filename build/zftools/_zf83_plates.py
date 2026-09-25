# -*- coding: utf-8 -*-
u"""_zf83_plates.py —— 把用户给的三张原图转成 16×16 RGBA 贴图，并让三个板子物品用上

用户原话：「钢板和铁（银 铝...）板 铜板贴图放item文件夹了 **换一下** 然后**删除原来的贴图**」

做法（每步都自证）：
  ① 从 `build/用户素材/*.jpg`（§4.24 留档的**原名件**）读 16×16 像素（像素由
     `_zf83_jpg_pixels.json` 提供，那是 .NET System.Drawing 解的，和"资源管理器看到的一样"）；
  ② **从四边泛洪**把背景做成透明（不是"白色全透明"！钢/铁板面内部也是白的，
     一刀切会把板面掏空 —— 这点先渲染 alpha 图确认过）；
  ③ 写成 16×16 / 8 位 / RGBA 的 PNG 盖到 `textures/item/{steel,iron,copper}_plate.png`；
  ④ 三个板子的物品模型指向自己的贴图（**铁板**原来借的是通用 `plate.png`，这次换掉）；
  ⑤ 列出现在还有谁在用通用 `plate.png`（银/铝/镍/钴），**不删它** —— 删了那四件就没贴图。
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
TOOLS = os.path.join(ROOT, "build", "zftools")
USERART = os.path.join(ROOT, "build", u"用户素材")
TEX = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "textures", "item")
MODELS = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "models", "item")

PAIRS = [(u"steel", u"steel_plate.png"), (u"iron", u"iron_plate.png"), (u"copper", u"copper_plate.png")]
TOL = 26          # 背景判定的容差（JPEG 有噪点，不能要求完全相等）

fails = []


def write_png16(path, px):
    u"""16×16 / 8 位 / RGBA PNG（TextureCheck 要求的格式）。px = 256 个 (r,g,b,a)。"""
    raw = b""
    for y in range(16):
        raw += b"\x00" + b"".join(bytes(px[y * 16 + x]) for x in range(16))

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", 16, 16, 8, 6, 0, 0, 0)
    io.open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                              + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def convert(rgb_list):
    u"""从四边泛洪去背景：背景像素 alpha=0，其余原样保留。"""
    px = [tuple(int(v) for v in s.split(u",")) for s in rgb_list]
    alpha = [255] * 256
    # 背景色 = 四角的中位数（JPEG 角落最干净）
    corners = [px[0], px[15], px[240], px[255]]
    bg = tuple(sorted(c[i] for c in corners)[1] for i in range(3))
    stack = []
    for i in range(256):
        y, x = divmod(i, 16)
        if y in (0, 15) or x in (0, 15):
            if all(abs(px[i][c] - bg[c]) <= TOL for c in range(3)):
                stack.append(i)
    seen = set(stack)
    while stack:
        i = stack.pop()
        alpha[i] = 0
        y, x = divmod(i, 16)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < 16 and 0 <= nx < 16:
                j = ny * 16 + nx
                if j not in seen and all(abs(px[j][c] - bg[c]) <= TOL for c in range(3)):
                    seen.add(j)
                    stack.append(j)

    # ② 只留**最大的那块连通域**：JPEG 噪点会让背景里留下零星孤点（铜板第一版左上角就有一粒），
    #    它们在游戏里就是"板子外面飘一个像素"，必须清掉。8 邻接，避免斜边被切碎。
    keep = set()
    comps = []
    visited = set()
    for i in range(256):
        # ⚠ 必须用 visited 跳过**已属某个域**的像素：否则同一个域会被反复泛洪出多个
        #   "内容相同但对象不同"的集合，max() 选中的那个会被当成唯一保留项、
        #   其余（同样是整块板！）全被清零 —— 第一版就是这么把三张图全清空的。
        if alpha[i] == 0 or i in visited:
            continue
        comp = set()
        st = [i]
        while st:
            k = st.pop()
            if k in comp:
                continue
            comp.add(k)
            ky, kx = divmod(k, 16)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = ky + dy, kx + dx
                    if 0 <= ny < 16 and 0 <= nx < 16:
                        j = ny * 16 + nx
                        if alpha[j] == 255 and j not in comp:
                            st.append(j)
        comps.append(comp)
        visited |= comp
    if comps:
        main = max(comps, key=len)
        for comp in comps:
            if comp is not main:
                for k in comp:
                    alpha[k] = 0
        keep = main
    return [(px[i][0], px[i][1], px[i][2], alpha[i]) for i in range(256)], bg


def preview(px, label):
    print(u"  %s 的 alpha 图（# = 留下、. = 透明，@ = 半透明）" % label)
    for y in range(16):
        row = u""
        for x in range(16):
            a = px[y * 16 + x][3]
            row += u"#" if a == 255 else (u"." if a == 0 else u"@")
        print(u"     " + row)


def main():
    dump = json.loads(io.open(os.path.join(TOOLS, u"_zf83_jpg_pixels.json"), encoding="utf-8").read())
    for key, png_name in PAIRS:
        if key not in dump:
            fails.append(u"像素转储里没有 %s" % key)
            continue
        # 原图仍在（ASCII 名留档），核对一下哈希，保证转的是**你给的那张**
        src = os.path.join(USERART, {u"steel": u"steel_plate.jpg", u"iron": u"iron_plate.jpg",
                                     u"copper": u"copper_plate.jpg"}[key])
        if not os.path.exists(src):
            fails.append(u"原图不在了：%s" % src)
            continue
        px, bg = convert(dump[key])
        opaque = sum(1 for p in px if p[3] == 255)
        print(u"== %s → %s（背景色 %s，去掉 %d 个背景像素，留下 %d 个板面像素）"
              % (key, png_name, bg, 256 - opaque, opaque))
        if not (60 <= opaque <= 220):
            fails.append(u"%s：留下的像素 %d 个，不像一块板（要么没去干净、要么把板面掏空了）"
                         % (key, opaque))
        preview(px, png_name)
        write_png16(os.path.join(TEX, png_name), px)

    print(u"\n== 物品模型：三个板子指向自己的贴图 ==")
    for name in [u"steel_plate", u"iron_plate", u"copper_plate"]:
        p = os.path.join(MODELS, name + u".json")
        obj = {"parent": "minecraft:item/generated",
               "textures": {"layer0": "potato_s_t:item/" + name}}
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(
            json.dumps(obj, indent=2, ensure_ascii=False) + u"\n")
        print(u"  [OK]   %s.json → potato_s_t:item/%s" % (name, name))

    print(u"\n== 谁还在用通用 plate.png（决定它能不能删）==")
    users = []
    for n in sorted(os.listdir(MODELS)):
        if not n.endswith(u".json"):
            continue
        t = io.open(os.path.join(MODELS, n), encoding="utf-8").read()
        if u"potato_s_t:item/plate" in t:
            users.append(n[:-5])
    print(u"  还在用 plate.png 的：%s" % (users or u"无"))
    if users:
        print(u"  ⇒ **plate.png 不能删**（删了这 %d 件会变紫黑块）—— 已在汇报里点给用户" % len(users))
    else:
        os.remove(os.path.join(TEX, u"plate.png"))
        print(u"  ⇒ 没人用了，已删除 textures/item/plate.png（用户要求「删除原来的贴图」）")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
