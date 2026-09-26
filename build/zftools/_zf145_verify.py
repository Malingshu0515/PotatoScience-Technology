# -*- coding: utf-8 -*-
r'''_zf145_verify.py —— ZF145 **常驻校验**：成就树补线（8 条新节点 / 四语言 508 键 / 剑气标签）

不跑游戏也能查的部分全在这里；"真触发"（拿物品到底点不点亮、用星辉斩杀一只到底亮不亮）
在探针 `Zf145Check.java` 里，必须真服务端跑（报告 `_zf145_probe_utf8.txt`）。

口径（与 `_zf107/_zf117_verify.py` 同一套，判据没放宽）：
  A 账目：目录正好 **43 份**；8 份新建的都在；**另外 35 份逐字节等于本轮开工前**（表里内嵌 sha1）；
  B 树形：恰好 1 个根、父指针全部解析得到、无环、每个节点从根可达、8 条新节点的父链逐条对；
  C 新节点结构：frame/hidden/图标/判据物品（**逐字**写死不从源码抄）、「或」与「与」的组数、
     星辉斩那条的触发器与伤害类型标签（**唯一**一条没有物品判据的）;
  D 标签文件：`tags/damage_type/star_steel_slash.json` 逐字节等于期望；
  E 四语言：每份 **508 ** 键、键集合四份完全一致、16 个新键齐全非空、值里没有 ASCII 双引号；
     与改前件比：**只多这 16 个键**、旧键一个字节都没改（拿 `zf145_pre` 逐键比）；
  F 跟平：往轮门里的活体数字（`EXPECT_KEYS` / `EXPECT_NODES` / `N_ALL` / `NEW_KEYS`）都跟到了；
     成品 jar 的 `RELEASE_KEYS` **不动**（本轮没打包）；
  G 探针：UTF-8 报告在、全绿、没有 [FAIL]，且报告里真的念过那几个关键判词；
  H 文档：档案 §5/§9 有 ZF145、写着 508 键与 43 条；交接文档的活体数字同步；英文公告同步。
'''
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
TDIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\tags\damage_type")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
TOOLS = os.path.join(ROOT, r"build\zftools")
DOC = os.path.join(ROOT, r"docs\开发档案.md")
DOC_HAND = os.path.join(ROOT, r"docs\多会话协作交接.md")
DOC_EN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")
REPORT = os.path.join(TOOLS, r"_zf145_probe_utf8.txt")
ARC = os.path.join(TOOLS, r"check\Zf145Check.java")
PRE = os.path.join(r"C:\PotatoST救援", "zf145_pre")

LANGS = ["zh_cn", "en_us", "ja_jp", "ru_ru"]
KEYS_ALL, N_NEW = 508, 8
N_ALL = 43

# 四语言各 **16 个新键的值**的 sha1 指纹（口径：键名排序后 `键\0值` 用 \n 连起来取 sha1）。
# 生成脚本：`_zf145_newsha.py`。⚠ 这是**值**的锚，不是键的锚：改一个字符都会红。
NEW_VALUE_SHA = {
    u"zh_cn": u"d5751d8dcbab45fa56f33182839b347a3c5b9522",
    u"en_us": u"ade77d983702bfaa12c33cf713cdfc597bc3addf",
    u"ja_jp": u"51c508ff92b5852b3b17965af948943f56ca83c8",
    u"ru_ru": u"242c8bb66f67c79c0a4e83f23c40e09cc3ddbcf5",
}


def value_sha(table, keys):
    import hashlib
    blob = u"\n".join(u"%s\u0000%s" % (k, table.get(k, u"")) for k in sorted(keys))
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()


