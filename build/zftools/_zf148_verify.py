# -*- coding: utf-8 -*-
r'''_zf148_verify.py —— ZF148 **常驻校验**：帕秋莉教程手册（书数据 / 物品 / 配方 / 五语言 / 依赖）

只读盘上文件，不开游戏。分区：
  A 依赖与构建：mods.toml 的硬依赖、build.gradle 的 compileOnly、libs 里的 jar、开发实例两份 jar；
  B 书定义 `book.json`：逐字段写死（含 `model` **不带 item/** 那个坑）；
  C 分类与条目：6 + 18 份，字段齐全、category/icon/recipe 三处交叉引用都成立、页号连续；
  D 配方与物品：书 + 铁锭 → 带 `patchouli:book` 组件的 `patchouli:guide_book`；模型与 16×16 贴图；
  E 五语言：645 × 4（lzh 653）、键集合对齐、手册 71 键一条不缺、与生成器表**逐字一致**；
  F Java：`GuideBook` 的关键片段（含"拿不到书不打标记"这条顺序）；
  G 文档：档案 §4.151/§5/§9、交接、英文公告；
  H 活体数字跟平：往轮门里没有残留 508（成品与 RELEASE_KEYS 那两类除外）。

跑法：python build\zftools\_zf148_verify.py
'''
import hashlib
import io
import json
import os
import re
import struct
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _zf148_text import LANGS, TEXTS  # noqa: E402

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
RES = os.path.join(ROOT, "src", "main", "resources")
ASSETS = os.path.join(RES, "assets", "potato_s_t")
DATA = os.path.join(RES, "data", "potato_s_t")
JAVA = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
DOC = os.path.join(ROOT, "docs", "开发档案.md")
HAND = os.path.join(ROOT, "docs", "多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
TOML = os.path.join(RES, "META-INF", "neoforge.mods.toml")
GRADLE = os.path.join(ROOT, "build.gradle")

BOOK_DIR = os.path.join(DATA, "patchouli_books", "guide")
ENT_DIR = os.path.join(ASSETS, "patchouli_books", "guide", "en_us", "entries")
CAT_DIR = os.path.join(ASSETS, "patchouli_books", "guide", "en_us", "categories")

CATS = [u"getting_started", u"power", u"materials", u"oil", u"starfall", u"faq"]
ENTRIES = [
    (u"getting_started", u"start", 3), (u"getting_started", u"rules", 2),
    (u"getting_started", u"first_line", 2),
    (u"power", u"wiring", 2), (u"power", u"generation", 3), (u"power", u"storage", 2),
    (u"power", u"fluids", 3),
    (u"materials", u"ore_chain", 2), (u"materials", u"blast_alloy", 3),
    (u"materials", u"salt", 2),
    (u"oil", u"crude", 2), (u"oil", u"distillation", 2), (u"oil", u"chemistry", 3),
    (u"oil", u"diesel_gen", 2),
    (u"starfall", u"sky_and_star", 3), (u"starfall", u"star_steel", 2),
    (u"faq", u"machine", 1), (u"faq", u"fluid", 1),
]
KEYS = {u"zh_cn": 645, u"en_us": 645, u"ja_jp": 645, u"ru_ru": 645, u"lzh": 653}

passed = 0
failed = 0
fails = []


def check(cond, label, detail=u""):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label if not detail else u"%s（%s）" % (label, detail))
        print(u"  [FAIL] " + label + (u" —— " + detail if detail else u""))


def read(path):
    if not os.path.isfile(path):
        return None
    return io.open(path, encoding=u"utf-8").read()


def jload(path):
    t = read(path)
    if t is None:
        return None
    try:
        return json.loads(t)
    except Exception:
        return None


