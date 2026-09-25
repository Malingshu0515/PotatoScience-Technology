# -*- coding: utf-8 -*-
u"""_zf107_verify.py —— ZF107 常驻校验：成就（进度）树 + 四语言

不跑游戏也能查的部分全在这里；"真触发"（拿物品到底点不点亮）在探针 `Zf107Check.java`
里，必须真服务端跑（见 §3 的验证流程）。

口径：
  · 树形闭合：恰好 1 个根、父指针全部解析得到、无环、每个节点从根可达；
  · 判据物品 / 图标物品**必须在盘上注册**（拿 ModItems/ModBlocks/... 的 register 名单对）；
  · 图标得是"拿到就会点亮的东西"（图标 ∈ 本节点判据物品）—— 这条是我给本轮定的规矩；
  · 老成就只许动该动的：`clean_energy`/`stronger_power` 只有 parent 变，
    `new_beginning` 只有 icon + criteria 变 —— 拿 `zf107_pre` 的改前件逐字段比；
  · 四语言：键集合四份完全一致、总数 398、48 个新键齐全非空、
    文本里不许出现 ASCII 双引号（本项目的中文串一律用「」）；
  · 与改前件相比：语言文件**只准** +48 键与 1 处值被改，别的一个字节都不许动。
"""
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ADIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\advancement")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
BK = r"C:\PotatoST救援\zf107_pre"
DOC = os.path.join(ROOT, r"docs\开发档案.md")
DOC_EN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")
TOOLS = os.path.join(ROOT, r"build\zftools")

NEW_NODES = [
    "crushing", "pressing", "wiring", "first_power", "capacitor",
    "blast_furnace", "steel", "titanium", "electrolyzer", "gas_handling",
    "alloy_smelter", "light_alloy", "hard_alloy", "stable_block",
    "titanium_tools", "oil", "distillation", "fuel", "sulfur", "ammonia",
    "combustion", "acid", "music_disc_anvil", "music_disc_jasmine",
]
OLD_NODES = ["new_beginning", "clean_energy", "stronger_power"]
ALL_NODES = OLD_NODES + NEW_NODES
HIDDEN = ["music_disc_anvil", "music_disc_jasmine"]
GOALS = ["blast_furnace", "steel", "titanium", "alloy_smelter", "hard_alloy",
         "distillation", "combustion", "acid"]
EXPECT_KEYS = 417           # … + ZF112 锂电池构造间 9 键
NEW_KEYS = 48
LANGS = ["zh_cn", "en_us", "ja_jp", "ru_ru"]

n_pass = 0
fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def check(name, cond, detail=None):
    global n_pass
    if cond:
        n_pass += 1
    else:
        fails.append(name + (u"  ← %s" % detail if detail else u""))


def eq(name, want, got):
    check(name, want == got, u"期望 %r 实际 %r" % (want, got))


def load_all():
    out = {}
    for n in ALL_NODES:
        p = os.path.join(ADIR, n + u".json")
        if not os.path.exists(p):
            continue
        try:
            out[n] = json.loads(read(p))
        except Exception as e:
            fails.append(u"%s.json 解析不了：%s" % (n, e))
    return out


def mod_ids():
    ids = set()
    for f in ("ModItems.java", "ModBlocks.java", "PotatoSTOres.java", "ModArmorItems.java"):
        p = os.path.join(JAVA, f)
        if os.path.exists(p):
            ids |= set(re.findall(r'register\(\s*"([a-z0-9_]+)"', read(p)))
    return ids


def crit_items(obj):
    u"""本节点判据里点名的一切物品/方块 id（不带命名空间）

    inventory_changed 认的是物品（`items`），placed_block 认的是方块（`location[].block`）——
    两种都要收，否则 clean_energy 那种"放方块"的节点会被误判成"没点名任何东西"。
    """
    out = []
    for c in obj.get("criteria", {}).values():
        cond = c.get("conditions", {})
        for pred in cond.get("items", []):
            i = pred.get("items")
            if isinstance(i, str) and i.startswith("potato_s_t:"):
                out.append(i.split(u":", 1)[1])
        for loc in cond.get("location", []):
            b = loc.get("block")
            if isinstance(b, str) and b.startswith("potato_s_t:"):
                out.append(b.split(u":", 1)[1])
    return out