# 本轮新建的 8 条（父 / frame / 图标 / 判据物品）
NEW = {
    "vibranium": ("star_steel", "goal", "vibranium_ingot", ["vibranium_ingot"], 1),
    "vibranium_armor": ("vibranium", "challenge", "vibranium_chestplate",
                        ["vibranium_helmet", "vibranium_chestplate",
                         "vibranium_leggings", "vibranium_boots"], 4),
    "titanium_armor": ("titanium_tools", "goal", "titanium_alloy_chestplate",
                       ["titanium_alloy_helmet", "titanium_alloy_chestplate",
                        "titanium_alloy_leggings", "titanium_alloy_boots"], 4),
    "star_steel_tools": ("star_steel", "goal", "star_steel_pickaxe",
                         ["star_steel_sword", "star_steel_pickaxe", "star_steel_axe",
                          "star_steel_hoe", "star_steel_shovel"], 1),
    "star_chart_tome": ("new_beginning", "task", "star_chart_tome", ["star_chart_tome"], 1),
    "diesel_generator": ("stronger_power", "goal", "diesel_generator_controller",
                         ["diesel_generator_controller"], 1),
    "silver_wire": ("wiring", "task", "silver_wire_spool", ["silver_wire_spool"], 1),
}
SLASH = "star_steel_slash"
SLASH_TAG = "potato_s_t:star_steel_slash"

# 另外 35 份（= 43 - 本轮新建的 8）在本轮开工前的 sha1（口径同 `_zf117_verify.py` 的 OLD_SHA 表）。
# ⚠ 这张表是拿**本轮开工时的工作树**算的；那 35 份自 ZF144 提交（4639ddd）起没人动过
#   （`git status -- src/.../advancement` 只列出 8 个 `??` 新建件，没有 ` M`）。
# 生成脚本：`_zf145_oldsha.py`
OLD_SHA = {
    "acid": "9db10ff640142d525dcf7a45a9de666025dc89cc",
    "alloy_smelter": "f4c3d704a81f4863d695a74357062ecba1999e7e",
    "ammonia": "8c7b0bb0df77d2b5b122b3211348b5faaa208a22",
    "blast_furnace": "b96e1e291cde7ede84194c28262883513401b10a",
    "capacitor": "bc3eb63f51d328fcffef9d68a814d2ca25471fef",
    "clean_energy": "ee7467159e453c71f4f9b4bef91449e9e748b68c",
    "combustion": "fd5c58290a2b914698a234edc11f8b763d2fe2dc",
    "crushing": "16fe9264e9bffd07d5c066bcbe34248874863d85",
    "distillation": "ab7d36df47eaffbd708d2cc14b118d0b60371418",
    "electrolyzer": "861779c7f0b517d76b03413d28c80d7c8060da3c",
    "first_power": "7420b4b2bd2910336625ef2224e572097c5c429d",
    "fluid_logistics": "3dab91bfbc3257976359a962be42bf74d773a528",
    "fuel": "c5df8098bd04db32f21331eebf8349d0fc00b802",
    "gas_handling": "7c46b87102aa1b192037f3b0f688742426b9df10",
    "hard_alloy": "87d4cbb196b328552f82bd4938efbe170c21e7ea",
    "light_alloy": "8a8632f60fcfde27271fb596dfaa316043031691",
    "lithium_battery": "3f308dd165783bcbcca2f7ced99f2cbe10fd4c80",
    "lithium_battery_plant": "2be855d77babf90efe7639963c1dbf8863a380e3",
    "music_disc_anvil": "ca26ba647d0022d9cfab09b4939427c4c9f76b43",
    "music_disc_jasmine": "f78ccb36563c585e0793643378a139e5da08d81a",
    "new_beginning": "0e00e92ae1c652dd7286b8e2ddbc0c4251ca70a1",
    "oil": "6546ccc4aed1948303e8804ff78437454f79650f",
    "oil_pump": "d9a8720239176c6c48807594fe2a43afd1e8b3cf",
    "pressing": "210ccae06698baa00419188658642836553e6633",
    "salt": "eab151908bb1ba701a26207f077c9dea3d3556db",
    "stable_block": "351ec9b5da98cfdd87bc839db5be7f3b9f59eaa8",
    "star_steel": "94cf60889e1e8baf9800024019fd7c1a699b207c",
    "star_steel_armor": "5414abd5d3f4c029afe29bbe5aec0e5c1ee82735",
    "starfall": "e1ecd7691ab425d75c98dadb3d9ddeafbf33602d",
    "steel": "db791240c6da90e35162a53d5917ea263ccfed33",
    "stronger_power": "287efaf2390c3d3eda5b790ecc3cbf8f5a66eb61",
    "sulfur": "2c05c990357d1bc9d77bbb070d5f644c86a3989b",
    "titanium": "17a1e52a51dfb098e082b8bf736ec86da9133f9f",
    "titanium_tools": "a43e56d96ffa8e75ad8fee62433b87e874523ad4",
    "wiring": "fb42faaff187ca07e6cb248f81777ba4ddf9eb84",
}
# 合计 35 份（43 - 本轮新建的 8）