def sha1(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()


def registered_ids():
    """本 mod 注册过的物品 id。

    ⚠ 口径按 §4.149 的教训来：**扫整个包**，不点名几个文件 ——
    第一版只扫 `ModItems/ModBlocks/PotatoSTOres`，于是 `star_steel_ingot`（注册在
    `ModArmorItems.java` 里）被判成"不存在的物品"而假红。扫描面要覆盖全部注册点。
    """
    ids = set()
    for fn in sorted(os.listdir(JAVA)):
        if not fn.endswith(u".java"):
            continue
        t = read(os.path.join(JAVA, fn)) or u""
        for m in re.finditer(r'register(?:Block|Vibranium|Armor|Ore|Item)?\(?\s*"([a-z0-9_]+)"', t):
            ids.add(u"potato_s_t:" + m.group(1))
    return ids


# ============================================================ A
def section_a():
    print(u"\n================ A 依赖与构建 ================")
    toml = read(TOML) or u""
    check(u'modId="patchouli"' in toml, u"A1 mods.toml 里声明了帕秋莉依赖")
    check(toml.count(u'[[dependencies.potato_s_t]]') == 2, u"A2 依赖块恰好两个（neoforge + patchouli）",
          u"实际 %d" % toml.count(u'[[dependencies.potato_s_t]]'))
    check(bool(re.search(r'modId="patchouli"\s*\ntype="required"', toml)), u"A3 帕秋莉是 required（硬依赖）")
    check(u'versionRange="[1.21.1-93,)"' in toml, u"A4 版本区间 [1.21.1-93,)")
    gr = read(GRADLE) or u""
    check(u"compileOnly files('libs/Patchouli-1.21.1-93-NEOFORGE.jar')" in gr,
          u"A5 build.gradle 里有帕秋莉的 compileOnly（离线用本地 jar）")
    jar = os.path.join(ROOT, "libs", "Patchouli-1.21.1-93-NEOFORGE.jar")
    check(os.path.isfile(jar), u"A6 libs 下那份 jar 在")
    if os.path.isfile(jar):
        h = sha1(jar)
        print(u"         （jar sha1 = %s，%d 字节）" % (h, os.path.getsize(jar)))
        check(os.path.getsize(jar) == 646777, u"A7 jar 大小 646777 字节（Modrinth 上那一份）",
              u"实际 %d" % os.path.getsize(jar))
    for d in (u"run/client/mods", u"run/server/mods"):
        p = os.path.join(ROOT, d.replace(u"/", os.sep), u"Patchouli-1.21.1-93-NEOFORGE.jar")
        check(os.path.isfile(p), u"A8 开发实例里有帕秋莉：%s" % d)


# ============================================================ B
def section_b():
    print(u"\n================ B 书定义 book.json ================")
    p = os.path.join(BOOK_DIR, u"book.json")
    raw = read(p)
    check(raw is not None, u"B1 book.json 在 data/potato_s_t/patchouli_books/guide/")
    if raw is None:
        return
    b = jload(p)
    want = {
        u"name": u"item.potato_s_t.guide_book",
        u"landing_text": u"potato_s_t.guide.landing",
        u"subtitle": u"potato_s_t.guide.subtitle",
        u"version": u"0",
        u"use_resource_pack": True,
        u"i18n": True,
        u"use_blocky_font": True,
        u"show_progress": False,
        # ⚠ 帕秋莉对 model 键**无条件** withPrefix("item/") ⇒ 这里**不能**写 item/
        u"model": u"potato_s_t:guide_book",
        u"creative_tab": u"potato_s_t:potato_s_t_tab",
    }
    for k in sorted(want):
        check(b.get(k) == want[k], u"B2 book.json['%s'] = %r" % (k, want[k]), u"实际 %r" % (b.get(k),))
    check(set(b.keys()) == set(want.keys()), u"B3 book.json 字段集合恰好是这 10 个",
          u"多/少：%s" % (set(b.keys()) ^ set(want.keys())))
    check(u"item/" not in b.get(u"model", u"item/") or b.get(u"model") == u"potato_s_t:guide_book",
          u"B4 model 不写成 item/xxx（那个前缀由帕秋莉自己加）")
    mi = read(os.path.join(JAVA, u"ModItems.java")) or u""
    m = re.search(r'CREATIVE_MODE_TABS\.register\("([a-z0-9_]+)"', mi)
    tab = u"%s:%s" % (u"potato_s_t", m.group(1)) if m else u"?"
    check(b.get(u"creative_tab") == tab, u"B5 creative_tab 与 ModItems 里注册的栏位一致（%s）" % tab)
    check(raw.endswith(u"}\n") and u"\r" not in raw and u'\n  "' in raw,
          u"B6 2 空格缩进 / LF / 结尾换行")


# ============================================================ C
def section_c():
    print(u"\n================ C 分类与条目 ================")
    ok_cat = 0
    reg0 = registered_ids()
    for c in CATS:
        o = jload(os.path.join(CAT_DIR, c + u".json"))
        icon_ok = o is not None and str(o.get(u"icon")) in reg0
        good = (o is not None and set(o.keys()) == {u"name", u"description", u"icon", u"sortnum"}
                and o[u"name"] == u"potato_s_t.guide.category.%s" % c
                and o[u"description"] == u"potato_s_t.guide.category.%s.desc" % c
                and icon_ok)
        if good:
            ok_cat += 1
        else:
            check(False, u"C1 分类 %s 的字段（含图标是注册过的物品）" % c, u"%r" % (o,))
    check(ok_cat == 6, u"C1 六份分类字段齐全、图标都是真物品（%d/6）" % ok_cat)

    reg = registered_ids()
    bad_cat, bad_icon, bad_rec, bad_page = [], [], [], []
    pages_total = 0
    ok_ent = 0
    for cat, name, npages in ENTRIES:
        p = os.path.join(ENT_DIR, cat, name + u".json")
        o = jload(p)
        if o is None:
            bad_page.append(u"%s/%s 读不到" % (cat, name))
            continue
        ok_ent += 1
        if o.get(u"name") != u"potato_s_t.guide.entry.%s.%s" % (cat, name):
            bad_page.append(u"%s/%s 的 name 键" % (cat, name))
        if o.get(u"category") != u"potato_s_t:%s" % cat:
            bad_cat.append(u"%s/%s → %s" % (cat, name, o.get(u"category")))
        icon = str(o.get(u"icon"))
        # 0.13 ZF162：扳手与电力高炉物品删了 ⇒ 图标换成帕秋莉手册本体 / 原版高炉，
        #   这两个**允许**（其余仍必须是我们注册过的物品）
        allowed_foreign = {u"patchouli:guide_book", u"minecraft:blast_furnace"}
        if (not icon.startswith(u"potato_s_t:") and icon not in allowed_foreign) \
                or (icon.startswith(u"potato_s_t:") and icon not in reg):
            bad_icon.append(u"%s/%s → %s" % (cat, name, icon))
        pg = o.get(u"pages") or []
        if not pg:
            bad_page.append(u"%s/%s 没有 pages" % (cat, name))
        textno = []
        for pe in pg:
            if pe.get(u"type") == u"patchouli:text":
                textno.append(pe.get(u"text"))
                pages_total += 1
            elif pe.get(u"type") == u"patchouli:crafting":
                rid = pe.get(u"recipe") or u""
                if not rid.startswith(u"potato_s_t:"):
                    bad_rec.append(u"%s/%s → %s" % (cat, name, rid))
                else:
                    rp = os.path.join(DATA, u"recipe", rid.split(u":", 1)[1] + u".json")
                    if not os.path.isfile(rp):
                        bad_rec.append(u"%s/%s → %s（文件不在）" % (cat, name, rid))
            else:
                bad_page.append(u"%s/%s 未知页型 %r" % (cat, name, pe.get(u"type")))
        want_txt = [u"potato_s_t.guide.entry.%s.%s.p%d" % (cat, name, i + 1)
                    for i in range(len(textno))]
        if textno != want_txt:
            bad_page.append(u"%s/%s 的正文键不是 p1..pn 连续：%s" % (cat, name, textno))
        if len(pg) != npages:
            bad_page.append(u"%s/%s 页数 %d ≠ 期望 %d" % (cat, name, len(pg), npages))

    check(ok_ent == 18, u"C2 十八份条目都读得到（%d/18）" % ok_ent)
    check(not bad_cat, u"C3 每份条目的 category 都指向这六个分类之一", u"／".join(bad_cat[:3]))
    check(not bad_icon, u"C4 每份条目的 icon 都是本 mod 注册过的物品", u"／".join(bad_icon[:3]))
    check(not bad_rec, u"C5 每个 crafting 页的配方文件都存在", u"／".join(bad_rec[:3]))
    check(not bad_page, u"C6 条目的 name / 页型 / 页号连续 / 页数都对", u"／".join(bad_page[:3]))
    check(pages_total == 37, u"C7 文本页合计 37（实际 %d）" % pages_total)


# ============================================================ D
def section_d():
    print(u"\n================ D 配方与物品 ================")
    p = os.path.join(DATA, u"recipe", u"guide_book.json")
    o = jload(p)
    check(o is not None, u"D1 recipe/guide_book.json 在且合法")
    if o:
        check(o.get(u"type") == u"minecraft:crafting_shapeless", u"D2 类型 shapeless（书 + 铁锭不分格）")
        check(o.get(u"category") == u"misc", u"D3 category = misc")
        ing = o.get(u"ingredients") or []
        check([i.get(u"item") for i in ing] == [u"minecraft:book", u"minecraft:iron_ingot"],
              u"D4 原料恰好是 minecraft:book + minecraft:iron_ingot", u"%r" % (ing,))
        r = o.get(u"result") or {}
        check(r.get(u"id") == u"patchouli:guide_book", u"D5 产物是帕秋莉的 guide_book")
        check(r.get(u"count") == 1, u"D6 产物数量 1")
        check((r.get(u"components") or {}).get(u"patchouli:book") == u"potato_s_t:guide",
              u"D7 产物带 patchouli:book 组件 = potato_s_t:guide（不带就是一本废书）")
    model = jload(os.path.join(ASSETS, u"models", u"item", u"guide_book.json"))
    check(model == {u"parent": u"minecraft:item/generated",
                    u"textures": {u"layer0": u"potato_s_t:item/guide_book"}},
          u"D8 物品模型 layer0 指向自己", u"%r" % (model,))
    tex = os.path.join(ASSETS, u"textures", u"item", u"guide_book.png")
    check(os.path.isfile(tex), u"D9 贴图 guide_book.png 在")
    if os.path.isfile(tex):
        d = open(tex, "rb").read()
        w, h = struct.unpack(">II", d[16:24])
        check(d[:8] == b"\x89PNG\r\n\x1a\n" and (w, h) == (16, 16) and d[25] == 6,
              u"D10 贴图是 16×16 RGBA PNG（实测 %d×%d，色彩类型 %d）" % (w, h, d[25]))


# ============================================================ E
def section_e():
    print(u"\n================ E 五语言 ================")
    tables = {}
    for lang in LANGS:
        p = os.path.join(ASSETS, u"lang", lang + u".json")
        t = jload(p)
        check(t is not None, u"E1 %s.json 合法" % lang)
        if t is None:
            continue
        tables[lang] = t
        # ⚠ 这里是 **≥** 不是 **==**：键总数是「活体数字」，由**加键那一轮**负责跟平
        #   （实测 ZF150 在我打包后 3 分钟就加了 4 个键）。本门只管**手册那 71 个键**
        #   在不在、值对不对（E6/E7），不替别人守全量总数 —— 否则「我的门红不红」
        #   就由别人的提交节奏决定（§5.1 同款）。当前实测值打在标签里给人看。
        check(len(t) >= KEYS[lang], u"E2 %s 键数 ≥ %d（实测 %d）" % (lang, KEYS[lang], len(t)),
              u"实际 %d" % len(t))
    base = set(tables.get(u"zh_cn", {}))
    for lang in (u"en_us", u"ja_jp", u"ru_ru"):
        check(set(tables.get(lang, {})) == base, u"E3 %s 键集合与 zh_cn 完全一致" % lang,
              u"差 %s" % (set(tables.get(lang, {})) ^ base,))
    lzh = set(tables.get(u"lzh", {}))
    check(lzh - base == {u"language.name", u"language.region"} and not (base - lzh),
          u"E4 lzh = 四份 + language.name/region 两个元数据键", u"差 %s" % (lzh ^ base,))

    tm = {row[0]: dict(zip(LANGS, row[1:])) for row in TEXTS}
    check(len(tm) == 71, u"E5 生成器表 71 键（实际 %d）" % len(tm))
    miss, mismatch, empty, quote = [], [], [], []
    for key, per in tm.items():
        for lang in LANGS:
            v = tables.get(lang, {}).get(key)
            if v is None:
                miss.append(u"%s/%s" % (lang, key))
            elif v != per[lang]:
                mismatch.append(u"%s/%s" % (lang, key))
            elif not v.strip():
                empty.append(u"%s/%s" % (lang, key))
            elif u'"' in v:
                quote.append(u"%s/%s" % (lang, key))
    check(not miss, u"E6 手册 71 键在五份里一条不缺", u"缺 %d：%s" % (len(miss), miss[:3]))
    check(not mismatch, u"E7 五份的值与生成器表**逐字一致**（文案改动必须同步改表）",
          u"%d 处不一致：%s" % (len(mismatch), mismatch[:3]))
    check(not empty, u"E8 没有空值", u"%s" % empty[:3])
    check(not quote, u"E9 值里没有 ASCII 双引号（中文用「」）", u"%s" % quote[:3])


# ============================================================ F
def section_f():
    print(u"\n================ F Java：GuideBook ================")
    p = os.path.join(JAVA, u"GuideBook.java")
    t = read(p)
    check(t is not None, u"F1 GuideBook.java 在")
    if t is None:
        return
    check(u"public static final ResourceLocation BOOK_ID" in t
          and u'fromNamespaceAndPath(PotatoST.MODID, "guide")' in t, u"F2 BOOK_ID = potato_s_t:guide")
    check(u"@EventBusSubscriber(modid = PotatoST.MODID)" in t and u"PlayerEvent.PlayerLoggedInEvent" in t,
          u"F3 监听登录事件（@EventBusSubscriber + PlayerLoggedInEvent）")
    check(u"instanceof ServerPlayer" in t, u"F4 只在服务端玩家上动手（instanceof ServerPlayer）")
    # ⚠ ZF156 把标记搬进附件（`ModAttachments`）之后，判据从"某段字面量在文件里的先后"
    #   改成"**登录处理里**的调用先后" —— 意图一个字没变（查过再取书、取到书才打标记），
    #   只是不再依赖那句话写在哪一行（旧判据在重构后按 `find` 顺序判，属于"锚点过期"而不是行为回归）。
    i_flag = t.find(u"shouldGive(player)")
    i_get = t.find(u"getBookStack(BOOK_ID)")
    i_empty = t.find(u"if (book.isEmpty())")
    i_put = t.rfind(u"markGiven(player)")      # ⚠ 用 rfind：老标记迁移那次也会调 markGiven（在书之前）
    if i_put < 0:      # 万一又改回老机制的写法，仍然认旧字面量
        i_put = t.rfind(u"putBoolean(GIVEN_TAG, true)")
    check(0 <= i_flag < i_get, u"F5 先查「送过没」再取书堆（顺序）")
    check(0 <= i_get and i_empty > i_get and i_put > i_empty,
          u"F6 发书那条路上：取到书堆、且书不是空的，才打标记 —— 书拿不到时下次还能再试")
    check(u"getInventory().add(book)" in t and u"player.drop(book, false)" in t,
          u"F7 背包塞不下就掉在脚下（不静吞）")
    check(u"displayClientMessage" in t and u"message.potato_s_t.guide_book.received" in t,
          u"F8 送书时给一条提示（键在五语言里）")
    check(u"ITEMS.register" not in t and u"DeferredRegister" not in t,
          u"F9 本类不注册物品（物品用帕秋莉自己的 guide_book）")
    check(not t.startswith(u"\ufeff") and u"\r" not in t, u"F10 无 BOM、LF 结尾")


# ============================================================ G
def section_g():
    print(u"\n================ G 文档 ================")
    doc = read(DOC) or u""
    hand = read(HAND) or u""
    ann = read(ANN) or u""
    check(u"### 4.158 【工具雷】**联动帕秋莉**这一轮踩到的四个坑（0.12 ZF148）" in doc, u"G1 档案里有 §4.158 那一节（逐字标题）")
    check(u"| ZF148 |" in doc, u"G2 档案 §5 表格里有 ZF148 行")
    check(bool(re.search(r"### ZF148", doc)), u"G3 档案 §9 有 ZF148 小节")
    # ⚠ G4/G5/G7 查的是「**本轮自己的记录还在不在**」，不是「文档等于盘上当前值」：
    #   键总数是活体数字（ZF150 已推到 645），钉死快照会变成"门红不红看别人的提交节奏"；
    #   钉"文档 == 盘上"又会变成"替别人守他们的文档进度"。所以查的是**本轮写下的那几处历史锚**。
    check(u"### ZF148" in doc and u"508 → 579" in doc,
          u"G4 档案里本轮的记录还在（§9 ZF148 + 键数链 508 → 579）")
    check(u"ZF148" in hand, u"G5 交接文档里有本轮那一条（ZF148）")
    check(u"74" in hand, u"G6 交接文档里配方数记着 74（本轮那次的数）")
    check(u"579 keys each" in ann or u"**579 keys each**" in ann,
          u"G7 英文公告里本轮那条写着 579 keys each")
    check(u"ZF148" in ann, u"G8 英文公告里有 ZF148 那一条")


# ============================================================ H
def section_h():
    print(u"\n================ H 活体数字跟平 ================")
    stale = []
    for fn in sorted(os.listdir(ZT)):
        if not fn.endswith(u"_verify.py") or fn == u"_zf148_verify.py":
            continue
        for i, line in enumerate((read(os.path.join(ZT, fn)) or u"").split(u"\n")):
            if u"508" not in line or u"RELEASE_KEYS" in line:
                continue
            if line.strip().startswith(u"#"):
                continue          # 注释不是断言（本轮自己那几行说明里就写着 508）
            if u'eq(u"语言键数（ZF112 起 508）"' in line:
                continue          # 点名排除：成品 jar 内部的键数，等打包那轮
            if re.search(r"[0-9a-fA-F]508|508[0-9a-fA-F]", line):
                continue          # sha1 里的 508
            stale.append(u"%s:%d" % (fn, i + 1))
    check(not stale, u"H1 往轮门里没有残留 508（成品 RELEASE_KEYS 与点名行除外）",
          u"%d 处：%s" % (len(stale), stale[:4]))
    g = read(os.path.join(ZT, u"_zf100_recipe_guard.py")) or u""
    check(u'u"guide_book.json",' in g, u"H2 配方守卫白名单里有 guide_book.json")
    z139 = read(os.path.join(ZT, u"_zf139_verify.py")) or u""
    z141 = read(os.path.join(ZT, u"_zf141_verify.py")) or u""
    check(u"check(n_recipe == 74," in z139, u"H3 _zf139 配方数 = 74")
    check(u"RECIPES, SHAPED = 74, 63" in z141, u"H4 _zf141 配方 74 / shaped 63（手册那条是 shapeless）")
    snap = os.path.join(ZT, u"_zf148_gatesnap.py")
    check(os.path.isfile(snap) and u"_zf148_verify.py" in (read(snap) or u""),
          u"H5 全门快照名单里有本轮这道门")


def main():
    print(u"================ ZF148 常驻校验：帕秋莉教程手册 ================")
    section_a()
    section_b()
    section_c()
    section_d()
    section_e()
    section_f()
    section_g()
    section_h()
    print(u"")
    print(u"================ 通过 %d / 失败 %d ================" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == u"__main__":
    sys.exit(main())
