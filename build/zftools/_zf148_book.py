# -*- coding: utf-8 -*-
u"""_zf148_book.py —— ZF148 生成器：帕秋莉手册（书数据 + 物品模型 + 贴图 + 配方 + 五语言键）。

产物（全部新建，除 lang 是插入）：
  data/potato_s_t/patchouli_books/guide/book.json
  assets/potato_s_t/patchouli_books/guide/en_us/categories/*.json        （6 份）
  assets/potato_s_t/patchouli_books/guide/en_us/entries/<分类>/*.json    （17 份）
  assets/potato_s_t/models/item/guide_book.json
  assets/potato_s_t/textures/item/guide_book.png                         （16×16，脚本生成）
  data/potato_s_t/recipe/guide_book.json                                 （书 + 铁锭 → 手册）
  assets/potato_s_t/lang/*.json                                          （追加 69 键 × 5 语言）

跑法：python build\\zftools\\_zf148_book.py            （默认 dry-run：只报要写什么）
      python build\\zftools\\_zf148_book.py --write    （真写）
"""
import io
import json
import os
import struct
import sys
import zlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _zf148_text import LANGS, TEXTS  # noqa: E402

PROJ = r"E:\PotatoST"
RES = os.path.join(PROJ, "src", "main", "resources")
ASSETS = os.path.join(RES, "assets", "potato_s_t")
DATA = os.path.join(RES, "data", "potato_s_t")

WRITE = u"--write" in sys.argv
BOOK_NS = u"potato_s_t"
BOOK_NAME = u"guide"
BOOK_ID = u"potato_s_t:guide"

# 键数基线（改前件实盘数字）
KEYS_BEFORE = {u"zh_cn": 508, u"en_us": 508, u"ja_jp": 508, u"ru_ru": 508, u"lzh": 510}

# ---------------------------------------------------------------- 结构定义
# (分类 id, sortnum, 图标)
CATS = [
    (u"getting_started", 1, u"potato_s_t:micro_crusher"),
    (u"power", 2, u"potato_s_t:terminal"),
    (u"materials", 3, u"potato_s_t:titanium_ingot"),
    (u"oil", 4, u"potato_s_t:oil_bucket"),
    (u"starfall", 5, u"potato_s_t:starfall_pendant"),
    (u"faq", 6, u"potato_s_t:filling_machine"),
]

# (分类, 条目名, 图标, sortnum, 页表)；页 = (u"text", 序号) 或 (u"crafting", 配方 id)
ENTRIES = [
    (u"getting_started", u"start", u"potato_s_t:micro_crusher", 1, [
        (u"text", 1), (u"crafting", u"potato_s_t:micro_crusher"), (u"text", 2)]),
    (u"getting_started", u"rules", u"patchouli:guide_book", 2, [
        (u"text", 1), (u"text", 2)]),
    (u"getting_started", u"first_line", u"potato_s_t:iron_plate", 3, [
        (u"text", 1), (u"crafting", u"potato_s_t:hydraulic_press")]),

    (u"power", u"wiring", u"potato_s_t:terminal", 1, [
        (u"text", 1), (u"text", 2)]),
    (u"power", u"generation", u"potato_s_t:low_generator", 2, [
        (u"text", 1), (u"text", 2), (u"text", 3)]),
    (u"power", u"storage", u"potato_s_t:lithium_battery", 3, [
        (u"text", 1), (u"text", 2)]),
    (u"power", u"fluids", u"potato_s_t:high_pressure_tank", 4, [
        (u"text", 1), (u"text", 2), (u"text", 3)]),

    (u"materials", u"ore_chain", u"potato_s_t:titanium_ingot", 1, [
        (u"text", 1), (u"text", 2)]),
    (u"materials", u"blast_alloy", u"minecraft:blast_furnace", 2, [
        (u"text", 1), (u"text", 2), (u"text", 3)]),
    (u"materials", u"salt", u"potato_s_t:sea_salt", 3, [
        (u"text", 1), (u"text", 2)]),

    (u"oil", u"crude", u"potato_s_t:oil_bucket", 1, [
        (u"text", 1), (u"text", 2)]),
    (u"oil", u"distillation", u"potato_s_t:distillation_controller", 2, [
        (u"text", 1), (u"text", 2)]),
    (u"oil", u"chemistry", u"potato_s_t:combustion_chamber", 3, [
        (u"text", 1), (u"text", 2), (u"text", 3)]),
    (u"oil", u"diesel_gen", u"potato_s_t:diesel_generator_controller", 4, [
        (u"text", 1), (u"text", 2)]),

    (u"starfall", u"sky_and_star", u"potato_s_t:star_chart_tome", 1, [
        (u"text", 1), (u"crafting", u"potato_s_t:star_chart_tome"), (u"text", 2)]),
    (u"starfall", u"star_steel", u"potato_s_t:star_steel_ingot", 2, [
        (u"text", 1), (u"text", 2)]),

    (u"faq", u"machine", u"potato_s_t:filling_machine", 1, [(u"text", 1)]),
    (u"faq", u"fluid", u"potato_s_t:oil_bucket", 2, [(u"text", 1)]),
]