def main():
    global n_pass
    # ============ A 文件与结构 ============
    files = sorted(f[:-5] for f in os.listdir(ADIR) if f.endswith(u".json"))
    eq(u"A1 advancement 目录正好 27 份（3 老 + 24 新）", 27, len(files))
    eq(u"A2 文件名集合 = 预期 27 个", sorted(ALL_NODES), files)
    adv = load_all()
    eq(u"A3 27 份全部解析成功", 27, len(adv))
    for n in ALL_NODES:
        o = adv.get(n)
        if o is None:
            continue
        for k in ("display", "criteria", "requirements", "sends_telemetry_event"):
            check(u"A4 %s 有 %s 段" % (n, k), k in o)
        check(u"A5 %s 的 display 四件套齐" % n,
              all(k in o["display"] for k in ("icon", "title", "description", "frame",
                                              "show_toast", "announce_to_chat", "hidden")))
        check(u"A6 %s 的 frame 合法（%s）" % (n, o["display"]["frame"]),
              o["display"]["frame"] in ("task", "goal", "challenge"))
        eq(u"A7 %s 的 frame 符合设计" % n,
           "challenge" if n in HIDDEN else ("goal" if n in GOALS else "task"),
           o["display"]["frame"])
        eq(u"A8 %s 的 hidden 位" % n, n in HIDDEN, bool(o["display"]["hidden"]))
        check(u"A9 %s 的 toast/公告都开" % n,
              o["display"]["show_toast"] is True and o["display"]["announce_to_chat"] is True)
        has_bg = "background" in o["display"]
        eq(u"A10 %s 的背景图（只有根有）" % n, n == "new_beginning", has_bg)
        check(u"A11 %s 的 requirements 覆盖全部判据" % n,
              sorted(x for g in o["requirements"] for x in g) == sorted(o["criteria"].keys()))

    # ============ B 树形 ============
    roots = [n for n in ALL_NODES if "parent" not in adv.get(n, {})]
    eq(u"B1 恰好 1 个根", ["new_beginning"], roots)
    par = dict((n, adv[n]["parent"].split(u":", 1)[1]) for n in ALL_NODES if "parent" in adv[n])
    bad = [n for n, p in par.items() if p not in ALL_NODES]
    eq(u"B2 所有父指针都指向树里的节点", [], bad)
    cyc = []
    for n in ALL_NODES:
        walk, cur = set(), n
        while cur in par:
            if cur in walk:
                cyc.append(n)
                break
            walk.add(cur)
            cur = par[cur]
    eq(u"B3 没有环", [], cyc)
    reach = set(["new_beginning"])
    grew = True
    while grew:
        grew = False
        for n, p in par.items():
            if p in reach and n not in reach:
                reach.add(n)
                grew = True
    eq(u"B4 每个节点从根可达", sorted(ALL_NODES), sorted(reach))
    eq(u"B5 clean_energy 的父链改挂 first_power", "first_power", par.get("clean_energy"))
    eq(u"B6 stronger_power 的父链改挂 first_power", "first_power", par.get("stronger_power"))
    # 深度：给文档用（最长链）
    # ⚠ 这里**必须**带步数上限：K82 那把刀造出一个环之后，本段第一版是
    #   `while cur in par: cur = par[cur]` —— 环上永远出不来 ⇒ **校验器卡死而不是报错**，
    #   于是"刀到底抓到没有"根本读不出来（反证跑成一坨超时）。坏数据下必须**报错**，不许**卡死**。
    depth = {}
    for n in ALL_NODES:
        d, cur, walk = 0, n, set()
        while cur in par and cur not in walk:
            walk.add(cur)
            d += 1
            cur = par[cur]
        if cur in walk or d > len(ALL_NODES):
            depth[n] = -1          # 环上：B3 已经会报，这里不再假装算得出深度
        else:
            depth[n] = d
    deepest = max([v for v in depth.values() if v >= 0] or [0])
    check(u"B7 树深 %d（≥4 层，说明不是一条平铺的链）" % deepest, deepest >= 4)
    check(u"B8 没有节点处在环上（深度算得出来）",
          all(v >= 0 for v in depth.values()),
          u"%s" % [k for k, v in depth.items() if v < 0])

    # ============ C 判据 / 图标 ============
    ids = mod_ids()
    for n in ALL_NODES:
        o = adv.get(n)
        if o is None:
            continue
        icon = o["display"]["icon"]["id"]
        check(u"C1 %s 的图标 id 带本模组命名空间" % n, icon.startswith("potato_s_t:"))
        check(u"C2 %s 的图标物品在盘上注册（%s）" % (n, icon), icon.split(u":", 1)[1] in ids)
        ci = crit_items(o)
        check(u"C3 %s 的判据至少点了一个物品" % n, len(ci) > 0)
        for i in ci:
            check(u"C4 %s 的判据物品 %s 在盘上注册" % (n, i), i in ids)
        check(u"C5 %s 的图标 ∈ 判据物品（拿到就会亮）" % n, icon.split(u":", 1)[1] in ci)
        trig = set(c["trigger"] for c in o["criteria"].values())
        check(u"C6 %s 的触发器都在白名单内（%s）" % (n, ",".join(sorted(trig))),
              trig <= set(["minecraft:inventory_changed", "minecraft:placed_block"]))
        if n in ("clean_energy",):
            eq(u"C7 clean_energy 用 placed_block", set(["minecraft:placed_block"]), trig)
    # 「和」与「或」的写法
    o = adv.get("gas_handling", {})
    eq(u"C8 gas_handling 是两条判据、两条 requirement（真「和」）",
       (2, 2), (len(o.get("criteria", {})), len(o.get("requirements", []))))
    o = adv.get("pressing", {})
    eq(u"C9 pressing 是 7 条判据 + 1 条 requirement 组（原版的「或」写法）",
       (7, 1), (len(o.get("criteria", {})), len(o.get("requirements", []))))
    eq(u"C10 pressing 那条组里装着全部 7 条判据", sorted(o["criteria"]),
       sorted(o["requirements"][0]))
    # ⚠ 本轮探针抓到的真雷：`conditions.items` 里的多个谓词是**「与」**，
    #   所以「任意一种板子」绝不能写成"一个判据 + 多个谓词"。这条断言把规矩钉住。
    multi = [(n, k) for n in ALL_NODES for k, c in adv.get(n, {}).get("criteria", {}).items()
             if len(c.get("conditions", {}).get("items", [])) > 1]
    eq(u"C14 没有「一个判据塞多个物品谓词」的写法（那是「与」不是「或」）", [], multi)
    shape = dict((n, (len(adv.get(n, {}).get("criteria", {})),
                      len(adv.get(n, {}).get("requirements", [])))) for n in ALL_NODES)
    eq(u"C15 「或」型的 5 条都是「多判据 + 1 个组」",
       dict((n, (len(adv[n]["criteria"]), 1)) for n in
            ("crushing", "pressing", "wiring", "titanium_tools", "fuel")),
       dict((n, shape[n]) for n in ("crushing", "pressing", "wiring", "titanium_tools", "fuel")))
    eq(u"C16 「与」型的 2 条都是「每条判据各占一个组」",
       dict((n, (2, 2)) for n in ("gas_handling", "stronger_power")),
       dict((n, shape[n]) for n in ("gas_handling", "stronger_power")))
    o = adv.get("oil", {})
    pred = o["criteria"]["oil"]["conditions"]["items"][0]
    eq(u"C11 oil 认的确实是油桶", "potato_s_t:oil_bucket", pred.get("items"))
    eq(u"C12 oil 带 custom_data 子谓词（空桶不算）", "minecraft:custom_data",
       list(pred.get("predicates", {}).keys())[0] if pred.get("predicates") else None)
    eq(u"C13 oil 的子谓词里写的是原油", "potato_s_t:crude_oil",
       pred.get("predicates", {}).get("minecraft:custom_data", {}).get("fluid", {}).get("id"))

    # ============ D 只动该动的（拿改前件比） ============
    for n in ("clean_energy", "stronger_power"):
        old = json.loads(read(os.path.join(BK, r"src\main\resources\data\potato_s_t\advancement", n + u".json")))
        new = adv[n]
        o2, n2 = dict(old), dict(new)
        o2.pop("parent", None)
        n2.pop("parent", None)
        eq(u"D1 %s 除了父链一个字段没动" % n, o2, n2)
    old_root = json.loads(read(os.path.join(BK, r"src\main\resources\data\potato_s_t\advancement",
                                            u"new_beginning.json")))
    new_root = adv["new_beginning"]
    eq(u"D2 根节点的判据换成微型粉碎机", "potato_s_t:micro_crusher",
       new_root["criteria"]["got"]["conditions"]["items"][0]["items"])
    eq(u"D3 根节点的图标换成微型粉碎机", "potato_s_t:micro_crusher",
       new_root["display"]["icon"]["id"])
    eq(u"D4 根节点的背景图与标题键没动",
       (old_root["display"]["background"], old_root["display"]["title"]),
       (new_root["display"]["background"], new_root["display"]["title"]))
    eq(u"D5 根节点的 frame/hidden 没动",
       (old_root["display"]["frame"], old_root["display"]["hidden"]),
       (new_root["display"]["frame"], new_root["display"]["hidden"]))
    for n in NEW_NODES:
        check(u"D6 %s.json 是本轮新建的（改前件里没有）" % n,
              not os.path.exists(os.path.join(BK, r"src\main\resources\data\potato_s_t\advancement",
                                              n + u".json")))

    # ============ E 四语言 ============
    lang, counts = {}, {}
    for l in LANGS:
        lang[l] = json.loads(read(os.path.join(LANG, l + u".json")))
        counts[l] = len(lang[l])
    eq(u"E1 四语言键数（每份 %d）" % EXPECT_KEYS, [EXPECT_KEYS] * 4,
       [counts[l] for l in LANGS])
    base = set(lang["zh_cn"].keys())
    for l in LANGS[1:]:
        eq(u"E2 %s 的键集合与 zh_cn 完全一致" % l, set(), base ^ set(lang[l].keys()))
    empty = [(l, k) for l in LANGS for k in lang[l]
             if k.startswith(u"advancements.") and not lang[l][k].strip()]
    eq(u"E3 成就文案没有空值", [], empty)
    miss = [(l, k) for l in LANGS for n in ALL_NODES
            for k in ("advancements.potato_s_t.%s.title" % n, "advancements.potato_s_t.%s.description" % n)
            if k not in lang[l]]
    eq(u"E4 27 个节点 × 标题/说明 × 四语言 = 216 条齐全", [], miss)
    # 与改前件比。⚠ 这棵树是**两条线共用的**：并行那条（盔甲）在本轮进行中又润色过
    #   `tooltip.potato_s_t.star_steel_set`（四语言，19:55 那次写入）—— 那是它的地盘，
    #   不是我的。所以严格判据只覆盖 `advancements.*` 这一片（本轮的地盘），
    #   其它键的改动**只报不改判**，但必须保证"不是本轮新加的那 48 个"。
    MY_KEYS = set("advancements.potato_s_t.%s.%s" % (n, f)
                  for n in ALL_NODES for f in ("title", "description"))
    for l in LANGS:
        old = json.loads(read(os.path.join(BK, r"src\main\resources\assets\potato_s_t\lang", l + u".json")))
        added = [k for k in lang[l] if k not in old]
        removed = [k for k in old if k not in lang[l]]
        changed = [k for k in old if k in lang[l] and old[k] != lang[l][k]]
        mine_add = [k for k in added if k.startswith(u"advancements.")]
        other_add = [k for k in added if not k.startswith(u"advancements.")]
        eq(u"E5 %s：本轮新增的成就键正好 %d 个" % (l, NEW_KEYS), NEW_KEYS, len(mine_add))
        eq(u"E6 %s：没有键被删掉" % l, [], removed)
        eq(u"E7 %s：advancements.* 里只有根节点说明这 1 处被改值" % l,
           [u"advancements.potato_s_t.new_beginning.description"],
           [k for k in changed if k.startswith(u"advancements.")])
        eq(u"E8 %s：本轮新加的键没被别的东西改过（根节点说明是本轮自己要改的那一条）" % l, [],
           [k for k in changed + other_add if k in MY_KEYS
            and k != u"advancements.potato_s_t.new_beginning.description"])
        if other_add or [k for k in changed if not k.startswith(u"advancements.")]:
            print(u"   （%s：非本轮改动 —— 新增 %s，改值 %s）"
                  % (l, other_add, [k for k in changed if not k.startswith(u"advancements.")]))
    # 引号纪律 + 翻译纪律
    quote = [(l, k) for l in LANGS for k in lang[l]
             if k.startswith(u"advancements.") and u'"' in lang[l][k]]
    eq(u"E9 成就文案里没有 ASCII 双引号（中文串一律用「」）", [], quote)
    same = [n for n in ALL_NODES
            if lang["zh_cn"]["advancements.potato_s_t.%s.title" % n]
            == lang["ru_ru"]["advancements.potato_s_t.%s.title" % n]]
    eq(u"E10 没有「俄语标题照抄中文」的节点", [], same)
    same2 = [n for n in ALL_NODES
             if lang["zh_cn"]["advancements.potato_s_t.%s.title" % n]
             == lang["en_us"]["advancements.potato_s_t.%s.title" % n]]
    eq(u"E11 没有「英文标题照抄中文」的节点", [], same2)

    # ============ F 文档 / 工具 ============
    doc = read(DOC)
    check(u"F1 档案里有 §5 的 ZF107 行", u"| ZF107 |" in doc)
    check(u"F2 档案里有 §9 的 ZF107 小节", u"ZF107（0.11）" in doc)
    check(u"F3 档案里写明 %d 键" % EXPECT_KEYS, u"%d 键" % EXPECT_KEYS in doc)
    check(u"F4 档案里写明 24 份/24 条新成就",
          u"24 份" in doc or u"24 条新的" in doc)
    en = read(DOC_EN)
    check(u"F5 英文公告的键数跟到 %d" % EXPECT_KEYS, u"%d keys each" % EXPECT_KEYS in en)
    check(u"F6 英文公告提到成就/进度", u"dvancement" in en)
    # 活体数字：往轮校验器里不该再有 350 这个旧值
    # ⚠ 第一版这里把"要找的旧值"写成了新值 398（我自己的 slip），于是把 16 份
    #   已经改好的校验器全报成"残留旧值" —— 检查会失败是好事，但它失败的理由必须是对的。
    stale = []
    for f in sorted(os.listdir(TOOLS)):
        if not f.endswith(u".py") or f.startswith(u"_zf107"):
            continue
        if not re.match(r"^_zf\d+_(verify|repro|recipe_guard|gatecount)\.py$", f):
            continue
        if f in (u"_zf104_verify.py",):      # ZF104 那份本来就刻意不写死数字
            continue
        t = read(os.path.join(TOOLS, f))
        if re.search(r"\b350\b", t):
            stale.append(f)
    eq(u"F7 往轮校验器里没有残留旧键数 350", [], stale)

    print(u"通过 = %d   失败 = %d" % (n_pass, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
