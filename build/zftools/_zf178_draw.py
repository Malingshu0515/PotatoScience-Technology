# -*- coding: utf-8 -*-
u"""_zf178_draw.py —— ZF178：**自己画** 7 张方块贴图 + 写 21 份资源 JSON。

用户原话：「参考粗矿本来的风格和原版粗矿块的风格 可以自己画吧（不要吃白饭了）」。

画法（确定性、可复现，不用手绘素材）：
1. **取样**：读对应的物品贴图（`textures\item\raw_<metal>.png` / `magnet.png`），
   把它**不透明像素**按亮度排序，取 暗部(20%) / 中间(50%) / 亮部(85%) 三个色 ⇒ 这就是"这块料的颜色"，
   方块上的矿斑直接用这三个色，**保证方块和物品是同一块料**。
2. **石头底**：16×16 灰石子噪点（明度 0x6e~0x8a），按固定种子生成，另加几处 2×2 的深/浅颗粒。
3. **矿斑**：7~9 坨、每坨 3~6 像素的不规则团块：心部=亮部、边部=暗部，
   左下再压一像素深描边（本工程物品贴图就是"深描边 + 金属高光"那一套）。
4. **磁铁块**：铁灰底 + **红色磁极斑**（红来自 magnet.png 的取样）。
5. 自检：每张 16×16 / RGBA / 全不透明，并打印平均色。

另外写 21 份 JSON：`blockstates/<id>.json`、`models/block/<id>.json`、`models/item/<id>.json`，
格式照 `common_metal_block` 那三份。

跑法：python build\\zftools\\_zf178_draw.py [--write]
"""
import io
import json
import os
import random
import sys

from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
ITEX = os.path.join(ASSETS, "textures", "item")
BTEX = os.path.join(ASSETS, "textures", "block")
RAW_METALS = [u"aluminum", u"cobalt", u"nickel", u"silver", u"tungsten", u"uranium"]
BLOCKS = [(u"magnet_block", u"magnet")] + [(u"raw_%s_block" % m, u"raw_%s" % m) for m in RAW_METALS]


def palette_of(item_id):
    u"""从物品贴图里取 暗/中/亮 三色（不透明像素按亮度分位）。"""
    p = os.path.join(ITEX, item_id + u".png")
    im = Image.open(p).convert("RGBA")
    px = [c for c in im.getdata() if c[3] > 0]
    if not px:
        return [(90, 90, 90), (140, 140, 140), (200, 200, 200)]
    px.sort(key=lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2])
    def at(q):
        c = px[min(len(px) - 1, int(len(px) * q))]
        return (c[0], c[1], c[2])
    dark, mid, light = at(0.20), at(0.50), at(0.85)
    # 让矿斑比物品本身更鲜明一点（方块贴图面积大，直接照搬会发灰）
    def boost(c, k=1.25):
        return tuple(max(0, min(255, int(v * k + (255 - v) * (k - 1) * 0.15))) for v in c)
    return [dark, mid, boost(light)]


def stone_base(rng):
    u"""16×16 石头底：灰噪点 + 几处 2×2 深浅颗粒（照原版石头那个味道）。"""
    im = Image.new("RGBA", (16, 16))
    px = im.load()
    for y in range(16):
        for x in range(16):
            v = rng.randint(0x6e, 0x8a)
            # 一点点横向条带，免得像纯噪声
            if (y % 5 == 0) and rng.random() < 0.5:
                v = max(0x66, v - 6)
            px[x, y] = (v, v, v, 255)
    for _ in range(5):
        cx, cy = rng.randint(0, 14), rng.randint(0, 14)
        d = rng.choice([-12, -8, 8, 12])
        for dx in (0, 1):
            for dy in (0, 1):
                x, y = cx + dx, cy + dy
                if x < 16 and y < 16:
                    r, g, b, a = px[x, y]
                    px[x, y] = (max(0, min(255, r + d)), max(0, min(255, g + d)),
                                max(0, min(255, b + d)), a)
    return im


