# -*- coding: utf-8 -*-
"""TextureCheck.py —— 贴图体检 + 待画清单（0.10 ZF61 新增）

**为什么需要它**（两件事各踩过一次）：
  ① ZF60：用户发来的 7 个文件**名字都是 .png、实际是 webp**，WPF 解码还丢了 alpha ⇒
     差点把花屏贴图装进游戏。⇒ 这条检查**逐个读文件头**，不是 PNG 直接 FAIL。
  ② 项目里很多物品/方块**还在借原版贴图**（§9 的"程序生成的占位色块"那批，以及 ZF48
     那句"钛粉用火药"）。这些不是 bug，但**是一份待画清单** —— 现在靠人肉记，容易漏。

查三件事：
  ① 我们自己 `textures/` 下的每个 .png：**文件头必须是 PNG**、能解出 IHDR、
     宽高是 2 的幂；物品贴图没有透明底的只报 WARN（占位色块本来就实心）
  ② 每个模型最终采用的贴图：属于我们 **还是原版**（借原版 = 待画）
  ③ `--plan` 时把这些写进 `docs/贴图清单.md`（用户照着放文件就行）

跑法：
    python build/zftools/TextureCheck.py            # 只体检 + 打印待画数量
    python build/zftools/TextureCheck.py --plan     # 顺便刷新 docs/贴图清单.md
退出码：有 FAIL 项 → 1
"""
import io
import json
import os
import re
import struct
import sys
import zipfile

PROJ = r"E:\PotatoST"
ASSETS = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t")
LANG = os.path.join(ASSETS, "lang", "zh_cn.json")
DOC = os.path.join(PROJ, "docs", u"贴图清单.md")
VANILLA_JAR = r"E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar"
MODID = "potato_s_t"
PNG_SIG = b"\x89PNG\r\n\x1a\n"

fails = []
warns = []


def check(cond, msg):
    print((u"  [OK]   " if cond else u"  [FAIL] ") + msg)
    if not cond:
        fails.append(msg)
    return cond


def warn(cond, msg):
    if not cond:
        print(u"  [WARN] " + msg)
        warns.append(msg)
    return cond


def read_json(path):
    return json.loads(io.open(path, encoding="utf-8").read())


class Vanilla:
    def __init__(self, path):
        self.zip = zipfile.ZipFile(path) if os.path.isfile(path) else None
        self.names = set(self.zip.namelist()) if self.zip else set()

    def model(self, rel):
        entry = "assets/minecraft/models/{0}.json".format(rel)
        if entry not in self.names:
            return None
        return json.loads(self.zip.read(entry).decode("utf-8"))

    def has_texture(self, rel):
        return "assets/minecraft/textures/{0}.png".format(rel) in self.names


def png_header(path):
    """返回 (宽, 高, 色深, 色型) 或抛异常。只读文件头，不解像素。"""
    with io.open(path, "rb") as fh:
        head = fh.read(33)
    if head[:8] != PNG_SIG:
        magic = " ".join("{0:02X}".format(b) for b in head[:12])
        raise ValueError(u"不是 PNG（头 12 字节 = %s）" % magic)
    if head[12:16] != b"IHDR":
        raise ValueError(u"第一个块不是 IHDR")
    width, height, depth, color, _c, _f, interlace = struct.unpack(">IIBBBBB", head[16:29])
    return width, height, depth, color, interlace


def final_textures(model_dir, name, vanilla, seen=None):
    """沿 parent 链解析出这个模型最终用的贴图（子覆盖父）。"""
    seen = seen or set()
    key = (model_dir, name)
    if key in seen:
        return {}
    seen.add(key)
    if model_dir == "ours":
        path = os.path.join(ASSETS, "models", name + ".json")
        if not os.path.isfile(path):
            return {}
        data = read_json(path)
    else:
        data = vanilla.model(name)
        if data is None:
            return {}
    out = {}
    parent = data.get("parent")
    if parent:
        if ":" in parent:
            ns, rel = parent.split(":", 1)
        else:
            ns, rel = ("minecraft", parent)
        out.update(final_textures("ours" if ns == MODID else "vanilla", rel, vanilla, seen))
    out.update(data.get("textures", {}))
    return out


def mtl_texture_ok(mtl_ref, vanilla):
    """OBJ 模型的贴图不在 textures 表里，在 MTL 的 map_Kd 上 —— 检查它指向的贴图真的存在。"""
    if not mtl_ref or ":" not in mtl_ref:
        return None
    _ns, rel = mtl_ref.split(":", 1)
    path = os.path.join(ASSETS, rel.replace("/", os.sep))
    if not os.path.isfile(path):
        return None
    m = re.search(r"map_Kd\s+(\S+)", io.open(path, encoding="utf-8").read())
    if not m:
        return None
    ref = m.group(1)
    if ":" not in ref:
        return None
    ns, tex = ref.split(":", 1)
    if ns == MODID:
        return os.path.isfile(os.path.join(ASSETS, "textures", tex.replace("/", os.sep) + ".png"))
    return vanilla.has_texture(tex)