# ---------------------------------------------------------------- 贴图（16×16）
PALETTE = {
    u".": None,                       # 透明
    u"O": (30, 33, 38, 255),           # 描边
    u"C": (62, 83, 114, 255),          # 封面
    u"P": (237, 227, 200, 255),        # 书口（纸）
    u"M": (195, 203, 212, 255),        # 钢芯
    u"m": (139, 149, 161, 255),        # 钢影
    u"G": (201, 138, 60, 255),         # 铜环
}
PIXELS = [
    u"................",
    u".OOOOOOOOOOOOOO.",
    u".OCCCCCCCCCCCCO.",
    u".OCCCCCCCCCCCPO.",
    u".OCCCGGGGGCCCPO.",
    u".OCCGmmmmmGCCPO.",
    u".OCCGm...mGCCPO.",
    u".OCCGm.M.mGCCPO.",
    u".OCCGm.M.mGCCPO.",
    u".OCCGm...mGCCPO.",
    u".OCCGmmmmmGCCPO.",
    u".OCCCGGGGGCCCPO.",
    u".OCCCCCCCCCCCPO.",
    u".OCCCCCCCCCCCCO.",
    u".OOOOOOOOOOOOOO.",
    u"................",
]


def png_bytes():
    assert len(PIXELS) == 16, u"贴图必须 16 行"
    raw = b""
    for row in PIXELS:
        assert len(row) == 16, u"每行必须 16 像素：%r" % row
        raw += b"\x00"
        for ch in row:
            px = PALETTE[ch]
            raw += b"\x00\x00\x00\x00" if px is None else bytes(px)

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 16, 16, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


# ---------------------------------------------------------------- 工具
def jdump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2) + u"\n"


def put(path, text):
    rel = os.path.relpath(path, PROJ)
    if os.path.exists(path):
        old = io.open(path, encoding=u"utf-8").read()
        if old == text:
            print(u"  [同] %s（内容一致，跳过）" % rel)
            return
        # 本脚本产出的全部是**本轮新建**的文件（书目录 + 模型 + 配方），
        # 所以「已存在且不同」只可能是本脚本自己改了口径 ⇒ 直接改，
        # 但把改前/改后字节数打出来留痕（第一次就是这么抓到 model 那个前缀坑的）。
        print(u"  [改] %s（%d → %d 字节）" % (rel, len(old.encode(u"utf-8")),
                                            len(text.encode(u"utf-8"))))
        if WRITE:
            io.open(path, u"w", encoding=u"utf-8", newline=u"\n").write(text)
        return
    print(u"  [新] %s（%d 字节）" % (rel, len(text.encode(u"utf-8"))))
    if WRITE:
        d = os.path.dirname(path)
        if not os.path.isdir(d):
            os.makedirs(d)
        io.open(path, u"w", encoding=u"utf-8", newline=u"\n").write(text)


def put_bytes(path, data):
    rel = os.path.relpath(path, PROJ)
    if os.path.exists(path):
        old = open(path, "rb").read()
        if old == data:
            print(u"  [同] %s（内容一致，跳过）" % rel)
            return
        print(u"  [改] %s（%d → %d 字节）" % (rel, len(old), len(data)))
        if WRITE:
            open(path, "wb").write(data)
        return
    print(u"  [新] %s（%d 字节）" % (rel, len(data)))
    if WRITE:
        d = os.path.dirname(path)
        if not os.path.isdir(d):
            os.makedirs(d)
        open(path, "wb").write(data)


def text_map():
    m = {}
    for row in TEXTS:
        assert len(row) == 6, u"文案表每行必须是 6 列：%r" % (row[0],)
        k = row[0]
        assert k not in m, u"键重复：%s" % k
        m[k] = dict(zip(LANGS, row[1:]))
    return m