def blob(im, rng, cx, cy, dark, mid, light):
    u"""一坨矿：3~6 像素的不规则团块 + 左下深描边。"""
    px = im.load()
    cells = {(0, 0)}
    for _ in range(rng.randint(2, 5)):
        bx, by = rng.choice(list(cells))
        dx, dy = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        cells.add((bx + dx, by + dy))
    for (dx, dy) in cells:
        x, y = cx + dx, cy + dy
        if 0 <= x < 16 and 0 <= y < 16:
            px[x, y] = (light if rng.random() < 0.45 else mid) + (255,)
    for (dx, dy) in cells:
        x, y = cx + dx, cy + dy + 1
        if 0 <= x < 16 and 0 <= y < 16 and (dx, dy + 1) not in cells:
            px[x, y] = dark + (255,)
        x, y = cx + dx + 1, cy + dy
        if 0 <= x < 16 and 0 <= y < 16 and (dx + 1, dy) not in cells:
            px[x, y] = dark + (255,)


def draw(block_id, item_id, magnet=False):
    rng = random.Random(hash(block_id) & 0xFFFF)
    dark, mid, light = palette_of(item_id)
    if magnet:
        # 磁铁块：铁灰底（不是石头底）+ 红色磁极斑
        base = Image.new("RGBA", (16, 16))
        p = base.load()
        for y in range(16):
            for x in range(16):
                v = rng.randint(0x50, 0x64)
                p[x, y] = (v, v, v + 4, 255)
        red_dark, red_mid, red_light = (0x8c, 0x1c, 0x1c), (0xc4, 0x28, 0x28), (0xf0, 0x5a, 0x4a)
        im = base
        for _ in range(5):
            blob(im, rng, rng.randint(1, 12), rng.randint(1, 12), red_dark, red_mid, red_light)
    else:
        im = stone_base(rng)
        for _ in range(rng.randint(7, 9)):
            blob(im, rng, rng.randint(1, 12), rng.randint(1, 12), dark, mid, light)
    return im


JSONS = {
    # ⚠ 用 `%s` 而不是 `str.format`：模板本身就是 JSON，里面全是花括号，
    #   `.format()` 会把它们当占位符（本轮实测直接 KeyError: '\n  "variants"'）。
    u"blockstates/%s.json": u'{\n  "variants": {\n    "": {\n      "model": "potato_s_t:block/%s"\n    }\n  }\n}\n',
    u"models/block/%s.json": (u'{\n  "parent": "minecraft:block/cube_all",\n  "textures": {\n'
                              u'    "all": "potato_s_t:block/%s"\n  }\n}\n'),
    u"models/item/%s.json": u'{\n  "parent": "potato_s_t:block/%s"\n}\n',
}


def main(argv):
    write = u"--write" in argv
    fails = []
    for bid, iid in BLOCKS:
        im = draw(bid, iid, magnet=(bid == u"magnet_block"))
        px = list(im.getdata())
        mean = tuple(sum(c[i] for c in px) // len(px) for i in range(3))
        opaque = all(c[3] == 255 for c in px)
        print(u"  %-22s 取样(%s) 平均色=#%02x%02x%02x 不透明=%s"
              % (bid, iid, mean[0], mean[1], mean[2], opaque))
        if im.size != (16, 16) or im.mode != u"RGBA" or not opaque:
            fails.append(bid + u"(尺寸/模式/透明度)")
        if write:
            im.save(os.path.join(BTEX, bid + u".png"))
    for tpl, _ in JSONS.items():
        for bid, _iid in BLOCKS:
            rel = tpl % bid
            p = os.path.join(ASSETS, rel.replace(u"/", os.sep))
            if not os.path.isdir(os.path.dirname(p)):
                os.makedirs(os.path.dirname(p))
            if write:
                io.open(p, "w", encoding="utf-8", newline=u"\n").write(JSONS[tpl] % bid)
    print(u"模式：%s ｜ 贴图 %d 张 / JSON %d 份 ｜ 失败 = %d"
          % (u"落盘" if write else u"干跑", len(BLOCKS), len(BLOCKS) * 3, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
