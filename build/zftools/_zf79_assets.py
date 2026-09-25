# -*- coding: utf-8 -*-
u"""_zf79_assets.py —— ZF79 的非 Java 资源

① **柏油块**的占位贴图：用户原话「先用煤炭块材质」⇒ 从原版 client.jar 抠
   `assets/minecraft/textures/block/coal_block.png`（原版是 **4 位调色板** PNG，
   本工程贴图必须是 8 位 ⇒ 解成 RGBA8 重写，像素不变），并落一份来源凭据。
② 柏油块的 blockstate + 方块模型（`cube_all`）+ 物品模型。
③ `mineable/pickaxe.json` 追加柏油块（煤炭块在原版里就只挂这一张，且不在 needs_stone_tool 里）。
④ **电力高炉新材质**（用户："我把电力高炉材质放进方块材质文件夹里了"）：
   `textures/block/电力高炉.png`（256×256，用户手绘）→ 按 §4.24 改成 ASCII 名，
   覆盖 `textures/block/electric_blast_furnace.png`（原先那张 16×16 是
   `MakeBlastFurnaceModel.py` 生成的"单色渲染"占位）。
   ⚠ 记一笔：**以后不要再跑那个生成脚本**，否则会把用户手绘的贴图盖回单色。
⑤ 语言：柏油块名字 + 液压机新状态"材料数量不够" + 液压机 tooltip 补一行（四语言，248 键）。
"""
import io
import json
import os
import shutil
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import PngRecolor as P

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
RES = os.path.join(ROOT, "src", "main", "resources")
ASSETS = os.path.join(RES, "assets", "potato_s_t")
DATA = os.path.join(RES, "data")
LANG = os.path.join(ASSETS, "lang")
TOOLS = os.path.join(ROOT, "build", "zftools")
VANILLA_JAR = r"E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar"

EXPECT_KEYS = 248
fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t)
    return True