def main():
    tm = text_map()
    print(u"文案键 %d 个" % len(tm))
    for k, v in tm.items():
        for lang, val in v.items():
            assert val.strip(), u"%s 的 %s 是空的" % (k, lang)
            assert u'"' not in val, u'%s 的 %s 里有 ASCII 双引号' % (k, lang)

    # ---- ① book.json ----
    print(u"---- ① 书定义 ----")
    put(os.path.join(DATA, u"patchouli_books", BOOK_NAME, u"book.json"), jdump({
        u"name": u"item.potato_s_t.guide_book",
        u"landing_text": u"potato_s_t.guide.landing",
        u"subtitle": u"potato_s_t.guide.subtitle",
        u"version": u"0",
        u"use_resource_pack": True,
        u"i18n": True,
        u"use_blocky_font": True,
        u"show_progress": False,
        # ⚠ `model` 键**不带** `item/`：帕秋莉在 Book 构造器里对解析结果**无条件**
        #   `withPrefix("item/")`（jar 字节码：getAsResourceLocation 之后直接
        #   invokevirtual ResourceLocation.withPrefix("item/")）⇒ 写 "potato_s_t:guide_book"
        #   才会落到 assets/potato_s_t/models/item/guide_book.json。
        #   第一版按文档字面写成 "potato_s_t:item/guide_book"，被探针 B11 当场抓住。
        u"model": u"potato_s_t:guide_book",
        u"creative_tab": u"potato_s_t:potato_s_t_tab",
    }))

    # ---- ② 分类 ----
    print(u"---- ② 分类 %d 份 ----" % len(CATS))
    for cid, sort, icon in CATS:
        put(os.path.join(ASSETS, u"patchouli_books", BOOK_NAME, u"en_us", u"categories",
                         cid + u".json"), jdump({
            u"name": u"potato_s_t.guide.category.%s" % cid,
            u"description": u"potato_s_t.guide.category.%s.desc" % cid,
            u"icon": icon,
            u"sortnum": sort,
        }))

    # ---- ③ 条目 ----
    n_pages = 0
    print(u"---- ③ 条目 %d 份 ----" % len(ENTRIES))
    for cat, name, icon, sort, pages in ENTRIES:
        plist = []
        for kind, arg in pages:
            if kind == u"text":
                plist.append({
                    u"type": u"patchouli:text",
                    u"text": u"potato_s_t.guide.entry.%s.%s.p%d" % (cat, name, arg),
                })
                n_pages += 1
            elif kind == u"crafting":
                plist.append({u"type": u"patchouli:crafting", u"recipe": arg})
            else:
                raise SystemExit(u"未知页型 %s" % kind)
        put(os.path.join(ASSETS, u"patchouli_books", BOOK_NAME, u"en_us", u"entries",
                         cat, name + u".json"), jdump({
            u"name": u"potato_s_t.guide.entry.%s.%s" % (cat, name),
            u"category": u"%s:%s" % (BOOK_NS, cat),
            u"icon": icon,
            u"sortnum": sort,
            u"pages": plist,
        }))
    print(u"  文本页合计 %d 页" % n_pages)

    # ---- ④ 物品模型 + 贴图 ----
    print(u"---- ④ 物品模型与贴图 ----")
    put(os.path.join(ASSETS, u"models", u"item", u"guide_book.json"), jdump({
        u"parent": u"minecraft:item/generated",
        u"textures": {u"layer0": u"potato_s_t:item/guide_book"},
    }))
    put_bytes(os.path.join(ASSETS, u"textures", u"item", u"guide_book.png"), png_bytes())

    # ---- ⑤ 配方 ----
    print(u"---- ⑤ 配方 ----")
    put(os.path.join(DATA, u"recipe", u"guide_book.json"), jdump({
        u"type": u"minecraft:crafting_shapeless",
        u"category": u"misc",
        u"ingredients": [{u"item": u"minecraft:book"}, {u"item": u"minecraft:iron_ingot"}],
        u"result": {
            u"id": u"patchouli:guide_book",
            u"count": 1,
            u"components": {u"patchouli:book": BOOK_ID},
        },
    }))

    # ---- ⑥ 五语言 ----
    print(u"---- ⑥ 语言键 %d × 5 ----" % len(tm))
    for lang in LANGS:
        p = os.path.join(ASSETS, u"lang", lang + u".json")
        raw = io.open(p, encoding=u"utf-8").read()
        table = json.loads(raw)
        before = len(table)
        # ⚠ 幂等口径：**按缺的键补**，不是「全有才跳过」。
        #   第一版写成「有就跳过 / 没有就必须等于基线」，第二轮想加一个键时
        #   会因为盘上已经是 578 而当场炸（档案 §4.148 同族教训）。
        todo = [row for row in TEXTS if row[0] not in table]
        if not todo:
            print(u"  [同] %s：%d 键全在（幂等）" % (lang, before))
            continue
        assert before == KEYS_BEFORE[lang] + (len(TEXTS) - len(todo)), \
            u"%s 键数 %d 与「基线 %d + 已插入 %d」对不上" % (
                lang, before, KEYS_BEFORE[lang], len(TEXTS) - len(todo))
        assert raw.endswith(u"}\n"), u"%s 结尾不是 }\n" % lang
        cut = raw.rstrip().rfind(u"\n}")
        assert cut > 0, u"%s 找不到最后一行" % lang
        head = raw[:cut]
        assert not head.rstrip().endswith(u","), u"%s 最后一行已经带逗号了？" % lang
        lines = []
        for row in todo:
            lines.append(u"  %s: %s" % (json.dumps(row[0], ensure_ascii=False),
                                        json.dumps(row[LANGS.index(lang) + 1], ensure_ascii=False)))
        new = head + u",\n" + u",\n".join(lines) + u"\n}\n"
        json.loads(new)          # 语法自检
        after = len(json.loads(new))
        assert after == before + len(todo), u"%s 写入后 %d ≠ %d" % (lang, after, before + len(todo))
        print(u"  [改] %s：%d → %d 键（补 %d）" % (lang, before, after, len(todo)))
        if WRITE:
            io.open(p, u"w", encoding=u"utf-8", newline=u"\n").write(new)

    print(u"")
    print(u"%s" % (u"已写入。" if WRITE else u"dry-run（加 --write 才落盘）。"))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