def main(argv):
    plan = "--plan" in argv
    vanilla = Vanilla(VANILLA_JAR)
    lang = read_json(LANG)

    # ---------- ① 我们自己的贴图本体 ----------
    tex_root = os.path.join(ASSETS, "textures")
    files = []
    for root, _dirs, names in os.walk(tex_root):
        for name in sorted(names):
            if name.lower().endswith(".png"):
                files.append(os.path.join(root, name))
    print(u"① 我们自己的 %d 张贴图" % len(files))
    bad = 0
    for path in files:
        rel = os.path.relpath(path, ASSETS).replace(os.sep, "/")
        try:
            width, height, depth, color, interlace = png_header(path)
        except Exception as exc:                      # noqa: BLE001
            check(False, u"%s：%s" % (rel, exc))
            bad += 1
            continue
        ok = check(depth == 8, u"%s：8 位色深（读到 %d）" % (rel, depth))
        if not ok:
            bad += 1
            continue
        # 【0.11 ZF106】盔甲层贴图（textures/models/armor/）**本来就该是 64×32** ——
        # 那不是方块/物品的图集贴图，而是人形模型直接采样的 UV 图；
        # 原版 iron_layer_1.png 也正是 64×32。对它套"2 的幂正方形"会得到 4 条假警告。
        is_armor_layer = rel.startswith("textures/models/armor/")
        if is_armor_layer:
            warn((width, height) == (64, 32),
                 u"%s：%dx%d 不是盔甲层的标准尺寸 64×32（人形模型的 UV 按这个尺寸切）"
                 % (rel, width, height))
        else:
            warn(width == height and (width & (width - 1)) == 0 and 16 <= width <= 256,
                 u"%s：%dx%d 不是 16~256 的 2 的幂正方形（游戏能读，但可能被图集拉伸）"
                 % (rel, width, height))
        warn(not interlace, u"%s：隔行扫描（MC 的图集加载不保证支持）" % rel)
        if rel.startswith("textures/item/"):
            warn(color in (4, 6), u"%s：物品贴图没有 alpha 通道（会是个实心方块）" % rel)
    print(u"     不合格 %d 张" % bad)

    # ---------- ② 每个模型最终用的是谁的贴图 ----------
    print(u"\n② 模型最终采用的贴图")
    borrowed = []
    for kind, folder in ((u"物品", "item"), (u"方块", "block")):
        path = os.path.join(ASSETS, "models", folder)
        for name in sorted(os.listdir(path)):
            if not name.endswith(".json"):
                continue
            mid = name[:-5]
            raw = read_json(os.path.join(path, name))
            if "obj" in str(raw.get("loader", "")):
                # OBJ 模型：贴图在 MTL 的 map_Kd 上（alloy_smelter / electric_blast_furnace 都是这样）
                state = mtl_texture_ok(raw.get("mtl_override"), vanilla)
                check(state is True, u"%s %s：MTL 的 map_Kd 指向的贴图存在" % (kind, mid))
                continue
            if str(raw.get("parent", "")).startswith("builtin/"):
                continue                     # 方块实体物品（模型由 BE 渲染，本来就没有贴图表）
            tex = final_textures("ours", folder + "/" + mid, vanilla)
            # ⚠ `"particle": "#all"` 这类是**贴图变量引用**，不是真的贴图 id（ZF61 第一版把它们
            #   当成了"借原版贴图"，一下虚报 60 多个）。真贴图 id 里不会有 `#`。
            refs = [v for v in tex.values() if isinstance(v, str) and not v.startswith("#")]
            if not refs:
                if raw.get("textures") == {}:
                    continue                 # **显式**空表 = 故意不画（不渲染的部件格）
                warn(False, u"%s %s：模型没有声明任何贴图" % (kind, mid))
                continue
            mine = [r for r in refs if r.startswith(MODID + ":")]
            theirs = [r for r in refs if not r.startswith(MODID + ":")]
            if theirs:
                key = (u"item." if folder == "item" else u"block.") + MODID + u"." + mid
                borrowed.append((folder, mid, lang.get(key, mid), sorted(set(theirs))))
    check(True, u"扫完 %d 个借原版贴图的模型（下有清单）" % len(borrowed))

    print(u"\n③ 还在借原版贴图的（待画清单）：%d 个" % len(borrowed))
    for folder, mid, zh, refs in borrowed:
        print(u"    %-28s %-22s <- %s" % (folder + "/" + mid, zh, ", ".join(refs)))

    # ---------- ④ 写清单 ----------
    if plan:
        lines = [u"# 贴图清单（待画 / 已完成）", u"",
                 u"> 由 `build/zftools/TextureCheck.py --plan` 生成。**你只要按「放哪」那一列把文件丢进去**，",
                 u"> 我这边跑一遍 `TextureCheck.py` + `ModelCheck.py` 就能确认。", u"",
                 u"## 怎么放（三条规矩）", u"",
                 u"1. **文件名必须是 ASCII**（小写字母/数字/`_`）——`ResourceLocation` 只放行 `[a-z0-9/._-]`，",
                 u"   中文文件名游戏直接报错（§4.24）。",
                 u"2. **必须是真 PNG**（别把 webp/jpg 改个后缀）—— 检查会读文件头，不是 PNG 会 FAIL。",
                 u"3. 方块贴图 **16×16**；物品贴图 **16×16 且背景透明**（32×32 也能用，但游戏按 16×16 渲染，会糊）。",
                 u"", u"## 放哪：两个目录", u"",
                 u"- 方块：`src\\main\\resources\\assets\\potato_s_t\\textures\\block\\`",
                 u"- 物品：`src\\main\\resources\\assets\\potato_s_t\\textures\\item\\`",
                 u"", u"## 待画（%d 个，现在借的是原版贴图）" % len(borrowed), u"",
                 u"| 放哪 | 文件名 | 是什么 | 现在借的 |", u"|---|---|---|---|"]
        for folder, mid, zh, refs in borrowed:
            texdir = "block" if folder == "block" else "item"
            lines.append(u"| `textures/%s/` | `%s.png` | %s | %s |"
                         % (texdir, mid, zh, ", ".join("`%s`" % r for r in refs)))
        lines += [u"", u"## 已经有自己贴图的（列出来是方便你替换）", u"",
                  u"| 放哪 | 文件名 | 是什么 |", u"|---|---|---|"]
        done = 0
        for kind, folder in ((u"物品", "item"), (u"方块", "block")):
            path = os.path.join(ASSETS, "models", folder)
            for name in sorted(os.listdir(path)):
                if not name.endswith(".json"):
                    continue
                mid = name[:-5]
                tex = final_textures("ours", folder + "/" + mid, vanilla)
                refs = [v for v in tex.values() if isinstance(v, str) and not v.startswith("#")]
                if refs and all(r.startswith(MODID + ":") for r in refs):
                    key = (u"item." if folder == "item" else u"block.") + MODID + u"." + mid
                    # ⚠ 0.11 ZF90：这里原来写的是「**模型名** + .png」—— 可模型名并不等于贴图名。
                    #   银/铝/镍/钴四块板共用 `item/iron_plate` 这件事当场把它戳穿：表里曾列出
                    #   四个**根本不存在**的文件（aluminum_plate.png 等）。现在改成打印
                    #   **模型真正引用的那个文件**（引用几个就列几个）。
                    paths = sorted(set(r.split(u":", 1)[1] for r in refs))
                    folders = sorted(set(p.split(u"/")[0] for p in paths))
                    where = folders[0] if len(folders) == 1 else u"+".join(folders)
                    names = [p.rsplit(u"/", 1)[-1] + u".png" for p in paths]
                    lines.append(u"| `textures/%s/` | `%s` | %s |"
                                 % (where, u"`, `".join(names), lang.get(key, mid)))
                    done += 1
        lines += [u"",
                  u"> 同一个贴图被多个模型用到时，表里会出现多行同名 —— 那是**共用一张**，不是重复。", u""]
        text = u"\n".join(lines) + u"\n"
        # ⚠ 0.11 ZF90：这份清单的**下半部分是手写的**（`---` 之后的各轮小节，ZF78 那节当时还专门
        #   留了一句「下次重跑 --plan 会把它冲掉，我再补回来」）。原版是**整份覆盖** ⇒ 手写内容
        #   会被静默冲掉。现在改成：生成的部分照旧，**`---` 之后原样接回去**。
        old = io.open(DOC, encoding="utf-8").read() if os.path.exists(DOC) else u""
        mark = u"\n---\n\n## ZF"
        i = old.find(mark)
        if i >= 0:
            text += u"\n" + old[i + 1:]
            print(u"  [OK]   手写部分原样接回（%d 字符，从 %s 开始）"
                  % (len(old) - i - 1, old[i + 5:i + 24].replace(u"\n", u" ")))
        else:
            print(u"  [WARN] 没找到手写部分的分隔标记（换行 + `---` + 空行 + `## ZF`）"
                  u"⇒ 本次只写生成的那半；若盘上原有的手写小节不见了，请立刻从备份取回。")
        io.open(DOC, "w", encoding="utf-8", newline="\n").write(text)
        print(u"\n已写出 %s（待画 %d 个 / 已有 %d 个）" % (DOC, len(borrowed), done))

    print(u"\n------------------------------")
    print(u"失败项 = %d   警告 = %d   待画 = %d" % (len(fails), len(warns), len(borrowed)))
    print(u"结论: " + (u"通过" if not fails else u"有失败项"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