def decode_png_any(data):
    u"""把 4 位调色板 / 8 位 RGBA 的 PNG 都解成 8 位 RGBA（借 PngRecolor 的 _unfilter）。"""
    import zlib
    w, h, bd, ct, comp, filt, inter = struct.unpack(">IIBBBBB", data[16:29])
    if inter != 0:
        raise ValueError("不支持隔行 PNG")
    idat = bytearray()
    plte = None
    trns = None
    i = 8
    while i < len(data):
        ln = struct.unpack(">I", data[i:i + 4])[0]
        ctype = data[i + 4:i + 8]
        payload = data[i + 8:i + 8 + ln]
        if ctype == b"IDAT":
            idat += payload
        elif ctype == b"PLTE":
            plte = payload
        elif ctype == b"tRNS":
            trns = payload
        i += 12 + ln
    raw = zlib.decompress(bytes(idat))
    if bd == 8 and ct == 6:
        stride = w * 4
        return w, h, bytearray(P._unfilter(raw, w, h, 4, stride))
    if bd == 4 and ct == 3:
        stride = w * 4 // 8
        flat = P._unfilter(raw, w, h, 1, stride)
        rgba = bytearray(w * h * 4)
        for y in range(h):
            row = flat[y * stride:(y + 1) * stride]
            for x in range(w):
                byte = row[x // 2]
                idx = (byte >> 4) if x % 2 == 0 else (byte & 0x0F)
                rgba[(y * w + x) * 4:(y * w + x) * 4 + 3] = plte[idx * 3:idx * 3 + 3]
                rgba[(y * w + x) * 4 + 3] = trns[idx] if (trns and idx < len(trns)) else 255
        return w, h, rgba
    if bd == 8 and ct == 2:
        stride = w * 3
        flat = P._unfilter(raw, w, h, 3, stride)
        rgba = bytearray(w * h * 4)
        for i in range(w * h):
            rgba[i * 4:i * 4 + 3] = flat[i * 3:i * 3 + 3]
            rgba[i * 4 + 3] = 255
        return w, h, rgba
    raise ValueError("没见过的 PNG 格式：bit%d type%d" % (bd, ct))


def install_asphalt_texture():
    dst = os.path.join(ASSETS, "textures", "block", "asphalt_block.png")
    if os.path.exists(dst):
        print(u"  [SKIP] asphalt_block.png 已存在（幂等）")
        return
    with zipfile.ZipFile(VANILLA_JAR) as zf:
        raw = zf.read("assets/minecraft/textures/block/coal_block.png")
    w, h, rgba = decode_png_any(raw)
    if (w, h) != (16, 16):
        fails.append(u"原版煤炭块贴图不是 16×16（%dx%d）" % (w, h))
        return
    P.write_png(dst, 16, 16, rgba)
    import hashlib
    io.open(os.path.join(TOOLS, "_zf79_asphalt_provenance.json"), "w", encoding="utf-8",
            newline=u"\n").write(json.dumps({
                "what": u"asphalt_block.png 的来源凭据（ZF79）",
                "source": "client.jar:assets/minecraft/textures/block/coal_block.png",
                "user_rule": u"用户原话「先用煤炭块材质」",
                "note": u"原版是 4 位调色板 PNG；本工程要求 8 位，解成 RGBA8 重写（像素不变）",
                "rgba_sha256": hashlib.sha256(bytes(rgba)).hexdigest(),
                "size": os.path.getsize(dst),
            }, ensure_ascii=False, indent=2) + u"\n")
    print(u"  [OK]   textures/block/asphalt_block.png ← 原版煤炭块（8 位 RGBA，%d B）"
          % os.path.getsize(dst))


def install_models():
    write(os.path.join(ASSETS, "blockstates", "asphalt_block.json"),
          u'{ "variants": { "": { "model": "potato_s_t:block/asphalt_block" } } }\n')
    write(os.path.join(ASSETS, "models", "block", "asphalt_block.json"),
          u'{\n  "parent": "minecraft:block/cube_all",\n'
          u'  "textures": { "all": "potato_s_t:block/asphalt_block" }\n}\n')
    write(os.path.join(ASSETS, "models", "item", "asphalt_block.json"),
          u'{ "parent": "potato_s_t:block/asphalt_block" }\n')
    print(u"  [OK]   blockstate + 方块模型（cube_all）+ 物品模型")


def patch_mineable():
    path = os.path.join(DATA, "minecraft", "tags", "block", "mineable", "pickaxe.json")
    text = read(path)
    if u'"potato_s_t:asphalt_block"' in text:
        print(u"  [SKIP] mineable/pickaxe.json 里已经有了（幂等）")
        return
    anchor = u'"potato_s_t:distillation_operator"'
    if text.count(anchor) != 1:
        fails.append(u"mineable/pickaxe.json：锚点命中 %d 次" % text.count(anchor))
        return
    i = text.index(anchor)
    eol = text.index(u"\n", i) + 1
    text = text[:eol] + u'    "potato_s_t:asphalt_block",\n' + text[eol:]
    write(path, text)
    data = json.loads(read(path))
    if u"potato_s_t:asphalt_block" not in data["values"]:
        fails.append(u"追加后仍然找不到 asphalt_block")
    else:
        print(u"  [OK]   mineable/pickaxe.json +asphalt_block（共 %d 项）" % len(data["values"]))


def install_ebf_texture():
    u"""用户手绘的 256×256 电力高炉材质 → ASCII 名覆盖旧的生成器占位图。"""
    src = os.path.join(ASSETS, "textures", "block", u"电力高炉.png")
    dst = os.path.join(ASSETS, "textures", "block", "electric_blast_furnace.png")
    if not os.path.exists(src):
        print(u"  [SKIP] 没看到 电力高炉.png（可能已经装过）")
        return
    d = open(src, "rb").read()
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        fails.append(u"电力高炉.png 不是真 PNG（头 %r）" % d[:12])
        return
    w, h, bd, ct = struct.unpack(">IIBB", d[16:26])
    old_name = os.path.join(ASSETS, "textures", "block", u"电力高炉.原名件")
    shutil.copy2(src, old_name)          # 原名件留档（§4.24：改名前后内容一致）
    shutil.copy2(src, dst)
    if open(old_name, "rb").read() != open(dst, "rb").read():
        fails.append(u"改名前后内容不一致")
    os.remove(src)
    print(u"  [OK]   电力高炉.png（%dx%d bit%d type%d）→ electric_blast_furnace.png"
          u"（原名件留档为 电力高炉.原名件）" % (w, h, bd, ct))


NEW_KEYS = {
    u"zh_cn.json": [
        (u"block.potato_s_t.asphalt_block", u"柏油块"),
        (u"gui.potato_s_t.hydraulic_press.status.material", u"材料不够：沥青要 12 个"),
    ],
    u"en_us.json": [
        (u"block.potato_s_t.asphalt_block", u"Asphalt Block"),
        (u"gui.potato_s_t.hydraulic_press.status.material", u"Not enough material: 12 bitumen needed"),
    ],
    u"ja_jp.json": [
        (u"block.potato_s_t.asphalt_block", u"アスファルトブロック"),
        (u"gui.potato_s_t.hydraulic_press.status.material", u"材料不足：瀝青が 12 個必要"),
    ],
    u"ru_ru.json": [
        (u"block.potato_s_t.asphalt_block", u"Блок асфальта"),
        (u"gui.potato_s_t.hydraulic_press.status.material",
         u"Недостаточно материала: нужно 12 битума"),
    ],
}

TOOLTIP_OLD = {
    u"zh_cn.json": u"可加工：铜、铁、镍、钴、银、铝、钢。\\n",
    u"en_us.json": u"Accepts copper, iron, nickel, cobalt, silver, aluminium and steel.\\n",
    u"ja_jp.json": u"加工可能：銅・鉄・ニッケル・コバルト・銀・アルミ・鋼。\\n",
    u"ru_ru.json": u"Обрабатывает медь, железо, никель, кобальт, серебро, алюминий и сталь.\\n",
}
TOOLTIP_ADD = {
    u"zh_cn.json": u"沥青 ×12 → 柏油块（纯建筑方块）。\\n",
    u"en_us.json": u"12 bitumen -> 1 asphalt block (decorative).\\n",
    u"ja_jp.json": u"瀝青 ×12 → アスファルトブロック（建築用）。\\n",
    u"ru_ru.json": u"12 битума -> блок асфальта (декоративный).\\n",
}


def install_lang():
    counts = {}
    for name, pairs in NEW_KEYS.items():
        path = os.path.join(LANG, name)
        text = read(path)
        # ① 工具提示补一行（在"可加工"那行后面）
        old_line = TOOLTIP_OLD[name]
        if TOOLTIP_ADD[name] in text:
            print(u"  [SKIP] %s：tooltip 那行已经在（幂等）" % name)
        elif text.count(old_line) == 1:
            text = text.replace(old_line, old_line + TOOLTIP_ADD[name], 1)
            write(path, text)
            print(u"  [OK]   %s：液压机 tooltip +1 行" % name)
        else:
            fails.append(u"%s：tooltip 锚点命中 %d 次" % (name, text.count(old_line)))
            continue
        # ② 两个新键
        for k, v in pairs:
            if (u'"%s"' % k) in text:
                continue
            anchor = u'"gui.potato_s_t.hydraulic_press.status.empty"' if u"status" in k else None
            if anchor is None:
                # 柏油块名字插在沥青物品那行后面
                anchor = u'"item.potato_s_t.bitumen"'
            if text.count(anchor) != 1:
                fails.append(u"%s：%s 的锚点命中 %d 次" % (name, k, text.count(anchor)))
                continue
            i = text.index(anchor)
            eol = text.index(u"\n", i) + 1
            text = text[:eol] + (u'  "%s":  "%s",\n' % (k, v)) + text[eol:]
        write(path, text)
        data = json.loads(read(path))
        counts[name] = len(data)
        for k, v in pairs:
            if data.get(k) != v:
                fails.append(u"%s：键 %s 不对" % (name, k))

    print(u"各语言键数：%s" % u", ".join(u"%s=%d" % (k, v) for k, v in sorted(counts.items())))
    if len(set(counts.values())) != 1:
        fails.append(u"四份键数不一致：%s" % counts)
    elif list(counts.values()) and list(counts.values())[0] != EXPECT_KEYS:
        fails.append(u"键数不是 %d（实际 %d）" % (EXPECT_KEYS, list(counts.values())[0]))


def main():
    print(u"== ① 柏油块占位贴图（借原版煤炭块）==")
    install_asphalt_texture()
    print(u"== ② 柏油块的 blockstate / 模型 ==")
    install_models()
    print(u"== ③ mineable/pickaxe ==")
    patch_mineable()
    print(u"== ④ 电力高炉新材质（用户手绘 256×256）==")
    install_ebf_texture()
    print(u"== ⑤ 语言（四份，246 → 248 键）==")
    install_lang()
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