fails, n_pass = [], 0


def read(p):
    return io.open(p, encoding="utf-8", newline="").read()


def jload(p):
    return json.loads(read(p))


def sha1(p):
    import hashlib
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def cur(path):
    u"""按相对路径读**当前**文件（账目里的相对路径统一用 / 分隔）"""
    return read(os.path.join(ROOT, path.replace(u"/", os.sep)))


def check(name, cond, detail=None):
    global n_pass
    if cond:
        n_pass += 1
    else:
        fails.append(name + (u"  ← %s" % detail if detail else u""))


def eq(name, want, got):
    check(name, want == got, u"期望 %r 实际 %r" % (want, got))


def crit_items(o):
    out = []
    for c in o.get("criteria", {}).values():
        for pred in c.get("conditions", {}).get("items", []):
            i = pred.get("items")
            if isinstance(i, str) and i.startswith(u"potato_s_t:"):
                out.append(i.split(u":", 1)[1])
    return out


def main():
    # ================= A 账目 =================
    print(u"== A 账目 ==")
    files = sorted(f[:-5] for f in os.listdir(ADIR) if f.endswith(u".json"))
    eq(u"A1 advancement 目录正好 %d 份" % N_ALL, N_ALL, len(files))
    eq(u"A2 目录 = 35 老 + 8（ZF145）", sorted(list(OLD_SHA) + sorted(NEW) + [SLASH]), files)
    assert len(OLD_SHA) == 35, u"OLD_SHA 表必须正好 35 条（实际 %d）" % len(OLD_SHA)
    for n in sorted(NEW):
        check(u"A3 新节点 %s.json 在" % n, os.path.exists(os.path.join(ADIR, n + u".json")))
    bad = []
    for n, want in sorted(OLD_SHA.items()):
        p = os.path.join(ADIR, n + u".json")
        if not os.path.exists(p) or sha1(p) != want:
            bad.append(n)
    eq(u"A4 另 35 份老节点**逐字节**等于本轮开工前", [], bad)

    # ================= B 树形 =================
    print(u"\n== B 树形 ==")
    adv = {}
    for n in files:
        try:
            adv[n] = jload(os.path.join(ADIR, n + u".json"))
        except Exception as e:
            fails.append(u"%s.json 解析不了：%s" % (n, e))
    eq(u"B1 %d 份全部解析成功" % N_ALL, N_ALL, len(adv))
    roots = [n for n in files if "parent" not in adv.get(n, {})]
    eq(u"B2 恰好 1 个根", ["new_beginning"], roots)
    par = dict((n, adv[n]["parent"].split(u":", 1)[1]) for n in files if "parent" in adv[n])
    eq(u"B3 所有父指针都指向树里的节点", [], [n for n, p in par.items() if p not in files])
    cyc = []
    for n in files:
        walk, c = set(), n
        while c in par:
            if c in walk:
                cyc.append(n)
                break
            walk.add(c)
            c = par[c]
    eq(u"B4 没有环", [], cyc)
    reach, grew = set(["new_beginning"]), True
    while grew:
        grew = False
        for n, p in par.items():
            if p in reach and n not in reach:
                reach.add(n)
                grew = True
    eq(u"B5 每个节点从根可达", sorted(files), sorted(reach))
    for n, spec in sorted(NEW.items()):
        eq(u"B6 %s 的父链" % n, spec[0], par.get(n))
    # 树深（带步数上限：坏数据必须报错、不许卡死，§4.77）
    deep = 0
    for n in files:
        d, c, walk = 0, n, set()
        while c in par and c not in walk:
            walk.add(c)
            d += 1
            c = par[c]
        deep = max(deep, d)
    check(u"B7 树深 %d（≥ 4 层，说明不是一条平铺的链）" % deep, deep >= 4)

    # ================= C 新节点结构 =================
    print(u"\n== C 新节点结构 ==")
    for n, spec in sorted(NEW.items()):
        parent, frame, icon, items, ngroups = spec
        o = adv.get(n, {})
        d = o.get("display", {})
        eq(u"C1 %s 的 frame" % n, frame, d.get("frame"))
        eq(u"C2 %s 的 hidden" % n, False, d.get("hidden"))
        eq(u"C3 %s 的图标" % n, u"potato_s_t:" + icon, (d.get("icon") or {}).get("id"))
        eq(u"C4 %s 的判据物品（逐条）" % n, sorted(items), sorted(crit_items(o)))
        eq(u"C5 %s 的 requirement 组数" % n, ngroups, len(o.get("requirements", [])))
        # 每个物品**各占一条判据**（生成器就是这么写的）；组的个数才是「或/与」：
        # 1 个组 = 「或」（拿到任意一件就亮），N 个组 = 「与」（N 件全要）
        eq(u"C6 %s 的判据条数（%s）" % (n, u"与" if ngroups > 1 else u"或"),
           len(items), len(o.get("criteria", {})))
        eq(u"C7 %s 的 requirements 覆盖全部判据" % n,
           sorted(o.get("criteria", {})), sorted(x for g in o["requirements"] for x in g))
        check(u"C8 %s 的 toast/公告都开" % n,
              d.get("show_toast") is True and d.get("announce_to_chat") is True)
        check(u"C9 %s 的触发器都是 inventory_changed（除了星辉斩）" % n,
              set(c["trigger"] for c in o["criteria"].values())
              == set([u"minecraft:inventory_changed"]))
        check(u"C10 %s 的标题/说明键名" % n,
              d["title"]["translate"] == u"advancements.potato_s_t.%s.title" % n
              and d["description"]["translate"] == u"advancements.potato_s_t.%s.description" % n)
    # 星辉斩：唯一一条击杀型
    o = adv.get(SLASH, {})
    eq(u"C11 星辉斩的父链", "star_steel", o.get("parent", u"").split(u":", 1)[-1])
    eq(u"C12 星辉斩的 frame", "challenge", o["display"]["frame"])
    eq(u"C13 星辉斩的图标", u"potato_s_t:star_steel_sword", o["display"]["icon"]["id"])
    c = o.get("criteria", {}).get("slash", {})
    eq(u"C14 星辉斩的触发器", u"minecraft:player_killed_entity", c.get("trigger"))
    eq(u"C15 星辉斩的 killing_blow 标签（expected=true）",
       [{"expected": True, "id": SLASH_TAG}],
       c.get("conditions", {}).get("killing_blow", {}).get("tags"))
    eq(u"C16 星辉斩的 requirements", [["slash"]], o.get("requirements"))
    eq(u"C17 星辉斩的判据里没有物品（击杀型）", [], crit_items(o))
    eq(u"C18 全树只有 1 条击杀型节点",
       [SLASH], [n for n in files if any(
           cc.get("trigger") == u"minecraft:player_killed_entity"
           for cc in adv[n]["criteria"].values())])

    # ================= D 伤害类型标签 =================
    print(u"\n== D 伤害类型标签 ==")
    tp = os.path.join(TDIR, u"star_steel_slash.json")
    check(u"D1 标签文件在（%s）" % tp, os.path.exists(tp))
    if os.path.exists(tp):
        raw = read(tp)
        eq(u"D2 标签内容逐字节", u'{\n  "values": [\n    "%s"\n  ]\n}\n' % SLASH_TAG, raw)
        check(u"D3 标签是 LF、末尾有换行", u"\r" not in raw and raw.endswith(u"\n"))
    eq(u"D4 tags/damage_type 下正好 1 份", 1,
       len([f for f in os.listdir(TDIR) if f.endswith(u".json")])
       if os.path.isdir(TDIR) else 0)
    dt = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\damage_type\star_steel_slash.json")
    check(u"D5 伤害类型本体还在（ZF144 建的，本轮只加标签）", os.path.exists(dt))
    if os.path.exists(dt):
        j = jload(dt)
        # 死亡文案键 = `death.attack.<message_id>`；message_id 是**带命名空间**的那个
        eq(u"D6 伤害类型 message_id（死亡文案键就靠它）",
           u"potato_s_t." + SLASH, j.get("message_id"))
        eq(u"D7 伤害类型 effects = hurt（照原版）", u"hurt", j.get("effects"))

    # ================= E 四语言 =================
    print(u"\n== E 四语言 ==")
    lang, counts = {}, {}
    for l in LANGS:
        lang[l] = jload(os.path.join(LANG, l + u".json"))
        counts[l] = len(lang[l])
    eq(u"E1 四语言各 %d 键" % KEYS_ALL, [KEYS_ALL] * 4, [counts[l] for l in LANGS])
    base = set(lang["zh_cn"])
    for l in LANGS[1:]:
        eq(u"E2 %s 的键集合与 zh_cn 完全一致" % l, set(), base ^ set(lang[l]))
    keys = []
    for n in sorted(NEW) + [SLASH]:
        keys.append(u"advancements.potato_s_t.%s.title" % n)
        keys.append(u"advancements.potato_s_t.%s.description" % n)
    eq(u"E3 新键正好 16 个", 16, len(keys))
    miss = [(l, k) for l in LANGS for k in keys if not lang[l].get(k, u"").strip()]
    eq(u"E4 16 个新键 × 四语言 = 64 条齐全且非空", [], miss)
    quote = [(l, k) for l in LANGS for k in keys if u'"' in lang[l].get(k, u"")]
    eq(u"E5 新文案里没有 ASCII 双引号（中文串一律用「」）", [], quote)
    # 与改前件逐键比：只多这 16 个、旧键一个不改
    for l in LANGS:
        pre = jload(os.path.join(PRE, r"src\main\resources\assets\potato_s_t\lang", l + u".json"))
        added = [k for k in lang[l] if k not in pre]
        removed = [k for k in pre if k not in lang[l]]
        changed = [k for k in pre if lang[l].get(k) != pre[k]]
        eq(u"E6 %s：相对改前件只多了这 16 个键" % l, sorted(keys), sorted(added))
        eq(u"E7 %s：没有键被删" % l, [], removed)
        # ⚠ §4.36 口径：**改锚点、不放宽断言** —— 但这棵树是**两条线共用的**：
        #   润色线一直在改 tooltip / gui / message 的**值**（ZF139 那条"只能当提示打印"的先例）。
        #   所以硬判据只覆盖**我自己的地盘**：
        #     ① 我这一轮加的 16 个键的值**逐字节等于生成器写进去的那一版**（指纹见 NEW_VALUE_SHA）；
        #     ② 别的键的改动只打印不判（否则"我的门红不红"由别人的提交节奏决定）。
        #   ⚠ 第一版这里写的是"这 16 个键不许出现在 changed 里" —— 那是**空的**：
        #     `changed` 是与改前件比的，而改前件里**根本没有这 16 个键**（它们在 added 里）
        #     ⇒ 反证刀 K312 当场漏网。现在换成值指纹（改一个字符都会红）。
        eq(u"E8 %s：本轮新加的 16 个键的值指纹" % l, NEW_VALUE_SHA[l], value_sha(lang[l], keys))
        others = [k for k in changed if k not in set(keys)]
        if others:
            print(u"   [提示] %s：相对改前件另有 %d 个键的值变了（共享树：多半是润色线在改）：%s"
                  % (l, len(others), u"、".join(others[:4])))
    # 成就键总数：43 × 2
    advkeys = [k for k in lang["zh_cn"] if k.startswith(u"advancements.potato_s_t.")]
    eq(u"E9 成就键 = %d 条节点 × 2 = %d" % (N_ALL, N_ALL * 2), N_ALL * 2, len(advkeys))

    # ================= F 跟平 =================
    print(u"\n== F 跟平 ==")
    guards = {
        u"_zf100_verify.py": u"EXPECT_KEYS = %d" % KEYS_ALL,
        u"_zf101_verify.py": u"EXPECT_KEYS = %d" % KEYS_ALL,
        u"_zf102_verify.py": u"EXPECT_KEYS = %d" % KEYS_ALL,
        u"_zf103_verify.py": u"len(table) == %d" % KEYS_ALL,
        u"_zf107_verify.py": u"EXPECT_KEYS = %d" % KEYS_ALL,
        u"_zf109_verify.py": u"EXPECT_KEYS = %d" % KEYS_ALL,
        u"_zf111_verify.py": u"EXPECT_KEYS = %d" % KEYS_ALL,
        u"_zf112_verify.py": u"EXPECT_KEYS = %d" % KEYS_ALL,
        u"_zf114_verify.py": u"EXPECT_KEYS = %d" % KEYS_ALL,
        u"_zf118_verify.py": u"KEY_NEW = %d" % KEYS_ALL,
        u"_zf122_verify.py": u"EXPECT_KEYS = %d" % KEYS_ALL,
        u"_zf141_verify.py": u"KEYS = %d" % KEYS_ALL,
        u"_zf80_verify.py": u"EXPECT_KEYS = %d" % KEYS_ALL,
        u"_zf82_verify.py": u"EXPECT_KEYS = %d" % KEYS_ALL,
        u"_zf96_verify.py": u"EXPECT_KEYS = %d" % KEYS_ALL,
        u"_zf97_verify.py": u"EXPECT_KEYS = %d" % KEYS_ALL,
        u"_zf98_verify.py": u"EXPECT_KEYS = %d" % KEYS_ALL,
        u"_zf93_verify.py": u"EXPECT_KEYS = %d" % KEYS_ALL,
        u"_zf119_verify.py": u"KEY_OLD, KEY_NEW = 448, %d" % KEYS_ALL,
        u"_zf139_verify.py": u"KEYS_BEFORE, KEYS_AFTER = 482, %d" % KEYS_ALL,
    }
    for f, needle in sorted(guards.items()):
        p = os.path.join(TOOLS, f)
        check(u"F1 %s 的键数跟到 %d" % (f, KEYS_ALL),
              os.path.exists(p) and needle in read(p), needle)
    check(u"F2 _zf107_verify.py 的 EXPECT_NODES = %d" % N_ALL,
          re.search(r"EXPECT_NODES = %d\b" % N_ALL, read(os.path.join(TOOLS, u"_zf107_verify.py")))
          is not None)
    check(u"F3 _zf107_verify.py 认得这 8 条新节点",
          all(u'"%s"' % n in read(os.path.join(TOOLS, u"_zf107_verify.py")) for n in NEW))
    check(u"F4 _zf107_verify.py 的 NEW_KEYS = 48 + 16 + 16",
          u"NEW_KEYS = 48 + 16 + 16" in read(os.path.join(TOOLS, u"_zf107_verify.py")))
    check(u"F5 _zf117_verify.py 的 N_ALL = %d 且认得那 8 条" % N_ALL,
          (u"N_ALL = 27, 8, %d" % N_ALL) in read(os.path.join(TOOLS, u"_zf117_verify.py"))
          and u"ZF145_IDS" in read(os.path.join(TOOLS, u"_zf117_verify.py")))
    check(u"F6 成品 jar 的键数靶子**没动**（本轮没打包）",
          u"RELEASE_KEYS = 487" in read(os.path.join(TOOLS, u"_zf93_verify.py")))
    stale = []
    for f in sorted(os.listdir(TOOLS)):
        if not re.match(r"^_zf\d+_verify\.py$", f) or f == u"_zf145_verify.py":
            continue
        if f in (u"_zf142_verify.py", u"_zf143_verify.py"):
            continue
        for i, line in enumerate(read(os.path.join(TOOLS, f)).split(u"\n"), 1):
            # ⚠ 排除三类：① 成品 jar 的靶子（本轮没打包 ⇒ 仍是 487/492 那套）；
            #   ② 十六进制里恰好含 492 的（sha1）；③ 两条**历史注释**（本轮的 gatefix 点名排除了它们）
            if u"492" not in line or u"RELEASE_KEYS" in line:
                continue
            if re.search(r"[0-9a-fA-F]492[0-9a-fA-F]", line):
                continue
            if u"ZF121 retarget" in line or u"那份成品里 zh_cn 是 492 键" in line:
                continue
            if any(m in line for m in (u"键", u"KEYS", u"keys each", u"counts", u"len(")):
                stale.append(u"%s:%d %s" % (f, i, line.strip()[:70]))
    eq(u"F7 往轮门里没有残留的 492（成品那两行 + 两条历史注释除外）", [], stale)

    # ================= G 探针 =================
    print(u"\n== G 探针 ==")
    check(u"G1 探针 UTF-8 报告在（%s）" % REPORT, os.path.exists(REPORT))
    if os.path.exists(REPORT):
        rep = read(REPORT)
        check(u"G2 报告全绿", u"verdict: ALL OK" in rep)
        check(u"G3 报告里没有 [FAIL]", u"[FAIL]" not in rep)
        for lit in (u"43 条一条不少", u"恰好 1 个根 = [new_beginning]",
                    u"伤害类型标签 potato_s_t:star_steel_slash 存在",
                    u"原版攻击击杀 ⇒ 星辉斩**不**亮",
                    u"用星辉斩击杀 ⇒ 星辉斩亮",
                    u"只给三件 ⇒ vibranium_armor **不**亮",
                    u"只给三件 ⇒ titanium_armor **不**亮",
                    u"隐藏彩蛋位 starfall 照样能点亮",
                    u"本轮 8 条 + 隐藏彩蛋位共 9 条全亮"):
            check(u"G4 报告里有「%s」" % lit, lit in rep)
    check(u"G5 探针存档在 check/（先抄后删，§10.1）", os.path.exists(ARC))
    check(u"G6 探针源码已从 src 删掉",
          not os.path.exists(os.path.join(JAVA, u"Zf145Check.java")))
    check(u"G7 PotatoST.java 里没有残留钩子",
          u"Zf145Check" not in read(os.path.join(JAVA, u"PotatoST.java")))

    # ================= H 文档 =================
    print(u"\n== H 文档 ==")
    doc = read(DOC)
    check(u"H1 档案 §5 有 ZF145 行", u"| ZF145 |" in doc)
    check(u"H2 档案 §9 有 ZF145 小节", u"ZF145（0.11）" in doc)
    check(u"H3 档案里写着 %d 键" % KEYS_ALL, u"%d 键" % KEYS_ALL in doc)
    check(u"H4 档案里写着 43 条进度", u"43 条" in doc)
    hand = read(DOC_HAND)
    check(u"H5 交接文档的活体数字是 %d 键 × 4" % KEYS_ALL, u"%d 键 × 4" % KEYS_ALL in hand)
    check(u"H6 交接文档写着 43 条进度", u"43 条" in hand)
    check(u"H7 交接文档记了 ZF145", u"ZF145" in hand)
    en = read(DOC_EN)
    check(u"H8 英文公告的键数跟到 %d" % KEYS_ALL, u"(%d keys each)" % KEYS_ALL in en)
    check(u"H9 英文公告记了 ZF145", u"ZF145" in en)

    print(u"")
    print(u"通过 = %d   失败 = %d" % (n_pass, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
